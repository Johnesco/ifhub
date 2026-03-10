#!/bin/bash
# Generic RegTest runner for Inform 7 projects
# Requires a project.conf file (--config) with test file, engine, and game paths.
#
# Usage:
#   bash run-tests.sh --config PATH                    # run all tests
#   bash run-tests.sh --config PATH -v                 # verbose (show transcripts)
#   bash run-tests.sh --config PATH -l                 # list available tests
#   bash run-tests.sh --config PATH cellar             # run only "cellar" test
#   bash run-tests.sh --config PATH -v --vital cellar  # verbose, stop on first error

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
I7_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Separate --config from other args (pass-through to regtest.py)
CONFIG=""
PASSTHROUGH_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --config)
            CONFIG="$2"
            shift 2
            ;;
        *)
            PASSTHROUGH_ARGS+=("$1")
            shift
            ;;
    esac
done

# Validate config
if [[ -z "$CONFIG" ]]; then
    echo "ERROR: --config PATH is required" >&2
    echo "Usage: $0 --config PATH [regtest-options...] [test-pattern]" >&2
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

python3 "$I7_ROOT/tools/regtest.py" \
    -i "$REGTEST_ENGINE -q" \
    -g "$REGTEST_GAME" \
    "$REGTEST_FILE" \
    "${PASSTHROUGH_ARGS[@]}"
