"""Path resolution for IF Hub tools (the receive side).

Layout:
    ifhub/                 HUB_ROOT
    ifhub/site/            SITE_DIR — the static hub site (games.json, cards.json, hubs.json, app.html, ...)
    ifhub/tools/           TOOLS_DIR
    ifhub/tools/web/       WEB_DIR — templates for the wrapper pages the hub generates
    ifhub/workspaces.json  roots scanned for game folders that contain an ifhub.conf
    ifhub/games-registry.json  optional per-game path overrides (normally empty)
    ifhub/games-local.json     per-developer overrides (gitignored)
"""

import json
import os
import re
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent
HUB_ROOT = TOOLS_DIR.parent
SITE_DIR = HUB_ROOT / "site"
WEB_DIR = TOOLS_DIR / "web"

GAMES_REGISTRY = HUB_ROOT / "games-registry.json"
GAMES_LOCAL = HUB_ROOT / "games-local.json"
WORKSPACES_FILE = HUB_ROOT / "workspaces.json"

# GitHub account that owns the game Pages repos — override with IFHUB_GH_ORG
GH_ORG = os.environ.get("IFHUB_GH_ORG", "Johnesco")


# --- Registry overrides ----------------------------------------------------

_registry_cache: dict | None = None


def _load_registry() -> dict:
    """Merged games-registry.json + games-local.json (local wins per game)."""
    global _registry_cache
    if _registry_cache is not None:
        return _registry_cache
    registry: dict = {}
    for file, merge in ((GAMES_REGISTRY, False), (GAMES_LOCAL, True)):
        if not file.exists():
            continue
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for name, entry in data.items():
            if merge and name in registry:
                registry[name].update(entry)
            else:
                registry[name] = entry
    _registry_cache = registry
    return registry


def _resolve_raw_path(raw: str) -> Path:
    """Absolute, or relative to HUB_ROOT. Accepts /c/... posix paths."""
    if not raw:
        return Path()
    if raw.startswith("/") and len(raw) > 2 and raw[2] == "/":
        raw = to_windows(raw)
    p = Path(raw)
    if not p.is_absolute():
        p = (HUB_ROOT / p).resolve()
    return p


def _resolve_game_path(entry: dict) -> Path:
    return _resolve_raw_path(entry.get("deploy", "") or entry.get("path", ""))


# --- Workspace discovery ---------------------------------------------------

_workspace_cache: dict[str, Path] | None = None


def _discover_from_workspaces() -> dict[str, Path]:
    """Scan every root in workspaces.json for subfolders that contain an ifhub.conf."""
    global _workspace_cache
    if _workspace_cache is not None:
        return dict(_workspace_cache)
    result: dict[str, Path] = {}
    if WORKSPACES_FILE.exists():
        try:
            data = json.loads(WORKSPACES_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
        for ws in data.get("workspaces", []):
            root = _resolve_raw_path(ws.get("root", ""))
            if root == Path() or not root.is_dir():
                continue
            try:
                entries = sorted(root.iterdir())
            except OSError:
                continue
            for subdir in entries:
                if subdir.is_dir() and (subdir / "ifhub.conf").exists():
                    result[subdir.name] = subdir
    _workspace_cache = result
    return dict(result)


def registered_games() -> dict[str, Path]:
    """name -> game folder for every discoverable game (registry overrides win)."""
    result = _discover_from_workspaces()
    for name, entry in _load_registry().items():
        resolved = _resolve_game_path(entry)
        if resolved != Path() and resolved.is_dir():
            result[name] = resolved
    return result


def project_dir(name: str | Path) -> Path | None:
    """Resolve a game folder by name (registry, then workspace scan) or by path. None if unknown."""
    p = Path(str(name))
    if (p / "ifhub.conf").exists():
        return p.resolve()
    entry = _load_registry().get(str(name))
    if entry:
        resolved = _resolve_game_path(entry)
        if resolved != Path():
            return resolved
    return _discover_from_workspaces().get(str(name))


# --- Path conversion -------------------------------------------------------

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
