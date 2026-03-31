#!/usr/bin/env python3
"""Build a Sharpee game and import into IF Hub.

Bridges the Sharpee authoring workspace (external npm project) and the
IF Hub project directory. Runs the npm build in the Sharpee source dir,
then delegates to jukebox.py import for the full import pipeline
(play.html, source files, walkthroughs, source.html, registration).

Usage:
    python tools/compile_sharpee.py <game-name>
    python tools/compile_sharpee.py <game-name> --force
    python tools/compile_sharpee.py <game-name> --force --ship

Source directory is resolved from games-registry.json ('source' field)
or tests/project.conf (SHARPEE_DIR=...).
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Ensure Unicode output works on Windows (transcript tests use ✓/✗ characters)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import config, paths


def main():
    parser = argparse.ArgumentParser(description="Build a Sharpee game and import into IF Hub.")
    parser.add_argument("game", help="Game name (as registered in games-registry.json)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing play.html")
    parser.add_argument("--no-test", action="store_true", help="Skip post-build validation")
    parser.add_argument("--ship", action="store_true", help="Also publish after import")
    args = parser.parse_args()

    # --- Resolve source directory ---
    # Try registry first, then project.conf fallback
    source_dir = paths.game_source_dir(args.game)
    if source_dir == Path() or not source_dir.is_dir():
        project_dir = paths.project_dir(args.game)
        conf = config.parse_conf_fields(project_dir)
        sharpee_dir_str = conf.get("SHARPEE_DIR", "")
        if sharpee_dir_str:
            if sharpee_dir_str.startswith("/"):
                sharpee_dir_str = paths.to_windows(sharpee_dir_str)
            source_dir = Path(sharpee_dir_str)

    if not source_dir.is_dir():
        print(f"ERROR: Source directory not found: {source_dir}", file=sys.stderr)
        print("  Set 'source' in games-registry.json or SHARPEE_DIR in tests/project.conf", file=sys.stderr)
        sys.exit(1)

    if not (source_dir / "package.json").exists():
        print(f"ERROR: No package.json in {source_dir} — not a valid npm project", file=sys.stderr)
        sys.exit(1)

    # --- Step 1: Install dependencies (if needed) ---
    pkg_json = (source_dir / "package.json").read_text(encoding="utf-8")
    is_workspace = "workspace:" in pkg_json

    if is_workspace:
        workspace_root = source_dir
        while workspace_root.parent != workspace_root:
            if (workspace_root / "pnpm-workspace.yaml").exists():
                break
            workspace_root = workspace_root.parent
        else:
            print("ERROR: workspace:* deps found but no pnpm-workspace.yaml in any parent", file=sys.stderr)
            sys.exit(1)

        node_modules = source_dir / "node_modules"
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
        node_modules = source_dir / "node_modules"
        if not node_modules.is_dir():
            print("=== Installing dependencies ===")
            result = subprocess.run(
                ["npm", "install"],
                cwd=str(source_dir),
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                print(f"ERROR: npm install failed:\n{result.stderr}", file=sys.stderr)
                sys.exit(1)
            print("  Dependencies installed.")

    # --- Step 2: Build ---
    # Read title from ifhub.conf
    ifhub_conf = source_dir / "ifhub.conf"
    title = args.game
    if ifhub_conf.exists():
        for line in ifhub_conf.read_text(encoding="utf-8").splitlines():
            if line.startswith("title"):
                title = line.split("=", 1)[1].strip()
                break

    print(f"=== Building {title} ===")
    print(f"  Source: {source_dir}")

    if is_workspace:
        cli_path = workspace_root / "packages" / "sharpee" / "dist" / "cli" / "index.js"
        build_cmd = ["node", str(cli_path), "build-browser"]
    else:
        build_cmd = ["npx", "sharpee", "build-browser"]

    result = subprocess.run(
        build_cmd,
        cwd=str(source_dir),
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: Build failed:\n{result.stdout}\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    for line in result.stdout.strip().splitlines():
        print(f"  {line}")

    dist_dir = source_dir / "dist" / "web"
    if not dist_dir.is_dir():
        print(f"ERROR: Build did not produce dist/web/ in {source_dir}", file=sys.stderr)
        sys.exit(1)

    # --- Step 3: Transcript tests (before dist cleanup) ---
    if not args.no_test:
        wt_dir = source_dir / "walkthroughs"
        test_dirs = [source_dir / "tests" / "transcripts"] if not wt_dir.is_dir() else []
        wt_dirs = [wt_dir] + test_dirs
        transcripts = []
        for d in wt_dirs:
            if d.is_dir():
                transcripts.extend(sorted(d.glob("*.transcript")))
        if transcripts:
            # Build Node.js version for transcript-test (tsc → dist/index.js)
            # Use --noCheck to skip type checking (we only need runnable JS)
            print(f"\n=== Running transcript tests ===")
            tsc_cmd = ["npx", "tsc", "--noCheck"]
            tsc_result = subprocess.run(
                tsc_cmd, cwd=str(source_dir),
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            if tsc_result.returncode != 0:
                print(f"  WARNING: tsc build failed, skipping transcript tests", file=sys.stderr)
                for line in (tsc_result.stderr or "").strip().splitlines()[-3:]:
                    print(f"    {line}")
            else:
                print(f"  Running {len(transcripts)} transcript test(s)...")
                try:
                    result = subprocess.run(
                        ["npx", "transcript-test", ".", *[str(t) for t in transcripts]],
                        cwd=str(source_dir),
                        capture_output=True, text=True, encoding="utf-8", errors="replace",
                        timeout=120,
                    )
                except subprocess.TimeoutExpired:
                    print(f"  WARNING: Transcript tests timed out", file=sys.stderr)
                else:
                    out = (result.stdout or "") + (result.stderr or "")
                    if result.returncode != 0:
                        for line in out.strip().splitlines()[-5:]:
                            print(f"    {line}")
                        print(f"  WARNING: Transcript tests failed", file=sys.stderr)
                    else:
                        for line in out.strip().splitlines():
                            if "passed" in line or "failed" in line:
                                print(f"    {line.strip()}")
                                break
                        print(f"  Transcript tests: OK")
        else:
            print(f"\n  No transcript tests found, skipping")

    # --- Step 4: Import via jukebox (handles source, walkthroughs, registration) ---
    print(f"\n=== Importing via jukebox ===", flush=True)
    jukebox_script = paths.TOOLS_DIR / "jukebox.py"
    import_cmd = [
        sys.executable, str(jukebox_script),
        "import", str(source_dir),
    ]
    if args.force:
        import_cmd.append("--force")
    if args.ship:
        import_cmd.append("--ship")

    result = subprocess.run(import_cmd)
    if result.returncode != 0:
        print(f"ERROR: Jukebox import failed", file=sys.stderr)
        sys.exit(1)

    # Clean up dist from source dir (keep source clean)
    dist_parent = source_dir / "dist"
    if dist_parent.is_dir():
        shutil.rmtree(str(dist_parent))
        print(f"  Cleaned dist/ from {source_dir.name}/")

    # --- Step 5: Validate deploy ---
    project_dir = paths.project_dir(args.game)
    print(f"\n=== Validating build ===")

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
        print(f"  WARNING: play.html not found", file=sys.stderr)

    print(f"\n=== Done ===")
    print(f"  Project: {project_dir}")
    if not args.ship:
        print(f"  Publish: python tools/publish.py {args.game}")


if __name__ == "__main__":
    main()
