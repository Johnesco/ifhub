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
#       --out /path/to/project/web \
#       [--sound]
#
# The --sound flag copies the shared sound-engine.js into lib/.
# You still need to create a game-specific lib/sound-config.js and
# add the two <script> tags to play.html (or your template).
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
TEMPLATE="$SCRIPT_DIR/play-template.html"

TITLE=""
ULX_PATH=""
OUT_DIR=""
SOUND=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --title)  TITLE="$2"; shift 2 ;;
        --ulx)    ULX_PATH="$2"; shift 2 ;;
        --out)    OUT_DIR="$2"; shift 2 ;;
        --sound)  SOUND=true; shift ;;
        *)        echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$TITLE" || -z "$ULX_PATH" || -z "$OUT_DIR" ]]; then
    echo "Usage: setup-web.sh --title \"Game Title\" --ulx path/to/game.ulx --out path/to/web [--sound]" >&2
    exit 1
fi

if [[ ! -f "$ULX_PATH" ]]; then
    echo "Error: ULX file not found: $ULX_PATH" >&2
    exit 1
fi

ULX_BASENAME="$(basename "$ULX_PATH")"
STORY_JS="${ULX_BASENAME}.js"

# Create output directories
mkdir -p "$OUT_DIR/lib/parchment"

# Copy Parchment libraries (all 7 required files)
echo "Copying Parchment libraries..."
cp "$PARCHMENT_SRC/jquery.min.js" \
   "$PARCHMENT_SRC/main.js" \
   "$PARCHMENT_SRC/main.css" \
   "$PARCHMENT_SRC/parchment.js" \
   "$PARCHMENT_SRC/parchment.css" \
   "$PARCHMENT_SRC/quixe.js" \
   "$PARCHMENT_SRC/glulxe.js" \
   "$OUT_DIR/lib/parchment/"

# Base64-encode the game binary
echo "Encoding $ULX_BASENAME → $STORY_JS..."
B64=$(base64 -w 0 "$ULX_PATH")
echo "processBase64Zcode('${B64}')" > "$OUT_DIR/lib/parchment/$STORY_JS"

# Generate play.html from template
echo "Generating play.html..."
sed -e "s/__TITLE__/$TITLE/g" \
    -e "s/__STORY_FILE__/$STORY_JS/g" \
    "$TEMPLATE" > "$OUT_DIR/play.html"

# Optionally copy sound engine
if [[ "$SOUND" == true ]]; then
    echo "Copying sound engine..."
    cp "$SCRIPT_DIR/sound-engine.js" "$OUT_DIR/lib/"
    echo "  → lib/sound-engine.js"
    echo "  NOTE: Create lib/sound-config.js with your game's triggers."
    echo "  Add to play.html before </body>:"
    echo '    <script src="lib/sound-engine.js"></script>'
    echo '    <script src="lib/sound-config.js"></script>'
fi

echo ""
echo "Web player ready at: $OUT_DIR/play.html"
echo ""
echo "To play locally:"
echo "  python -m http.server 8000 --directory \"$OUT_DIR\""
echo "  # then open http://localhost:8000/play.html"
echo ""
echo "To update after recompiling:"
echo "  B64=\$(base64 -w 0 \"$ULX_PATH\") && echo \"processBase64Zcode('\${B64}')\" > \"$OUT_DIR/lib/parchment/$STORY_JS\""
