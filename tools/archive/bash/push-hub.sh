#!/bin/bash
# Push IF Hub registry changes (games.json + cards.json) to GitHub.
#
# Usage:
#   bash tools/push-hub.sh <game-name>
#
# Stages games.json and cards.json, commits with a message referencing the
# game name, and pushes. Skips commit if there are no staged changes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
I7_ROOT="$(dirname "$SCRIPT_DIR")"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <game-name>" >&2
    exit 1
fi

GAME="$1"

cd "$I7_ROOT"
git add ifhub/games.json ifhub/cards.json
if git diff --cached --quiet; then
    echo "No hub registry changes to push."
else
    git commit -m "Register $GAME in IF Hub"
    git push
fi
