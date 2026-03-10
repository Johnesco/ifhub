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

if [[ ! -f "$PROJECT_DIR/play.html" && ! -f "$PROJECT_DIR/web/play.html" ]]; then
    echo "ERROR: play.html not found. Run compile.sh first." >&2
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

    echo "  Enabling GitHub Pages (workflow deployment)..."
    # Ensure workflow file exists for deployment
    if [[ ! -f ".github/workflows/deploy-pages.yml" ]]; then
        echo "  Adding deploy-pages.yml workflow..."
        mkdir -p .github/workflows
        cat > .github/workflows/deploy-pages.yml << 'WORKFLOW_EOF'
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - name: Assemble site
        run: |
          mkdir -p _site
          [ -d web ] && cp -r web/* _site/ || true
          [ -d lib ] && cp -r lib _site/ || true
          cp *.html _site/ 2>/dev/null || true
          cp *.txt _site/ 2>/dev/null || true
          cp story.ni _site/ 2>/dev/null || true
          shopt -s nullglob
          for v in v[0-9]*/; do
            cp -r "$v" "_site/$v"
          done
      - uses: actions/upload-pages-artifact@v3
        with:
          path: _site
      - id: deployment
        uses: actions/deploy-pages@v4
WORKFLOW_EOF
        git add .github/workflows/deploy-pages.yml
        git commit --amend --no-edit
    fi
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
