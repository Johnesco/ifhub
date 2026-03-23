"""Project discovery and metadata — shared by run.py and dashboard.py.

Scans the projects/ directory, detects engines, capabilities, and pipeline
state for each project.  Both the CLI runner and the web dashboard import
this module instead of maintaining their own copies.
"""

import glob as _glob_mod
import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import config as _libconfig
from . import paths


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ProjectInfo:
    """Metadata for a single game project.

    Fields used by run.py:
        name, dir, engine, source_file, sound, hub_id, tests,
        has_walkthrough, has_regtest, golden_seed

    Additional fields used by dashboard.py:
        has_source, has_test_me, has_play_html, has_binary, has_index,
        has_source_html, has_git, registered, pipeline_state, binary_name,
        binary_size, binary_mtime, source_mtime, compile_stale, test_stale,
        failed_stage, stage_status
    """

    name: str
    dir: str
    engine: str = "unknown"
    source_file: str = ""
    sound: bool = False
    hub_id: str = ""
    tests: str = ""
    has_source: bool = False
    has_walkthrough: bool = False
    has_regtest: bool = False
    has_test_me: bool = False
    has_play_html: bool = False
    has_binary: bool = False
    has_index: bool = False
    has_source_html: bool = False
    has_git: bool = False
    registered: bool = False
    golden_seed: str | None = None
    # Pipeline state enrichment
    pipeline_state: dict = field(default_factory=dict)
    binary_name: str = ""
    binary_size: int = 0
    binary_mtime: float = 0
    source_mtime: float = 0
    compile_stale: bool = True
    test_stale: bool = True
    failed_stage: str = ""
    stage_status: dict = field(default_factory=dict)


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


def load_projects(
    *,
    enrich_pipeline: bool = False,
) -> list[ProjectInfo]:
    """Discover games from registry + projects/ and return ProjectInfo objects.

    Discovery merges games from games-registry.json / games-local.json with
    any additional projects found in the projects/ directory.  Registry entries
    take priority when a game appears in both places.

    Args:
        enrich_pipeline: If True, read .pipeline-state files and compute
            staleness, binary details, per-stage status, and registration
            status.  The dashboard sets this to True; the CLI runner leaves
            it False for speed.
    """
    registered_ids = _load_registered_ids() if enrich_pipeline else set()
    projects: list[ProjectInfo] = []

    # Build name -> dir mapping: registry first, then projects/ for any extras
    game_dirs: dict[str, str] = {}

    # From registry (local overrides defaults)
    for name, resolved_path in paths.registered_games().items():
        game_dirs[name] = str(resolved_path)

    # From projects/ directory (adds any not already in registry)
    projects_dir = str(paths.PROJECTS_DIR)
    if os.path.isdir(projects_dir):
        for name in os.listdir(projects_dir):
            pdir = os.path.join(projects_dir, name)
            if os.path.isdir(pdir) and name not in game_dirs:
                game_dirs[name] = pdir

    for name in sorted(game_dirs):
        project_dir = game_dirs[name]
        if not os.path.isdir(project_dir):
            continue

        # Detect engine and source file
        conf_fields = _libconfig.parse_conf_fields(project_dir)
        engine = _libconfig.detect_engine(project_dir, conf_fields)
        source_file = _libconfig.detect_source_file(project_dir, engine, conf_fields)
        source_path = os.path.join(project_dir, source_file) if source_file else ""
        has_source = bool(source_file) and os.path.isfile(source_path)
        engine_spec = _libconfig.get_engine_spec(engine)

        # Skip truly empty directories (no source and no play.html)
        has_play = os.path.isfile(os.path.join(project_dir, "play.html"))
        if not source_file and not has_play:
            continue

        # Pipeline fields from project.conf
        pipeline_fields = _libconfig.parse_pipeline_fields(
            os.path.join(project_dir, "tests", "project.conf")
        )

        # Infer capabilities
        sound = pipeline_fields.get("PIPELINE_SOUND", "").lower() == "true"
        if not sound and os.path.isdir(os.path.join(project_dir, "Sounds")):
            sound = True

        hub_id = pipeline_fields.get("PIPELINE_HUB_ID", "") or name
        tests = pipeline_fields.get("PIPELINE_TESTS", "")

        # Detect capabilities from test data files
        has_walkthrough = os.path.isfile(
            os.path.join(project_dir, "tests", "inform7", "walkthrough.txt")
        )
        has_regtest = bool(
            _glob_mod.glob(os.path.join(project_dir, "tests", "*.regtest"))
            if os.path.isdir(os.path.join(project_dir, "tests"))
            else []
        )

        # Test me detection (Inform 7 only)
        has_test_me = False
        if engine == "inform7" and has_source:
            try:
                with open(source_path, "r", encoding="utf-8") as f:
                    has_test_me = bool(
                        re.search(r"Test\s+\w+\s+with", f.read(), re.IGNORECASE)
                    )
            except OSError:
                pass

        # Only look up golden seed for engines with CLI tests
        golden_seed = None
        if engine_spec and engine_spec.has_cli_tests:
            golden_seed = _libconfig.get_golden_seed(project_dir)

        # Detect compiled binaries (engine-appropriate)
        dir_files = os.listdir(project_dir)
        if engine == "inform7":
            has_binary = any(
                f.endswith((".ulx", ".gblorb"))
                for f in dir_files
                if os.path.isfile(os.path.join(project_dir, f))
            )
        else:
            has_binary = has_play

        has_index = os.path.isfile(os.path.join(project_dir, "index.html"))
        has_source_html = os.path.isfile(os.path.join(project_dir, "source.html"))
        has_git = os.path.isdir(os.path.join(project_dir, ".git"))

        # --- Pipeline state enrichment (dashboard only) ---
        pipeline_state: dict = {}
        binary_name_str = ""
        binary_sz = 0
        binary_mt = 0.0
        source_mt = 0.0
        compile_stale = True
        test_stale = True
        failed_stage = ""
        stage_status: dict = {}
        is_registered = False

        if enrich_pipeline:
            is_registered = (
                name in registered_ids
                or conf_fields.get("PIPELINE_HUB_ID", "") in registered_ids
                or any(rid.startswith(name) for rid in registered_ids)
            )

            # Read .pipeline-state
            state_file = os.path.join(project_dir, ".pipeline-state")
            try:
                if os.path.isfile(state_file):
                    with open(state_file, "r", encoding="utf-8") as f:
                        pipeline_state = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

            # Source mtime
            if has_source and source_path:
                try:
                    source_mt = os.path.getmtime(source_path)
                except OSError:
                    pass

            # Find binary file for details
            if engine == "inform7":
                for fname in dir_files:
                    if fname.endswith((".gblorb", ".ulx")):
                        bp = os.path.join(project_dir, fname)
                        if os.path.isfile(bp):
                            binary_name_str = fname
                            try:
                                binary_sz = os.path.getsize(bp)
                                binary_mt = os.path.getmtime(bp)
                            except OSError:
                                pass
                            break
            elif has_play:
                binary_name_str = "play.html"
                bp = os.path.join(project_dir, "play.html")
                try:
                    binary_sz = os.path.getsize(bp)
                    binary_mt = os.path.getmtime(bp)
                except OSError:
                    pass

            # Staleness: compare current hashes to pipeline state
            if has_source and source_path:
                try:
                    cur_hash = hashlib.md5(
                        open(source_path, "rb").read()
                    ).hexdigest()
                    saved = pipeline_state.get("STAGE_COMPILE_SOURCE_HASH", "")
                    if saved and saved == cur_hash:
                        compile_stale = False
                except OSError:
                    pass

            if binary_name_str:
                bp = os.path.join(project_dir, binary_name_str)
                try:
                    cur_hash = hashlib.md5(open(bp, "rb").read()).hexdigest()
                    saved = pipeline_state.get("STAGE_TEST_BINARY_HASH", "")
                    if saved and saved == cur_hash:
                        test_stale = False
                except OSError:
                    pass

            failed_stage = pipeline_state.get("STAGE_FAILED", "")

            # Derive per-stage status
            has_cli_tests = engine_spec.has_cli_tests if engine_spec else False
            is_buildable = engine in (
                "inform7", "wwwbasic", "qbjc", "applesoft",
                "bwbasic", "basic", "ink", "jsdos",
            )

            # Build status
            if not is_buildable:
                stage_status["build"] = "n/a"
            elif failed_stage == "compile":
                stage_status["build"] = "failed"
            elif not pipeline_state.get("STAGE_COMPILE_SOURCE_HASH"):
                stage_status["build"] = "not-run"
            elif compile_stale:
                stage_status["build"] = "stale"
            else:
                stage_status["build"] = "done"

            # Test status
            if not has_cli_tests or not (has_walkthrough or has_regtest):
                stage_status["test"] = "n/a"
            elif failed_stage == "test":
                stage_status["test"] = "failed"
            elif not has_binary:
                stage_status["test"] = "blocked"
            elif not pipeline_state.get("STAGE_TEST_BINARY_HASH"):
                stage_status["test"] = "not-run"
            elif test_stale:
                stage_status["test"] = "stale"
            else:
                stage_status["test"] = "done"

            # Package status
            if has_index and has_source_html:
                stage_status["package"] = "done"
            else:
                stage_status["package"] = "not-run"

            # Register status
            stage_status["register"] = "done" if is_registered else "not-run"

            # Publish status
            stage_status["publish"] = "done" if has_git else "not-run"

        projects.append(
            ProjectInfo(
                name=name,
                dir=project_dir,
                engine=engine,
                source_file=source_file,
                sound=sound,
                hub_id=hub_id,
                tests=tests,
                has_source=has_source,
                has_walkthrough=has_walkthrough,
                has_regtest=has_regtest,
                has_test_me=has_test_me,
                has_play_html=has_play,
                has_binary=has_binary,
                has_index=has_index,
                has_source_html=has_source_html,
                has_git=has_git,
                registered=is_registered,
                golden_seed=golden_seed,
                pipeline_state=pipeline_state,
                binary_name=binary_name_str,
                binary_size=binary_sz,
                binary_mtime=binary_mt,
                source_mtime=source_mt,
                compile_stale=compile_stale,
                test_stale=test_stale,
                failed_stage=failed_stage,
                stage_status=stage_status,
            )
        )
    return projects
