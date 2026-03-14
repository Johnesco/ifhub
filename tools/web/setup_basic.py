#!/usr/bin/env python3
"""Set up a web player for a BASIC program.

Generates a self-contained play.html from engine-specific templates.
Supports wwwbasic, bwbasic, qbjc, applesoft, and jsdos engines.

Usage:
    python tools/web/setup_basic.py \
        --engine wwwbasic --title "My Game" \
        --source path/to/game.bas --out path/to/project

    python tools/web/setup_basic.py \
        --engine bwbasic --title "My Game" \
        --source path/to/game.bas --out path/to/project

    python tools/web/setup_basic.py \
        --engine qbjc --title "My Game" \
        --compiled path/to/game.js --out path/to/project

    python tools/web/setup_basic.py \
        --engine jsdos --title "My Game" \
        --bundle path/to/game.jsdos --out path/to/project
"""

import argparse
import shutil
import sys
from pathlib import Path

# Engine → template file mapping
ENGINE_TEMPLATES = {
    "wwwbasic": "play-wwwbasic.html",
    "bwbasic": "play-bwbasic.html",
    "qbjc": "play-qbjc.html",
    "applesoft": "play-applesoft.html",
    "jsdos": "play-jsdos.html",
    "basic": "play-wwwbasic.html",    # generic basic defaults to wwwbasic
}

# Engines that inline .bas source into the template
INLINE_SOURCE_ENGINES = {"wwwbasic", "bwbasic", "applesoft", "basic"}

# Shared bwBASIC WASM runtime location
BWBASIC_WASM_DIR = Path(__file__).resolve().parent.parent / "engines" / "bwbasic" / "wasm"


def main():
    parser = argparse.ArgumentParser(
        description="Set up a BASIC web player.")
    parser.add_argument("--engine", required=True,
                        choices=sorted(ENGINE_TEMPLATES),
                        help="BASIC engine to use")
    parser.add_argument("--title", required=True, help="Game title")
    parser.add_argument("--source", help="Path to .bas source file")
    parser.add_argument("--compiled",
                        help="Path to pre-compiled .js file (qbjc only)")
    parser.add_argument("--bundle",
                        help="Path to .jsdos bundle file (jsdos only)")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--version-label", default="",
                        help="Version subtitle (e.g. 'v0 — Original BASIC')")
    parser.add_argument("--back-href", default="./",
                        help="Back link target (default: ./)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing play.html")
    args = parser.parse_args()

    engine = args.engine
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    script_dir = Path(__file__).resolve().parent

    # --- Validate engine-specific inputs ---
    if engine in INLINE_SOURCE_ENGINES:
        if not args.source:
            # Auto-detect: look for .bas file in --out directory or src/basic/
            bas_files = list(out_dir.glob("*.bas")) + list(out_dir.glob("*.BAS"))
            if not bas_files:
                src_dir = out_dir / "src" / "basic"
                bas_files = list(src_dir.glob("*.bas")) + list(src_dir.glob("*.BAS"))
            if not bas_files:
                print("Error: no .bas file found. Specify --source.",
                      file=sys.stderr)
                sys.exit(1)
            source_path = bas_files[0]
            print(f"  Auto-detected source: {source_path}")
        else:
            source_path = Path(args.source)
        if not source_path.exists():
            print(f"Error: source file not found: {source_path}",
                  file=sys.stderr)
            sys.exit(1)
    elif engine == "qbjc":
        if not args.compiled:
            js_files = [f for f in out_dir.glob("*.js")
                        if f.name not in ("wwwbasic.js", "bwbasic.js")]
            if not js_files:
                print("Error: no compiled .js file found. Specify --compiled.",
                      file=sys.stderr)
                sys.exit(1)
            compiled_path = js_files[0]
            print(f"  Auto-detected compiled JS: {compiled_path.name}")
        else:
            compiled_path = Path(args.compiled)
        if not compiled_path.exists():
            print(f"Error: compiled file not found: {compiled_path}",
                  file=sys.stderr)
            sys.exit(1)
    elif engine == "jsdos":
        if not args.bundle:
            jsdos_files = list(out_dir.glob("*.jsdos"))
            if not jsdos_files:
                print("Error: no .jsdos bundle found. Specify --bundle.",
                      file=sys.stderr)
                sys.exit(1)
            bundle_path = jsdos_files[0]
            print(f"  Auto-detected bundle: {bundle_path.name}")
        else:
            bundle_path = Path(args.bundle)
        if not bundle_path.exists():
            print(f"Error: bundle not found: {bundle_path}",
                  file=sys.stderr)
            sys.exit(1)

    # --- Load template ---
    template_name = ENGINE_TEMPLATES[engine]
    template_path = script_dir / "templates" / template_name
    if not template_path.exists():
        print(f"Error: template not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    template = template_path.read_text(encoding="utf-8")

    # --- Substitute placeholders ---
    html = template.replace("__TITLE__", args.title)
    html = html.replace("__VERSION_LABEL__", args.version_label)
    html = html.replace("__BACK_HREF__", args.back_href)

    if engine in INLINE_SOURCE_ENGINES:
        basic_source = source_path.read_text(encoding="utf-8",
                                             errors="replace")
        # Strip ^Z EOF markers (DOS artifact)
        basic_source = basic_source.split("\x1a")[0]
        html = html.replace("__BASIC_SOURCE__", basic_source)
    elif engine == "qbjc":
        if compiled_path.parent.resolve() == out_dir.resolve():
            js_ref = compiled_path.name
        else:
            js_ref = compiled_path.name
            dest = out_dir / compiled_path.name
            if not dest.exists() or args.force:
                shutil.copy2(compiled_path, dest)
                print(f"  Copied {compiled_path.name} -> {dest}")
        html = html.replace("__COMPILED_JS__", js_ref)
    elif engine == "jsdos":
        if bundle_path.parent.resolve() == out_dir.resolve():
            bundle_ref = bundle_path.name
        else:
            bundle_ref = bundle_path.name
            dest = out_dir / bundle_path.name
            if not dest.exists() or args.force:
                shutil.copy2(bundle_path, dest)
                print(f"  Copied {bundle_path.name} -> {dest}")
        html = html.replace("__BUNDLE__", bundle_ref)

    # --- Copy engine runtime files ---
    if engine == "bwbasic":
        bw_dest = out_dir / "lib" / "bwbasic"
        bw_dest.mkdir(parents=True, exist_ok=True)
        for fname in ("bwbasic.js", "bwbasic.wasm"):
            src = BWBASIC_WASM_DIR / fname
            dst = bw_dest / fname
            if src.exists() and (not dst.exists() or args.force):
                shutil.copy2(src, dst)
                print(f"  Copied {fname} -> {bw_dest}")
            elif not src.exists():
                print(f"  Warning: {src} not found — bwBASIC runtime missing")
    elif engine in ("wwwbasic", "basic"):
        wwwbasic_js = out_dir / "wwwbasic.js"
        if not wwwbasic_js.exists():
            print(f"  Warning: wwwbasic.js not found in {out_dir}")
            print("  The player needs wwwbasic.js to run. Copy it manually or"
                  " use new_project.py to scaffold the project.")

    # --- Write play.html ---
    play_html = out_dir / "play.html"
    if play_html.exists() and not args.force:
        print(f"  play.html already exists (use --force to overwrite)")
    else:
        print(f"Generating play.html ({engine})...")
        play_html.write_text(html, encoding="utf-8")
        print(f"  Created: {play_html}")

    print()
    print(f"Web player ready at: {play_html}")
    print()
    print("To play locally:")
    print(f'  python -m http.server 8000 --directory "{out_dir}"')
    print("  # then open http://localhost:8000/play.html")


if __name__ == "__main__":
    main()
