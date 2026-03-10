#!/usr/bin/env python3
"""Unregister a game from the IF Hub (removes from games.json and cards.json).

The game's own repo, GitHub Pages site, and standalone pages are NOT affected.
This only removes the game's visibility from the IF Hub landing page and player.

Usage:
    python tools/unregister_game.py <game-name>
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import IFHUB_DIR, I7_ROOT


def main():
    parser = argparse.ArgumentParser(description="Unregister a game from IF Hub.")
    parser.add_argument("name", help="Game name to unregister")
    args = parser.parse_args()

    name = args.name
    games_path = IFHUB_DIR / "games.json"
    cards_path = IFHUB_DIR / "cards.json"

    print(f"=== Unregistering {name} from IF Hub ===")

    # games.json
    games = json.loads(games_path.read_text(encoding="utf-8"))
    before = len(games)
    games = [g for g in games if g["id"] != name]
    if len(games) < before:
        games_path.write_text(json.dumps(games, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
        print(f"  games.json: removed '{name}'")
    else:
        print(f"  games.json: '{name}' not found, skipping")

    # cards.json
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    before = len(cards)
    cards = [c for c in cards if c["id"] != name]
    if len(cards) < before:
        cards_path.write_text(json.dumps(cards, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
        print(f"  cards.json: removed '{name}'")
    else:
        print(f"  cards.json: '{name}' not found, skipping")

    print()
    print("=== Done ===")
    print(f"  Game still live at: https://johnesco.github.io/{name}/")
    print(f"  Push hub changes:   python {I7_ROOT}/tools/push_hub.py {name}")


if __name__ == "__main__":
    main()
