#!/usr/bin/env bash
# serve.sh — Start/stop a local HTTP server for IF Hub.
#
# Usage:
#   bash serve.sh          Start server (kills any existing one first)
#   bash serve.sh stop     Stop running server
#   bash serve.sh status   Check if server is running
#
# Uses a PID file to track the server process, so only one instance runs at a time.

set -euo pipefail
cd "$(dirname "$0")"

PORT=8000
PIDFILE=".serve.pid"

stop_server() {
    if [[ -f "$PIDFILE" ]]; then
        local pid
        pid=$(<"$PIDFILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            echo "Stopped server (PID $pid)"
        fi
        rm -f "$PIDFILE"
    fi
    # Also kill any stray processes on the port
    local stray
    stray=$(netstat -ano 2>/dev/null | grep ":${PORT}.*LISTEN" | awk '{print $5}' | sort -u || true)
    if [[ -n "$stray" ]]; then
        echo "$stray" | while read -r pid; do
            taskkill //F //PID "$pid" 2>/dev/null && echo "Killed stray process $pid" || true
        done
    fi
}

status_server() {
    if [[ -f "$PIDFILE" ]]; then
        local pid
        pid=$(<"$PIDFILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Server running (PID $pid) at http://localhost:${PORT}/"
            return 0
        else
            rm -f "$PIDFILE"
        fi
    fi
    echo "Server not running"
    return 1
}

case "${1:-start}" in
    stop)
        stop_server
        ;;
    status)
        status_server
        ;;
    start|"")
        stop_server
        python3 -m http.server "$PORT" --directory "$(pwd)" &
        echo $! > "$PIDFILE"
        echo "Server started (PID $!) at http://localhost:${PORT}/"
        echo "Stop with: bash serve.sh stop"
        ;;
    *)
        echo "Usage: bash serve.sh [start|stop|status]"
        exit 1
        ;;
esac
