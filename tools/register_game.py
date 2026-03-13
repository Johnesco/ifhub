#!/usr/bin/env python3
"""Register a game in the IF Hub (adds entries to games.json and cards.json).

Usage:
    python tools/register_game.py \
        --name game-name \
        --title "Game Title" \
        --meta "Subtitle" \
        --description "Game description"

Options:
    --name TEXT         Project directory name (required)
    --title TEXT        Display title (required)
    --meta TEXT         Subtitle / tagline (default: "An Interactive Fiction")
    --description TEXT  Card description (default: "An interactive fiction game.")
    --source-browser    Use source.html iframe instead of raw .ni (default: true)
    --sound TYPE        Sound type: "blorb" or omit for no sound
    --engine TYPE       Engine type: inform7, ink, basic (default: inform7)
    --tags LIST         Comma-separated tags (e.g. 'horror,classic')
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import IFHUB_DIR


def main():
    parser = argparse.ArgumentParser(description="Register a game in IF Hub.")
    parser.add_argument("--name", required=True, help="Project directory name")
    parser.add_argument("--title", required=True, help="Display title")
    parser.add_argument("--meta", default="An Interactive Fiction", help="Subtitle")
    parser.add_argument("--description", default="An interactive fiction game.", help="Description")
    parser.add_argument("--source-browser", action="store_true", default=True,
                        help="Use source.html iframe")
    parser.add_argument("--sound", default="", help="Sound type: 'blorb' or empty")
    parser.add_argument("--engine", default="inform7", help="Engine type: inform7, ink, basic")
    parser.add_argument("--tags", default="", help="Comma-separated tags (e.g. 'horror,classic')")
    args = parser.parse_args()

    games_path = IFHUB_DIR / "games.json"
    cards_path = IFHUB_DIR / "cards.json"

    if not games_path.exists() or not cards_path.exists():
        print(f"ERROR: games.json or cards.json not found in {IFHUB_DIR}", file=sys.stderr)
        sys.exit(1)

    name = args.name
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    # --- games.json ---
    games = json.loads(games_path.read_text(encoding="utf-8"))
    if any(g["id"] == name for g in games):
        print(f"  games.json: '{name}' already exists, skipping")
    else:
        entry: dict = {
            "id": name,
            "title": args.title,
            "sourceLabel": f"{name}.ni",
            "playUrl": f"/{name}/play.html",
            "walkthroughUrl": f"/{name}/walkthrough.html",
            "landingUrl": f"/{name}/",
        }
        if args.source_browser:
            entry["sourceBrowser"] = True
            entry["sourceUrl"] = f"/{name}/source.html"
        else:
            entry["sourceUrl"] = f"/{name}/story.ni"
        if args.sound:
            entry["sound"] = args.sound
        entry["engine"] = args.engine
        entry["tags"] = tags

        games.append(entry)
        games_path.write_text(json.dumps(games, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
        print(f"  games.json: added '{name}'")

    # --- cards.json ---
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    if any(c["id"] == name for c in cards):
        print(f"  cards.json: '{name}' already exists, skipping")
    else:
        card: dict = {
            "id": name,
            "base": name,
            "title": args.title,
            "meta": args.meta,
            "description": args.description,
            "playUrl": f"/{name}/play.html",
            "landingUrl": f"/{name}/",
        }
        if args.sound:
            card["sound"] = args.sound
        card["engine"] = args.engine
        card["tags"] = tags

        cards.append(card)
        cards_path.write_text(json.dumps(cards, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
        print(f"  cards.json: added '{name}'")

    print(f"\nDone. Next: publish to GitHub Pages with:")
    print(f"  python tools/publish.py {name}")


if __name__ == "__main__":
    main()
