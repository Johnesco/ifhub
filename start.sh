#!/usr/bin/env bash
# start.sh — Launch IF Hub Dashboard + Portman together.
#
# Usage:
#   ./start.sh              Start both servers
#   ./start.sh --dashboard  Dashboard only (port 5000)
#   ./start.sh --portman    Portman only (port 9000)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORTMAN_DIR="/c/code/portman"
DASHBOARD_PORT=5000
PORTMAN_PORT=9000

cleanup() {
  echo ""
  echo "Shutting down..."
  kill $DASHBOARD_PID 2>/dev/null || true
  kill $PORTMAN_PID 2>/dev/null || true
  wait 2>/dev/null
  echo "Done."
}

DASHBOARD_PID=""
PORTMAN_PID=""
RUN_DASHBOARD=true
RUN_PORTMAN=true

for arg in "$@"; do
  case "$arg" in
    --dashboard) RUN_PORTMAN=false ;;
    --portman)   RUN_DASHBOARD=false ;;
    --help|-h)
      echo "Usage: ./start.sh [--dashboard | --portman]"
      echo ""
      echo "  --dashboard   Dashboard only (port $DASHBOARD_PORT)"
      echo "  --portman     Portman only (port $PORTMAN_PORT)"
      echo "  (default)     Both servers"
      exit 0
      ;;
  esac
done

trap cleanup EXIT INT TERM

echo "=== IF Hub ==="
echo ""

if $RUN_PORTMAN; then
  if [ ! -f "$PORTMAN_DIR/portman.py" ]; then
    echo "Warning: Portman not found at $PORTMAN_DIR"
    RUN_PORTMAN=false
  fi
fi

if $RUN_PORTMAN; then
  python "$PORTMAN_DIR/portman.py" serve --port $PORTMAN_PORT &
  PORTMAN_PID=$!
  echo "  Portman:    http://127.0.0.1:$PORTMAN_PORT"
fi

if $RUN_DASHBOARD; then
  python "$SCRIPT_DIR/tools/dashboard.py" --port $DASHBOARD_PORT &
  DASHBOARD_PID=$!
  echo "  Dashboard:  http://127.0.0.1:$DASHBOARD_PORT"
fi

echo ""
echo "  Press Ctrl-C to stop."
echo ""

wait
