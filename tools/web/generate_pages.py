#!/usr/bin/env python3
"""Generate project web pages (landing page + source browser) from templates.

Usage:
    python tools/web/generate_pages.py \
        --title "Game Title" \
        --meta "Subtitle" \
        --description "Game description" \
        --out /path/to/project
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.web import substitute_template


def main():
    parser = argparse.ArgumentParser(description="Generate project web pages from templates.")
    parser.add_argument("--title", required=True, help="Game title")
    parser.add_argument("--meta", default="An Interactive Fiction", help="Subtitle")
    parser.add_argument("--description", default="An interactive fiction game.", help="Description")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    out_dir = Path(args.out)
    generated = 0

    # Landing page (index.html)
    landing_template = script_dir / "landing-template.html"
    if not landing_template.exists():
        print(f"ERROR: Landing template not found: {landing_template}", file=sys.stderr)
        sys.exit(1)

    index_out = out_dir / "index.html"
    if not index_out.exists() or args.force:
        print("Generating index.html...")
        substitute_template(
            landing_template, index_out,
            {"__TITLE__": args.title, "__META__": args.meta, "__DESCRIPTION__": args.description},
        )
        generated += 1
    else:
        print("  index.html already exists (use --force to overwrite)")

    # Source browser (source.html)
    source_template = script_dir / "source-template.html"
    if not source_template.exists():
        print(f"ERROR: Source template not found: {source_template}", file=sys.stderr)
        sys.exit(1)

    source_out = out_dir / "source.html"
    if not source_out.exists() or args.force:
        print("Generating source.html...")
        substitute_template(source_template, source_out, {"__TITLE__": args.title})
        generated += 1
    else:
        print("  source.html already exists (use --force to overwrite)")

    print(f"\nGenerated {generated} page(s) in {out_dir}")


if __name__ == "__main__":
    main()
