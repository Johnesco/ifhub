#!/usr/bin/env python3
"""Generate walkthrough.html pages for each game in games.json.

Parallel to generate-play-pages.py. Reads the walkthrough template and
substitutes per-game placeholders for each game that has a walkthrough.

Usage:
    python3 generate-walkthrough-pages.py \
        --games-json PATH \
        --template PATH \
        [--output-dir PATH]
"""

import argparse
import json
import os
import re


def main():
    parser = argparse.ArgumentParser(description="Generate walkthrough pages from games.json")
    parser.add_argument("--games-json", required=True, help="Path to games.json")
    parser.add_argument("--template", required=True, help="Path to walkthrough-template.html")
    parser.add_argument("--output-dir", default="games", help="Base output directory")
    args = parser.parse_args()

    with open(args.games_json, encoding="utf-8") as f:
        games = json.load(f)

    with open(args.template, encoding="utf-8") as f:
        template = f.read()

    for g in games:
        gid = g["id"]

        # Only generate for games that have a walkthrough field
        if "walkthrough" not in g:
            continue

        dest = os.path.join(args.output_dir, gid)
        if not os.path.isdir(dest):
            continue

        title = "Walkthrough \u2014 " + g["title"]

        # Header: include version label if versioned
        version_label = g.get("versionLabel", "")
        if version_label:
            # Extract version number (e.g. "v4" from "v4 — Modern IF (Current)")
            m = re.match(r"(v\d+)", version_label)
            header = "Walkthrough (" + m.group(1) + ")" if m else "Walkthrough"
        else:
            header = "Walkthrough"

        # In hub context, walkthrough.html and play.html are in the same directory
        back_href = "play.html"

        # Storage key: base game name (e.g. "zork1" for "zork1-v4", "sample" for "sample")
        storage_key = gid.split("-v")[0] if re.search(r"-v\d+$", gid) else gid

        page = template.replace("__TITLE__", title)
        page = page.replace("__HEADER__", header)
        page = page.replace("__BACK_HREF__", back_href)
        page = page.replace("__STORAGE_KEY__", storage_key)

        out_path = os.path.join(dest, "walkthrough.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page)
        print("  " + gid + ": walkthrough.html generated")


if __name__ == "__main__":
    main()
