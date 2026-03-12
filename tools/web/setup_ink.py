#!/usr/bin/env python3
"""Set up a web player for an Ink story.

Compiles .ink source to JSON via inklecate, then generates a self-contained
play.html with the story data inlined.

Usage:
    python tools/web/setup_ink.py \
        --title "My Story" --ink path/to/story.ink --out path/to/project

    python tools/web/setup_ink.py \
        --title "My Story" --json path/to/story.json --out path/to/project
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Known inklecate locations (checked in order)
INKLECATE_PATHS = [
    Path("C:/Program Files/Inky/resources/app.asar.unpacked/"
         "main-process/ink/inkjs-compatible/inklecate_win.exe"),
]


def find_inklecate():
    """Find inklecate executable."""
    for p in INKLECATE_PATHS:
        if p.exists():
            return p
    return None


def compile_ink(ink_path, json_path):
    """Compile .ink to .json using inklecate."""
    inklecate = find_inklecate()
    if not inklecate:
        print("Error: inklecate not found.", file=sys.stderr)
        print("  Install Inky from https://github.com/inkle/inky/releases",
              file=sys.stderr)
        sys.exit(1)

    ink_abs = str(ink_path.resolve())
    json_abs = str(json_path.resolve())
    print(f"Compiling {ink_path.name} -> {json_path.name}...")
    result = subprocess.run(
        [str(inklecate), "-o", json_abs, ink_abs],
        capture_output=True, text=True,
        cwd=str(ink_path.resolve().parent),
    )

    # inklecate prints warnings to stdout even on success
    if result.stdout.strip():
        for line in result.stdout.strip().splitlines():
            print(f"  {line}")

    if result.returncode != 0:
        print(f"Error: inklecate failed (exit code {result.returncode})",
              file=sys.stderr)
        if result.stderr.strip():
            print(result.stderr, file=sys.stderr)
        sys.exit(1)

    if not json_path.exists():
        print(f"Error: expected output not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    print(f"  Compiled: {json_path}")


def main():
    parser = argparse.ArgumentParser(description="Set up Ink web player.")
    parser.add_argument("--title", required=True, help="Story title")
    parser.add_argument("--ink", help="Path to .ink source file")
    parser.add_argument("--json", help="Path to pre-compiled .json story")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite play.html")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    script_dir = Path(__file__).resolve().parent

    # Determine story JSON
    if args.ink and args.json:
        print("Error: specify --ink or --json, not both", file=sys.stderr)
        sys.exit(1)

    if args.ink:
        ink_path = Path(args.ink)
        if not ink_path.exists():
            print(f"Error: file not found: {ink_path}", file=sys.stderr)
            sys.exit(1)
        json_path = out_dir / (ink_path.stem + ".json")
        compile_ink(ink_path, json_path)
    elif args.json:
        json_path = Path(args.json)
        if not json_path.exists():
            print(f"Error: file not found: {json_path}", file=sys.stderr)
            sys.exit(1)
    else:
        # Auto-detect: look for .ink file in --out directory
        ink_files = list(out_dir.glob("*.ink"))
        if not ink_files:
            print("Error: no .ink file found. Specify --ink or --json.",
                  file=sys.stderr)
            sys.exit(1)
        ink_path = ink_files[0]
        json_path = out_dir / (ink_path.stem + ".json")
        compile_ink(ink_path, json_path)

    # Read compiled JSON
    story_data = json_path.read_text(encoding="utf-8").strip()
    # Validate it's actual JSON
    try:
        json.loads(story_data)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {json_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate play.html from template
    template_path = script_dir / "templates" / "play-ink.html"
    if not template_path.exists():
        print(f"Error: template not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    play_html = out_dir / "play.html"
    if play_html.exists() and not args.force:
        print(f"  play.html already exists (use --force to overwrite)")
    else:
        print("Generating play.html...")
        template = template_path.read_text(encoding="utf-8")
        html = template.replace("__TITLE__", args.title)
        html = html.replace("__STORY_DATA__", story_data)
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
