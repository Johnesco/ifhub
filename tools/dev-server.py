#!/usr/bin/env python3
"""
Dev server for ifhub — serves all games + hub at production-equivalent URLs.

Maps local directories to URL paths matching GitHub Pages deployment:
  /ifhub/*      -> ifhub/
  /zork1/*      -> projects/zork1/
  /dracula/*    -> projects/dracula/
  /feverdream/* -> projects/feverdream/
  /sample/*     -> projects/sample/

Usage:
  python tools/dev-server.py [--port 8000]

Then open http://127.0.0.1:8000/ifhub/app.html
"""

import argparse
import mimetypes
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote

SCRIPT_DIR = Path(__file__).resolve().parent
IFHUB_ROOT = SCRIPT_DIR.parent

ROUTES = {}

# Ensure .ni and .bas files get sensible MIME types
mimetypes.add_type("text/plain", ".ni")
mimetypes.add_type("text/plain", ".bas")
mimetypes.add_type("text/plain", ".zil")
mimetypes.add_type("application/javascript", ".js")


def discover_routes():
    """Build route table from available directories."""
    hub_dir = IFHUB_ROOT / "ifhub"
    if hub_dir.is_dir():
        ROUTES["/ifhub"] = hub_dir

    # Games from projects/
    projects_dir = IFHUB_ROOT / "projects"
    if projects_dir.is_dir():
        for entry in sorted(projects_dir.iterdir()):
            if entry.is_dir() and not entry.name.startswith("."):
                ROUTES[f"/{entry.name}"] = entry

    print("Route table:")
    for prefix, path in sorted(ROUTES.items()):
        print(f"  {prefix:<20} -> {path}")
    print()


def resolve_path(url_path):
    """Resolve a URL path to a local file path using the route table."""
    path = unquote(url_path).split("?")[0].split("#")[0]
    if not path.startswith("/"):
        path = "/" + path

    # Find matching route (longest prefix match)
    best_prefix = None
    best_dir = None
    for prefix, local_dir in ROUTES.items():
        if path == prefix or path.startswith(prefix + "/"):
            if best_prefix is None or len(prefix) > len(best_prefix):
                best_prefix = prefix
                best_dir = local_dir

    if best_dir is None:
        return None

    # Map remainder to local directory
    if path == best_prefix:
        remainder = ""
    else:
        remainder = path[len(best_prefix) + 1:]  # skip the /

    local_path = best_dir / remainder if remainder else best_dir

    # Serve index.html for directories
    if local_path.is_dir():
        index = local_path / "index.html"
        if index.is_file():
            return index
        return None

    if local_path.is_file():
        return local_path

    return None


class DevHandler(BaseHTTPRequestHandler):
    """HTTP handler that routes requests to different directories by URL prefix."""

    def do_GET(self):
        # Root index
        if self.path == "/" or self.path == "":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            links = "".join(
                f'<li><a href="{p}/">{p}/</a></li>'
                for p in sorted(ROUTES.keys())
            )
            self.wfile.write(f"""<!DOCTYPE html>
<html><head><title>ifhub dev server</title>
<style>body{{font-family:monospace;background:#0a0a0a;color:#d4c5a9;padding:40px;}}
a{{color:#e8d090;}}h1{{margin-bottom:20px;}}li{{margin:4px 0;}}</style></head>
<body><h1>ifhub dev server</h1>
<p>Routes:</p><ul>{links}</ul>
<p style="margin-top:20px;"><a href="/ifhub/app.html">Open IF Hub</a></p>
</body></html>""".encode())
            return

        local_path = resolve_path(self.path)

        if local_path is None:
            self.send_error(404, f"Not found: {self.path}")
            return

        # Serve the file
        content_type, _ = mimetypes.guess_type(str(local_path))
        if content_type is None:
            content_type = "application/octet-stream"

        try:
            data = local_path.read_bytes()
        except (OSError, PermissionError) as e:
            self.send_error(500, str(e))
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(data))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def do_HEAD(self):
        local_path = resolve_path(self.path)
        if local_path is None:
            self.send_error(404)
            return
        content_type, _ = mimetypes.guess_type(str(local_path))
        self.send_response(200)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", local_path.stat().st_size)
        self.end_headers()

    def log_message(self, format, *args):
        msg = format % args
        # Compact log
        sys.stderr.write(f"  {msg}\n")


def main():
    parser = argparse.ArgumentParser(description="ifhub dev server")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    discover_routes()

    server = HTTPServer(("127.0.0.1", args.port), DevHandler)
    print(f"Serving on http://127.0.0.1:{args.port}/")
    print(f"Hub:  http://127.0.0.1:{args.port}/ifhub/app.html")
    print(f"Stop: Ctrl+C\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
