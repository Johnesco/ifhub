#!/bin/bash
# Generic seed sweep for walkthrough testing
# Tries many RNG seeds to find one where the walkthrough achieves a passing score.
#
# Requires a project.conf file (--config) with engine paths, patterns, etc.
#
# Usage:
#   bash find-seeds.sh --config PATH                # Primary engine (default)
#   bash find-seeds.sh --config PATH --alt           # Alternate engine
#   bash find-seeds.sh --config PATH --max 500       # Search range (default: 200)
#   bash find-seeds.sh --config PATH --stop          # Stop on first pass (default)
#   bash find-seeds.sh --config PATH --no-stop       # Continue sweep after finding pass

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PCRE_GREP="$SCRIPT_DIR/pcre_grep.py"

# Defaults
CONFIG=""
MODE_FLAG=""
MAX_SEEDS=200
STOP_ON_HIT=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --config)
            CONFIG="$2"
            shift 2
            ;;
        --alt)
            MODE_FLAG="--alt"
            shift
            ;;
        --max)
            MAX_SEEDS="$2"
            shift 2
            ;;
        --stop)
            STOP_ON_HIT=true
            shift
            ;;
        --no-stop)
            STOP_ON_HIT=false
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Usage: $0 --config PATH [--alt] [--max N] [--stop|--no-stop]" >&2
            exit 2
            ;;
    esac
done

# Validate config
if [[ -z "$CONFIG" ]]; then
    echo "ERROR: --config PATH is required" >&2
    echo "Usage: $0 --config PATH [--alt] [--max N] [--stop|--no-stop]" >&2
    exit 2
fi
if [[ ! -f "$CONFIG" ]]; then
    echo "ERROR: Config file not found: $CONFIG" >&2
    exit 2
fi

# Derive PROJECT_DIR from config file location (config is in tests/)
PROJECT_DIR="$(cd "$(dirname "$(dirname "$CONFIG")")" && pwd)"
export PROJECT_DIR

# Source project config for display info
source "$CONFIG"

# Determine engine info for output
if [[ "$MODE_FLAG" == "--alt" ]]; then
    if [[ -z "${ALT_ENGINE_NAME:-}" ]]; then
        echo "ERROR: Alternate engine not configured in project.conf" >&2
        exit 2
    fi
    ENGINE_NAME="$ALT_ENGINE_NAME"
    GAME_PATH="$ALT_GAME_PATH"
    MODE_LABEL="$ALT_ENGINE_NAME"
else
    ENGINE_NAME="$PRIMARY_ENGINE_NAME"
    GAME_PATH="$PRIMARY_GAME_PATH"
    MODE_LABEL="$PRIMARY_ENGINE_NAME"
fi

# Use PASS_THRESHOLD from config (default 350 for backward compat)
THRESHOLD="${PASS_THRESHOLD:-350}"
MAX_SCORE_DISPLAY="${DEFAULT_MAX_SCORE:-$THRESHOLD}"

echo "=== ${PROJECT_NAME} Seed Sweep ==="
echo "Mode:    $MODE_LABEL ($ENGINE_NAME)"
echo "Range:   1..$MAX_SEEDS"
echo "Target:  ${THRESHOLD}/${MAX_SCORE_DISPLAY}"
echo ""

# Track statistics
BEST_SCORE=0
BEST_SEED=0
WORST_SCORE=999
WORST_SEED=0
TOTAL_SCORE=0
PASS_COUNT=0
PASS_SEEDS=""
ALL_SCORES=""

RUN_WALKTHROUGH="$SCRIPT_DIR/run-walkthrough.sh"

for SEED in $(seq 1 "$MAX_SEEDS"); do
    # Run walkthrough once, capture diagnostic output
    DIAG=$(bash "$RUN_WALKTHROUGH" --config "$CONFIG" $MODE_FLAG --seed "$SEED" --no-save 2>/dev/null) || true

    # Extract score from "Score:   N/MAX" line
    SCORE=$(echo "$DIAG" | python3 "$PCRE_GREP" -o -l 'Score:\s+\K[0-9]+') || SCORE=""

    # Fallback: try N/N pattern
    if [[ -z "$SCORE" ]]; then
        SCORE=$(echo "$DIAG" | python3 "$PCRE_GREP" -o '[0-9]+(?=/[0-9]+)' | head -1) || SCORE="0"
    fi
    [[ -z "$SCORE" ]] && SCORE=0

    ALL_SCORES="$ALL_SCORES $SCORE"
    TOTAL_SCORE=$((TOTAL_SCORE + SCORE))

    # Update best/worst
    if [[ "$SCORE" -gt "$BEST_SCORE" ]]; then
        BEST_SCORE=$SCORE
        BEST_SEED=$SEED
    fi
    if [[ "$SCORE" -lt "$WORST_SCORE" ]]; then
        WORST_SCORE=$SCORE
        WORST_SEED=$SEED
    fi

    # Check for pass
    if [[ "$SCORE" -ge "$THRESHOLD" ]]; then
        PASS_COUNT=$((PASS_COUNT + 1))
        PASS_SEEDS="$PASS_SEEDS $SEED"
        echo "[seed $SEED/$MAX_SEEDS] *** ${THRESHOLD}/${MAX_SCORE_DISPLAY} PASS *** (seed $SEED)"

        if [[ "$STOP_ON_HIT" == true ]]; then
            echo ""
            echo "=== Golden Seed Found! ==="

            # Compute binary hash
            GAME_HASH=$(sha256sum "$GAME_PATH" 2>/dev/null | cut -c1-8 || echo "none")
            TODAY=$(date +%Y-%m-%d)

            echo "Engine:  $ENGINE_NAME"
            echo "Seed:    $SEED"
            echo "Score:   ${THRESHOLD}/${MAX_SCORE_DISPLAY}"
            echo "Hash:    $GAME_HASH"
            echo ""
            echo "seeds.conf line:"
            echo "${ENGINE_NAME}:${SEED}:${GAME_HASH}:${TODAY}"
            exit 0
        fi
    fi

    # Progress update every 10 seeds
    if [[ $((SEED % 10)) -eq 0 ]]; then
        echo "[seed $SEED/$MAX_SEEDS] best so far: $BEST_SCORE/${MAX_SCORE_DISPLAY} (seed $BEST_SEED)"
    fi
done

# === Summary ===
echo ""
echo "=== Seed Sweep Complete ==="
echo "Range:      1..$MAX_SEEDS"
echo "Best score: $BEST_SCORE/${MAX_SCORE_DISPLAY} (seed $BEST_SEED)"
echo "Worst:      $WORST_SCORE/${MAX_SCORE_DISPLAY} (seed $WORST_SEED)"

# Compute median
if command -v sort &>/dev/null; then
    MEDIAN=$(echo "$ALL_SCORES" | tr ' ' '\n' | grep -v '^$' | sort -n | awk '{a[NR]=$1} END{print a[int(NR/2)+1]}')
    echo "Median:     $MEDIAN/${MAX_SCORE_DISPLAY}"
fi

AVERAGE=$((TOTAL_SCORE / MAX_SEEDS))
echo "Average:    $AVERAGE/${MAX_SCORE_DISPLAY}"
echo "Pass rate:  $PASS_COUNT/$MAX_SEEDS"

if [[ "$PASS_COUNT" -gt 0 ]]; then
    GAME_HASH=$(sha256sum "$GAME_PATH" 2>/dev/null | cut -c1-8 || echo "none")
    TODAY=$(date +%Y-%m-%d)
    FIRST_PASS=$(echo "$PASS_SEEDS" | tr ' ' '\n' | grep -v '^$' | head -1)

    echo ""
    echo "Recommended golden seed: $FIRST_PASS"
    echo "seeds.conf line:"
    echo "${ENGINE_NAME}:${FIRST_PASS}:${GAME_HASH}:${TODAY}"
    echo ""
    echo "All passing seeds:$PASS_SEEDS"
else
    echo ""
    echo "NO SEED achieved ${THRESHOLD}/${MAX_SCORE_DISPLAY}."
    echo "Best achievable: $BEST_SCORE/${MAX_SCORE_DISPLAY} (seed $BEST_SEED)"
    echo ""
    echo "This suggests the walkthrough itself has issues (not just RNG)."
    echo "Run with the best seed to diagnose:"
    echo "  bash run-walkthrough.sh --config $CONFIG $MODE_FLAG --seed $BEST_SEED"
fi

exit $([[ "$PASS_COUNT" -gt 0 ]] && echo 0 || echo 1)
