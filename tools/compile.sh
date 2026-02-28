#!/bin/bash
# Compile an Inform 7 project and update its web player.
#
# Usage:
#   bash /c/code/ifhub/tools/compile.sh <game-name>
#
# Example:
#   bash /c/code/ifhub/tools/compile.sh RNG
#
# Steps:
#   1. Compiles story.ni → story.i6 (Inform 7 → Inform 6)
#   2. Compiles story.i6 → <name>.ulx (Inform 6 → Glulx)
#   3. Cleans up story.i6
#   4. Sets up web player (copies Parchment libs if needed, encodes .ulx)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
I7_ROOT="$(dirname "$SCRIPT_DIR")"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <game-name>" >&2
    echo "  Example: $0 RNG" >&2
    exit 1
fi

NAME="$1"
PROJECT_DIR="$I7_ROOT/projects/$NAME"

if [[ ! -f "$PROJECT_DIR/story.ni" ]]; then
    echo "ERROR: story.ni not found at $PROJECT_DIR/story.ni" >&2
    exit 1
fi

I7_COMPILER="/c/Program Files/Inform7IDE/Compilers/inform7.exe"
I6_COMPILER="/c/Program Files/Inform7IDE/Compilers/inform6.exe"
I7_INTERNAL="/c/Program Files/Inform7IDE/Internal"

echo "=== Compiling $NAME ==="

# Step 1: I7 → I6
echo "  [1/4] Inform 7 → Inform 6..."
"$I7_COMPILER" \
    -internal "$I7_INTERNAL" \
    -source "$PROJECT_DIR/story.ni" \
    -o "$PROJECT_DIR/story.i6" \
    -silence

# Step 2: I6 → Glulx
echo "  [2/4] Inform 6 → Glulx..."
"$I6_COMPILER" -w -G \
    "$PROJECT_DIR/story.i6" \
    "$PROJECT_DIR/$NAME.ulx"

# Step 3: Clean intermediate
echo "  [3/4] Cleaning up..."
rm -f "$PROJECT_DIR/story.i6"

# Step 4: Update web player
echo "  [4/4] Updating web player..."
bash "$SCRIPT_DIR/web/setup-web.sh" \
    --title "$NAME" \
    --ulx "$PROJECT_DIR/$NAME.ulx" \
    --out "$PROJECT_DIR/web"

ULX_SIZE=$(wc -c < "$PROJECT_DIR/$NAME.ulx" | tr -d ' ')
echo ""
echo "=== Done ==="
echo "  Binary: $PROJECT_DIR/$NAME.ulx ($ULX_SIZE bytes)"
echo "  Web:    $PROJECT_DIR/web/play.html"
echo ""
echo "  Test:   cd $PROJECT_DIR && wsl -e bash tests/run-tests.sh"
echo "  Play:   python -m http.server 8000 --directory $PROJECT_DIR/web"
