#!/bin/bash
# Generate a .blurb file for inblorb from an Inform 7 source file.
#
# Parses story.ni for "Sound of ... is the file ..." declarations,
# assigns resource IDs starting from 3 (1=cover, 2=small cover by convention),
# and outputs a .blurb file suitable for inblorb.
#
# Usage:
#   bash /c/code/ifhub/tools/generate-blurb.sh \
#       --ulx /path/to/game.ulx \
#       --source /path/to/story.ni \
#       --sounds /path/to/Sounds/ \
#       --out /path/to/game.blurb
#
# Example:
#   bash /c/code/ifhub/tools/generate-blurb.sh \
#       --ulx projects/zork1/zork1.ulx \
#       --source projects/zork1/story.ni \
#       --sounds projects/zork1/Sounds/ \
#       --out projects/zork1/zork1.blurb

set -euo pipefail

ULX_PATH=""
SOURCE_PATH=""
SOUNDS_DIR=""
OUT_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ulx)     ULX_PATH="$2"; shift 2 ;;
        --source)  SOURCE_PATH="$2"; shift 2 ;;
        --sounds)  SOUNDS_DIR="$2"; shift 2 ;;
        --out)     OUT_PATH="$2"; shift 2 ;;
        *)         echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$ULX_PATH" || -z "$SOURCE_PATH" || -z "$SOUNDS_DIR" || -z "$OUT_PATH" ]]; then
    echo "Usage: generate-blurb.sh --ulx game.ulx --source story.ni --sounds Sounds/ --out game.blurb" >&2
    exit 1
fi

if [[ ! -f "$SOURCE_PATH" ]]; then
    echo "Error: Source file not found: $SOURCE_PATH" >&2
    exit 1
fi

if [[ ! -f "$ULX_PATH" ]]; then
    echo "Error: ULX file not found: $ULX_PATH" >&2
    exit 1
fi

if [[ ! -d "$SOUNDS_DIR" ]]; then
    echo "Error: Sounds directory not found: $SOUNDS_DIR" >&2
    exit 1
fi

# Extract sound declarations from story.ni in order
# Pattern: Sound of <name> is the file "<filename>"
# Resource IDs start at 3 (1=cover image, 2=small cover by convention)

# Collect filenames into an array to avoid subshell issues
mapfile -t SOUND_FILES < <(grep -o 'Sound of .* is the file "[^"]*"' "$SOURCE_PATH" | sed 's/.*is the file "\([^"]*\)"/\1/' || true)

if [[ ${#SOUND_FILES[@]} -eq 0 ]]; then
    echo "Error: No sound declarations found in $SOURCE_PATH" >&2
    exit 1
fi

# Convert Git Bash paths to Windows paths for inblorb.exe
to_win_path() {
    local p="$1"
    # Convert /c/... to C:\...
    if [[ "$p" =~ ^/([a-zA-Z])/ ]]; then
        p="${BASH_REMATCH[1]^^}:${p:2}"
    fi
    # Convert forward slashes to backslashes
    echo "${p//\//\\}"
}

{
    echo "storyfile \"$(to_win_path "$ULX_PATH")\" include"

    RESOURCE_ID=3
    for filename in "${SOUND_FILES[@]}"; do
        SOUND_FILE="$SOUNDS_DIR/$filename"
        if [[ ! -f "$SOUND_FILE" ]]; then
            echo "WARNING: Sound file not found: $SOUND_FILE" >&2
        fi
        echo "sound $RESOURCE_ID \"$(to_win_path "$SOUNDS_DIR/$filename")\""
        RESOURCE_ID=$((RESOURCE_ID + 1))
    done
} > "$OUT_PATH"

COUNT=${#SOUND_FILES[@]}
echo "Generated $OUT_PATH with $COUNT sound resources (IDs 3–$((3 + COUNT - 1)))"
