#!/bin/bash
# Compile an Inform 7 project and update its web player.
#
# Usage:
#   bash /c/code/ifhub/tools/compile.sh <game-name> [--sound]
#
# Examples:
#   bash /c/code/ifhub/tools/compile.sh sample
#   bash /c/code/ifhub/tools/compile.sh zork1 --sound
#
# Steps:
#   1. Compiles story.ni → story.i6 (Inform 7 → Inform 6)
#   2. Compiles story.i6 → <name>.ulx (Inform 6 → Glulx)
#   When --sound is passed:
#     2b. generate-blurb.sh → <name>.blurb
#     2c. inblorb <name>.blurb → <name>.gblorb
#   3. Cleans up intermediates (story.i6, .blurb)
#   4. Sets up web player (encodes .gblorb if --sound, otherwise .ulx)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
I7_ROOT="$(dirname "$SCRIPT_DIR")"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <game-name> [--sound]" >&2
    echo "  Example: $0 zork1 --sound" >&2
    exit 1
fi

NAME="$1"
shift
SOUND=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sound) SOUND=true; shift ;;
        *)       echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

PROJECT_DIR="$I7_ROOT/projects/$NAME"

if [[ ! -f "$PROJECT_DIR/story.ni" ]]; then
    echo "ERROR: story.ni not found at $PROJECT_DIR/story.ni" >&2
    exit 1
fi

# --- Pre-flight checks (catch problems before expensive compilation) ---

# Check for colons in the story title — Windows cannot have colons in filenames,
# and Inform 7 derives filenames from the title. This causes inblorb to fail with
# an invalid "storyfile leafname" error on Windows.
TITLE_LINE=$(head -1 "$PROJECT_DIR/story.ni")
if [[ "$TITLE_LINE" == *":"* ]]; then
    echo "ERROR: story.ni title contains a colon:" >&2
    echo "  $TITLE_LINE" >&2
    echo "" >&2
    echo "  Colons in titles produce invalid filenames on Windows." >&2
    echo "  Replace ':' with '-' in the title (e.g. \"Zork I - The Great\")." >&2
    exit 1
fi

# When --sound is passed, verify Sounds/ directory exists at the project root
# BEFORE starting the expensive I7 compilation. compile.sh passes this path to
# generate-blurb.sh which would fail late otherwise.
if [[ "$SOUND" == true && ! -d "$PROJECT_DIR/Sounds" ]]; then
    echo "ERROR: --sound requires a Sounds/ directory at $PROJECT_DIR/Sounds" >&2
    echo "" >&2
    echo "  If your .ogg files are elsewhere (e.g. $NAME.materials/Sounds/)," >&2
    echo "  copy them to the project root:" >&2
    echo "    cp -r $PROJECT_DIR/$NAME.materials/Sounds $PROJECT_DIR/Sounds" >&2
    exit 1
fi

I7_COMPILER="/c/Program Files/Inform7IDE/Compilers/inform7.exe"
I6_COMPILER="/c/Program Files/Inform7IDE/Compilers/inform6.exe"
INBLORB="/c/Program Files/Inform7IDE/Compilers/inblorb.exe"
I7_INTERNAL="/c/Program Files/Inform7IDE/Internal"

if [[ "$SOUND" == true ]]; then
    TOTAL_STEPS=6
else
    TOTAL_STEPS=4
fi

echo "=== Compiling $NAME ==="

# Step 1: I7 → I6
echo "  [1/$TOTAL_STEPS] Inform 7 → Inform 6..."
"$I7_COMPILER" \
    -internal "$I7_INTERNAL" \
    -source "$PROJECT_DIR/story.ni" \
    -o "$PROJECT_DIR/story.i6" \
    -silence

# Step 2: I6 → Glulx
echo "  [2/$TOTAL_STEPS] Inform 6 → Glulx..."
"$I6_COMPILER" -w -G \
    "$PROJECT_DIR/story.i6" \
    "$PROJECT_DIR/$NAME.ulx"

if [[ "$SOUND" == true ]]; then
    # Step 2b: Generate blurb
    echo "  [3/$TOTAL_STEPS] Generating blurb..."
    bash "$SCRIPT_DIR/generate-blurb.sh" \
        --ulx "$PROJECT_DIR/$NAME.ulx" \
        --source "$PROJECT_DIR/story.ni" \
        --sounds "$PROJECT_DIR/Sounds" \
        --out "$PROJECT_DIR/$NAME.blurb"

    # Step 2c: Build blorb
    echo "  [4/$TOTAL_STEPS] Building blorb..."
    "$INBLORB" "$PROJECT_DIR/$NAME.blurb" "$PROJECT_DIR/$NAME.gblorb"
fi

# Step 3: Clean intermediates
STEP_CLEAN=$((TOTAL_STEPS - 1))
echo "  [$STEP_CLEAN/$TOTAL_STEPS] Cleaning up..."
rm -f "$PROJECT_DIR/story.i6"
if [[ "$SOUND" == true ]]; then
    rm -f "$PROJECT_DIR/$NAME.blurb"
fi

# Step 4: Update web player
echo "  [$TOTAL_STEPS/$TOTAL_STEPS] Updating web player..."
TEMPLATE_FLAG=""
if [[ -f "$PROJECT_DIR/play-template.html" ]]; then
    TEMPLATE_FLAG="--template $PROJECT_DIR/play-template.html"
    echo "  Using project template: $PROJECT_DIR/play-template.html"
fi
if [[ "$SOUND" == true ]]; then
    bash "$SCRIPT_DIR/web/setup-web.sh" \
        --title "$NAME" \
        --blorb "$PROJECT_DIR/$NAME.gblorb" \
        --out "$PROJECT_DIR/web" \
        $TEMPLATE_FLAG
else
    bash "$SCRIPT_DIR/web/setup-web.sh" \
        --title "$NAME" \
        --ulx "$PROJECT_DIR/$NAME.ulx" \
        --out "$PROJECT_DIR/web" \
        $TEMPLATE_FLAG
fi

ULX_SIZE=$(wc -c < "$PROJECT_DIR/$NAME.ulx" | tr -d ' ')
echo ""
echo "=== Done ==="
echo "  Binary: $PROJECT_DIR/$NAME.ulx ($ULX_SIZE bytes)"
if [[ "$SOUND" == true ]]; then
    BLORB_SIZE=$(wc -c < "$PROJECT_DIR/$NAME.gblorb" | tr -d ' ')
    echo "  Blorb:  $PROJECT_DIR/$NAME.gblorb ($BLORB_SIZE bytes)"
fi
echo "  Web:    $PROJECT_DIR/web/play.html"
echo ""
echo "  Test:   cd $PROJECT_DIR && wsl -e bash tests/run-tests.sh"
echo "  Play:   python -m http.server 8000 --directory $PROJECT_DIR/web"
