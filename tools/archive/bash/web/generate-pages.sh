#!/bin/bash
# Generate project web pages (landing page + source browser) from templates.
#
# Usage:
#   bash /c/code/ifhub/tools/web/generate-pages.sh \
#       --title "Game Title" \
#       --meta "Subtitle" \
#       --description "Game description" \
#       --out /path/to/project
#
# Options:
#   --title TEXT        Game title (required)
#   --meta TEXT         Subtitle / tagline (default: "An Interactive Fiction")
#   --description TEXT  Game description (default: "An interactive fiction game.")
#   --out DIR           Output directory (required)
#   --force             Overwrite existing files
#
# Generates:
#   index.html    — Landing page (from landing-template.html)
#   source.html   — Source browser (from source-template.html)
#
# Skips files that already exist unless --force is passed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

TITLE=""
META="An Interactive Fiction"
DESCRIPTION="An interactive fiction game."
OUT_DIR=""
FORCE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --title)       TITLE="$2"; shift 2 ;;
        --meta)        META="$2"; shift 2 ;;
        --description) DESCRIPTION="$2"; shift 2 ;;
        --out)         OUT_DIR="$2"; shift 2 ;;
        --force)       FORCE=true; shift ;;
        *)             echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$TITLE" || -z "$OUT_DIR" ]]; then
    echo "Usage: generate-pages.sh --title \"Title\" --out /path/to/project" >&2
    echo "  Optional: --meta \"Subtitle\" --description \"Description\" --force" >&2
    exit 1
fi

# Escape values for sed safety (handles /, &, \ in text)
esc_sed() { printf '%s\n' "$1" | sed 's/[&/\]/\\&/g'; }
TITLE_ESC=$(esc_sed "$TITLE")
META_ESC=$(esc_sed "$META")
DESC_ESC=$(esc_sed "$DESCRIPTION")

GENERATED=0

# --- Landing page (index.html) ---
LANDING_TEMPLATE="$SCRIPT_DIR/landing-template.html"
if [[ ! -f "$LANDING_TEMPLATE" ]]; then
    echo "ERROR: Landing template not found: $LANDING_TEMPLATE" >&2
    exit 1
fi

if [[ ! -f "$OUT_DIR/index.html" || "$FORCE" == true ]]; then
    echo "Generating index.html..."
    sed -e "s/__TITLE__/$TITLE_ESC/g" \
        -e "s/__META__/$META_ESC/g" \
        -e "s/__DESCRIPTION__/$DESC_ESC/g" \
        "$LANDING_TEMPLATE" > "$OUT_DIR/index.html"
    GENERATED=$((GENERATED + 1))
else
    echo "  index.html already exists (use --force to overwrite)"
fi

# --- Source browser (source.html) ---
SOURCE_TEMPLATE="$SCRIPT_DIR/source-template.html"
if [[ ! -f "$SOURCE_TEMPLATE" ]]; then
    echo "ERROR: Source template not found: $SOURCE_TEMPLATE" >&2
    exit 1
fi

if [[ ! -f "$OUT_DIR/source.html" || "$FORCE" == true ]]; then
    echo "Generating source.html..."
    sed -e "s/__TITLE__/$TITLE_ESC/g" \
        "$SOURCE_TEMPLATE" > "$OUT_DIR/source.html"
    GENERATED=$((GENERATED + 1))
else
    echo "  source.html already exists (use --force to overwrite)"
fi

echo ""
echo "Generated $GENERATED page(s) in $OUT_DIR"
