#!/usr/bin/env python3
"""Sync built Sharpee engine packages from the fork to game projects.

Copies dist/ files from /c/code/fork/sharpee/packages/*/ into
/c/code/sharpee/*/node_modules/@sharpee/*/ so game projects use
the latest engine build without waiting for an npm publish.

Usage:
    python tools/sync_fork.py                    # sync all packages to all projects
    python tools/sync_fork.py --project familyzoo  # sync to one project
    python tools/sync_fork.py --no-build         # skip browser rebuild after sync
    python tools/sync_fork.py --dry-run          # show what would be copied
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import output

# Defaults (override with env vars or CLI args)
# Resolve Git Bash paths (/c/code/...) to Windows (C:\code\...) on Windows
def _resolve_default(posix_path: str) -> Path:
    p = Path(posix_path)
    if not p.is_dir() and sys.platform == "win32" and posix_path.startswith("/"):
        # Convert /c/code/... → C:\code\...
        drive = posix_path[1].upper()
        win = f"{drive}:{posix_path[2:]}"
        p = Path(win)
    return p

DEFAULT_FORK_DIR = _resolve_default(os.environ.get("SHARPEE_FORK_DIR", "/c/code/fork/sharpee/packages"))
DEFAULT_WORKSPACE = _resolve_default(os.environ.get("SHARPEE_WORKSPACE", "/c/code/sharpee"))


def discover_projects(workspace: Path) -> list[Path]:
    """Find Sharpee game projects (dirs with package.json referencing @sharpee)."""
    projects = []
    for d in sorted(workspace.iterdir()):
        pkg = d / "package.json"
        if pkg.exists():
            try:
                data = json.loads(pkg.read_text(encoding="utf-8"))
                deps = data.get("dependencies", {})
                if any(k.startswith("@sharpee") for k in deps):
                    projects.append(d)
            except (json.JSONDecodeError, OSError):
                pass
    return projects


# Packages to skip — these have workspace-relative paths that break in npm layout
SKIP_PACKAGES = {"sharpee", "zifmia", "platform-cli-en-us", "platforms"}


def discover_fork_packages(fork_dir: Path) -> dict[str, Path]:
    """Find built fork packages (dirs with dist/), excluding workspace-only packages."""
    packages = {}
    for d in sorted(fork_dir.iterdir()):
        if d.is_dir() and (d / "dist").is_dir() and d.name not in SKIP_PACKAGES:
            packages[d.name] = d
    return packages


def sync_package(fork_pkg_dir: Path, target_dir: Path, dry_run: bool) -> bool:
    """Copy fork dist files into a project's node_modules package dir."""
    src = fork_pkg_dir / "dist"
    if not src.is_dir() or not target_dir.is_dir():
        return False

    if dry_run:
        return True

    # Copy all files from dist/ into the target (which IS the package root in node_modules)
    for item in src.iterdir():
        dest = target_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)
    return True


def main():
    parser = argparse.ArgumentParser(description="Sync Sharpee fork packages to game projects.")
    parser.add_argument("--project", help="Sync only this project (directory name)")
    parser.add_argument("--fork-dir", type=Path, default=DEFAULT_FORK_DIR, help="Fork packages dir")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE, help="Sharpee workspace dir")
    parser.add_argument("--no-build", action="store_true", help="Skip browser rebuild after sync")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied")
    args = parser.parse_args()

    fork_dir = args.fork_dir
    workspace = args.workspace

    if not fork_dir.is_dir():
        print(f"ERROR: Fork packages dir not found: {fork_dir}", file=sys.stderr)
        sys.exit(1)
    if not workspace.is_dir():
        print(f"ERROR: Sharpee workspace not found: {workspace}", file=sys.stderr)
        sys.exit(1)

    # Discover
    fork_packages = discover_fork_packages(fork_dir)
    projects = discover_projects(workspace)

    if args.project:
        projects = [p for p in projects if p.name == args.project]
        if not projects:
            print(f"ERROR: Project '{args.project}' not found in {workspace}", file=sys.stderr)
            sys.exit(1)

    print(f"=== Syncing fork packages ===")
    print(f"  Fork: {fork_dir}")
    print(f"  Projects: {', '.join(p.name for p in projects)}")
    print(f"  Packages: {len(fork_packages)} available")
    if args.dry_run:
        print(f"  Mode: DRY RUN")
    print()

    results = {}
    for proj in projects:
        print(f"=== {proj.name} ===")
        nm = proj / "node_modules" / "@sharpee"
        if not nm.is_dir():
            print(f"  SKIP: node_modules/@sharpee/ not found (run npm install first)")
            results[proj.name] = "skipped"
            continue

        synced = 0
        for pkg_name, fork_pkg_dir in fork_packages.items():
            target = nm / pkg_name
            if not target.is_dir():
                continue
            ok = sync_package(fork_pkg_dir, target, args.dry_run)
            if ok:
                action = "would sync" if args.dry_run else "synced"
                print(f"  @sharpee/{pkg_name} — {action}")
                synced += 1

        print(f"  {synced} packages {'would be ' if args.dry_run else ''}synced")

        # Rebuild browser bundle
        if not args.no_build and not args.dry_run and synced > 0:
            print(f"  Building browser bundle...")
            result = subprocess.run(
                ["npx", "sharpee", "build-browser"],
                cwd=str(proj),
                capture_output=True, text=True,
                timeout=120,
            )
            if result.returncode != 0:
                print(f"  WARNING: Build failed")
                for line in (result.stdout + result.stderr).strip().splitlines()[-3:]:
                    print(f"    {line}")
                results[proj.name] = "sync ok, build failed"
            else:
                # Extract bundle size
                for line in result.stdout.splitlines():
                    if "Bundle size" in line:
                        print(f"  {line.strip()}")
                        break
                results[proj.name] = "ok"
        else:
            results[proj.name] = "ok" if synced > 0 else "nothing to sync"
        print()

    # Summary
    print(f"=== Summary ===")
    for name, status in results.items():
        print(f"  {name}: {status}")


if __name__ == "__main__":
    main()
