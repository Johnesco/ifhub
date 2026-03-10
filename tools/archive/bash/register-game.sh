#!/bin/bash
# Register a game in the IF Hub (adds entries to games.json and cards.json).
#
# Usage:
#   bash /c/code/ifhub/tools/register-game.sh \
#       --name game-name \
#       --title "Game Title" \
#       --meta "Subtitle" \
#       --description "Game description"
#
# Options:
#   --name TEXT         Project directory name (required)
#   --title TEXT        Display title (required)
#   --meta TEXT         Subtitle / tagline (default: "An Interactive Fiction")
#   --description TEXT  Card description (default: "An interactive fiction game.")
#   --source-browser    Use source.html iframe instead of raw .ni (default: true)
#   --sound TYPE        Sound type: "blorb" or omit for no sound
#
# Adds entries to:
#   ifhub/games.json  — Game registry (URLs for app.html)
#   ifhub/cards.json  — Card metadata (for landing page)
#
# Skips if the game ID already exists in either file.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
I7_ROOT="$(dirname "$SCRIPT_DIR")"

NAME=""
TITLE=""
META="An Interactive Fiction"
DESCRIPTION="An interactive fiction game."
SOURCE_BROWSER=true
SOUND=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --name)            NAME="$2"; shift 2 ;;
        --title)           TITLE="$2"; shift 2 ;;
        --meta)            META="$2"; shift 2 ;;
        --description)     DESCRIPTION="$2"; shift 2 ;;
        --source-browser)  SOURCE_BROWSER=true; shift ;;
        --sound)           SOUND="$2"; shift 2 ;;
        *)                 echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$NAME" || -z "$TITLE" ]]; then
    echo "Usage: register-game.sh --name game-name --title \"Title\"" >&2
    echo "  Optional: --meta \"Sub\" --description \"Desc\" --sound blorb" >&2
    exit 1
fi

GAMES_JSON="$I7_ROOT/ifhub/games.json"
CARDS_JSON="$I7_ROOT/ifhub/cards.json"

if [[ ! -f "$GAMES_JSON" || ! -f "$CARDS_JSON" ]]; then
    echo "ERROR: games.json or cards.json not found in $I7_ROOT/ifhub/" >&2
    exit 1
fi

# Use Python for safe JSON manipulation
python3 - "$NAME" "$TITLE" "$META" "$DESCRIPTION" "$SOURCE_BROWSER" "$SOUND" "$GAMES_JSON" "$CARDS_JSON" << 'PYEOF'
import json
import sys

name, title, meta, description, source_browser, sound, games_path, cards_path = sys.argv[1:9]
source_browser = source_browser.lower() == "true"

# --- games.json ---
with open(games_path, "r", encoding="utf-8") as f:
    games = json.load(f)

if any(g["id"] == name for g in games):
    print(f"  games.json: '{name}' already exists, skipping")
else:
    entry = {
        "id": name,
        "title": title,
        "sourceLabel": f"{name}.ni",
        "playUrl": f"/{name}/play.html",
        "walkthroughUrl": f"/{name}/walkthrough.html",
        "landingUrl": f"/{name}/"
    }
    if source_browser:
        entry["sourceBrowser"] = True
        entry["sourceUrl"] = f"/{name}/source.html"
    else:
        entry["sourceUrl"] = f"/{name}/story.ni"
    if sound:
        entry["sound"] = sound

    games.append(entry)
    with open(games_path, "w", encoding="utf-8") as f:
        json.dump(games, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  games.json: added '{name}'")

# --- cards.json ---
with open(cards_path, "r", encoding="utf-8") as f:
    cards = json.load(f)

if any(c["id"] == name for c in cards):
    print(f"  cards.json: '{name}' already exists, skipping")
else:
    card = {
        "id": name,
        "base": name,
        "title": title,
        "meta": meta,
        "description": description,
        "playUrl": f"/{name}/play.html",
        "landingUrl": f"/{name}/"
    }
    if sound:
        card["sound"] = sound

    cards.append(card)
    with open(cards_path, "w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  cards.json: added '{name}'")

print(f"\nDone. Next: publish to GitHub Pages with:")
print(f"  bash /c/code/ifhub/tools/publish.sh {name}")
PYEOF
