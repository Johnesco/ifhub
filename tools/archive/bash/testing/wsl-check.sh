#!/bin/bash
# WSL health check and path conversion utilities.
# Source this file from scripts that need WSL fallback support.
#
# Provides:
#   check_wsl_health    — Tests WSL responsiveness, attempts recovery
#   gitbash_to_wsl_path — Converts Git Bash paths (/c/...) to WSL (/mnt/c/...)

# Check if WSL is responsive. Returns 0 if healthy, 1 if unrecoverable.
# Attempts auto-recovery via taskkill if initial check fails.
check_wsl_health() {
    # Quick check: can WSL respond within 5 seconds?
    if timeout 5 wsl -e echo "ok" &>/dev/null; then
        return 0
    fi

    echo "WARNING: WSL is unresponsive. Attempting recovery..." >&2

    # Try shutting down WSL via taskkill (less destructive than wsl --shutdown
    # which requires PowerShell elevation)
    taskkill //F //IM wslservice.exe &>/dev/null || true
    sleep 2

    # Retry
    if timeout 10 wsl -e echo "ok" &>/dev/null; then
        echo "WSL recovered." >&2
        return 0
    fi

    echo "ERROR: WSL is unrecoverable. Try from PowerShell: wsl --shutdown" >&2
    echo "       Then retry. No Windows-native fallback available for WSL tests." >&2
    return 1
}

# Convert a Git Bash path to a WSL path.
# /c/code/ifhub -> /mnt/c/code/ifhub
# Handles the common case of drive letter paths.
gitbash_to_wsl_path() {
    local path="$1"
    # Match /x/... where x is a drive letter
    if [[ "$path" =~ ^/([a-zA-Z])/(.*) ]]; then
        local drive="${BASH_REMATCH[1]}"
        local rest="${BASH_REMATCH[2]}"
        echo "/mnt/${drive,,}/$rest"
    else
        # Already a WSL-compatible path or relative path
        echo "$path"
    fi
}
