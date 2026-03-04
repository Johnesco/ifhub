#!/bin/bash
# Generic walkthrough test runner for Inform 7 projects
# Runs a walkthrough through an interpreter with optional RNG seeding
# and produces diagnostic output.
#
# Requires a project.conf file (--config) with engine paths, patterns, etc.
#
# Usage:
#   bash run-walkthrough.sh --config PATH              # Primary engine, golden seed
#   bash run-walkthrough.sh --config PATH --alt         # Alternate engine, golden seed
#   bash run-walkthrough.sh --config PATH --seed 42     # Override seed
#   bash run-walkthrough.sh --config PATH --no-seed     # True randomness
#   bash run-walkthrough.sh --config PATH --diff        # Compare output vs saved baseline
#   bash run-walkthrough.sh --config PATH --quiet       # Suppress diagnostic output, just exit code
#   bash run-walkthrough.sh --config PATH --no-save     # Don't overwrite saved output file
#   bash run-walkthrough.sh --config PATH --copy-output DIR  # Copy output to DIR after success

set -euo pipefail

# Resolve PCRE grep helper (portable grep -oP replacement)
PCRE_GREP="$(cd "$(dirname "$0")" && pwd)/pcre_grep.py"

# Defaults
CONFIG=""
MODE="primary"
SEED=""
NO_SEED=false
DIFF_MODE=false
QUIET=false
SAVE_OUTPUT=true
COPY_OUTPUT_DIR=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --config)
            CONFIG="$2"
            shift 2
            ;;
        --alt)
            MODE="alt"
            shift
            ;;
        --seed)
            SEED="$2"
            shift 2
            ;;
        --no-seed)
            NO_SEED=true
            shift
            ;;
        --diff)
            DIFF_MODE=true
            shift
            ;;
        --quiet|-q)
            QUIET=true
            shift
            ;;
        --no-save)
            SAVE_OUTPUT=false
            shift
            ;;
        --copy-output)
            COPY_OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Usage: $0 --config PATH [--alt] [--seed N] [--no-seed] [--diff] [--quiet] [--no-save] [--copy-output DIR]" >&2
            exit 2
            ;;
    esac
done

# Validate config
if [[ -z "$CONFIG" ]]; then
    echo "ERROR: --config PATH is required" >&2
    echo "Usage: $0 --config PATH [--alt] [--seed N] [--no-seed] [--diff] [--quiet] [--no-save]" >&2
    exit 2
fi
if [[ ! -f "$CONFIG" ]]; then
    echo "ERROR: Config file not found: $CONFIG" >&2
    exit 2
fi

# Derive PROJECT_DIR from config file location (config is in tests/)
PROJECT_DIR="$(cd "$(dirname "$(dirname "$CONFIG")")" && pwd)"
export PROJECT_DIR

# Source project config
source "$CONFIG"

# Default diagnostics_extra (no-op; project.conf can override)
if ! type diagnostics_extra &>/dev/null; then
    diagnostics_extra() { :; }
fi

# Configure engine, game, and walkthrough paths based on mode
if [[ "$MODE" == "alt" ]]; then
    if [[ -z "${ALT_ENGINE_NAME:-}" ]]; then
        echo "ERROR: Alternate engine not configured in project.conf" >&2
        exit 2
    fi
    ENGINE_NAME="$ALT_ENGINE_NAME"
    ENGINE_PATH="$ALT_ENGINE_PATH"
    ENGINE_SEED_FLAG="$ALT_ENGINE_SEED_FLAG"
    GAME_PATH="$ALT_GAME_PATH"
    WALKTHROUGH="$ALT_WALKTHROUGH"
    OUTPUT_FILE="$ALT_OUTPUT_FILE"
    SEEDS_ENGINE="$ALT_SEEDS_KEY"
    MODE_LABEL="$ALT_ENGINE_NAME"
else
    ENGINE_NAME="$PRIMARY_ENGINE_NAME"
    ENGINE_PATH="$PRIMARY_ENGINE_PATH"
    ENGINE_SEED_FLAG="$PRIMARY_ENGINE_SEED_FLAG"
    GAME_PATH="$PRIMARY_GAME_PATH"
    WALKTHROUGH="$PRIMARY_WALKTHROUGH"
    OUTPUT_FILE="$PRIMARY_OUTPUT_FILE"
    SEEDS_ENGINE="$PRIMARY_SEEDS_KEY"
    MODE_LABEL="$PRIMARY_ENGINE_NAME"
fi

# Verify files exist
if [[ ! -x "$ENGINE_PATH" ]]; then
    echo "ERROR: Engine not found: $ENGINE_PATH" >&2
    exit 2
fi
if [[ ! -f "$GAME_PATH" ]]; then
    echo "ERROR: Game file not found: $GAME_PATH" >&2
    exit 2
fi
if [[ ! -f "$WALKTHROUGH" ]]; then
    echo "ERROR: Walkthrough not found: $WALKTHROUGH" >&2
    exit 2
fi

# Determine seed
if [[ "$NO_SEED" == true ]]; then
    SEED=""
elif [[ -z "$SEED" ]]; then
    # Try to load golden seed from seeds.conf
    SEEDS_CONF="$PROJECT_DIR/tests/seeds.conf"
    if [[ -f "$SEEDS_CONF" ]]; then
        SEED_LINE=$(grep "^${SEEDS_ENGINE}:" "$SEEDS_CONF" 2>/dev/null | head -1 || true)
        if [[ -n "$SEED_LINE" ]]; then
            SEED=$(echo "$SEED_LINE" | cut -d: -f2)
            # Check binary hash for staleness
            STORED_HASH=$(echo "$SEED_LINE" | cut -d: -f3)
            if [[ -n "$STORED_HASH" && "$STORED_HASH" != "none" ]]; then
                CURRENT_HASH=$(sha256sum "$GAME_PATH" 2>/dev/null | cut -c1-8 || echo "unknown")
                if [[ "$CURRENT_HASH" != "$STORED_HASH" && "$CURRENT_HASH" != "unknown" ]]; then
                    [[ "$QUIET" != true ]] && echo "WARNING: Game binary hash changed ($STORED_HASH -> $CURRENT_HASH). Golden seed may need re-discovery." >&2
                fi
            fi
        fi
    fi
fi

# Build interpreter command
if [[ -n "$SEED" ]]; then
    CMD="$ENGINE_PATH $ENGINE_SEED_FLAG $SEED -q $GAME_PATH"
else
    CMD="$ENGINE_PATH -q $GAME_PATH"
fi

# Run the walkthrough (append "score" command to ensure final score is in output)
TMPFILE=$(mktemp /tmp/walkthrough-test.XXXXXX)
INPUTFILE=$(mktemp /tmp/walkthrough-input.XXXXXX)
trap "rm -f '$TMPFILE' '$INPUTFILE'" EXIT

cat "$WALKTHROUGH" > "$INPUTFILE"
# Ensure walkthrough ends with a score command
if ! tail -5 "$INPUTFILE" | grep -qx 'score'; then
    echo "score" >> "$INPUTFILE"
fi

$CMD < "$INPUTFILE" > "$TMPFILE" 2>&1 || true

# === Diagnostics ===

# Helper: grep -c that returns 0 instead of failing on no match
count_matches() {
    local count
    count=$(grep -c "$@" 2>/dev/null) || count=0
    echo "$count"
}
count_matches_i() {
    local count
    count=$(grep -ciE "$@" 2>/dev/null) || count=0
    echo "$count"
}

# Extract final score
FINAL_SCORE=$(python3 "$PCRE_GREP" -o -i -l "${SCORE_REGEX}" "$TMPFILE" 2>/dev/null) || FINAL_SCORE=""
if [[ -z "$FINAL_SCORE" ]]; then
    FINAL_SCORE=$(python3 "$PCRE_GREP" -o -l "${SCORE_FALLBACK_REGEX}" "$TMPFILE" 2>/dev/null) || FINAL_SCORE="?"
fi
[[ -z "$FINAL_SCORE" ]] && FINAL_SCORE="?"

# Max score
MAX_SCORE=$(python3 "$PCRE_GREP" -o -l "${MAX_SCORE_REGEX}" "$TMPFILE" 2>/dev/null) || MAX_SCORE="${DEFAULT_MAX_SCORE}"
[[ -z "$MAX_SCORE" ]] && MAX_SCORE="${DEFAULT_MAX_SCORE}"

# Death count
DEATH_COUNT=$(count_matches_i "${DEATH_PATTERNS}" "$TMPFILE")

# Error commands
CANT_SEE=$(count_matches "can't see any such thing" "$TMPFILE")
CANT_GO=$(count_matches "can't go that way" "$TMPFILE")
NOT_POSSIBLE=$(count_matches_i "that.s not something you can|I only understood" "$TMPFILE")

# Score changes
SCORE_UPS=$(count_matches "score has just gone up" "$TMPFILE")
SCORE_DOWNS=$(count_matches "score has just gone down" "$TMPFILE")

# Check for won-flag / endgame
WON_FLAG=false
if grep -qiE "${WON_PATTERNS}" "$TMPFILE" 2>/dev/null; then
    WON_FLAG=true
fi

# Determine pass/fail
PASS=false
if [[ "$FINAL_SCORE" =~ ^[0-9]+$ ]] && [[ "$FINAL_SCORE" -ge "${PASS_THRESHOLD}" ]]; then
    PASS=true
fi

# Output diagnostics
if [[ "$QUIET" != true ]]; then
    echo "=== ${PROJECT_NAME} Walkthrough Test ==="
    echo "Engine:  $ENGINE_NAME ($MODE_LABEL)"
    if [[ -n "$SEED" ]]; then
        echo "Seed:    $SEED"
    else
        echo "Seed:    (none — true randomness)"
    fi
    echo "Score:   ${FINAL_SCORE}/${MAX_SCORE}  $(if [[ "$PASS" == true ]]; then echo '✓'; else echo 'FAIL'; fi)"
    echo "Deaths:  $DEATH_COUNT"

    # Project-specific diagnostics
    diagnostics_extra "$TMPFILE"

    echo "Errors:  $CANT_SEE \"can't see\" / $CANT_GO \"can't go\" / $NOT_POSSIBLE other"
    echo "Scoring: $SCORE_UPS increases, $SCORE_DOWNS decreases"

    if [[ "$WON_FLAG" == true ]]; then
        echo "Endgame: REACHED"
    else
        echo "Endgame: NOT reached"
    fi

    if [[ "$PASS" == true ]]; then
        echo "Result:  PASS"
    else
        echo "Result:  FAIL — see output for details"
    fi
fi

# Diff mode
if [[ "$DIFF_MODE" == true ]]; then
    if [[ -f "$OUTPUT_FILE" ]]; then
        echo ""
        echo "=== Diff vs saved baseline ==="
        diff --unified=3 "$OUTPUT_FILE" "$TMPFILE" || true
    else
        echo ""
        echo "No saved baseline found at: $OUTPUT_FILE"
    fi
fi

# Save output
if [[ "$SAVE_OUTPUT" == true ]]; then
    cp "$TMPFILE" "$OUTPUT_FILE"
    [[ "$QUIET" != true ]] && echo ""
    [[ "$QUIET" != true ]] && echo "Output saved to: $OUTPUT_FILE"
fi

# Copy output to additional directory if requested (only on success)
if [[ -n "$COPY_OUTPUT_DIR" && "$PASS" == true && -f "$OUTPUT_FILE" ]]; then
    if [[ -d "$COPY_OUTPUT_DIR" ]]; then
        cp "$OUTPUT_FILE" "$COPY_OUTPUT_DIR/walkthrough_output.txt"
        [[ "$QUIET" != true ]] && echo "Output copied to: $COPY_OUTPUT_DIR/walkthrough_output.txt"
    else
        echo "WARNING: --copy-output directory not found: $COPY_OUTPUT_DIR" >&2
    fi
fi

# Exit code
if [[ "$PASS" == true ]]; then
    exit 0
else
    exit 1
fi
