#!/bin/bash
# Unregister a game from the IF Hub (removes from games.json and cards.json).
#
# The game's own repo, GitHub Pages site, and standalone pages are NOT affected.
# This only removes the game's visibility from the IF Hub landing page and player.
#
# Usage:
#   bash /c/code/ifhub/tools/unregister-game.sh <game-name>
#
# After unregistering, push the changes:
#   bash /c/code/ifhub/tools/push-hub.sh <game-name>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
I7_ROOT="$(dirname "$SCRIPT_DIR")"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <game-name>" >&2
    exit 1
fi

NAME="$1"
GAMES_JSON="$I7_ROOT/ifhub/games.json"
CARDS_JSON="$I7_ROOT/ifhub/cards.json"

echo "=== Unregistering $NAME from IF Hub ==="

python3 - "$NAME" "$GAMES_JSON" "$CARDS_JSON" << 'PYEOF'
import json
import sys

name, games_path, cards_path = sys.argv[1:4]

# games.json
with open(games_path, "r", encoding="utf-8") as f:
    games = json.load(f)
before = len(games)
games = [g for g in games if g["id"] != name]
if len(games) < before:
    with open(games_path, "w", encoding="utf-8") as f:
        json.dump(games, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  games.json: removed '{name}'")
else:
    print(f"  games.json: '{name}' not found, skipping")

# cards.json
with open(cards_path, "r", encoding="utf-8") as f:
    cards = json.load(f)
before = len(cards)
cards = [c for c in cards if c["id"] != name]
if len(cards) < before:
    with open(cards_path, "w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  cards.json: removed '{name}'")
else:
    print(f"  cards.json: '{name}' not found, skipping")
PYEOF

echo ""
echo "=== Done ==="
echo "  Game still live at: https://johnesco.github.io/$NAME/"
echo "  Push hub changes:   bash $I7_ROOT/tools/push-hub.sh $NAME"
