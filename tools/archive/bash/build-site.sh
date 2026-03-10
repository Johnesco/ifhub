#!/bin/bash
# Assemble a deployable _site/ directory from a flat project layout.
#
# Usage:
#   bash /c/code/ifhub/tools/build-site.sh <game-name>
#
# Copies site-level files (HTML, lib/, data) and version directories (v0/, v1/, etc.)
# into _site/ for local preview. GitHub Pages can deploy the project root directly.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
I7_ROOT="$(dirname "$SCRIPT_DIR")"

# --- Args ---
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <game-name>" >&2
    echo "  Example: $0 zork1" >&2
    exit 1
fi

NAME="$1"
PROJECT_DIR="$I7_ROOT/projects/$NAME"

if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "ERROR: Project not found: $PROJECT_DIR" >&2
    exit 1
fi

SITE_DIR="$PROJECT_DIR/_site"

# --- Clean ---
rm -rf "$SITE_DIR"
mkdir -p "$SITE_DIR"

# --- Copy site-level files ---
for f in "$PROJECT_DIR"/*.html "$PROJECT_DIR"/*.txt "$PROJECT_DIR"/*.ni; do
    [[ -f "$f" ]] && cp "$f" "$SITE_DIR/" && echo "  Copied $(basename "$f")"
done
[[ -d "$PROJECT_DIR/lib" ]] && cp -r "$PROJECT_DIR/lib" "$SITE_DIR/lib" && echo "  Copied lib/"
[[ -d "$PROJECT_DIR/scenarios" ]] && cp -r "$PROJECT_DIR/scenarios" "$SITE_DIR/scenarios" && echo "  Copied scenarios/"

# --- Copy version snapshots ---
found_versions=false
for v in "$PROJECT_DIR"/v[0-9]*/; do
    if [[ -d "$v" ]]; then
        vname="$(basename "$v")"
        cp -r "$v" "$SITE_DIR/$vname"
        echo "  Copied $vname/"
        found_versions=true
    fi
done
if [[ "$found_versions" == false ]]; then
    echo "  No version snapshots found"
fi

echo ""
echo "Site assembled at: $SITE_DIR"
echo "Serve with:  python -m http.server 8000 --directory \"$SITE_DIR\""
