"""Path resolution for IF Hub tools (the receive side).

Layout:
    ifhub/                 HUB_ROOT
    ifhub/site/            SITE_DIR — the static hub site (games.json, cards.json, hubs.json, app.html, ...)
    ifhub/tools/           TOOLS_DIR
    ifhub/tools/web/       WEB_DIR — templates for the wrapper pages the hub generates
    ifhub/workspaces.json  roots scanned for game folders that contain an ifhub.conf

Game discovery is the workspace scan and nothing else: a game is a subfolder of a
workspace root that contains an ifhub.conf, and its id is the folder name.
"""

import json
import os
import re
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent
HUB_ROOT = TOOLS_DIR.parent
SITE_DIR = HUB_ROOT / "site"
WEB_DIR = TOOLS_DIR / "web"
WORKSPACES_FILE = HUB_ROOT / "workspaces.json"

# GitHub account that owns the game Pages repos — override with IFHUB_GH_ORG
GH_ORG = os.environ.get("IFHUB_GH_ORG", "Johnesco")


def resolve_root(raw: str) -> Path:
    """A workspaces.json root: absolute, or relative to HUB_ROOT. Accepts /c/... posix paths."""
    if not raw:
        return Path()
    if raw.startswith("/") and len(raw) > 2 and raw[2] == "/":
        raw = to_windows(raw)
    p = Path(raw)
    if not p.is_absolute():
        p = (HUB_ROOT / p).resolve()
    return p


_cache: dict[str, Path] | None = None


def discover_games() -> dict[str, Path]:
    """folder name -> game folder, for every subfolder with an ifhub.conf under a workspace root."""
    global _cache
    if _cache is not None:
        return dict(_cache)
    result: dict[str, Path] = {}
    if WORKSPACES_FILE.exists():
        try:
            data = json.loads(WORKSPACES_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
        for ws in data.get("workspaces", []):
            root = resolve_root(ws.get("root", ""))
            if root == Path() or not root.is_dir():
                continue
            try:
                entries = sorted(root.iterdir())
            except OSError:
                continue
            for subdir in entries:
                if subdir.is_dir() and (subdir / "ifhub.conf").exists():
                    result[subdir.name] = subdir
    _cache = result
    return dict(result)


def project_dir(name: str | Path) -> Path | None:
    """Resolve a game folder by name (workspace scan) or by path. None if unknown."""
    p = Path(str(name))
    if (p / "ifhub.conf").exists():
        return p.resolve()
    return discover_games().get(str(name))


def to_posix(path: str | Path) -> str:
    """C:\\code\\ifhub -> /c/code/ifhub"""
    s = str(path).replace("\\", "/")
    m = re.match(r"^([A-Za-z]):/", s)
    if m:
        s = "/" + m.group(1).lower() + "/" + s[3:]
    return s


def to_windows(path: str) -> str:
    """/c/code/ifhub -> C:\\code\\ifhub"""
    m = re.match(r"^/([a-zA-Z])/(.*)", path)
    if m:
        return f"{m.group(1).upper()}:\\{m.group(2).replace('/', chr(92))}"
    return path.replace("/", "\\")
