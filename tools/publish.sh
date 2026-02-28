#!/bin/bash
# Publish an Inform 7 project to GitHub Pages.
#
# First run:  creates the GitHub repo, enables Pages, pushes everything.
# Later runs: commits changes and pushes to trigger redeployment.
#
# Usage:
#   bash /c/code/ifhub/tools/publish.sh <game-name>
#   bash /c/code/ifhub/tools/publish.sh <game-name> "commit message"
#
# Example:
#   bash /c/code/ifhub/tools/publish.sh RNG
#   bash /c/code/ifhub/tools/publish.sh RNG "Add kitchen puzzle"
#
# Publishes to: johnesco.github.io/<game-name>/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
I7_ROOT="$(dirname "$SCRIPT_DIR")"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <game-name> [\"commit message\"]" >&2
    exit 1
fi

NAME="$1"
MSG="${2:-Update $NAME}"
PROJECT_DIR="$I7_ROOT/projects/$NAME"

if [[ ! -d "$PROJECT_DIR/web" ]]; then
    echo "ERROR: web/ directory not found. Run compile.sh first." >&2
    exit 1
fi

cd "$PROJECT_DIR"

# --- First-time setup ---
if [[ ! -d ".git" ]]; then
    echo "=== First-time setup ==="
    echo "  Initializing git repo..."
    git init
    git branch -M main

    echo "  Creating GitHub repo..."
    gh repo create "Johnesco/$NAME" --public --source=. \
        --description "$NAME — An Inform 7 Game"

    echo "  Adding all files..."
    git add .
    git commit -m "Initial commit: $NAME

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

    echo "  Pushing to GitHub..."
    git push -u origin main

    echo "  Enabling GitHub Pages..."
    gh api "repos/Johnesco/$NAME/pages" -X POST -f build_type=workflow 2>/dev/null || true

    echo ""
    echo "=== Published ==="
    echo "  Repo:  https://github.com/Johnesco/$NAME"
    echo "  Site:  https://johnesco.github.io/$NAME/play.html"
    echo "  (Pages may take a minute to deploy)"
else
    # --- Subsequent publishes ---
    echo "=== Publishing $NAME ==="

    # Stage everything
    git add .

    # Check if there are changes
    if git diff --cached --quiet; then
        echo "  No changes to publish."
        exit 0
    fi

    git commit -m "$MSG

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

    git push

    echo ""
    echo "=== Pushed ==="
    echo "  Site:  https://johnesco.github.io/$NAME/play.html"
    echo "  (Pages will redeploy automatically)"
fi
