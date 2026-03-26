"""Project discovery and artifact-based state model.

Shared by run.py and dashboard.py.  Each game has 4 artifacts whose status
(present / missing / stale / failed / n/a) is derived from the filesystem
and .pipeline-state hashes.

Artifacts: compile, test, published, registered
"""

import glob as _glob_mod
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from . import config as _libconfig
from . import paths


# ---------------------------------------------------------------------------
# Artifact state model
# ---------------------------------------------------------------------------


class ArtifactStatus(Enum):
    PRESENT = "present"   # File exists and is current
    MISSING = "missing"   # File does not exist
    STALE = "stale"       # File exists but source changed since it was built
    FAILED = "failed"     # Last build attempt failed
    NA = "n/a"            # Not applicable for this engine


@dataclass
class ArtifactState:
    """Status of a single build artifact."""
    status: ArtifactStatus = ArtifactStatus.MISSING
    path: str = ""       # Filesystem path (for clickable links)
    size: int = 0        # File size in bytes
    mtime: float = 0.0   # Last modified epoch
    detail: str = ""     # Human-readable summary


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _fmt_size(nbytes: int) -> str:
    if nbytes <= 0:
        return ""
    if nbytes < 1024:
        return f"{nbytes} B"
    if nbytes < 1024 * 1024:
        return f"{nbytes / 1024:.1f} KB"
    return f"{nbytes / (1024 * 1024):.1f} MB"


def _fmt_rel_time(epoch: float) -> str:
    if not epoch:
        return ""
    diff = time.time() - epoch
    if diff < 60:
        return "just now"
    if diff < 3600:
        return f"{int(diff / 60)}m ago"
    if diff < 86400:
        return f"{int(diff / 3600)}h ago"
    if diff < 172800:
        return "yesterday"
    return time.strftime("%b %d", time.localtime(epoch))


# ---------------------------------------------------------------------------
# Engine → compile script mapping (for display in dashboard)
# ---------------------------------------------------------------------------

ENGINE_COMPILE_SCRIPTS = {
    "inform7": "compile.py \u2192 setup_web.py",
    "zmachine": "setup_web.py",
    "sharpee": "compile_sharpee.py",
    "rez": "compile_rez.py",
    "ink": "setup_ink.py",
    "wwwbasic": "setup_basic.py",
    "qbjc": "setup_basic.py",
    "applesoft": "setup_basic.py",
    "bwbasic": "setup_basic.py",
    "jsdos": "setup_basic.py",
    "twine": "(no build tool)",
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


ARTIFACT_KEYS = ("compile", "published", "registered")


@dataclass
class ProjectInfo:
    """Metadata for a single game project."""

    # Identity
    name: str
    dir: str
    engine: str = "unknown"
    source_file: str = ""

    # Config
    sound: bool = False
    hub_id: str = ""

    # Artifact states — keys: compile, published, registered
    artifacts: dict[str, ArtifactState] = field(default_factory=dict)

    # --- Backward-compat properties (used by run.py, pipeline.py) ---

    @property
    def has_source(self) -> bool:
        return bool(self.source_file) and os.path.isfile(
            os.path.join(self.dir, self.source_file)
        )

    @property
    def has_play_html(self) -> bool:
        a = self.artifacts.get("compile")
        return a is not None and a.status not in (ArtifactStatus.MISSING, ArtifactStatus.NA)

    @property
    def has_binary(self) -> bool:
        return self.has_play_html

    @property
    def has_index(self) -> bool:
        return os.path.isfile(os.path.join(self.dir, "index.html"))

    @property
    def has_source_html(self) -> bool:
        return os.path.isfile(os.path.join(self.dir, "source.html"))

    @property
    def has_git(self) -> bool:
        a = self.artifacts.get("published")
        return a is not None and a.status not in (ArtifactStatus.MISSING, ArtifactStatus.NA)

    @property
    def registered(self) -> bool:
        a = self.artifacts.get("registered")
        return a is not None and a.status == ArtifactStatus.PRESENT

    @property
    def compile_scripts(self) -> str:
        """Which scripts the compile step runs for this engine."""
        return ENGINE_COMPILE_SCRIPTS.get(self.engine, "")

    @property
    def overall_status(self) -> str:
        """Single word: 'ready', 'stale', 'incomplete', 'failed'."""
        statuses = [a.status for a in self.artifacts.values()
                    if a.status != ArtifactStatus.NA]
        if any(s == ArtifactStatus.FAILED for s in statuses):
            return "failed"
        if any(s == ArtifactStatus.STALE for s in statuses):
            return "stale"
        if any(s == ArtifactStatus.MISSING for s in statuses):
            return "incomplete"
        return "ready"


# ---------------------------------------------------------------------------
# Discovery helpers
# ---------------------------------------------------------------------------


def _load_registered_ids() -> set[str]:
    """Return set of game IDs currently in games.json."""
    games_path = paths.IFHUB_DIR / "games.json"
    try:
        with open(games_path, "r", encoding="utf-8") as f:
            return {g["id"] for g in json.load(f)}
    except (OSError, json.JSONDecodeError):
        return set()


def _load_registry_repos() -> dict[str, str]:
    """Return mapping of game name -> repo string from games-registry.json."""
    reg_path = paths.I7_ROOT / "games-registry.json"
    try:
        with open(reg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {name: entry.get("repo", "") for name, entry in data.items()}
    except (OSError, json.JSONDecodeError):
        return {}


def _file_stat(filepath: str) -> tuple[int, float]:
    """Return (size, mtime) for a file, or (0, 0.0) if it doesn't exist."""
    try:
        st = os.stat(filepath)
        return st.st_size, st.st_mtime
    except OSError:
        return 0, 0.0


def _md5_file(filepath: str) -> str:
    """Return MD5 hex digest of a file, or '' on error."""
    try:
        return hashlib.md5(open(filepath, "rb").read()).hexdigest()
    except OSError:
        return ""


def walkthrough_path(project_dir: str) -> str:
    """Return the walkthrough file path, preferring universal location.

    Priority: tests/walkthrough.txt > tests/inform7/walkthrough.txt
    """
    universal = os.path.join(project_dir, "tests", "walkthrough.txt")
    if os.path.isfile(universal):
        return universal
    i7_path = os.path.join(project_dir, "tests", "inform7", "walkthrough.txt")
    if os.path.isfile(i7_path):
        return i7_path
    # Default to universal location for new writes
    return universal


# ---------------------------------------------------------------------------
# Artifact computation
# ---------------------------------------------------------------------------


def _compute_artifacts(
    name: str,
    project_dir: str,
    engine: str,
    engine_spec: _libconfig.EngineSpec | None,
    source_file: str,
    registered_ids: set[str],
    registry_repos: dict[str, str],
    conf_fields: dict[str, str],
) -> dict[str, ArtifactState]:
    """Compute artifact states for a project from filesystem + pipeline state."""

    dir_files = os.listdir(project_dir)

    # --- Load .pipeline-state ---
    pipeline_state: dict = {}
    state_file = os.path.join(project_dir, ".pipeline-state")
    try:
        if os.path.isfile(state_file):
            with open(state_file, "r", encoding="utf-8") as f:
                pipeline_state = json.load(f)
    except (json.JSONDecodeError, OSError):
        pass

    failed_stage = pipeline_state.get("STAGE_FAILED", "")

    # --- Source file info ---
    source_path = os.path.join(project_dir, source_file) if source_file else ""
    source_hash = _md5_file(source_path) if source_path else ""

    # =====================================================================
    # COMPILE artifact (was: build + pages)
    # =====================================================================
    compile_art = ArtifactState()

    # Find the primary build output
    build_file = ""
    if engine == "inform7":
        for fname in dir_files:
            if fname.endswith((".gblorb", ".ulx")):
                fp = os.path.join(project_dir, fname)
                if os.path.isfile(fp):
                    build_file = fp
                    break
    if not build_file:
        ph = os.path.join(project_dir, "play.html")
        if os.path.isfile(ph):
            build_file = ph

    if build_file:
        sz, mt = _file_stat(build_file)
        compile_art.path = build_file
        compile_art.size = sz
        compile_art.mtime = mt
        fname = os.path.basename(build_file)
        compile_art.detail = f"{fname} \u00b7 {_fmt_size(sz)} \u00b7 {_fmt_rel_time(mt)}"

        if failed_stage == "compile":
            compile_art.status = ArtifactStatus.FAILED
            compile_art.detail = f"{fname} \u00b7 compile failed"
        elif source_hash:
            saved = pipeline_state.get("STAGE_COMPILE_SOURCE_HASH", "")
            if saved and saved == source_hash:
                compile_art.status = ArtifactStatus.PRESENT
            elif saved:
                compile_art.status = ArtifactStatus.STALE
                compile_art.detail = f"{fname} \u00b7 source changed"
            else:
                compile_art.status = ArtifactStatus.PRESENT
        else:
            compile_art.status = ArtifactStatus.PRESENT
    else:
        compile_art.status = ArtifactStatus.MISSING
        compile_art.detail = "not compiled"

    # =====================================================================
    # PUBLISHED artifact
    # =====================================================================
    published = ArtifactState()
    has_git = os.path.isdir(os.path.join(project_dir, ".git"))

    if has_git:
        published.status = ArtifactStatus.PRESENT
        repo = registry_repos.get(name, "")
        published.path = os.path.join(project_dir, ".git")
        published.detail = repo if repo else "git repo"
    else:
        published.status = ArtifactStatus.MISSING
        published.detail = "no repo"

    # =====================================================================
    # REGISTERED artifact
    # =====================================================================
    registered = ArtifactState()
    hub_id = conf_fields.get("PIPELINE_HUB_ID", "") or name
    is_registered = (
        name in registered_ids
        or hub_id in registered_ids
        or any(rid.startswith(name) for rid in registered_ids)
    )

    if is_registered:
        registered.status = ArtifactStatus.PRESENT
        registered.detail = "in games.json"
    else:
        registered.status = ArtifactStatus.MISSING
        registered.detail = "not registered"

    return {
        "compile": compile_art,
        "published": published,
        "registered": registered,
    }


# ---------------------------------------------------------------------------
# Main discovery
# ---------------------------------------------------------------------------


def load_projects() -> list[ProjectInfo]:
    """Discover games from registry + projects/ and return ProjectInfo objects."""
    registered_ids = _load_registered_ids()
    registry_repos = _load_registry_repos()
    projects: list[ProjectInfo] = []

    game_dirs: dict[str, str] = {}

    for gname, resolved_path in paths.registered_games().items():
        game_dirs[gname] = str(resolved_path)

    projects_dir = str(paths.PROJECTS_DIR)
    if os.path.isdir(projects_dir):
        for dname in os.listdir(projects_dir):
            pdir = os.path.join(projects_dir, dname)
            if os.path.isdir(pdir) and dname not in game_dirs:
                game_dirs[dname] = pdir

    for name in sorted(game_dirs):
        project_dir = game_dirs[name]
        if not os.path.isdir(project_dir):
            continue

        conf_fields = _libconfig.parse_conf_fields(project_dir)
        engine = _libconfig.detect_engine(project_dir, conf_fields)
        source_file = _libconfig.detect_source_file(project_dir, engine, conf_fields)
        source_path = os.path.join(project_dir, source_file) if source_file else ""
        has_source = bool(source_file) and os.path.isfile(source_path)
        engine_spec = _libconfig.get_engine_spec(engine)

        has_play = os.path.isfile(os.path.join(project_dir, "play.html"))
        if not source_file and not has_play:
            continue

        pipeline_fields = _libconfig.parse_pipeline_fields(
            os.path.join(project_dir, "tests", "project.conf")
        )

        sound = pipeline_fields.get("PIPELINE_SOUND", "").lower() == "true"
        if not sound and os.path.isdir(os.path.join(project_dir, "Sounds")):
            sound = True

        hub_id = pipeline_fields.get("PIPELINE_HUB_ID", "") or name

        artifacts = _compute_artifacts(
            name=name,
            project_dir=project_dir,
            engine=engine,
            engine_spec=engine_spec,
            source_file=source_file,
            registered_ids=registered_ids,
            registry_repos=registry_repos,
            conf_fields=conf_fields,
        )

        projects.append(
            ProjectInfo(
                name=name,
                dir=project_dir,
                engine=engine,
                source_file=source_file,
                sound=sound,
                hub_id=hub_id,
                artifacts=artifacts,
            )
        )
    return projects
