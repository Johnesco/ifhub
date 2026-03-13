#!/usr/bin/env python3
"""Interactive Pipeline Runner for IF Hub.

Presents arrow-key menus to select pipeline tasks and games,
then delegates to Python scripts via subprocess.

Usage:
    python tools/run.py

Requires: pip install InquirerPy
"""

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------

try:
    from InquirerPy import inquirer
    from InquirerPy.separator import Separator
except ImportError:
    print("Missing dependency: InquirerPy")
    print()
    print("  pip install InquirerPy")
    print()
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants (resolved relative to this script)
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
I7_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECTS_DIR = os.path.join(I7_ROOT, "projects")

sys.path.insert(0, SCRIPT_DIR)
from lib import config  # noqa: E402
IFHUB_DIR = os.path.join(I7_ROOT, "ifhub")
PIPELINE_PY = os.path.join(SCRIPT_DIR, "pipeline.py")
PUBLISH_PY = os.path.join(SCRIPT_DIR, "publish.py")
DEV_SERVER_PY = os.path.join(SCRIPT_DIR, "dev-server.py")
COMPILE_PY = os.path.join(SCRIPT_DIR, "compile.py")
EXTRACT_COMMANDS_PY = os.path.join(SCRIPT_DIR, "extract_commands.py")
GENERATE_PAGES_PY = os.path.join(SCRIPT_DIR, "web", "generate_pages.py")
REGISTER_GAME_PY = os.path.join(SCRIPT_DIR, "register_game.py")
PUSH_HUB_PY = os.path.join(SCRIPT_DIR, "push_hub.py")
NEW_PROJECT_PY = os.path.join(SCRIPT_DIR, "new_project.py")
TESTING_DIR = os.path.join(SCRIPT_DIR, "testing")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_command(cmd: list[str], cwd: str | None = None) -> int:
    """Run a command with live terminal output. Returns exit code.

    cmd is a list of arguments (first element is the executable).
    """
    try:
        result = subprocess.run(cmd, cwd=cwd)
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        return 130


def py_cmd(*args: str) -> list[str]:
    """Build a Python subprocess command list."""
    return [sys.executable, *args]


def prompt_or_cancel(prompt_fn):
    """Wrap an InquirerPy prompt; exit cleanly on Ctrl-C."""
    try:
        return prompt_fn()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ProjectInfo:
    name: str
    dir: str
    engine: str = "unknown"
    source_file: str = ""
    sound: bool = False
    hub_id: str = ""
    tests: str = ""
    has_walkthrough: bool = False
    has_regtest: bool = False
    golden_seed: str | None = None


# ---------------------------------------------------------------------------
# Project discovery
# ---------------------------------------------------------------------------


def load_projects() -> list[ProjectInfo]:
    """Scan projects/ and return a list of ProjectInfo objects."""
    projects = []
    for name in sorted(os.listdir(PROJECTS_DIR)):
        project_dir = os.path.join(PROJECTS_DIR, name)
        if not os.path.isdir(project_dir):
            continue

        # Detect engine and source file
        conf_fields = config.parse_conf_fields(project_dir)
        engine = config.detect_engine(project_dir, conf_fields)
        source_file = config.detect_source_file(project_dir, engine, conf_fields)
        engine_spec = config.get_engine_spec(engine)

        # Skip truly empty directories (no source and no play.html)
        has_play = os.path.isfile(os.path.join(project_dir, "play.html"))
        if not source_file and not has_play:
            continue

        fields = config.parse_pipeline_fields(
            os.path.join(project_dir, "tests", "project.conf")
        )

        # Infer capabilities
        sound = fields.get("PIPELINE_SOUND", "").lower() == "true"
        if not sound and os.path.isdir(os.path.join(project_dir, "Sounds")):
            sound = True

        hub_id = fields.get("PIPELINE_HUB_ID", name)
        tests = fields.get("PIPELINE_TESTS", "")

        # Detect capabilities from test data files
        has_walkthrough = os.path.isfile(
            os.path.join(project_dir, "tests", "inform7", "walkthrough.txt")
        )
        has_regtest = bool(
            list(Path(project_dir, "tests").glob("*.regtest"))
            if Path(project_dir, "tests").is_dir() else []
        )

        # Only look up golden seed for engines with CLI tests
        golden_seed = None
        if engine_spec and engine_spec.has_cli_tests:
            golden_seed = config.get_golden_seed(project_dir)

        projects.append(
            ProjectInfo(
                name=name,
                dir=project_dir,
                engine=engine,
                source_file=source_file,
                sound=sound,
                hub_id=hub_id,
                tests=tests,
                has_walkthrough=has_walkthrough,
                has_regtest=has_regtest,
                golden_seed=golden_seed,
            )
        )
    return projects


# ---------------------------------------------------------------------------
# Game selection UI
# ---------------------------------------------------------------------------


def build_game_annotation(p: ProjectInfo) -> str:
    """Build a tag string like '(Ink)' or '(sound, walkthrough+regtest, seed:2)'."""
    tags = []
    # Show engine label for non-Inform 7 projects
    if p.engine != "inform7":
        spec = config.get_engine_spec(p.engine)
        tags.append(spec.label if spec else p.engine)
    if p.sound:
        tags.append("sound")
    # Test types
    test_parts = []
    if p.has_walkthrough:
        test_parts.append("walkthrough")
    if p.has_regtest:
        test_parts.append("regtest")
    if test_parts:
        tags.append("+".join(test_parts))
    if p.golden_seed:
        tags.append(f"seed:{p.golden_seed}")
    return f"  ({', '.join(tags)})" if tags else ""


def prompt_game(
    projects: list[ProjectInfo],
    *,
    needs_walkthrough: bool = False,
    needs_regtest: bool = False,
) -> ProjectInfo:
    """Prompt the user to select a game, filtered by requirements."""
    eligible = projects
    if needs_walkthrough:
        eligible = [p for p in eligible if p.has_walkthrough]
    if needs_regtest:
        eligible = [p for p in eligible if p.has_regtest]

    if not eligible:
        filters = []
        if needs_walkthrough:
            filters.append("walkthrough")
        if needs_regtest:
            filters.append("regtest")
        print(f"No projects match filters: {', '.join(filters)}")
        sys.exit(1)

    choices = []
    for p in eligible:
        annotation = build_game_annotation(p)
        choices.append({"name": f"{p.name}{annotation}", "value": p.name})

    game_name = prompt_or_cancel(
        lambda: inquirer.select(
            message="Select a game:", choices=choices, pointer=">"
        ).execute()
    )
    return next(p for p in projects if p.name == game_name)


# ---------------------------------------------------------------------------
# Command execution engine
# ---------------------------------------------------------------------------


def fmt_cmd(cmd: list[str]) -> str:
    """Format a command list as a readable string for display."""
    return " ".join(cmd)


def preview_commands(commands: list[tuple[list[str], str | None]]):
    """Print a numbered command preview."""
    print()
    print("Commands to run:")
    for i, (cmd, cwd) in enumerate(commands, 1):
        display = fmt_cmd(cmd)
        if cwd:
            print(f"  {i}. (cd {cwd}) {display}")
        else:
            print(f"  {i}. {display}")
    print()


def execute_commands(commands: list[tuple[list[str], str | None]]):
    """Execute commands with error handling and continue/abort prompt."""
    total = len(commands)
    for i, (cmd, cwd) in enumerate(commands, 1):
        if total > 1:
            print(f"\n[{i}/{total}] {fmt_cmd(cmd)}")
        exit_code = run_command(cmd, cwd)

        if exit_code == 130:
            # Ctrl-C — clean exit
            return

        if exit_code != 0:
            remaining = total - i
            print(f"\n[{i}/{total}] FAILED (exit code {exit_code})")
            if remaining > 0:
                cont = prompt_or_cancel(
                    lambda: inquirer.confirm(
                        message=f"{remaining} command(s) remaining. Continue?",
                        default=False,
                    ).execute()
                )
                if not cont:
                    sys.exit(exit_code)
            else:
                sys.exit(exit_code)


def confirm_and_run(commands: list[tuple[list[str], str | None]]):
    """Preview, confirm, and execute commands."""
    if not commands:
        print("Nothing to run.")
        sys.exit(0)

    preview_commands(commands)

    confirm = prompt_or_cancel(
        lambda: inquirer.confirm(message="Execute?", default=True).execute()
    )
    if not confirm:
        print("Cancelled.")
        sys.exit(0)

    execute_commands(commands)
    print("\nDone.")


# ---------------------------------------------------------------------------
# Preset implementations
# ---------------------------------------------------------------------------

# Shared command builders (return list[str] for subprocess)
def pipeline_cmd(game: str, *args: str) -> list[str]:
    return py_cmd(PIPELINE_PY, game, *args)


def publish_cmd(game: str, message: str = "") -> list[str]:
    cmd = py_cmd(PUBLISH_PY, game)
    if message:
        cmd.append(message)
    return cmd


def compile_cmd(game: str, sound: bool = False) -> list[str]:
    cmd = py_cmd(COMPILE_PY, game)
    if sound:
        cmd.append("--sound")
    return cmd


def extract_commands_cmd(source_path: str, output_path: str) -> list[str]:
    return py_cmd(EXTRACT_COMMANDS_PY, "--from-source", source_path, "-o", output_path)


def generate_pages_cmd(title: str, meta: str, description: str, out_dir: str) -> list[str]:
    return py_cmd(
        GENERATE_PAGES_PY,
        "--title", title, "--meta", meta, "--description", description,
        "--out", out_dir,
    )


def register_game_cmd(
    name: str, title: str, meta: str, description: str, sound: str = ""
) -> list[str]:
    cmd = py_cmd(
        REGISTER_GAME_PY,
        "--name", name, "--title", title, "--meta", meta,
        "--description", description,
    )
    if sound:
        cmd.extend(["--sound", sound])
    return cmd


def push_hub_cmd(game: str) -> list[str]:
    return py_cmd(PUSH_HUB_PY, game)


def new_project_cmd(title: str, name: str) -> list[str]:
    return py_cmd(NEW_PROJECT_PY, title, name)


# --- Build ---


def preset_create_project(projects: list[ProjectInfo]):
    """Create a new project (scaffold with new_project.py)."""
    name = prompt_or_cancel(
        lambda: inquirer.text(
            message="Game name (lowercase, hyphens ok):", default=""
        ).execute()
    ).strip()
    if not name:
        print("No name provided.")
        sys.exit(0)
    if not re.match(r"^[a-z0-9]([a-z0-9_-]*[a-z0-9])?$", name):
        print("Name must be lowercase alphanumeric (hyphens/underscores ok).")
        sys.exit(1)

    # Check if it already exists
    project_dir = os.path.join(PROJECTS_DIR, name)
    if os.path.isdir(project_dir):
        print(f"ERROR: Project '{name}' already exists at {project_dir}")
        sys.exit(1)

    title = prompt_or_cancel(
        lambda: inquirer.text(
            message="Title:",
            default=name.replace("-", " ").replace("_", " ").title(),
        ).execute()
    )

    confirm_and_run([(new_project_cmd(title, name), None)])
    print()
    print(f"Next: edit projects/{name}/story.ni, then use 'Publish new game'")



def preset_quick_build(projects: list[ProjectInfo]):
    """Quick build (compile only)."""
    project = prompt_game(projects)
    confirm_and_run([(pipeline_cmd(project.name, "compile", "--force"), None)])


def preset_build_test(projects: list[ProjectInfo]):
    """Build & test."""
    project = prompt_game(projects)
    confirm_and_run(
        [(pipeline_cmd(project.name, "compile", "test", "--force"), None)]
    )


def preset_release(projects: list[ProjectInfo]):
    """Release (compile + test + push)."""
    project = prompt_game(projects)
    confirm_and_run(
        [(pipeline_cmd(project.name, "compile", "test", "push", "--force"), None)]
    )


# --- Test ---


def preset_walkthroughs(projects: list[ProjectInfo]):
    """Run walkthroughs."""
    project = prompt_game(projects, needs_walkthrough=True)

    seed_default = project.golden_seed or ""
    seed_hint = f" (golden seed {project.golden_seed})" if project.golden_seed else ""
    seed = prompt_or_cancel(
        lambda: inquirer.text(
            message=f"Override seed?{seed_hint} (blank = golden seed):",
            default=seed_default,
        ).execute()
    )

    conf_path = os.path.join(project.dir, "tests", "project.conf")
    cmd = py_cmd(os.path.join(TESTING_DIR, "run_walkthrough.py"), "--config", conf_path)
    if seed.strip():
        cmd.extend(["--seed", seed.strip()])

    confirm_and_run([(cmd, None)])


def preset_regtests(projects: list[ProjectInfo]):
    """Run regtests."""
    project = prompt_game(projects, needs_regtest=True)

    pattern = prompt_or_cancel(
        lambda: inquirer.text(
            message="Test pattern (blank = all):", default=""
        ).execute()
    )

    conf_path = os.path.join(project.dir, "tests", "project.conf")
    cmd = py_cmd(os.path.join(TESTING_DIR, "run_tests.py"), "--config", conf_path)
    if pattern.strip():
        cmd.append(pattern.strip())

    confirm_and_run([(cmd, None)])


def preset_find_seeds(projects: list[ProjectInfo]):
    """Find seeds (RNG sweep)."""
    project = prompt_game(projects, needs_walkthrough=True)

    max_seeds = prompt_or_cancel(
        lambda: inquirer.text(
            message="Max seeds:", default="200"
        ).execute()
    )

    stop_first = prompt_or_cancel(
        lambda: inquirer.confirm(
            message="Stop on first passing seed?", default=True
        ).execute()
    )

    conf_path = os.path.join(project.dir, "tests", "project.conf")
    find_seeds_py = os.path.join(TESTING_DIR, "find_seeds.py")
    cmd = py_cmd(find_seeds_py, "--config", conf_path)
    if max_seeds.strip():
        cmd.extend(["--max", max_seeds.strip()])
    cmd.append("--stop" if stop_first else "--no-stop")

    confirm_and_run([(cmd, None)])


# --- Publish & Serve ---


def preset_publish(projects: list[ProjectInfo]):
    """Publish update to GitHub Pages."""
    project = prompt_game(projects)

    message = prompt_or_cancel(
        lambda: inquirer.text(
            message="Commit message (blank = default):", default=""
        ).execute()
    )

    confirm_and_run([(publish_cmd(project.name, message.strip()), None)])


def preset_publish_new(projects: list[ProjectInfo]):
    """Publish new game (extract → compile → pages → register → publish)."""
    project = prompt_game(projects)

    title = prompt_or_cancel(
        lambda: inquirer.text(
            message="Title:",
            default=project.name.replace("-", " ").replace("_", " ").title(),
        ).execute()
    )
    meta = prompt_or_cancel(
        lambda: inquirer.text(
            message="Subtitle:", default="An Interactive Fiction"
        ).execute()
    )
    description = prompt_or_cancel(
        lambda: inquirer.text(
            message="Description:", default="An interactive fiction game."
        ).execute()
    )
    sound = prompt_or_cancel(
        lambda: inquirer.confirm(
            message="Sound enabled (blorb)?", default=project.sound
        ).execute()
    )

    commands: list[tuple[str, str | None]] = []

    # Step 1: Extract walkthrough from Test me (if present in source)
    story_path = os.path.join(project.dir, "story.ni")
    has_test_me = False
    try:
        with open(story_path, "r", encoding="utf-8") as f:
            has_test_me = bool(
                re.search(r"Test\s+\w+\s+with", f.read(), re.IGNORECASE)
            )
    except OSError:
        pass

    if has_test_me:
        walk_dir = os.path.join(project.dir, "tests", "inform7")
        walk_file = os.path.join(walk_dir, "walkthrough.txt")
        os.makedirs(walk_dir, exist_ok=True)
        commands.append((extract_commands_cmd(story_path, walk_file), None))

    # Step 2: Compile (+ web player + auto-walkthrough)
    commands.append((compile_cmd(project.name, sound), None))

    # Step 3: Generate pages (index.html + source.html)
    commands.append(
        (generate_pages_cmd(title, meta, description, project.dir), None)
    )

    # Step 4: Register in hub (games.json + cards.json)
    sound_type = "blorb" if sound else ""
    commands.append(
        (register_game_cmd(project.name, title, meta, description, sound_type), None)
    )

    # Step 5: Publish to GitHub Pages
    commands.append(
        (publish_cmd(project.name, f"Initial publish: {title}"), None)
    )

    # Step 6: Push hub changes (games.json + cards.json)
    commands.append((push_hub_cmd(project.name), None))

    confirm_and_run(commands)


def preset_serve(projects: list[ProjectInfo]):
    """Serve locally."""
    serve_choices = [
        {"name": "IF Hub + all games (dev-server.py)", "value": "dev-server"},
    ]
    # Also offer per-project simple servers
    for p in projects:
        serve_choices.append(
            {"name": f"{p.name} only (projects/{p.name}/)", "value": p.name}
        )

    target = prompt_or_cancel(
        lambda: inquirer.select(
            message="Select target:", choices=serve_choices, pointer=">"
        ).execute()
    )

    port = prompt_or_cancel(
        lambda: inquirer.text(message="Port:", default="8000").execute()
    )

    if target == "dev-server":
        # Use the multi-root dev server
        print(f"\nServing IF Hub + all games at http://127.0.0.1:{port.strip()}/ifhub/app.html")
        print("Press Ctrl-C to stop.\n")
        exit_code = run_command(py_cmd(DEV_SERVER_PY, "--port", port.strip()))
    else:
        # Simple per-project server
        project = next(p for p in projects if p.name == target)
        cmd = py_cmd("-m", "http.server", port.strip(), "--directory", project.dir)
        print(f"\nServing {target} at http://localhost:{port.strip()}/")
        print("Press Ctrl-C to stop.\n")
        exit_code = run_command(cmd)

    if exit_code != 0 and exit_code != 130:
        print(f"\nServer exited with code {exit_code}")


# --- Advanced ---


def preset_full_pipeline(projects: list[ProjectInfo]):
    """Full pipeline."""
    project = prompt_game(projects)

    message = prompt_or_cancel(
        lambda: inquirer.text(
            message="Commit message (blank = default):", default=""
        ).execute()
    )

    cmd = pipeline_cmd(project.name, "--all", "--force")
    if message.strip():
        cmd.extend(["--message", message.strip()])

    confirm_and_run([(cmd, None)])


def preset_custom(projects: list[ProjectInfo]):
    """Custom (pick stages)."""
    project = prompt_game(projects)

    all_stages = ["compile", "test", "push"]
    stages = prompt_or_cancel(
        lambda: inquirer.checkbox(
            message="Select stages:",
            choices=all_stages,
            pointer=">",
        ).execute()
    )
    if not stages:
        print("No stages selected.")
        sys.exit(0)

    message = ""
    if "push" in stages:
        message = prompt_or_cancel(
            lambda: inquirer.text(
                message="Commit message (blank = default):", default=""
            ).execute()
        )

    cmd = pipeline_cmd(project.name, *stages, "--force")
    if message.strip():
        cmd.extend(["--message", message.strip()])

    confirm_and_run([(cmd, None)])


# ---------------------------------------------------------------------------
# Preset registry
# ---------------------------------------------------------------------------

PRESETS = [
    Separator("--- Build ---"),
    {
        "name": "Create new project",
        "value": preset_create_project,
    },
    {
        "name": "Quick build (compile only)",
        "value": preset_quick_build,
    },
    {
        "name": "Build & test",
        "value": preset_build_test,
    },
    {
        "name": "Release (compile + test + push)",
        "value": preset_release,
    },
    Separator("--- Test ---"),
    {
        "name": "Run walkthroughs",
        "value": preset_walkthroughs,
    },
    {
        "name": "Run regtests",
        "value": preset_regtests,
    },
    {
        "name": "Find seeds (RNG sweep)",
        "value": preset_find_seeds,
    },
    Separator("--- Publish & Serve ---"),
    {
        "name": "Publish new game (full flow)",
        "value": preset_publish_new,
    },
    {
        "name": "Publish update",
        "value": preset_publish,
    },
    {
        "name": "Serve locally",
        "value": preset_serve,
    },
    Separator("--- Advanced ---"),
    {
        "name": "Full pipeline",
        "value": preset_full_pipeline,
    },
    {
        "name": "Custom (pick stages)",
        "value": preset_custom,
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print()
    print("=== IF Hub Pipeline Runner ===")
    print()

    projects = load_projects()
    if not projects:
        print("No projects found in", PROJECTS_DIR)
        sys.exit(1)

    # --- Task selection ---
    preset_fn = prompt_or_cancel(
        lambda: inquirer.select(
            message="Select a task:", choices=PRESETS, pointer=">"
        ).execute()
    )

    # Execute the selected preset
    preset_fn(projects)


if __name__ == "__main__":
    main()
