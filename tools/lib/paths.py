"""Path resolution and conversion utilities for IF Hub tools.

Consolidates duplicated path logic from run.py, dashboard.py, and explore.py
into a single source of truth.
"""

import json
import os
import re
import sys
from pathlib import Path

# Resolved once at import time, relative to this file:
#   tools/lib/paths.py -> tools/ -> repo root
TOOLS_DIR = Path(__file__).resolve().parent.parent
I7_ROOT = TOOLS_DIR.parent
PROJECTS_DIR = I7_ROOT / "projects"
IFHUB_DIR = I7_ROOT / "site"
TESTING_DIR = TOOLS_DIR / "testing"  # legacy — I7 tools now at text-games/i7/tools/
WEB_DIR = TOOLS_DIR / "web"

# Per-engine tools directories (outside ifhub, alongside games)
TEXT_GAMES_DIR = I7_ROOT.parent / "text-games"
ENGINE_DIR_KEYS = {"inform7": "i7", "zmachine": "i7"}  # engines that map to a different dir name


def engine_dir_key(engine: str) -> str:
    """Return the folder name for an engine (e.g., 'inform7' -> 'i7')."""
    return ENGINE_DIR_KEYS.get(engine, engine)


def engine_tools_dir(engine: str) -> Path:
    """Return the per-engine tools directory at text-games/<engine>/tools/."""
    return TEXT_GAMES_DIR / engine_dir_key(engine) / "tools"


def new_project_dir(engine: str, name: str) -> Path:
    """Return the directory for a new project: text-games/<engine>/<name>/."""
    return TEXT_GAMES_DIR / engine_dir_key(engine) / name

# Game registry files
GAMES_REGISTRY = I7_ROOT / "games-registry.json"
GAMES_LOCAL = I7_ROOT / "games-local.json"
WORKSPACES_FILE = I7_ROOT / "workspaces.json"

# Compiler paths — override with INFORM7_HOME env var if installed elsewhere
_I7_HOME = Path(os.environ.get("INFORM7_HOME", r"C:\Program Files\Inform7IDE"))
I7_COMPILER = _I7_HOME / "Compilers" / "inform7.exe"
I6_COMPILER = _I7_HOME / "Compilers" / "inform6.exe"
INBLORB = _I7_HOME / "Compilers" / "inblorb.exe"
I7_INTERNAL = _I7_HOME / "Internal"

# GitHub organization — override with IFHUB_GH_ORG env var
GH_ORG = os.environ.get("IFHUB_GH_ORG", "Johnesco")

# Native interpreters
NATIVE_GLULXE = TOOLS_DIR / "interpreters" / "glulxe.exe"
NATIVE_DFROTZ = TOOLS_DIR / "interpreters" / "dfrotz.exe"


# --- Game registry ---

_registry_cache: dict | None = None


def _load_registry() -> dict:
    """Load the merged game registry (local overrides defaults).

    Returns dict mapping game name -> {"path": str, "repo": str, ...}.
    """
    global _registry_cache
    if _registry_cache is not None:
        return _registry_cache

    registry = {}

    # Layer 1: committed defaults
    if GAMES_REGISTRY.exists():
        try:
            registry.update(json.loads(GAMES_REGISTRY.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass

    # Layer 2: local overrides (merge per-game, not full replace)
    if GAMES_LOCAL.exists():
        try:
            local = json.loads(GAMES_LOCAL.read_text(encoding="utf-8"))
            for name, entry in local.items():
                if name in registry:
                    registry[name].update(entry)
                else:
                    registry[name] = entry
        except (json.JSONDecodeError, OSError):
            pass

    _registry_cache = registry
    return registry


def _resolve_raw_path(raw: str) -> Path:
    """Resolve a raw path string to an absolute Path.

    Relative paths are resolved from the ifhub root (I7_ROOT).
    POSIX paths (/c/code/...) are converted to Windows.
    """
    if not raw:
        return Path()
    # Convert POSIX paths to Windows if needed
    if raw.startswith("/") and len(raw) > 2 and raw[2] == "/":
        raw = to_windows(raw)
    p = Path(raw)
    if not p.is_absolute():
        p = (I7_ROOT / p).resolve()
    return p


def _resolve_game_path(entry: dict) -> Path:
    """Resolve a registry entry's deploy/path to an absolute Path."""
    # Prefer 'deploy', fall back to 'path' (legacy)
    raw = entry.get("deploy", "") or entry.get("path", "")
    return _resolve_raw_path(raw)


def registered_games() -> dict[str, Path]:
    """Return dict mapping game name -> resolved absolute path for all registered games.

    Resolution order:
    1. Workspace discovery (scans workspaces.json roots for ifhub.conf files)
    2. games-registry.json / games-local.json (overrides workspace-discovered paths)

    If the deploy directory doesn't exist yet but a source directory does,
    include the game anyway so the dashboard can trigger the first build.
    """
    # Start with workspace-discovered games
    result = _discover_from_workspaces()

    # Layer registry on top (registry entries override workspace discovery)
    registry = _load_registry()
    for name, entry in registry.items():
        resolved = _resolve_game_path(entry)
        if resolved != Path() and resolved.is_dir():
            result[name] = resolved
        elif entry.get("source"):
            # Deploy dir missing but source exists — still discoverable
            source = _resolve_raw_path(entry["source"])
            if source != Path() and source.is_dir():
                result[name] = resolved  # keep deploy path as target
    return result


# --- Workspace discovery ---

_workspace_cache: dict[str, Path] | None = None


def _discover_from_workspaces() -> dict[str, Path]:
    """Scan workspace roots from workspaces.json for games with ifhub.conf.

    For "in-place" deploy workspaces, the game directory IS the deploy dir.
    For workspaces with a separate deploy root, the deploy dir is
    <deploy_root>/<game_name>/ (looked up via the 'name' field in ifhub.conf,
    falling back to the directory name).
    """
    global _workspace_cache
    if _workspace_cache is not None:
        return dict(_workspace_cache)

    result: dict[str, Path] = {}

    if not WORKSPACES_FILE.exists():
        _workspace_cache = result
        return dict(result)

    try:
        data = json.loads(WORKSPACES_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        _workspace_cache = result
        return dict(result)

    for ws in data.get("workspaces", []):
        root_raw = ws.get("root", "")
        deploy_mode = ws.get("deploy", "in-place")

        root = _resolve_raw_path(root_raw)
        if root == Path() or not root.is_dir():
            continue

        # Resolve deploy root for non-in-place workspaces
        deploy_root = None
        if deploy_mode != "in-place":
            deploy_root = _resolve_raw_path(deploy_mode)

        # Scan subdirectories for ifhub.conf
        try:
            entries = sorted(root.iterdir())
        except OSError:
            continue

        for subdir in entries:
            if not subdir.is_dir():
                continue
            conf_file = subdir / "ifhub.conf"
            if not conf_file.exists():
                continue

            # Read the game name from ifhub.conf (fall back to dir name)
            game_name = subdir.name
            try:
                for line in conf_file.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if stripped.startswith("name") and "=" in stripped:
                        game_name = stripped.split("=", 1)[1].strip()
                        break
            except OSError:
                pass

            if deploy_mode == "in-place":
                result[game_name] = subdir
            elif deploy_root is not None:
                deploy_dir = deploy_root / game_name
                result[game_name] = deploy_dir

    _workspace_cache = result
    return dict(result)


def game_source_dir(name: str) -> Path:
    """Return absolute path to a game's source directory.

    Resolution order:
    1. 'source' field in games-registry.json / games-local.json
    2. Workspace scan (for non-in-place workspaces, source is the workspace subdir)
    """
    registry = _load_registry()
    entry = registry.get(name, {})
    source = entry.get("source", "")
    if source:
        return _resolve_raw_path(source)

    # Fall back to workspace discovery — find the workspace subdir containing this game
    if not WORKSPACES_FILE.exists():
        return Path()

    try:
        data = json.loads(WORKSPACES_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return Path()

    for ws in data.get("workspaces", []):
        if ws.get("deploy", "in-place") == "in-place":
            continue  # in-place games have no separate source dir
        root = _resolve_raw_path(ws.get("root", ""))
        if root == Path() or not root.is_dir():
            continue
        # Check each subdir for a matching game name
        try:
            for subdir in root.iterdir():
                if not subdir.is_dir():
                    continue
                conf_file = subdir / "ifhub.conf"
                if not conf_file.exists():
                    continue
                game_name = subdir.name
                try:
                    for line in conf_file.read_text(encoding="utf-8").splitlines():
                        stripped = line.strip()
                        if stripped.startswith("name") and "=" in stripped:
                            game_name = stripped.split("=", 1)[1].strip()
                            break
                except OSError:
                    pass
                if game_name == name:
                    return subdir
        except OSError:
            continue

    return Path()


def game_repo(name: str) -> str:
    """Return the GitHub repo (e.g., 'Johnesco/zork1') for a registered game, or ''."""
    registry = _load_registry()
    entry = registry.get(name, {})
    return entry.get("repo", "")


def project_dir(name: str) -> Path:
    """Return absolute path to a game's project directory.

    Resolution order:
    1. games-local.json (per-developer overrides)
    2. games-registry.json (committed overrides)
    3. Workspace scan (ifhub.conf discovery)
    4. projects/<name>/ (legacy fallback)
    """
    # Check registry overrides first (local + committed)
    registry = _load_registry()
    entry = registry.get(name)
    if entry:
        resolved = _resolve_game_path(entry)
        if resolved != Path():
            return resolved
    # Workspace discovery
    all_games = _discover_from_workspaces()
    if name in all_games:
        return all_games[name]
    # Legacy fallback
    return PROJECTS_DIR / name


def to_posix(path: str | Path) -> str:
    """Convert a Windows path to MSYS2/Git Bash posix form.

    C:\\code\\ifhub -> /c/code/ifhub
    """
    s = str(path).replace("\\", "/")
    m = re.match(r"^([A-Za-z]):/", s)
    if m:
        s = "/" + m.group(1).lower() + "/" + s[3:]
    return s


def to_windows(path: str) -> str:
    """Convert a MSYS2/Git Bash path to Windows form.

    /c/code/ifhub -> C:\\code\\ifhub
    """
    m = re.match(r"^/([a-zA-Z])/(.*)", path)
    if m:
        drive = m.group(1).upper()
        rest = m.group(2).replace("/", "\\")
        return f"{drive}:\\{rest}"
    return path.replace("/", "\\")
