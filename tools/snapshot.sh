#!/bin/bash
# Freeze current working source into a version snapshot.
#
# Usage:
#   bash /c/code/ifhub/tools/snapshot.sh <game-name> <version>
#   bash /c/code/ifhub/tools/snapshot.sh <game-name> <version> --update
#
# Creates (or updates) a frozen version snapshot at versions/<version>/ in the project.
#
# New version (no --update):
#   1. Creates <version>/ directory
#   2. Copies story.ni from project root
#   3. Base64-encodes .ulx into <name>.ulx.js
#   4. Copies template files (player pages, lib/) from the previous version
#
# Update existing version (--update):
#   1. Overwrites story.ni from project root
#   2. Re-encodes .ulx into <name>.ulx.js
#   3. Copies walkthrough data from tests/ if present

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
I7_ROOT="$(dirname "$SCRIPT_DIR")"

# --- Args ---
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <game-name> <version> [--update]" >&2
    echo "  Example: $0 zork1 v4" >&2
    echo "  Example: $0 zork1 v3 --update" >&2
    exit 1
fi

NAME="$1"
VERSION="$2"
UPDATE=false
if [[ "${3:-}" == "--update" ]]; then
    UPDATE=true
fi

PROJECT_DIR="$I7_ROOT/projects/$NAME"
VERSIONS_DIR="$PROJECT_DIR/versions"
VERSION_DIR="$VERSIONS_DIR/$VERSION"

if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "ERROR: Project not found: $PROJECT_DIR" >&2
    exit 1
fi

# --- Validate source files ---
if [[ ! -f "$PROJECT_DIR/story.ni" ]]; then
    echo "ERROR: No story.ni in $PROJECT_DIR" >&2
    exit 1
fi

ULX_FILE="$PROJECT_DIR/$NAME.ulx"
if [[ ! -f "$ULX_FILE" ]]; then
    echo "ERROR: No $NAME.ulx in $PROJECT_DIR — compile first" >&2
    exit 1
fi

if [[ "$UPDATE" == true ]]; then
    # --- Update existing version ---
    if [[ ! -d "$VERSION_DIR" ]]; then
        echo "ERROR: Version $VERSION does not exist yet. Run without --update to create it." >&2
        exit 1
    fi

    echo "Updating $VERSION..."

    # Copy source
    cp "$PROJECT_DIR/story.ni" "$VERSION_DIR/story.ni"
    echo "  story.ni updated"

    # Encode binary
    B64=$(base64 -w 0 "$ULX_FILE")
    echo "processBase64Zcode('${B64}')" > "$VERSION_DIR/lib/parchment/$NAME.ulx.js"
    echo "  $NAME.ulx.js updated"

    # Copy walkthrough data if present
    WALK_DIR="$PROJECT_DIR/tests/inform7"
    if [[ -d "$WALK_DIR" ]]; then
        for wf in walkthrough.txt walkthrough-guide.txt walkthrough_output.txt; do
            if [[ -f "$WALK_DIR/$wf" ]]; then
                cp "$WALK_DIR/$wf" "$VERSION_DIR/$wf"
                echo "  $wf updated"
            fi
        done
    fi
else
    # --- Create new version ---
    if [[ -d "$VERSION_DIR" ]]; then
        echo "ERROR: Version $VERSION already exists. Use --update to refresh it." >&2
        exit 1
    fi

    # Find previous version to copy template from
    mkdir -p "$VERSIONS_DIR"
    PREV_VERSION=""
    PREV_VERSION=$(ls -1d "$VERSIONS_DIR"/v[0-9]* 2>/dev/null | sort -V | tail -1 || true)

    echo "Creating $VERSION..."
    mkdir -p "$VERSION_DIR"

    # Copy source
    cp "$PROJECT_DIR/story.ni" "$VERSION_DIR/story.ni"
    echo "  story.ni copied"

    # Encode binary
    mkdir -p "$VERSION_DIR/lib/parchment"
    B64=$(base64 -w 0 "$ULX_FILE")
    echo "processBase64Zcode('${B64}')" > "$VERSION_DIR/lib/parchment/$NAME.ulx.js"
    echo "  $NAME.ulx.js created"

    # Copy template files from previous version
    if [[ -n "$PREV_VERSION" && -d "$PREV_VERSION" ]]; then
        PREV_NAME="$(basename "$PREV_VERSION")"
        echo "  Copying template from $PREV_NAME..."

        # Copy player pages
        for page in index.html parchment.html glulxe.html source.html walkthrough.html; do
            if [[ -f "$PREV_VERSION/$page" ]]; then
                cp "$PREV_VERSION/$page" "$VERSION_DIR/$page"
                echo "    $page"
            fi
        done

        # Copy lib/ (except the binary we already created)
        if [[ -d "$PREV_VERSION/lib" ]]; then
            # Copy non-parchment lib files (e.g., ambient-audio.js)
            for f in "$PREV_VERSION"/lib/*; do
                fname="$(basename "$f")"
                if [[ "$fname" != "parchment" ]]; then
                    cp -r "$f" "$VERSION_DIR/lib/$fname"
                    echo "    lib/$fname"
                fi
            done
            # Copy parchment engine files (not the binary)
            for f in "$PREV_VERSION"/lib/parchment/*; do
                fname="$(basename "$f")"
                if [[ "$fname" != *".ulx.js" && "$fname" != *".z3.js" ]]; then
                    cp "$f" "$VERSION_DIR/lib/parchment/$fname"
                    echo "    lib/parchment/$fname"
                fi
            done
        fi

        # Copy media/ if present
        if [[ -d "$PREV_VERSION/media" ]]; then
            cp -r "$PREV_VERSION/media" "$VERSION_DIR/media"
            echo "    media/"
        fi

        # Copy audio/ if present
        if [[ -d "$PREV_VERSION/audio" ]]; then
            cp -r "$PREV_VERSION/audio" "$VERSION_DIR/audio"
            echo "    audio/"
        fi
    else
        echo "  No previous version found — created minimal snapshot"
        echo "  You will need to add player pages manually"
    fi

    # Copy walkthrough data if present
    WALK_DIR="$PROJECT_DIR/tests/inform7"
    if [[ -d "$WALK_DIR" ]]; then
        for wf in walkthrough.txt walkthrough-guide.txt; do
            if [[ -f "$WALK_DIR/$wf" ]]; then
                cp "$WALK_DIR/$wf" "$VERSION_DIR/$wf"
                echo "  $wf copied"
            fi
        done
    fi
fi

echo ""
echo "Done. Version at: $VERSION_DIR"
