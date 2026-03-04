#!/bin/bash
# Set up a Parchment web player for an Inform 7 project.
#
# Copies shared Parchment libraries from the central hub, base64-encodes the
# compiled .ulx binary, and generates play.html from the template.
#
# Usage:
#   bash /c/code/ifhub/tools/web/setup-web.sh \
#       --title "My Game" \
#       --ulx /path/to/game.ulx \
#       --out /path/to/project/web
#
#   bash /c/code/ifhub/tools/web/setup-web.sh \
#       --title "My Game" \
#       --blorb /path/to/game.gblorb \
#       --out /path/to/project/web
#
# --ulx:   Encode a naked .ulx binary (no embedded resources)
# --blorb: Encode a .gblorb blorb file (with embedded sounds/images)
#
# After setup, serve locally with:
#   python -m http.server 8000 --directory /path/to/project/web
#   # then open http://localhost:8000/play.html
#
# To update the game binary after recompiling, re-run this script or just:
#   B64=$(base64 -w 0 game.ulx) && echo "processBase64Zcode('${B64}')" > web/lib/parchment/game.ulx.js

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARCHMENT_SRC="$SCRIPT_DIR/parchment"
TITLE=""
ULX_PATH=""
BLORB_PATH=""
OUT_DIR=""
CUSTOM_TEMPLATE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --title)  TITLE="$2"; shift 2 ;;
        --ulx)    ULX_PATH="$2"; shift 2 ;;
        --blorb)  BLORB_PATH="$2"; shift 2 ;;
        --out)    OUT_DIR="$2"; shift 2 ;;
        --template) CUSTOM_TEMPLATE="$2"; shift 2 ;;
        *)        echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

TEMPLATE="${CUSTOM_TEMPLATE:-$SCRIPT_DIR/play-template.html}"

if [[ -z "$TITLE" || -z "$OUT_DIR" ]]; then
    echo "Usage: setup-web.sh --title \"Game Title\" --ulx path/to/game.ulx --out path/to/web" >&2
    echo "   or: setup-web.sh --title \"Game Title\" --blorb path/to/game.gblorb --out path/to/web" >&2
    exit 1
fi

if [[ -n "$BLORB_PATH" && -n "$ULX_PATH" ]]; then
    echo "Error: specify --ulx or --blorb, not both" >&2
    exit 1
fi

if [[ -z "$BLORB_PATH" && -z "$ULX_PATH" ]]; then
    echo "Error: specify --ulx or --blorb" >&2
    exit 1
fi

# Determine which binary to encode
if [[ -n "$BLORB_PATH" ]]; then
    if [[ ! -f "$BLORB_PATH" ]]; then
        echo "Error: Blorb file not found: $BLORB_PATH" >&2
        exit 1
    fi
    GAME_PATH="$BLORB_PATH"
    GAME_BASENAME="$(basename "$BLORB_PATH")"
else
    if [[ ! -f "$ULX_PATH" ]]; then
        echo "Error: ULX file not found: $ULX_PATH" >&2
        exit 1
    fi
    GAME_PATH="$ULX_PATH"
    GAME_BASENAME="$(basename "$ULX_PATH")"
fi

STORY_JS="${GAME_BASENAME}.js"

# Create output directories
mkdir -p "$OUT_DIR/lib/parchment"

# Copy Parchment libraries (Parchment 2025.1)
#
# IMPORTANT: parchment.js vs main.js
#   parchment.js — Full Parchment engine with AudioContext sound channel support.
#                  play.html MUST load this file for blorb sound to work.
#   main.js      — AsyncGlk standalone build with STUB sound functions (throws on
#                  schannel calls, hardcodes gestalt_Sound=0). Loading this instead
#                  of parchment.js silently disables all Glk sound — the game prints
#                  "[Sound effect number N here.]" text fallback instead of playing audio.
#
echo "Copying Parchment libraries..."
cp "$PARCHMENT_SRC/jquery.min.js" \
   "$PARCHMENT_SRC/main.js" \
   "$PARCHMENT_SRC/main.css" \
   "$PARCHMENT_SRC/parchment.js" \
   "$PARCHMENT_SRC/parchment.css" \
   "$PARCHMENT_SRC/quixe.js" \
   "$PARCHMENT_SRC/glulxe.js" \
   "$PARCHMENT_SRC/ie.js" \
   "$PARCHMENT_SRC/bocfel.js" \
   "$PARCHMENT_SRC/resourcemap.js" \
   "$PARCHMENT_SRC/zvm.js" \
   "$PARCHMENT_SRC/waiting.gif" \
   "$OUT_DIR/lib/parchment/"

# Base64-encode the game binary
echo "Encoding $GAME_BASENAME → $STORY_JS..."
B64=$(base64 -w 0 "$GAME_PATH")
echo "processBase64Zcode('${B64}')" > "$OUT_DIR/lib/parchment/$STORY_JS"

# Generate play.html from template
# Cache-busting: append ?v=<timestamp> to .js and .css src/href so browsers
# don't serve stale scripts after a rebuild. Without this, switching from
# main.js to parchment.js (or updating any library) can appear to have no
# effect until the user manually clears their cache.
CACHE_BUST="v=$(date +%s)"
echo "Generating play.html..."
sed -e "s/__TITLE__/$TITLE/g" \
    -e "s/__STORY_FILE__/$STORY_JS/g" \
    -e "s|__STORY_PATH__|lib/parchment/$STORY_JS|g" \
    -e "s|__LIB_PATH__|lib/parchment/|g" \
    -e "s/\.js\"/\.js?$CACHE_BUST\"/g" \
    -e "s/\.css\"/\.css?$CACHE_BUST\"/g" \
    "$TEMPLATE" > "$OUT_DIR/play.html"

# Validate: play.html must load parchment.js (not main.js) for sound to work.
# See the comment above about the difference between the two files.
# Patterns account for cache-busting query params (e.g. main.js?v=12345).
if grep -qE 'src="[^"]*main\.js(\?[^"]*)?"' "$OUT_DIR/play.html" && \
   ! grep -qE 'src="[^"]*parchment\.js(\?[^"]*)?"' "$OUT_DIR/play.html"; then
    echo "WARNING: play.html loads main.js instead of parchment.js!" >&2
    echo "  Blorb sound will NOT work. Fix the template at:" >&2
    echo "  $TEMPLATE" >&2
    echo "  Change: main.js → parchment.js" >&2
fi

# Validate: parchment_options must include story_name — parchment.js calls
# .substring() on it and crashes with "TypeError: Cannot read properties of
# undefined (reading 'substring')" if it's missing.
if ! grep -q 'story_name' "$OUT_DIR/play.html"; then
    echo "WARNING: play.html is missing story_name in parchment_options!" >&2
    echo "  parchment.js will crash. Fix the template at:" >&2
    echo "  $TEMPLATE" >&2
fi

echo ""
echo "Web player ready at: $OUT_DIR/play.html"
echo ""
echo "To play locally:"
echo "  python -m http.server 8000 --directory \"$OUT_DIR\""
echo "  # then open http://localhost:8000/play.html"
echo ""
echo "To update after recompiling:"
echo "  B64=\$(base64 -w 0 \"$GAME_PATH\") && echo \"processBase64Zcode('\${B64}')\" > \"$OUT_DIR/lib/parchment/$STORY_JS\""
