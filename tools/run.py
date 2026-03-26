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
# Shared library imports
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from lib import config  # noqa: E402
from lib import paths  # noqa: E402
from lib.projects import ProjectInfo, ArtifactStatus, load_projects  # noqa: E402

# ---------------------------------------------------------------------------
# Path constants (from lib.paths + script-relative tools)
# ---------------------------------------------------------------------------

PROJECTS_DIR = str(paths.PROJECTS_DIR)
PIPELINE_PY = str(paths.TOOLS_DIR / "pipeline.py")
PUBLISH_PY = str(paths.TOOLS_DIR / "publish.py")
DEV_SERVER_PY = str(paths.TOOLS_DIR / "dev-server.py")
COMPILE_PY = str(paths.TOOLS_DIR / "compile.py")
EXTRACT_COMMANDS_PY = str(paths.TOOLS_DIR / "extract_commands.py")
GENERATE_PAGES_PY = str(paths.WEB_DIR / "generate_pages.py")
REGISTER_GAME_PY = str(paths.TOOLS_DIR / "register_game.py")
PUSH_HUB_PY = str(paths.TOOLS_DIR / "push_hub.py")
NEW_PROJECT_PY = str(paths.TOOLS_DIR / "new_project.py")
I7_TESTING_DIR = str(paths.engine_tools_dir("inform7"))

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


# ProjectInfo and load_projects are imported from lib.projects above.


# ---------------------------------------------------------------------------
# Game selection UI
# ---------------------------------------------------------------------------


def build_game_annotation(p: ProjectInfo) -> str:
    """Build a tag string showing engine + artifact status indicators."""
    parts = []

    # Engine label
    spec = config.get_engine_spec(p.engine)
    engine_label = spec.label if spec else p.engine
    if p.engine != "inform7":
        parts.append(engine_label)

    # Artifact status indicators: C=compile T=test P=publish R=register
    status_chars = {
        ArtifactStatus.PRESENT: "+",
        ArtifactStatus.MISSING: ".",
        ArtifactStatus.STALE: "~",
        ArtifactStatus.FAILED: "!",
        ArtifactStatus.NA: "-",
    }
    if p.artifacts:
        indicators = []
        for key in ("compile", "published", "registered"):
            art = p.artifacts.get(key)
            if art:
                indicators.append(status_chars.get(art.status, "?"))
        parts.append("".join(indicators))

    if p.sound:
        parts.append("sound")

    return f"  ({', '.join(parts)})" if parts else ""


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
    cmd = py_cmd(os.path.join(I7_TESTING_DIR, "run_walkthrough.py"), "--config", conf_path)
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
    cmd = py_cmd(os.path.join(I7_TESTING_DIR, "run_tests.py"), "--config", conf_path)
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
    find_seeds_py = os.path.join(I7_TESTING_DIR, "find_seeds.py")
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
