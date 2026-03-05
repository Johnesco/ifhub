#!/bin/bash
# pipeline.sh — Unified build pipeline for Inform 7 projects.
#
# A thin orchestrator that calls existing scripts in order with error handling.
# Every existing script continues to work standalone.
#
# Usage:
#   bash /c/code/ifhub/tools/pipeline.sh <game-name> [stages...] [flags]
#
# Stages (in pipeline order):
#   compile   — I7 → I6 → Glulx → Blorb(if sound) → web player
#   test      — Walkthrough + regtest (native or WSL)
#   snapshot  — Freeze to versions/vN/ (requires --version)
#   deploy    — Copy to ifhub/games/, generate pages
#   push      — Stage changes, show summary, prompt before commit/push
#
# Flags:
#   --all             Run: compile test deploy push
#   --ship            Run: compile test snapshot deploy push (requires --version)
#   --version vN      Version for snapshot stage
#   --force           Skip staleness checks
#   --dry-run         Show what would happen without executing
#   --continue        Resume from last failed stage
#   --message "msg"   Commit message for push stage
#
# Examples:
#   bash pipeline.sh zork1                          # compile only (default)
#   bash pipeline.sh zork1 compile test             # compile + test
#   bash pipeline.sh zork1 --all                    # compile test deploy push
#   bash pipeline.sh zork1 --ship --version v4      # full release pipeline
#   bash pipeline.sh zork1 --continue               # resume after failure

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
I7_ROOT="$(dirname "$SCRIPT_DIR")"

# --- Color output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --- Parse arguments ---
NAME=""
STAGES=()
VERSION=""
FORCE=false
DRY_RUN=false
CONTINUE=false
COMMIT_MSG=""
ALL=false
SHIP=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --all)       ALL=true; shift ;;
        --ship)      SHIP=true; shift ;;
        --version)   VERSION="$2"; shift 2 ;;
        --force)     FORCE=true; shift ;;
        --dry-run)   DRY_RUN=true; shift ;;
        --continue)  CONTINUE=true; shift ;;
        --message)   COMMIT_MSG="$2"; shift 2 ;;
        -*)          echo "Unknown flag: $1" >&2; exit 1 ;;
        *)
            if [[ -z "$NAME" ]]; then
                NAME="$1"
            else
                # It's a stage name
                case "$1" in
                    compile|test|snapshot|deploy|push) STAGES+=("$1") ;;
                    *) echo "Unknown stage: $1" >&2; exit 1 ;;
                esac
            fi
            shift
            ;;
    esac
done

if [[ -z "$NAME" ]]; then
    echo "Usage: pipeline.sh <game-name> [stages...] [flags]" >&2
    echo "" >&2
    echo "  bash pipeline.sh zork1                     # compile only" >&2
    echo "  bash pipeline.sh zork1 compile test        # compile + test" >&2
    echo "  bash pipeline.sh zork1 --all               # compile test deploy push" >&2
    echo "  bash pipeline.sh zork1 --ship --version v4 # full release" >&2
    exit 1
fi

PROJECT_DIR="$I7_ROOT/projects/$NAME"
STATE_FILE="$PROJECT_DIR/.pipeline-state"

if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "ERROR: Project not found: $PROJECT_DIR" >&2
    exit 1
fi

# --- Expand --all and --ship into stage lists ---
if [[ "$SHIP" == true ]]; then
    STAGES=(compile test snapshot deploy push)
    if [[ -z "$VERSION" ]]; then
        echo "ERROR: --ship requires --version" >&2
        exit 1
    fi
elif [[ "$ALL" == true ]]; then
    STAGES=(compile test deploy push)
fi

# Default: compile only
if [[ ${#STAGES[@]} -eq 0 ]]; then
    STAGES=(compile)
fi

# Enforce stage ordering — reorder to pipeline order
ORDERED_STAGES=()
for stage in compile test snapshot deploy push; do
    for s in "${STAGES[@]}"; do
        if [[ "$s" == "$stage" ]]; then
            ORDERED_STAGES+=("$stage")
            break
        fi
    done
done
STAGES=("${ORDERED_STAGES[@]}")

# Snapshot requires --version in v[0-9]+ format
for s in "${STAGES[@]}"; do
    if [[ "$s" == "snapshot" ]]; then
        if [[ -z "$VERSION" ]]; then
            echo "ERROR: snapshot stage requires --version" >&2
            exit 1
        fi
        if [[ ! "$VERSION" =~ ^v[0-9]+$ ]]; then
            echo "ERROR: --version must match v[0-9]+ format (got: $VERSION)" >&2
            exit 1
        fi
    fi
done

# --- Project capability detection ---
PIPELINE_SOUND=false
PIPELINE_VERSIONED=false
PIPELINE_CURRENT_VERSION=""
PIPELINE_HUB_ID=""
PIPELINE_TESTS=""

CONF_FILE="$PROJECT_DIR/tests/project.conf"
if [[ -f "$CONF_FILE" ]]; then
    # Source pipeline fields (they're bash-compatible)
    eval "$(grep '^PIPELINE_' "$CONF_FILE" 2>/dev/null || true)"
fi

# Fallback inference from filesystem
if [[ "$PIPELINE_SOUND" != true && -d "$PROJECT_DIR/Sounds" ]]; then
    PIPELINE_SOUND=true
fi
if [[ "$PIPELINE_VERSIONED" != true && -d "$PROJECT_DIR/versions" ]]; then
    PIPELINE_VERSIONED=true
fi

# --- Staleness detection ---
compute_hash() {
    if [[ -f "$1" ]]; then
        md5sum "$1" 2>/dev/null | cut -d' ' -f1
    else
        echo "none"
    fi
}

load_state() {
    if [[ -f "$STATE_FILE" ]]; then
        source "$STATE_FILE"
    fi
}

save_state() {
    local key="$1" value="$2"
    # Create or update the state file
    if [[ -f "$STATE_FILE" ]]; then
        # Remove existing key if present
        grep -v "^${key}=" "$STATE_FILE" > "$STATE_FILE.tmp" 2>/dev/null || true
        mv "$STATE_FILE.tmp" "$STATE_FILE"
    fi
    echo "${key}=${value}" >> "$STATE_FILE"
}

is_stale() {
    local stage="$1"
    if [[ "$FORCE" == true ]]; then
        return 0  # always run
    fi

    load_state

    case "$stage" in
        compile)
            local current_hash
            current_hash=$(compute_hash "$PROJECT_DIR/story.ni")
            if [[ "${STAGE_COMPILE_SOURCE_HASH:-}" == "$current_hash" ]]; then
                return 1  # not stale
            fi
            ;;
        test)
            # Find the compiled binary
            local binary=""
            if [[ -f "$PROJECT_DIR/$NAME.gblorb" ]]; then
                binary="$PROJECT_DIR/$NAME.gblorb"
            elif [[ -f "$PROJECT_DIR/$NAME.ulx" ]]; then
                binary="$PROJECT_DIR/$NAME.ulx"
            fi
            if [[ -n "$binary" ]]; then
                local current_hash
                current_hash=$(compute_hash "$binary")
                if [[ "${STAGE_TEST_BINARY_HASH:-}" == "$current_hash" ]]; then
                    return 1  # not stale
                fi
            fi
            ;;
    esac
    return 0  # stale (run it)
}

# --- Resume support ---
if [[ "$CONTINUE" == true ]]; then
    if [[ ! -f "$STATE_FILE" ]]; then
        echo "ERROR: No pipeline state found at $STATE_FILE" >&2
        echo "  Run a fresh pipeline first." >&2
        exit 1
    fi
    load_state
    if [[ -z "${STAGE_FAILED:-}" ]]; then
        echo "No failed stage recorded. Nothing to resume." >&2
        exit 0
    fi
    echo -e "${YELLOW}Resuming from failed stage: ${STAGE_FAILED}${NC}"
    # Build stage list starting from the failed stage
    RESUME_STAGES=()
    FOUND=false
    for stage in compile test snapshot deploy push; do
        if [[ "$stage" == "$STAGE_FAILED" ]]; then
            FOUND=true
        fi
        if [[ "$FOUND" == true ]]; then
            # Only include stages that were in the original run
            for s in ${STAGE_ORIGINAL_STAGES:-compile}; do
                if [[ "$s" == "$stage" ]]; then
                    RESUME_STAGES+=("$stage")
                    break
                fi
            done
        fi
    done
    STAGES=("${RESUME_STAGES[@]}")
    # Clear the failed marker
    save_state "STAGE_FAILED" ""
fi

# Save original stages for resume
save_state "STAGE_ORIGINAL_STAGES" "${STAGES[*]}"

# --- Stage execution ---
STAGE_RESULTS=()
STAGE_TIMES=()
PIPELINE_START=$(date +%s)

run_stage() {
    local stage="$1"
    local start end elapsed

    echo ""
    echo -e "${BLUE}${BOLD}=== Stage: $stage ===${NC}"

    if [[ "$DRY_RUN" == true ]]; then
        echo -e "  ${YELLOW}[DRY RUN] Would execute: $stage${NC}"
        case "$stage" in
            compile)
                echo "    compile.sh $NAME$(if [[ "$PIPELINE_SOUND" == true ]]; then echo ' --sound'; fi)"
                ;;
            test)
                echo "    run-walkthrough.sh (if configured)"
                echo "    run-tests.sh (if configured)"
                ;;
            snapshot)
                echo "    snapshot.sh $NAME $VERSION --update"
                ;;
            deploy)
                echo "    deploy.sh (from ifhub/)"
                ;;
            push)
                echo "    git add + commit + push (with confirmation)"
                ;;
        esac
        STAGE_RESULTS+=("$stage:DRY_RUN")
        STAGE_TIMES+=("$stage:0")
        return 0
    fi

    # Staleness check
    if ! is_stale "$stage"; then
        echo -e "  ${GREEN}[SKIP] No changes since last successful $stage${NC}"
        STAGE_RESULTS+=("$stage:SKIP")
        STAGE_TIMES+=("$stage:0")
        return 0
    fi

    start=$(date +%s)

    case "$stage" in
        compile)  stage_compile ;;
        test)     stage_test ;;
        snapshot) stage_snapshot ;;
        deploy)   stage_deploy ;;
        push)     stage_push ;;
    esac

    end=$(date +%s)
    elapsed=$((end - start))
    STAGE_RESULTS+=("$stage:OK")
    STAGE_TIMES+=("$stage:$elapsed")

    # Update staleness state
    case "$stage" in
        compile)
            save_state "STAGE_COMPILE_SOURCE_HASH" "$(compute_hash "$PROJECT_DIR/story.ni")"
            local binary=""
            if [[ -f "$PROJECT_DIR/$NAME.gblorb" ]]; then
                binary="$PROJECT_DIR/$NAME.gblorb"
            elif [[ -f "$PROJECT_DIR/$NAME.ulx" ]]; then
                binary="$PROJECT_DIR/$NAME.ulx"
            fi
            if [[ -n "$binary" ]]; then
                save_state "STAGE_COMPILE_BINARY_HASH" "$(compute_hash "$binary")"
            fi
            ;;
        test)
            local binary=""
            if [[ -f "$PROJECT_DIR/$NAME.gblorb" ]]; then
                binary="$PROJECT_DIR/$NAME.gblorb"
            elif [[ -f "$PROJECT_DIR/$NAME.ulx" ]]; then
                binary="$PROJECT_DIR/$NAME.ulx"
            fi
            if [[ -n "$binary" ]]; then
                save_state "STAGE_TEST_BINARY_HASH" "$(compute_hash "$binary")"
            fi
            ;;
    esac
}

# --- Stage implementations ---

stage_compile() {
    local sound_flag=""
    if [[ "$PIPELINE_SOUND" == true ]]; then
        sound_flag="--sound"
    fi
    bash "$SCRIPT_DIR/compile.sh" "$NAME" $sound_flag
}

stage_test() {
    local has_tests=false

    # Detect native Windows interpreter
    local native_glulxe="$SCRIPT_DIR/interpreters/glulxe.exe"
    local use_native=false
    if [[ ("$OSTYPE" == "msys" || "$OSTYPE" == "cygwin") && -x "$native_glulxe" ]]; then
        use_native=true
        echo -e "  ${GREEN}Using native glulxe.exe (no WSL needed)${NC}"
    fi

    # Walkthrough test
    if [[ -f "$PROJECT_DIR/tests/run-walkthrough.sh" ]]; then
        echo "  Running walkthrough..."
        # Read seeds.conf for a golden seed
        local seed_flag=""
        if [[ -f "$PROJECT_DIR/tests/seeds.conf" ]]; then
            local seed
            seed=$(grep -E '^glulxe:[0-9]+:' "$PROJECT_DIR/tests/seeds.conf" 2>/dev/null | head -1 | cut -d: -f2)
            if [[ -n "$seed" ]]; then
                seed_flag="--seed $seed"
            fi
        fi

        # Determine walkthrough output copy destination
        local copy_flag=""
        local wt_output_dir="${PIPELINE_WALKTHROUGH_OUTPUT_DIR:-}"
        if [[ -z "$wt_output_dir" ]]; then
            # Derive from project layout
            if [[ "$PIPELINE_VERSIONED" == true && -n "$PIPELINE_CURRENT_VERSION" ]]; then
                wt_output_dir="$PROJECT_DIR/versions/$PIPELINE_CURRENT_VERSION"
            elif [[ -d "$PROJECT_DIR/web" ]]; then
                wt_output_dir="$PROJECT_DIR/web"
            fi
        fi
        if [[ -n "$wt_output_dir" && -d "$wt_output_dir" ]]; then
            copy_flag="--copy-output $wt_output_dir"
        fi

        if [[ "$use_native" == true ]]; then
            # Run directly with bash (project.conf picks up native paths)
            bash "$PROJECT_DIR/tests/run-walkthrough.sh" $seed_flag $copy_flag
        else
            # WSL fallback
            source "$SCRIPT_DIR/testing/wsl-check.sh"
            check_wsl_health
            local wsl_path
            wsl_path=$(gitbash_to_wsl_path "$PROJECT_DIR/tests/run-walkthrough.sh")
            timeout 300 wsl -e bash "$wsl_path" $seed_flag $copy_flag
        fi
        has_tests=true
    fi

    # RegTest
    if [[ -f "$PROJECT_DIR/tests/run-tests.sh" ]]; then
        echo "  Running regtests..."
        if [[ "$use_native" == true ]]; then
            bash "$PROJECT_DIR/tests/run-tests.sh"
        else
            if ! type gitbash_to_wsl_path &>/dev/null; then
                source "$SCRIPT_DIR/testing/wsl-check.sh"
                check_wsl_health
            fi
            local wsl_path
            wsl_path=$(gitbash_to_wsl_path "$PROJECT_DIR/tests/run-tests.sh")
            timeout 300 wsl -e bash "$wsl_path"
        fi
        has_tests=true
    fi

    if [[ "$has_tests" == false ]]; then
        echo -e "  ${YELLOW}No tests configured — skipping${NC}"
    fi
}

stage_snapshot() {
    # Sync root story.ni to the version directory before recompiling.
    # snapshot.sh --update never overwrites frozen source (it compiles from
    # the version's own story.ni), so pipeline must sync it explicitly.
    local version_dir="$PROJECT_DIR/versions/$VERSION"
    if [[ -d "$version_dir" && -f "$PROJECT_DIR/story.ni" ]]; then
        cp "$PROJECT_DIR/story.ni" "$version_dir/story.ni"
        echo "  story.ni synced to $VERSION"
    fi
    bash "$SCRIPT_DIR/snapshot.sh" "$NAME" "$VERSION" --update
}

stage_deploy() {
    pushd "$I7_ROOT/ifhub" > /dev/null
    bash deploy.sh
    popd > /dev/null
}

stage_push() {
    echo "  Staging changes..."
    cd "$I7_ROOT"

    # Show what would be committed
    echo ""
    echo -e "${BOLD}Changed files:${NC}"
    git status --short

    local file_count
    file_count=$(git status --short | wc -l | tr -d ' ')

    if [[ "$file_count" -eq 0 ]]; then
        echo -e "  ${YELLOW}No changes to commit.${NC}"
        return 0
    fi

    echo ""
    echo -e "${BOLD}$file_count file(s) changed.${NC}"

    # Prompt for confirmation
    local msg="${COMMIT_MSG:-#139: Pipeline build for $NAME}"
    echo ""
    echo -e "  Commit message: ${BLUE}$msg${NC}"
    echo ""
    read -rp "  Commit and push? [y/N] " confirm
    if [[ "$confirm" != [yY] ]]; then
        echo -e "  ${YELLOW}Push cancelled. Changes remain staged.${NC}"
        return 0
    fi

    git add -A
    git commit -m "$msg"
    git push
    echo -e "  ${GREEN}Pushed successfully.${NC}"
}

# --- Main execution loop ---
echo -e "${BOLD}=== PIPELINE: $NAME ===${NC}"
echo -e "  Stages: ${STAGES[*]}"
if [[ "$DRY_RUN" == true ]]; then
    echo -e "  ${YELLOW}Mode: DRY RUN${NC}"
fi
if [[ "$FORCE" == true ]]; then
    echo -e "  ${YELLOW}Mode: FORCE (skip staleness checks)${NC}"
fi

for stage in "${STAGES[@]}"; do
    if ! run_stage "$stage"; then
        save_state "STAGE_FAILED" "$stage"
        echo ""
        echo -e "${RED}${BOLD}=== PIPELINE FAILED at stage: $stage ===${NC}"
        echo ""
        echo "Options:"
        echo "  Fix and resume:  bash pipeline.sh $NAME --continue"
        echo "  Force retry:     bash pipeline.sh $NAME $stage --force"
        exit 1
    fi
done

# --- Summary ---
PIPELINE_END=$(date +%s)
TOTAL_TIME=$((PIPELINE_END - PIPELINE_START))

echo ""
echo -e "${BOLD}=== PIPELINE SUMMARY ($NAME) ===${NC}"
for result in "${STAGE_RESULTS[@]}"; do
    _stage="${result%%:*}"
    _status="${result#*:}"
    _time_str=""

    for t in "${STAGE_TIMES[@]}"; do
        if [[ "${t%%:*}" == "$_stage" ]]; then
            _secs="${t#*:}"
            if [[ "$_secs" -gt 0 ]]; then
                _time_str=" (${_secs}s)"
            fi
            break
        fi
    done

    case "$_status" in
        OK)      echo -e "  $_stage:$(printf '%*s' $((12 - ${#_stage})) '')${GREEN}OK${NC}$_time_str" ;;
        SKIP)    echo -e "  $_stage:$(printf '%*s' $((12 - ${#_stage})) '')${YELLOW}SKIP${NC} (unchanged)" ;;
        DRY_RUN) echo -e "  $_stage:$(printf '%*s' $((12 - ${#_stage})) '')${BLUE}DRY RUN${NC}" ;;
    esac
done
echo -e "  Total: ${TOTAL_TIME}s"

# Clear failed state on success
save_state "STAGE_FAILED" ""
