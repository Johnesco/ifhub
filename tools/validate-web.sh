#!/usr/bin/env bash
# validate-web.sh — Validate a web player directory for common deployment issues.
#
# Usage:
#   bash tools/validate-web.sh <path-to-web-dir>
#   bash tools/validate-web.sh projects/sample/web
#   bash tools/validate-web.sh ifhub/games/zork1-v4
#
# Checks:
#   1. play.html exists
#   2. No unsubstituted template tokens remain
#   3. All src/href references point to existing files
#   4. Binary .js file is exactly 1 line
#   5. Binary .js file starts with processBase64Zcode('
#   6. parchment_options contains story_name
#   7. parchment.js is loaded (not just main.js)
#
# Exit codes: 0 = all pass, 1 = any check failed

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <path-to-web-dir>" >&2
    exit 1
fi

WEB_DIR="$1"
ERRORS=0

fail() {
    echo "  FAIL: $1" >&2
    ERRORS=$((ERRORS + 1))
}

pass() {
    echo "  OK:   $1"
}

echo "Validating: $WEB_DIR"

# --- Check 1: play.html exists ---
PLAY_HTML="$WEB_DIR/play.html"
if [[ ! -f "$PLAY_HTML" ]]; then
    fail "play.html not found"
    echo ""
    echo "Validation failed with $ERRORS error(s)."
    exit 1
fi
pass "play.html exists"

# --- Check 2: No unsubstituted template tokens ---
TOKENS="__TITLE__|__STORY_FILE__|__STORY_PATH__|__LIB_PATH__|__BINARY__"
if grep -qE "$TOKENS" "$PLAY_HTML"; then
    found=$(grep -oE "$TOKENS" "$PLAY_HTML" | sort -u | tr '\n' ' ')
    fail "Unsubstituted template tokens: $found"
else
    pass "No unsubstituted template tokens"
fi

# --- Check 3: All src/href references resolve to existing files ---
# Extract src="..." and href="..." values, skip http/https/data/# URLs
refs=$(grep -oE '(src|href)="[^"]*"' "$PLAY_HTML" | \
    sed 's/^[^"]*"//; s/"$//' | \
    grep -vE '^(https?://|data:|#|javascript:)' | \
    sed 's/[?].*$//' || true)

missing_refs=0
if [[ -n "$refs" ]]; then
    while IFS= read -r ref; do
        ref_path="$WEB_DIR/$ref"
        if [[ ! -f "$ref_path" ]]; then
            fail "Referenced file not found: $ref"
            missing_refs=$((missing_refs + 1))
        fi
    done <<< "$refs"
fi
if [[ $missing_refs -eq 0 ]]; then
    pass "All src/href references resolve"
fi

# --- Check 4 & 5: Binary .js file ---
# Find the binary: look for .ulx.js, .gblorb.js, or .z3.js in the play.html
binary_file=$(grep -oE 'story_name: *'"'"'[^'"'"']*'"'" "$PLAY_HTML" | \
    sed "s/story_name: *'//; s/'$//" || true)

if [[ -z "$binary_file" ]]; then
    # Try alternate: look for default_story reference
    binary_file=$(grep -oE "default_story:.*\[.*'([^']*)'" "$PLAY_HTML" | \
        sed "s/.*'//; s/'$//" || true)
    if [[ -n "$binary_file" ]]; then
        binary_file=$(basename "$binary_file")
    fi
fi

if [[ -n "$binary_file" ]]; then
    # Search for the binary in the web dir and subdirectories
    binary_path=""
    if [[ -f "$WEB_DIR/$binary_file" ]]; then
        binary_path="$WEB_DIR/$binary_file"
    elif [[ -f "$WEB_DIR/lib/parchment/$binary_file" ]]; then
        binary_path="$WEB_DIR/lib/parchment/$binary_file"
    fi

    if [[ -n "$binary_path" ]]; then
        # Check 4: exactly 1 line
        line_count=$(wc -l < "$binary_path" | tr -d ' ')
        if [[ "$line_count" -ne 1 ]]; then
            fail "Binary $binary_file has $line_count lines (must be exactly 1)"
        else
            pass "Binary $binary_file is 1 line"
        fi

        # Check 5: starts with processBase64Zcode('
        if head -c 22 "$binary_path" | grep -q "^processBase64Zcode('"; then
            pass "Binary $binary_file has correct JSONP format"
        else
            fail "Binary $binary_file does not start with processBase64Zcode('"
        fi
    else
        fail "Binary file $binary_file not found in $WEB_DIR"
    fi
else
    fail "Could not determine binary filename from play.html"
fi

# --- Check 6: parchment_options contains story_name ---
if grep -q 'story_name' "$PLAY_HTML"; then
    pass "parchment_options contains story_name"
else
    fail "parchment_options missing story_name (causes TypeError crash)"
fi

# --- Check 7: parchment.js is loaded ---
if grep -q 'parchment\.js' "$PLAY_HTML"; then
    pass "parchment.js is loaded"
else
    if grep -q 'main\.js' "$PLAY_HTML"; then
        fail "main.js loaded instead of parchment.js (silently disables sound)"
    else
        fail "Neither parchment.js nor main.js found in play.html"
    fi
fi

echo ""
if [[ $ERRORS -gt 0 ]]; then
    echo "Validation FAILED with $ERRORS error(s)."
    exit 1
else
    echo "Validation passed."
    exit 0
fi
