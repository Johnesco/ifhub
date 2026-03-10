#!/bin/bash
# Compile an Inform 7 project and optionally update its web player.
#
# Usage:
#   bash /c/code/ifhub/tools/compile.sh <game-name> [--sound] [--source PATH] [--compile-only] [--force]
#
# Options:
#   --sound          Embed .ogg audio in a .gblorb binary
#   --source PATH    Use this story.ni instead of the project's own
#   --compile-only   Skip the web player update step (setup-web.sh + validate-web.sh)
#   --force          Overwrite play.html even if it already exists (may have custom CSS)
#
# Examples:
#   bash /c/code/ifhub/tools/compile.sh sample
#   bash /c/code/ifhub/tools/compile.sh zork1 --sound
#   bash /c/code/ifhub/tools/compile.sh zork1 --source v1/story.ni --compile-only
#
# Steps:
#   1. Compiles story.ni → story.i6 (Inform 7 → Inform 6)
#   2. Compiles story.i6 → <name>.ulx (Inform 6 → Glulx)
#   When --sound is passed:
#     2b. generate-blurb.sh → <name>.blurb
#     2c. inblorb <name>.blurb → <name>.gblorb
#   3. Cleans up intermediates (story.i6, .blurb)
#   4. Sets up web player (unless --compile-only)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
I7_ROOT="$(dirname "$SCRIPT_DIR")"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <game-name> [--sound] [--source PATH] [--compile-only]" >&2
    echo "  Example: $0 zork1 --sound" >&2
    exit 1
fi

NAME="$1"
shift
SOUND=false
SOURCE_PATH=""
COMPILE_ONLY=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sound)        SOUND=true; shift ;;
        --source)       SOURCE_PATH="$2"; shift 2 ;;
        --compile-only) COMPILE_ONLY=true; shift ;;
        --force)        FORCE=true; shift ;;
        *)              echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

PROJECT_DIR="$I7_ROOT/projects/$NAME"

SOURCE_FILE="${SOURCE_PATH:-$PROJECT_DIR/story.ni}"

if [[ ! -f "$SOURCE_FILE" ]]; then
    echo "ERROR: story.ni not found at $SOURCE_FILE" >&2
    exit 1
fi

# --- Pre-flight checks (catch problems before expensive compilation) ---

# Check for colons in the story title — Windows cannot have colons in filenames,
# and Inform 7 derives filenames from the title. This causes inblorb to fail with
# an invalid "storyfile leafname" error on Windows.
TITLE_LINE=$(head -1 "$SOURCE_FILE")

# Extract the game title from story.ni (first quoted string on the first line)
# e.g. "Zork I - The Great Underground Empire" by "John Doe" → Zork I - The Great Underground Empire
GAME_TITLE=$(echo "$TITLE_LINE" | sed -n 's/^"\([^"]*\)".*/\1/p')
if [[ -z "$GAME_TITLE" ]]; then
    GAME_TITLE="$NAME"  # fallback to directory name
fi

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
    -source "$SOURCE_FILE" \
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
        --source "$SOURCE_FILE" \
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

# Step 4: Update web player (skip with --compile-only)
if [[ "$COMPILE_ONLY" != true ]]; then
    echo "  [$TOTAL_STEPS/$TOTAL_STEPS] Updating web player..."
    # Detect web output directory: web/ if it exists (versioned projects), else project root
    if [[ -d "$PROJECT_DIR/web" ]]; then
        WEB_DIR="$PROJECT_DIR/web"
    else
        WEB_DIR="$PROJECT_DIR"
    fi
    TEMPLATE_FLAG=""
    if [[ -f "$PROJECT_DIR/play-template.html" ]]; then
        TEMPLATE_FLAG="--template $PROJECT_DIR/play-template.html"
        echo "  Using project template: $PROJECT_DIR/play-template.html"
    fi
    FORCE_FLAG=""
    if [[ "$FORCE" == true ]]; then
        FORCE_FLAG="--force"
    fi
    if [[ "$SOUND" == true ]]; then
        bash "$SCRIPT_DIR/web/setup-web.sh" \
            --title "$GAME_TITLE" \
            --blorb "$PROJECT_DIR/$NAME.gblorb" \
            --out "$WEB_DIR" \
            --walkthrough \
            $TEMPLATE_FLAG $FORCE_FLAG
    else
        bash "$SCRIPT_DIR/web/setup-web.sh" \
            --title "$GAME_TITLE" \
            --ulx "$PROJECT_DIR/$NAME.ulx" \
            --out "$WEB_DIR" \
            --walkthrough \
            $TEMPLATE_FLAG $FORCE_FLAG
    fi

    # Generate walkthrough transcript if commands exist and interpreter is available
    WALK_CMDS="$PROJECT_DIR/tests/inform7/walkthrough.txt"
    WALK_OUT="$PROJECT_DIR/tests/inform7/walkthrough_output.txt"
    WALK_GUIDE="$PROJECT_DIR/tests/inform7/walkthrough-guide.txt"
    GLULXE="$SCRIPT_DIR/interpreters/glulxe.exe"
    if [[ -f "$WALK_CMDS" && -x "$GLULXE" ]]; then
        echo ""
        echo "Generating walkthrough transcript..."
        mkdir -p "$PROJECT_DIR/tests/inform7"
        "$GLULXE" -q "$PROJECT_DIR/$NAME.ulx" < "$WALK_CMDS" > "$WALK_OUT" 2>/dev/null || true
        if [[ -s "$WALK_OUT" ]]; then
            echo "  Transcript: $WALK_OUT"
            # Generate annotated guide
            python "$SCRIPT_DIR/testing/generate-guide.py" \
                --walkthrough "$WALK_CMDS" \
                --transcript "$WALK_OUT" \
                -o "$WALK_GUIDE" 2>/dev/null || true
            # Copy to project root for web serving
            cp "$WALK_OUT" "$WEB_DIR/"
            cp "$WALK_CMDS" "$WEB_DIR/"
            [[ -f "$WALK_GUIDE" ]] && cp "$WALK_GUIDE" "$WEB_DIR/"
        fi
    fi

    # Validate web player
    echo ""
    echo "Validating web player..."
    bash "$SCRIPT_DIR/validate-web.sh" "$WEB_DIR"
else
    echo "  [$TOTAL_STEPS/$TOTAL_STEPS] Skipping web player (--compile-only)"
fi

ULX_SIZE=$(wc -c < "$PROJECT_DIR/$NAME.ulx" | tr -d ' ')
echo ""
echo "=== Done ==="
echo "  Binary: $PROJECT_DIR/$NAME.ulx ($ULX_SIZE bytes)"
if [[ "$SOUND" == true ]]; then
    BLORB_SIZE=$(wc -c < "$PROJECT_DIR/$NAME.gblorb" | tr -d ' ')
    echo "  Blorb:  $PROJECT_DIR/$NAME.gblorb ($BLORB_SIZE bytes)"
fi
echo "  Web:    $WEB_DIR/play.html"
echo ""
if [[ ("$OSTYPE" == "msys" || "$OSTYPE" == "cygwin") && -x "$SCRIPT_DIR/interpreters/glulxe.exe" ]]; then
    echo "  Test:   cd $PROJECT_DIR && bash tests/run-tests.sh"
else
    echo "  Test:   cd $PROJECT_DIR && wsl -e bash tests/run-tests.sh"
fi
echo "  Play:   python -m http.server 8000 --directory $WEB_DIR"
