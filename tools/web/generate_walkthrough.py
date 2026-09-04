#!/usr/bin/env python3
"""Generate a walkthrough viewer (walkthrough.html + supporting txt files)
in a game's deploy directory.

The walkthrough viewer is engine-agnostic: it's a static HTML page that
loads walkthrough.txt (commands), walkthrough-guide.txt (annotated guide),
and walkthrough_output.txt (transcript) at runtime.

This tool:
  1. Copies walkthrough source files (walkthrough.txt / walkthrough-guide.txt /
     walkthrough_output.txt) from a source directory to the deploy root.
  2. Generates walkthrough.html from the shared template.

Usage:
    python tools/web/generate_walkthrough.py \
        --title "Game Title" \
        --src tests/inform7 \
        --out path/to/deploy_root

If --src is omitted, defaults to <out>/tests/<engine>/ (auto-detected from
ifhub.conf), then <out>/tests/. If no walkthrough.txt is found, the tool
exits with a non-zero status and a message — the caller should either
provide a source or remove the walkthroughUrl from games.json.
"""

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.web import substitute_template

WALKTHROUGH_FILES = ("walkthrough.txt", "walkthrough-guide.txt", "walkthrough_output.txt")


def find_source_dir(out_dir: Path) -> Path | None:
    """Look for walkthrough.txt in <out>/ itself, then under <out>/tests/{<engine>/,}/."""
    if (out_dir / "walkthrough.txt").exists():
        return out_dir
    tests = out_dir / "tests"
    if not tests.exists():
        return None
    if (tests / "walkthrough.txt").exists():
        return tests
    for sub in tests.iterdir():
        if sub.is_dir() and (sub / "walkthrough.txt").exists():
            return sub
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate walkthrough viewer for a game.")
    parser.add_argument("--title", required=True, help="Game title (used in viewer chrome)")
    parser.add_argument("--out", required=True, help="Deploy directory")
    parser.add_argument("--src", help="Directory containing walkthrough.txt and friends "
                                      "(default: auto-detect under <out>/tests/)")
    parser.add_argument("--storage-key", default="",
                        help="localStorage key for replay-speed persistence (default: out dir name)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    if not out_dir.exists():
        print(f"ERROR: Deploy directory not found: {out_dir}", file=sys.stderr)
        return 1

    src_dir = Path(args.src).resolve() if args.src else find_source_dir(out_dir)
    if src_dir is None or not (src_dir / "walkthrough.txt").exists():
        print(f"ERROR: walkthrough.txt not found "
              f"(searched: {src_dir or (out_dir / 'tests')})", file=sys.stderr)
        print("Either provide --src, or remove walkthroughUrl from games.json "
              "via 'python tools/check_links.py --fix'.", file=sys.stderr)
        return 2

    copied = 0
    for name in WALKTHROUGH_FILES:
        src = src_dir / name
        if not src.exists():
            continue
        dst = out_dir / name
        if src.resolve() == dst.resolve():
            continue
        if dst.exists() and not args.force:
            print(f"  {name}: exists (use --force to overwrite)")
            continue
        shutil.copy2(str(src), str(dst))
        print(f"  copied {name}")
        copied += 1

    template = Path(__file__).resolve().parent / "walkthrough-template.html"
    if not template.exists():
        print(f"ERROR: Walkthrough template not found: {template}", file=sys.stderr)
        return 1

    walk_html = out_dir / "walkthrough.html"
    if walk_html.exists() and not args.force:
        print("  walkthrough.html: exists (use --force to overwrite)")
    else:
        storage_key = args.storage_key or out_dir.name
        substitute_template(template, walk_html, {
            "__TITLE__": f"Walkthrough -- {args.title}",
            "__HEADER__": "Walkthrough",
            "__BACK_HREF__": "play.html",
            "__STORAGE_KEY__": storage_key,
        })
        print(f"  generated walkthrough.html")

    print(f"\nWalkthrough viewer ready at: {walk_html}")
    print(f"  ({copied} support file(s) copied from {src_dir})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
