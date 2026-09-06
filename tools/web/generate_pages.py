#!/usr/bin/env python3
"""Write a game's landing page (index.html) from tools/web/landing-template.html.

Usage:
    python tools/web/generate_pages.py --title "Game Title" --meta "Subtitle" \
        --description "Game description" --id <game> --out /path/to/game

The landing page is the only file IF Hub writes into a game folder. Source and
walkthrough views are rendered by the hub itself from the game's raw files.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.web import substitute_template


def main():
    parser = argparse.ArgumentParser(description="Write a game's landing page from the hub template.")
    parser.add_argument("--title", required=True, help="Game title")
    parser.add_argument("--meta", default="An Interactive Fiction", help="Subtitle")
    parser.add_argument("--description", default="An interactive fiction game.", help="Description")
    parser.add_argument("--id", default="", help="Game ID (for IF Hub links; defaults to the output dir name)")
    parser.add_argument("--out", required=True, help="Game folder")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing index.html")
    args = parser.parse_args()

    template = Path(__file__).resolve().parent / "landing-template.html"
    if not template.exists():
        print(f"ERROR: landing template not found: {template}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out)
    index_out = out_dir / "index.html"
    if index_out.exists() and not args.force:
        print("  index.html already exists (use --force to overwrite)")
        return
    print("Generating index.html...")
    substitute_template(template, index_out, {
        "__TITLE__": args.title, "__META__": args.meta, "__DESCRIPTION__": args.description,
        "__ID__": args.id or out_dir.name,
    })


if __name__ == "__main__":
    main()
