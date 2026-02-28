#!/bin/bash
# Assemble a deployable _site/ directory from web/ + version snapshots.
#
# Usage:
#   bash /c/code/ifhub/tools/build-site.sh <game-name>
#
# Copies web/* into _site/, then overlays each versions/vN/ as _site/vN/.
# If no version snapshots exist, _site/ is just a copy of web/.
#
# The assembled _site/ is what gets deployed to GitHub Pages.

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

if [[ ! -d "$PROJECT_DIR/web" ]]; then
    echo "ERROR: No web/ directory in $PROJECT_DIR" >&2
    exit 1
fi

SITE_DIR="$PROJECT_DIR/_site"

# --- Clean ---
rm -rf "$SITE_DIR"
mkdir -p "$SITE_DIR"

# --- Copy web/ ---
cp -r "$PROJECT_DIR/web/"* "$SITE_DIR/"
echo "  Copied web/ -> _site/"

# --- Overlay version snapshots ---
VERSIONS_DIR="$PROJECT_DIR/versions"
found_versions=false
if [[ -d "$VERSIONS_DIR" ]]; then
    for v in "$VERSIONS_DIR"/v[0-9]*/; do
        if [[ -d "$v" ]]; then
            vname="$(basename "$v")"
            cp -r "$v" "$SITE_DIR/$vname"
            echo "  Copied versions/$vname/ -> _site/$vname/"
            found_versions=true
        fi
    done
fi
if [[ "$found_versions" == false ]]; then
    echo "  No version snapshots found — _site/ is web/ only"
fi

echo ""
echo "Site assembled at: $SITE_DIR"
echo "Serve with:  python -m http.server 8000 --directory \"$SITE_DIR\""
