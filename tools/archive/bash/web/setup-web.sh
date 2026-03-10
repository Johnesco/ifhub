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
# --force: Overwrite play.html and walkthrough.html even if they already exist
#
# Safety: play.html and walkthrough.html are SKIPPED if they already exist
# (they may contain custom CSS, effects, or hand-crafted content).
# The game binary and Parchment libraries are always updated.
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
WALKTHROUGH=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --title)  TITLE="$2"; shift 2 ;;
        --ulx)    ULX_PATH="$2"; shift 2 ;;
        --blorb)  BLORB_PATH="$2"; shift 2 ;;
        --out)    OUT_DIR="$2"; shift 2 ;;
        --template) CUSTOM_TEMPLATE="$2"; shift 2 ;;
        --walkthrough) WALKTHROUGH=true; shift ;;
        --force)  FORCE=true; shift ;;
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

# Generate play.html from template (skip if exists — may contain custom work)
if [[ -f "$OUT_DIR/play.html" && "$FORCE" != true ]]; then
    echo "  play.html already exists (use --force to overwrite)"
else
    # Cache-busting: append ?v=<timestamp> to .js and .css src/href so browsers
    # don't serve stale scripts after a rebuild. Without this, switching from
    # main.js to parchment.js (or updating any library) can appear to have no
    # effect until the user manually clears their cache.
    CACHE_BUST="v=$(date +%s)"
    # Escape title for sed safety (handles /, &, \ in titles)
    TITLE_ESCAPED=$(printf '%s\n' "$TITLE" | sed 's/[&/\]/\\&/g')
    echo "Generating play.html..."
    sed -e "s/__TITLE__/$TITLE_ESCAPED/g" \
        -e "s/__STORY_FILE__/$STORY_JS/g" \
        -e "s|__STORY_PATH__|lib/parchment/$STORY_JS|g" \
        -e "s|__LIB_PATH__|lib/parchment/|g" \
        -e "s/\.js\"/\.js?$CACHE_BUST\"/g" \
        -e "s/\.css\"/\.css?$CACHE_BUST\"/g" \
        "$TEMPLATE" > "$OUT_DIR/play.html"
fi

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

# Generate walkthrough.html from template if requested (skip if exists)
if [[ "$WALKTHROUGH" == true ]]; then
    if [[ -f "$OUT_DIR/walkthrough.html" && "$FORCE" != true ]]; then
        echo "  walkthrough.html already exists (use --force to overwrite)"
    else
        WALK_TEMPLATE="$SCRIPT_DIR/walkthrough-template.html"
        if [[ -f "$WALK_TEMPLATE" ]]; then
            # Derive storage key from game binary name (e.g. "zork1" from "zork1.ulx")
            STORAGE_KEY=$(basename "${GAME_PATH%.*}" | sed 's/\..*//')
            TITLE_ESCAPED_WALK=$(printf '%s\n' "Walkthrough — $TITLE" | sed 's/[&/\]/\\&/g')
            echo "Generating walkthrough.html..."
            sed -e "s/__TITLE__/$TITLE_ESCAPED_WALK/g" \
                -e "s/__HEADER__/Walkthrough/g" \
                -e "s|__BACK_HREF__|play.html|g" \
                -e "s/__STORAGE_KEY__/$STORAGE_KEY/g" \
                "$WALK_TEMPLATE" > "$OUT_DIR/walkthrough.html"
            echo "  walkthrough.html generated"
        else
            echo "WARNING: walkthrough template not found at $WALK_TEMPLATE" >&2
        fi
    fi
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
