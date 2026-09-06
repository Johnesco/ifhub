#!/usr/bin/env python3
"""Serve IF Hub and every game folder locally at production-equivalent URLs.

Usage:
    python tools/serve.py [--port 8892] [--bind 127.0.0.1]

    /ifhub/...    -> site/                  (the hub)
    /<game>/...   -> that game's folder     (every ifhub.conf folder under the workspaces.json roots)
    /             -> redirects to /ifhub/

This is the same one-origin layout as johnesco.github.io, so app.html can iframe
games, fetch their source and walkthrough files, and inject themes exactly as it
does live. There is no registration step and nothing to install: games are found
the way build_games.py finds them. Files are served with Cache-Control: no-cache.

The Browser pane's `hub-site` launch config runs this; stop it with preview_stop
or Ctrl-C.
"""

import argparse
import http.server
import posixpath
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import paths

TEXT = "text/plain; charset=utf-8"
BINARY = "application/octet-stream"


class HubHandler(http.server.SimpleHTTPRequestHandler):
    roots: dict[str, Path] = {}

    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".ni": TEXT, ".rez": TEXT, ".ink": TEXT, ".bas": TEXT, ".txt": TEXT,
        ".transcript": TEXT, ".conf": TEXT, ".md": TEXT,
        ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json",
        ".wasm": "application/wasm",
        ".z3": BINARY, ".z5": BINARY, ".z8": BINARY, ".ulx": BINARY, ".gblorb": BINARY,
    }

    def translate_path(self, path: str) -> str:
        path = urllib.parse.urlsplit(path).path
        path = posixpath.normpath(urllib.parse.unquote(path))
        parts = [p for p in path.split("/") if p and p not in (".", "..")]
        if not parts:
            return str(self.roots["ifhub"])
        root = self.roots.get(parts[0])
        if root is None:
            # Unknown first segment: point at a path that cannot exist -> 404
            return str(self.roots["ifhub"] / "__no_such_site__" / "__missing__")
        target = root
        for part in parts[1:]:
            target = target / part
        return str(target)

    def do_GET(self) -> None:
        if urllib.parse.urlsplit(self.path).path in ("", "/"):
            self.send_response(302)
            self.send_header("Location", "/ifhub/")
            self.end_headers()
            return
        super().do_GET()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:
        # One compact line per request; quiet enough to leave running in a pane.
        sys.stderr.write("  %s\n" % (fmt % args))


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the hub and every game folder on one port.")
    parser.add_argument("--port", type=int, default=8892)
    parser.add_argument("--bind", default="127.0.0.1")
    args = parser.parse_args()

    roots: dict[str, Path] = {"ifhub": paths.SITE_DIR}
    roots.update(paths.discover_games())
    HubHandler.roots = roots

    server = http.server.ThreadingHTTPServer((args.bind, args.port), HubHandler)
    print(f"IF Hub local preview: http://{args.bind}:{args.port}/ifhub/   ({len(roots) - 1} game folders)")
    print(f"  player:  http://{args.bind}:{args.port}/ifhub/app.html?game=<game>")
    print("  Ctrl-C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
