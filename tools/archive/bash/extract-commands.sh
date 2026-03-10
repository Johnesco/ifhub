#!/bin/bash
# Extract walkthrough commands from a game transcript.
#
# Takes a transcript file (produced by the TRANSCRIPT command in any
# interpreter — Parchment, Inform 7 IDE, glulxe, etc.) and extracts
# just the player commands into walkthrough.txt format.
#
# Usage:
#   bash /c/code/ifhub/tools/extract-commands.sh transcript.txt
#   bash /c/code/ifhub/tools/extract-commands.sh transcript.txt -o walkthrough.txt
#   bash /c/code/ifhub/tools/extract-commands.sh --from-source story.ni
#
# Modes:
#   (default)       Extract commands from a TRANSCRIPT file (lines starting with >)
#   --from-source   Extract commands from "Test me with ..." in a story.ni file
#
# Output goes to stdout by default. Use -o to write to a file.
#
# After extracting, run compile.sh to generate the full walkthrough:
#   bash /c/code/ifhub/tools/compile.sh <game-name>

set -euo pipefail

MODE="transcript"
INPUT=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --from-source) MODE="source"; shift ;;
        -o)            OUTPUT="$2"; shift 2 ;;
        -*)            echo "Unknown option: $1" >&2; exit 1 ;;
        *)             INPUT="$1"; shift ;;
    esac
done

if [[ -z "$INPUT" ]]; then
    echo "Usage: extract-commands.sh TRANSCRIPT_FILE [-o OUTPUT]" >&2
    echo "       extract-commands.sh --from-source STORY.NI [-o OUTPUT]" >&2
    exit 1
fi

if [[ ! -f "$INPUT" ]]; then
    echo "ERROR: File not found: $INPUT" >&2
    exit 1
fi

extract_from_transcript() {
    # Transcript lines look like:  >command  or  > command
    # Skip meta-commands: TRANSCRIPT, SCRIPT, QUIT, RESTART, RESTORE, SAVE, UNDO
    grep '^>' "$1" \
        | sed 's/^> *//' \
        | grep -ivE '^(transcript|script|quit|restart|restore|save|undo)( |$)' \
        | sed '/^$/d'
}

extract_from_source() {
    # Parse Inform 7 "Test ... with ..." definitions.
    # Starts from "Test me" and expands references to sub-tests recursively.
    # e.g. Test me with "test first / test second".
    #      Test first with "n / take key".
    # → outputs: n / take key / (commands from test second)
    python3 -c "
import re, sys

text = open(sys.argv[1], 'r', encoding='utf-8').read()

# Build lookup: test name → list of commands
tests = {}
for m in re.finditer(r'Test\s+(\w+)\s+with\s+\"([^\"]+)\"', text, re.IGNORECASE):
    name = m.group(1).lower()
    cmds = [c.strip() for c in m.group(2).split(' / ') if c.strip()]
    tests[name] = cmds

def expand(cmds, seen=None):
    if seen is None:
        seen = set()
    result = []
    for cmd in cmds:
        # Check if this command is 'test <name>' referencing another test
        ref = re.match(r'^test\s+(\w+)$', cmd, re.IGNORECASE)
        if ref and ref.group(1).lower() in tests and ref.group(1).lower() not in seen:
            seen.add(ref.group(1).lower())
            result.extend(expand(tests[ref.group(1).lower()], seen))
        else:
            result.append(cmd)
    return result

# Start from 'Test me', fall back to all tests in order
if 'me' in tests:
    for cmd in expand(tests['me']):
        print(cmd)
else:
    for name in tests:
        for cmd in expand(tests[name]):
            print(cmd)
" "$1"
}

# Run extraction
if [[ "$MODE" == "transcript" ]]; then
    RESULT=$(extract_from_transcript "$INPUT")
else
    RESULT=$(extract_from_source "$INPUT")
fi

COUNT=$(echo "$RESULT" | grep -c . || true)

if [[ "$COUNT" -eq 0 ]]; then
    echo "No commands found in $INPUT" >&2
    exit 1
fi

# Output
if [[ -n "$OUTPUT" ]]; then
    if [[ -f "$OUTPUT" ]]; then
        echo "WARNING: $OUTPUT already exists — overwriting" >&2
    fi
    echo "$RESULT" > "$OUTPUT"
    echo "Extracted $COUNT commands → $OUTPUT"
else
    echo "$RESULT"
fi
