#!/usr/bin/env python3
"""Build a Sharpee game and import into IF Hub.

Bridges the Sharpee authoring workspace (external npm project) and the
IF Hub project directory. Runs the npm build in the Sharpee source dir,
then imports the dist output into the ifhub project via setup_sharpee.

Usage:
    python tools/compile_sharpee.py <game-name>
    python tools/compile_sharpee.py <game-name> --force

The game's tests/project.conf must define:
    SHARPEE_DIR=<path to npm project>   (where npx sharpee build-browser runs)
    TITLE="Game Title"                  (for play.html <title>)
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import config, output, paths


def main():
    parser = argparse.ArgumentParser(description="Build a Sharpee game and import into IF Hub.")
    parser.add_argument("game", help="Game name (ifhub project directory under projects/)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing play.html")
    parser.add_argument("--no-test", action="store_true", help="Skip post-build validation")
    args = parser.parse_args()

    project_dir = paths.project_dir(args.game)
    if not project_dir.is_dir():
        print(f"ERROR: Project directory not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    # Read project.conf
    conf = config.parse_conf_fields(project_dir)
    sharpee_dir = conf.get("SHARPEE_DIR", "")
    title = conf.get("TITLE", args.game)

    if not sharpee_dir:
        print("ERROR: SHARPEE_DIR not set in tests/project.conf", file=sys.stderr)
        print("  Add: SHARPEE_DIR=/path/to/sharpee/project", file=sys.stderr)
        sys.exit(1)

    # Convert POSIX paths (/c/code/...) to Windows (C:\code\...) if needed
    if sharpee_dir.startswith("/"):
        sharpee_dir = paths.to_windows(sharpee_dir)
    sharpee_dir = Path(sharpee_dir)
    if not sharpee_dir.is_dir():
        print(f"ERROR: Sharpee source directory not found: {sharpee_dir}", file=sys.stderr)
        sys.exit(1)

    if not (sharpee_dir / "package.json").exists():
        print(f"ERROR: No package.json in {sharpee_dir} — not a valid npm project", file=sys.stderr)
        sys.exit(1)

    # --- Step 1: Install dependencies (if needed) ---
    # Detect workspace project (pnpm monorepo) vs standalone (npm)
    pkg_json = (sharpee_dir / "package.json").read_text(encoding="utf-8")
    is_workspace = "workspace:" in pkg_json

    if is_workspace:
        # Workspace project — install from monorepo root via pnpm
        workspace_root = sharpee_dir
        while workspace_root.parent != workspace_root:
            if (workspace_root / "pnpm-workspace.yaml").exists():
                break
            workspace_root = workspace_root.parent
        else:
            print("ERROR: workspace:* deps found but no pnpm-workspace.yaml in any parent", file=sys.stderr)
            sys.exit(1)

        node_modules = sharpee_dir / "node_modules"
        if not node_modules.is_dir():
            print(f"=== Installing dependencies (pnpm workspace at {workspace_root.name}/) ===")
            result = subprocess.run(
                ["pnpm", "install"],
                cwd=str(workspace_root),
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                print(f"ERROR: pnpm install failed:\n{result.stderr}", file=sys.stderr)
                sys.exit(1)
            print("  Dependencies installed.")
    else:
        # Standalone project — npm install in the story dir
        node_modules = sharpee_dir / "node_modules"
        if not node_modules.is_dir():
            print("=== Installing dependencies ===")
            result = subprocess.run(
                ["npm", "install"],
                cwd=str(sharpee_dir),
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                print(f"ERROR: npm install failed:\n{result.stderr}", file=sys.stderr)
                sys.exit(1)
            print("  Dependencies installed.")

    # --- Step 2: Build ---
    print(f"=== Building {title} ===")
    print(f"  Source: {sharpee_dir}")
    print(f"  Output: {project_dir}")
    if is_workspace:
        # Workspace: invoke CLI directly via node from the story dir
        cli_path = workspace_root / "packages" / "sharpee" / "dist" / "cli" / "index.js"
        build_cmd = ["node", str(cli_path), "build-browser"]
    else:
        build_cmd = ["npx", "sharpee", "build-browser"]
    result = subprocess.run(
        build_cmd,
        cwd=str(sharpee_dir),
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: Build failed:\n{result.stdout}\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    # Show build output (contains bundle size info)
    for line in result.stdout.strip().splitlines():
        print(f"  {line}")

    dist_dir = sharpee_dir / "dist" / "web"
    if not dist_dir.is_dir():
        print(f"ERROR: Build did not produce dist/web/ in {sharpee_dir}", file=sys.stderr)
        sys.exit(1)

    # --- Step 3: Import into IF Hub ---
    print(f"\n=== Importing into {project_dir.name} ===")
    setup_script = paths.WEB_DIR / "setup_sharpee.py"
    import_args = [
        sys.executable, str(setup_script),
        "--title", title,
        "--dist", str(dist_dir),
        "--out", str(project_dir),
    ]
    if args.force:
        import_args.append("--force")

    result = subprocess.run(import_args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: Import failed:\n{result.stdout}\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    for line in result.stdout.strip().splitlines():
        print(f"  {line}")

    # Clean up dist from source dir (keep fork clean)
    dist_parent = sharpee_dir / "dist"
    if dist_parent.is_dir():
        shutil.rmtree(str(dist_parent))
        print(f"  Cleaned dist/ from {sharpee_dir.name}/")

    # --- Step 4: Validate build ---
    print(f"\n=== Validating build ===")

    # 4a: Check bundle exists and has required markers
    bundle_files = [f for f in project_dir.glob("*.js") if f.name != "theme-listener.js"]
    if bundle_files:
        bundle = max(bundle_files, key=lambda p: p.stat().st_size)
        size_kb = bundle.stat().st_size / 1024
        text = bundle.read_text(encoding="utf-8", errors="replace")
        markers = ["initializeWorld", "GameEngine"]
        found = [m for m in markers if m in text]
        if not found:
            print(f"  WARNING: Bundle {bundle.name} ({size_kb:.0f} KB) missing expected markers", file=sys.stderr)
        elif size_kb < 10:
            print(f"  WARNING: Bundle {bundle.name} suspiciously small ({size_kb:.0f} KB)", file=sys.stderr)
        else:
            print(f"  Bundle: {bundle.name} ({size_kb:.0f} KB) — OK")
    else:
        print(f"  WARNING: No JS bundle found in {project_dir}", file=sys.stderr)

    # 4b: Check play.html references a bundle that exists
    play_html = project_dir / "play.html"
    if play_html.exists():
        import re as _re
        html = play_html.read_text(encoding="utf-8", errors="replace")
        script_refs = _re.findall(r'<script src="([^"]+\.js)"', html)
        missing = [s for s in script_refs if s != "theme-listener.js" and not (project_dir / s).exists()]
        if missing:
            print(f"  ERROR: play.html references missing bundle: {missing}", file=sys.stderr)
            sys.exit(1)
        elif script_refs:
            print(f"  play.html: OK (loads {', '.join(s for s in script_refs if s != 'theme-listener.js')})")
        else:
            print(f"  WARNING: play.html has no script references", file=sys.stderr)
    else:
        print(f"  WARNING: play.html not found", file=sys.stderr)

    # 4c: Run transcript tests if available
    if not args.no_test:
        wt_dir = sharpee_dir / "walkthroughs"
        transcripts = list(wt_dir.glob("*.transcript")) if wt_dir.is_dir() else []
        if transcripts:
            print(f"  Running {len(transcripts)} transcript test(s)...")
            result = subprocess.run(
                ["npx", "transcript-test", ".", *[str(t) for t in transcripts]],
                cwd=str(sharpee_dir),
                capture_output=True, text=True,
                timeout=60,
            )
            if result.returncode != 0:
                # Show last few lines of output
                lines = (result.stdout + result.stderr).strip().splitlines()
                for line in lines[-5:]:
                    print(f"    {line}")
                print(f"  WARNING: Transcript tests failed", file=sys.stderr)
            else:
                # Extract summary line
                for line in result.stdout.strip().splitlines():
                    if "passed" in line or "failed" in line:
                        print(f"    {line.strip()}")
                        break
                print(f"  Transcript tests: OK")
        else:
            print(f"  No transcript tests found, skipping")

    print(f"\n=== Done ===")
    print(f"  Project: {project_dir}")
    print(f"  Test:    python -m http.server 8000 --directory \"{project_dir}\"")
    print(f"  Publish: python tools/publish.py {args.game}")


if __name__ == "__main__":
    main()
