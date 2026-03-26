#!/usr/bin/env python3
"""Start/stop a local HTTP server for IF Hub.

Usage:
    python serve.py          Start server (kills any existing one first)
    python serve.py stop     Stop running server
    python serve.py status   Check if server is running
"""

import argparse
import http.server
import os
import signal
import sys
from pathlib import Path

PIDFILE = Path(__file__).resolve().parent / ".serve.pid"
PORT = 8000


def stop_server():
    if PIDFILE.exists():
        pid = int(PIDFILE.read_text().strip())
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"Stopped server (PID {pid})")
        except (ProcessLookupError, PermissionError):
            pass
        PIDFILE.unlink(missing_ok=True)


def status_server():
    if PIDFILE.exists():
        pid = int(PIDFILE.read_text().strip())
        try:
            os.kill(pid, 0)  # Check if process exists
            print(f"Server running (PID {pid}) at http://localhost:{PORT}/")
            return True
        except (ProcessLookupError, PermissionError):
            PIDFILE.unlink(missing_ok=True)
    print("Server not running")
    return False


def start_server():
    stop_server()
    serve_dir = Path(__file__).resolve().parent
    os.chdir(str(serve_dir))
    PIDFILE.write_text(str(os.getpid()))
    print(f"Server started (PID {os.getpid()}) at http://localhost:{PORT}/")
    print("Stop with: python serve.py stop")
    try:
        handler = http.server.SimpleHTTPRequestHandler
        with http.server.HTTPServer(("", PORT), handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        PIDFILE.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="IF Hub local server.")
    parser.add_argument("action", nargs="?", default="start",
                        choices=["start", "stop", "status"])
    args = parser.parse_args()

    if args.action == "stop":
        stop_server()
    elif args.action == "status":
        sys.exit(0 if status_server() else 1)
    else:
        start_server()


if __name__ == "__main__":
    main()
