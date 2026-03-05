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
#   3. Base64-encodes .ulx (or .gblorb) into the web binary
#   4. Copies template files (player pages, lib/) from the previous version
#
# Update existing version (--update):
#   1. Recompiles from the version's own frozen story.ni (never overwrites it)
#   2. Auto-detects binary type (.gblorb vs .ulx) from existing web files
#   3. Re-encodes the compiled binary into the version's lib/parchment/
#   4. Copies walkthrough command files from tests/ (but not walkthrough_output.txt)

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
VERSION_DIR="$PROJECT_DIR/$VERSION"

if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "ERROR: Project not found: $PROJECT_DIR" >&2
    exit 1
fi

# --- Validate project ---
if [[ ! -f "$PROJECT_DIR/story.ni" && "$UPDATE" != true ]]; then
    echo "ERROR: No story.ni in $PROJECT_DIR" >&2
    exit 1
fi

if [[ "$UPDATE" == true ]]; then
    # --- Update existing version ---
    if [[ ! -d "$VERSION_DIR" ]]; then
        echo "ERROR: Version $VERSION does not exist yet. Run without --update to create it." >&2
        exit 1
    fi

    # Never overwrite frozen source — compile from the version's own story.ni
    if [[ ! -f "$VERSION_DIR/story.ni" ]]; then
        echo "ERROR: No frozen story.ni in $VERSION_DIR" >&2
        echo "  (This version may not have Inform 7 source — e.g. ZIL-only versions)" >&2
        exit 1
    fi

    echo "Updating $VERSION..."

    # Auto-detect binary type from existing web files
    BINARY_TYPE="ulx"
    if [[ -f "$VERSION_DIR/lib/parchment/$NAME.gblorb.js" ]]; then
        BINARY_TYPE="gblorb"
    fi
    echo "  Binary type: $BINARY_TYPE"

    # Recompile from the version's frozen source
    COMPILE_ARGS=("$NAME" --source "$VERSION_DIR/story.ni" --compile-only)
    if [[ "$BINARY_TYPE" == "gblorb" ]]; then
        COMPILE_ARGS+=(--sound)
    fi
    bash "$SCRIPT_DIR/compile.sh" "${COMPILE_ARGS[@]}"

    # Encode the compiled binary into the version's lib/parchment/
    if [[ "$BINARY_TYPE" == "gblorb" ]]; then
        B64=$(base64 -w 0 "$PROJECT_DIR/$NAME.gblorb")
        echo "processBase64Zcode('${B64}')" > "$VERSION_DIR/lib/parchment/$NAME.gblorb.js"
        echo "  $NAME.gblorb.js updated"
        # Also update .ulx.js companion if it exists
        if [[ -f "$VERSION_DIR/lib/parchment/$NAME.ulx.js" ]]; then
            B64_ULX=$(base64 -w 0 "$PROJECT_DIR/$NAME.ulx")
            echo "processBase64Zcode('${B64_ULX}')" > "$VERSION_DIR/lib/parchment/$NAME.ulx.js"
            echo "  $NAME.ulx.js updated (companion)"
        fi
    else
        B64=$(base64 -w 0 "$PROJECT_DIR/$NAME.ulx")
        echo "processBase64Zcode('${B64}')" > "$VERSION_DIR/lib/parchment/$NAME.ulx.js"
        echo "  $NAME.ulx.js updated"
    fi

    # Copy walkthrough command files if present (but NOT walkthrough_output.txt —
    # that's version-specific game output, generated from THIS version's binary)
    WALK_DIR="$PROJECT_DIR/tests/inform7"
    if [[ -d "$WALK_DIR" ]]; then
        for wf in walkthrough.txt walkthrough-guide.txt; do
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
    PREV_VERSION=""
    PREV_VERSION=$(ls -1d "$PROJECT_DIR"/v[0-9]* 2>/dev/null | sort -V | tail -1 || true)

    echo "Creating $VERSION..."
    mkdir -p "$VERSION_DIR"

    # Copy source
    cp "$PROJECT_DIR/story.ni" "$VERSION_DIR/story.ni"
    echo "  story.ni copied"

    # Encode binary — prefer .gblorb if it exists, else .ulx
    mkdir -p "$VERSION_DIR/lib/parchment"
    if [[ -f "$PROJECT_DIR/$NAME.gblorb" ]]; then
        B64=$(base64 -w 0 "$PROJECT_DIR/$NAME.gblorb")
        echo "processBase64Zcode('${B64}')" > "$VERSION_DIR/lib/parchment/$NAME.gblorb.js"
        echo "  $NAME.gblorb.js created"
        # Also encode .ulx companion if it exists
        if [[ -f "$PROJECT_DIR/$NAME.ulx" ]]; then
            B64_ULX=$(base64 -w 0 "$PROJECT_DIR/$NAME.ulx")
            echo "processBase64Zcode('${B64_ULX}')" > "$VERSION_DIR/lib/parchment/$NAME.ulx.js"
            echo "  $NAME.ulx.js created (companion)"
        fi
    elif [[ -f "$PROJECT_DIR/$NAME.ulx" ]]; then
        B64=$(base64 -w 0 "$PROJECT_DIR/$NAME.ulx")
        echo "processBase64Zcode('${B64}')" > "$VERSION_DIR/lib/parchment/$NAME.ulx.js"
        echo "  $NAME.ulx.js created"
    else
        echo "ERROR: No $NAME.gblorb or $NAME.ulx in $PROJECT_DIR — compile first" >&2
        exit 1
    fi

    # Copy template files from previous version
    if [[ -n "$PREV_VERSION" && -d "$PREV_VERSION" ]]; then
        PREV_NAME="$(basename "$PREV_VERSION")"
        echo "  Copying template from $PREV_NAME..."

        # Copy player pages (walkthrough.html generated from template below)
        for page in index.html parchment.html glulxe.html source.html; do
            if [[ -f "$PREV_VERSION/$page" ]]; then
                cp "$PREV_VERSION/$page" "$VERSION_DIR/$page"
                echo "    $page"
            fi
        done

        # Generate walkthrough.html from template
        WALK_TEMPLATE="$SCRIPT_DIR/web/walkthrough-template.html"
        if [[ -f "$WALK_TEMPLATE" ]]; then
            WALK_TITLE="Walkthrough — $(basename "$PROJECT_DIR") ($VERSION)"
            WALK_TITLE_ESCAPED=$(printf '%s\n' "$WALK_TITLE" | sed 's/[&/\]/\\&/g')
            sed -e "s/__TITLE__/$WALK_TITLE_ESCAPED/g" \
                -e "s/__HEADER__/Walkthrough ($VERSION)/g" \
                -e "s|__BACK_HREF__|../|g" \
                -e "s/__STORAGE_KEY__/$NAME/g" \
                "$WALK_TEMPLATE" > "$VERSION_DIR/walkthrough.html"
            echo "    walkthrough.html (generated from template)"
        elif [[ -f "$PREV_VERSION/walkthrough.html" ]]; then
            cp "$PREV_VERSION/walkthrough.html" "$VERSION_DIR/walkthrough.html"
            echo "    walkthrough.html (copied from $PREV_NAME)"
        fi

        # Copy lib/ (except the binary we already created)
        if [[ -d "$PREV_VERSION/lib" ]]; then
            # Copy non-parchment lib files (if any)
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
                if [[ "$fname" != *".ulx.js" && "$fname" != *".gblorb.js" && "$fname" != *".z3.js" ]]; then
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
