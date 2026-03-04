#!/usr/bin/env python3
"""Extract card metadata from project-owned landing pages into cards.json.

Reads games.json to find entries with `landing` fields, parses <meta name="ifhub:*">
tags from each landing page, groups version entries by base ID, and writes cards.json.

Usage:
    python3 extract-cards.py \
        --games-json PATH \
        --i7-root PATH \
        --output PATH
"""

import argparse
import json
import os
import re
from html.parser import HTMLParser


class MetaExtractor(HTMLParser):
    """Extract ifhub:* meta tag content from HTML."""

    def __init__(self):
        super().__init__()
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        if tag != "meta":
            return
        attr_dict = dict(attrs)
        name = attr_dict.get("name", "")
        if name.startswith("ifhub:"):
            key = name[len("ifhub:"):]
            self.meta[key] = attr_dict.get("content", "")


def extract_meta(filepath):
    """Parse an HTML file and return ifhub:* meta values."""
    parser = MetaExtractor()
    with open(filepath, encoding="utf-8") as f:
        parser.feed(f.read())
    return parser.meta


def main():
    ap = argparse.ArgumentParser(description="Extract card metadata from landing pages")
    ap.add_argument("--games-json", required=True, help="Path to games.json")
    ap.add_argument("--i7-root", required=True, help="Path to ifhub root")
    ap.add_argument("--output", default=None, help="Output cards.json path (default: alongside games.json)")
    args = ap.parse_args()

    with open(args.games_json, encoding="utf-8") as f:
        games = json.load(f)

    game_map = {g["id"]: g for g in games}

    # Find primary entries (those with landing fields)
    primaries = [g for g in games if g.get("landing")]

    # Group version entries by base ID
    # A version entry has no landing field and its base (strip -v\d+$) matches a primary
    primary_bases = {}
    for g in primaries:
        base = re.sub(r"-v\d+$", "", g["id"])
        primary_bases[base] = g

    cards = []
    for g in primaries:
        gid = g["id"]
        base = re.sub(r"-v\d+$", "", gid)

        # Resolve landing page path
        landing_path = os.path.join(args.i7_root, g["landing"])
        if not os.path.isfile(landing_path):
            print(f"  WARNING: landing page not found: {landing_path}")
            continue

        meta = extract_meta(landing_path)
        if not meta.get("title"):
            print(f"  WARNING: no ifhub:title meta tag in {landing_path}")
            continue

        card = {
            "id": gid,
            "base": base,
            "title": meta["title"],
            "meta": meta.get("meta", ""),
            "description": meta.get("description", ""),
        }

        if g.get("sound"):
            card["sound"] = g["sound"]

        # Collect version entries for this base
        versions = []
        for other in games:
            if other["id"] == gid:
                continue
            other_base = re.sub(r"-v\d+$", "", other["id"])
            if other_base == base and other["id"] != base:
                v = {"id": other["id"]}
                if other.get("versionLabel"):
                    v["label"] = other["versionLabel"]
                if other.get("sound"):
                    v["sound"] = other["sound"]
                versions.append(v)

        if versions:
            # Sort versions by version number descending (v3 before v2 before v1 before v0)
            def version_sort_key(v):
                m = re.search(r"-v(\d+)$", v["id"])
                return int(m.group(1)) if m else 0
            versions.sort(key=version_sort_key, reverse=True)
            card["versions"] = versions

        cards.append(card)

    # Write output
    output_path = args.output
    if not output_path:
        output_path = os.path.join(os.path.dirname(args.games_json), "cards.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2, ensure_ascii=False)

    print(f"  cards.json: {len(cards)} cards extracted -> {output_path}")


if __name__ == "__main__":
    main()
