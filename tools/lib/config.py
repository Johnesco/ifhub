"""Project configuration loading — reads project.conf and seeds.conf.

project.conf is a bash-sourceable file. We parse the simple key=value
assignments and PIPELINE_* fields without actually sourcing bash.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import paths


@dataclass
class EngineConfig:
    name: str = ""
    path: str = ""
    seed_flag: str = "--rngseed"
    game_path: str = ""
    walkthrough: str = ""
    output_file: str = ""
    seeds_key: str = ""


@dataclass
class ScoringConfig:
    score_regex: str = r"score is (?P<score>[0-9]+)"
    fallback_regex: str = r"(?P<score>[0-9]+)(?= \(total of [0-9]+ points\))"
    max_regex: str = r"total of (?P<max>[0-9]+)"
    pass_threshold: int = 350
    default_max: int = 350


@dataclass
class DiagConfig:
    death_patterns: str = "you have died"
    won_patterns: str = "You have won"
    scoreless: bool = False


@dataclass
class PipelineConfig:
    sound: bool = False
    versioned: bool = False
    current_version: str = ""
    hub_id: str = ""
    tests: str = ""
    walkthrough_output_dir: str = ""


@dataclass
class ProjectConfig:
    """Parsed project configuration."""

    project_name: str = ""
    project_dir: Path = field(default_factory=Path)
    primary: EngineConfig = field(default_factory=EngineConfig)
    alt: EngineConfig = field(default_factory=EngineConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    diagnostics: DiagConfig = field(default_factory=DiagConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    regtest_file: str = ""
    regtest_engine: str = ""
    regtest_game: str = ""


def _expand_vars(value: str, project_dir: Path) -> str:
    """Expand $PROJECT_DIR, $HOME, and $_IFHUB_ROOT in config values."""
    value = value.replace("$PROJECT_DIR", str(project_dir))
    value = value.replace("${PROJECT_DIR}", str(project_dir))
    value = value.replace("$HOME", os.path.expanduser("~"))
    value = value.replace("${HOME}", os.path.expanduser("~"))
    # $_IFHUB_ROOT used in zork1's project.conf
    ifhub_root = str(paths.I7_ROOT)
    value = value.replace("$_IFHUB_ROOT", ifhub_root)
    value = value.replace("${_IFHUB_ROOT}", ifhub_root)
    return value


def _parse_kv(conf_path: Path, project_dir: Path) -> dict[str, str]:
    """Parse simple KEY=VALUE or KEY="VALUE" lines from a bash config file.

    Skips lines with conditionals, function defs, and complex bash logic.
    """
    kv: dict[str, str] = {}
    try:
        text = conf_path.read_text(encoding="utf-8")
    except OSError:
        return kv

    for line in text.splitlines():
        line = line.strip()
        # Skip comments, empty, conditionals, function defs
        if not line or line.startswith("#") or line.startswith("if ") or line.startswith("fi"):
            continue
        if line.startswith("else") or line.startswith("elif"):
            continue
        if "()" in line or line.startswith("local "):
            continue

        m = re.match(r'^(\w+)=["\']?(.*?)["\']?\s*$', line)
        if m:
            key = m.group(1)
            val = _expand_vars(m.group(2), project_dir)
            kv[key] = val

    return kv


def load_config(conf_path: Path | str) -> ProjectConfig:
    """Load a project configuration from a project.conf file.

    Parses simple assignments and resolves platform-appropriate engine paths.
    For engine paths that depend on platform detection (the if/else blocks in
    project.conf), we use our own detection logic.
    """
    conf_path = Path(conf_path)
    # project.conf lives in tests/, project_dir is one level up
    project_dir = conf_path.parent.parent
    kv = _parse_kv(conf_path, project_dir)

    cfg = ProjectConfig(project_dir=project_dir)
    cfg.project_name = kv.get("PROJECT_NAME", "")

    # Resolve engine paths using platform detection
    native_glulxe = paths.NATIVE_GLULXE
    native_dfrotz = paths.NATIVE_DFROTZ
    use_native = native_glulxe.exists() and os.access(str(native_glulxe), os.X_OK)

    if use_native:
        cfg.primary.path = str(native_glulxe)
        cfg.alt.path = str(native_dfrotz) if native_dfrotz.exists() else ""
    else:
        cfg.primary.path = kv.get("PRIMARY_ENGINE_PATH",
                                   os.path.expanduser("~/glulxe/glulxe"))
        cfg.alt.path = kv.get("ALT_ENGINE_PATH",
                               os.path.expanduser("~/frotz-install/usr/games/dfrotz"))

    # Primary engine
    cfg.primary.name = kv.get("PRIMARY_ENGINE_NAME", "glulxe")
    cfg.primary.seed_flag = kv.get("PRIMARY_ENGINE_SEED_FLAG", "--rngseed")
    cfg.primary.game_path = kv.get("PRIMARY_GAME_PATH",
                                    str(project_dir / f"{project_dir.name}.ulx"))
    cfg.primary.walkthrough = kv.get("PRIMARY_WALKTHROUGH",
                                      str(project_dir / "tests" / "inform7" / "walkthrough.txt"))
    cfg.primary.output_file = kv.get("PRIMARY_OUTPUT_FILE",
                                      str(project_dir / "tests" / "inform7" / "walkthrough_output.txt"))
    cfg.primary.seeds_key = kv.get("PRIMARY_SEEDS_KEY", "glulxe")

    # Alt engine
    cfg.alt.name = kv.get("ALT_ENGINE_NAME", "dfrotz")
    cfg.alt.seed_flag = kv.get("ALT_ENGINE_SEED_FLAG", "-s")
    cfg.alt.game_path = kv.get("ALT_GAME_PATH", "")
    cfg.alt.walkthrough = kv.get("ALT_WALKTHROUGH", "")
    cfg.alt.output_file = kv.get("ALT_OUTPUT_FILE", "")
    cfg.alt.seeds_key = kv.get("ALT_SEEDS_KEY", "dfrotz")

    # Scoring
    cfg.scoring.score_regex = kv.get("SCORE_REGEX", cfg.scoring.score_regex)
    cfg.scoring.fallback_regex = kv.get("SCORE_FALLBACK_REGEX", cfg.scoring.fallback_regex)
    cfg.scoring.max_regex = kv.get("MAX_SCORE_REGEX", cfg.scoring.max_regex)
    try:
        cfg.scoring.pass_threshold = int(kv.get("PASS_THRESHOLD", str(cfg.scoring.pass_threshold)))
    except ValueError:
        pass
    try:
        cfg.scoring.default_max = int(kv.get("DEFAULT_MAX_SCORE", str(cfg.scoring.default_max)))
    except ValueError:
        pass

    # Diagnostics
    cfg.diagnostics.death_patterns = kv.get("DEATH_PATTERNS", cfg.diagnostics.death_patterns)
    cfg.diagnostics.won_patterns = kv.get("WON_PATTERNS", cfg.diagnostics.won_patterns)
    cfg.diagnostics.scoreless = kv.get("SCORELESS_GAME", "").lower() == "true"

    # RegTest
    cfg.regtest_file = kv.get("REGTEST_FILE", "")
    if use_native:
        cfg.regtest_engine = str(native_glulxe)
    else:
        cfg.regtest_engine = kv.get("REGTEST_ENGINE",
                                     os.path.expanduser("~/glulxe/glulxe"))
    cfg.regtest_game = kv.get("REGTEST_GAME", "")

    # Pipeline
    cfg.pipeline.sound = kv.get("PIPELINE_SOUND", "").lower() == "true"
    cfg.pipeline.versioned = kv.get("PIPELINE_VERSIONED", "").lower() == "true"
    cfg.pipeline.current_version = kv.get("PIPELINE_CURRENT_VERSION", "")
    cfg.pipeline.hub_id = kv.get("PIPELINE_HUB_ID", "")
    cfg.pipeline.tests = kv.get("PIPELINE_TESTS", "")
    cfg.pipeline.walkthrough_output_dir = kv.get("PIPELINE_WALKTHROUGH_OUTPUT_DIR", "")

    return cfg


def parse_pipeline_fields(conf_path: str | Path) -> dict[str, str]:
    """Extract PIPELINE_* fields from a project.conf file.

    Backward-compatible helper used by run.py during the transition.
    """
    fields: dict[str, str] = {}
    try:
        with open(conf_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                m = re.match(r'^(PIPELINE_\w+)=["\']?(.*?)["\']?\s*$', line)
                if m:
                    fields[m.group(1)] = m.group(2)
    except OSError:
        pass
    return fields


def get_golden_seed(project_dir: str | Path, engine_key: str = "glulxe") -> str | None:
    """Read the first seed for the given engine from tests/seeds.conf."""
    seeds_path = Path(project_dir) / "tests" / "seeds.conf"
    try:
        for line in seeds_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(f"{engine_key}:"):
                parts = line.split(":")
                if len(parts) >= 2 and parts[1]:
                    return parts[1]
    except OSError:
        pass
    return None


def get_seed_hash(project_dir: str | Path, engine_key: str = "glulxe") -> str | None:
    """Read the binary hash for the given engine from tests/seeds.conf."""
    seeds_path = Path(project_dir) / "tests" / "seeds.conf"
    try:
        for line in seeds_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(f"{engine_key}:"):
                parts = line.split(":")
                if len(parts) >= 3 and parts[2] and parts[2] != "none":
                    return parts[2]
    except OSError:
        pass
    return None
