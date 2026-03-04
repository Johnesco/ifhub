#!/usr/bin/env python3
"""Generate standalone play.html pages for each game in games.json.

Usage:
    python3 generate-play-pages.py \
        --games-json PATH \
        --template PATH \
        --i7-root PATH \
        [--output-dir PATH]
"""

import argparse
import json
import os
import re
import time


def main():
    parser = argparse.ArgumentParser(description="Generate play pages from games.json")
    parser.add_argument("--games-json", required=True, help="Path to games.json")
    parser.add_argument("--template", required=True, help="Path to generic play template")
    parser.add_argument("--i7-root", required=True, help="ifhub root directory")
    parser.add_argument("--output-dir", default="games", help="Base output directory")
    args = parser.parse_args()

    with open(args.games_json, encoding="utf-8") as f:
        games = json.load(f)

    with open(args.template, encoding="utf-8") as f:
        generic_template = f.read()

    # Cache-busting: append ?v=<timestamp> to .js and .css references so browsers
    # don't serve stale scripts after a rebuild (e.g. after switching parchment.js).
    cache_bust = "v=" + str(int(time.time()))

    for g in games:
        gid = g["id"]
        dest = os.path.join(args.output_dir, gid)
        if not os.path.isdir(dest):
            continue

        title = g["title"]
        binary = g["binary"].split("/")[-1]

        # Per-game template support: if playTemplate is set in games.json,
        # use that project-specific template (preserves CSS atmospheric effects).
        # Otherwise fall back to the generic hub template.
        custom_tmpl = g.get("playTemplate")
        if custom_tmpl:
            tmpl_path = os.path.join(args.i7_root, custom_tmpl)
            if os.path.isfile(tmpl_path):
                with open(tmpl_path, encoding="utf-8") as f:
                    tmpl = f.read()
                print("  " + gid + ": using custom template " + custom_tmpl)
            else:
                print("  WARNING: " + tmpl_path + " not found, using generic template")
                tmpl = generic_template
        else:
            tmpl = generic_template

        page = tmpl.replace("__TITLE__", title)
        page = page.replace("__BINARY__", binary)
        page = page.replace("__STORY_FILE__", binary)
        page = page.replace("__STORY_PATH__", binary)
        page = page.replace("__LIB_PATH__", "../../lib/parchment/")
        page = re.sub(r'\.js"', ".js?" + cache_bust + '"', page)
        page = re.sub(r'\.css"', ".css?" + cache_bust + '"', page)

        # Write play.html
        with open(os.path.join(dest, "play.html"), "w", encoding="utf-8") as f:
            f.write(page)
        print("  " + gid + ": play.html generated")

        # For versioned games, write a backward-compat redirect at index.html
        # (non-versioned games get a landing page at index.html instead)
        if re.search(r"-v\d+$", gid):
            redirect = (
                '<!DOCTYPE html>\n'
                '<html><head>\n'
                '<meta charset="utf-8">\n'
                '<meta http-equiv="refresh" content="0;url=play.html">\n'
                '<title>Redirecting...</title>\n'
                '</head><body>\n'
                '<p>Redirecting to <a href="play.html">play page</a>...</p>\n'
                '</body></html>'
            )
            with open(os.path.join(dest, "index.html"), "w", encoding="utf-8") as f:
                f.write(redirect)
            print("  " + gid + ": index.html redirect generated")


if __name__ == "__main__":
    main()
