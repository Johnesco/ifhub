#!/usr/bin/env python3
"""Interactive Pipeline Runner for IF Hub.

Presents arrow-key menus to select pipeline tasks and games,
then delegates to existing bash scripts via subprocess.

Usage:
    python tools/run.py

Requires: pip install InquirerPy
"""

import glob
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field

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
IFHUB_DIR = os.path.join(I7_ROOT, "ifhub")
PIPELINE_SH = os.path.join(SCRIPT_DIR, "pipeline.sh")
SNAPSHOT_SH = os.path.join(SCRIPT_DIR, "snapshot.sh")
PUBLISH_SH = os.path.join(SCRIPT_DIR, "publish.sh")
DEV_SERVER_PY = os.path.join(SCRIPT_DIR, "dev-server.py")
TESTING_DIR = os.path.join(SCRIPT_DIR, "testing")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def to_posix(path: str) -> str:
    """Convert a Windows path to MSYS2/Git Bash posix form.

    C:\\code\\ifhub -> /c/code/ifhub
    """
    path = path.replace("\\", "/")
    # Convert drive letter  C:/... -> /c/...
    m = re.match(r"^([A-Za-z]):/", path)
    if m:
        path = "/" + m.group(1).lower() + "/" + path[3:]
    return path


def find_bash() -> str:
    """Return the path to a usable bash executable."""
    # Prefer Git Bash on Windows
    git_bash = r"C:\Program Files\Git\bin\bash.exe"
    if os.path.isfile(git_bash):
        return git_bash
    found = shutil.which("bash")
    if found:
        return found
    print("ERROR: Cannot find bash. Install Git for Windows or add bash to PATH.")
    sys.exit(1)


def run_command(cmd: str, cwd: str | None = None) -> int:
    """Run a bash command with live terminal output. Returns exit code."""
    bash = find_bash()
    posix_cwd = to_posix(cwd) if cwd else None

    # Build the full command — cd first if cwd is specified
    if posix_cwd:
        full_cmd = f'cd "{posix_cwd}" && {cmd}'
    else:
        full_cmd = cmd

    try:
        result = subprocess.run([bash, "-c", full_cmd], cwd=cwd)
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        return 130


def run_python(cmd: str) -> int:
    """Run a Python command with live terminal output. Returns exit code."""
    try:
        result = subprocess.run([sys.executable] + cmd.split())
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        return 130


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
    sound: bool = False
    versioned: bool = False
    current_version: str = ""
    hub_id: str = ""
    tests: str = ""
    has_walkthrough: bool = False
    has_regtest: bool = False
    golden_seed: str | None = None
    versions: list[str] = field(default_factory=list)
    compilable_versions: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Project discovery
# ---------------------------------------------------------------------------


def parse_pipeline_fields(conf_path: str) -> dict:
    """Extract PIPELINE_* fields from a project.conf file."""
    fields = {}
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


def get_golden_seed(project_dir: str) -> str | None:
    """Read the first glulxe seed from tests/seeds.conf."""
    seeds_path = os.path.join(project_dir, "tests", "seeds.conf")
    try:
        with open(seeds_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("glulxe:"):
                    parts = line.split(":")
                    if len(parts) >= 2:
                        return parts[1]
    except OSError:
        pass
    return None


def get_versions(project_dir: str) -> list[str]:
    """Return sorted list of version names (e.g., ['v0', 'v1', 'v2']).

    Versions are flat directories at the project root (v0/, v1/, etc.),
    not inside a versions/ subdirectory.
    """
    versions = []
    for name in os.listdir(project_dir):
        if re.match(r"^v\d+$", name) and os.path.isdir(
            os.path.join(project_dir, name)
        ):
            versions.append(name)
    return sorted(versions, key=lambda v: int(re.search(r"\d+", v).group()))


def get_compilable_versions(project_dir: str, versions: list[str]) -> list[str]:
    """Filter to versions that have a story.ni (excludes ZIL-only like v0)."""
    return [
        v
        for v in versions
        if os.path.isfile(os.path.join(project_dir, v, "story.ni"))
    ]


def detect_version_binary_type(project_dir: str, game_name: str, version: str) -> str:
    """Detect binary type (.gblorb or .ulx) for a version snapshot."""
    parchment_dir = os.path.join(project_dir, version, "lib", "parchment")
    # Check for gblorb first (sound-enabled)
    gblorb_pattern = os.path.join(parchment_dir, "*.gblorb.js")
    if glob.glob(gblorb_pattern):
        return ".gblorb"
    ulx_pattern = os.path.join(parchment_dir, "*.ulx.js")
    if glob.glob(ulx_pattern):
        return ".ulx"
    return ".ulx"  # default


def load_projects() -> list[ProjectInfo]:
    """Scan projects/ and return a list of ProjectInfo objects."""
    projects = []
    for name in sorted(os.listdir(PROJECTS_DIR)):
        project_dir = os.path.join(PROJECTS_DIR, name)
        if not os.path.isdir(project_dir):
            continue
        if not os.path.isfile(os.path.join(project_dir, "story.ni")):
            continue

        conf_path = os.path.join(project_dir, "tests", "project.conf")
        fields = parse_pipeline_fields(conf_path)

        # Infer capabilities
        sound = fields.get("PIPELINE_SOUND", "").lower() == "true"
        if not sound and os.path.isdir(os.path.join(project_dir, "Sounds")):
            sound = True

        versioned = fields.get("PIPELINE_VERSIONED", "").lower() == "true"
        if not versioned:
            # Check flat layout: v0/, v1/, etc. at project root
            for entry in os.listdir(project_dir):
                if re.match(r"^v\d+$", entry) and os.path.isdir(
                    os.path.join(project_dir, entry)
                ):
                    versioned = True
                    break

        current_version = fields.get("PIPELINE_CURRENT_VERSION", "")
        hub_id = fields.get("PIPELINE_HUB_ID", name)
        tests = fields.get("PIPELINE_TESTS", "")

        has_walkthrough = os.path.isfile(
            os.path.join(project_dir, "tests", "run-walkthrough.sh")
        )
        has_regtest = os.path.isfile(
            os.path.join(project_dir, "tests", "run-tests.sh")
        )

        versions = get_versions(project_dir) if versioned else []
        compilable = get_compilable_versions(project_dir, versions) if versioned else []

        projects.append(
            ProjectInfo(
                name=name,
                dir=project_dir,
                sound=sound,
                versioned=versioned,
                current_version=current_version,
                hub_id=hub_id,
                tests=tests,
                has_walkthrough=has_walkthrough,
                has_regtest=has_regtest,
                golden_seed=get_golden_seed(project_dir),
                versions=versions,
                compilable_versions=compilable,
            )
        )
    return projects


# ---------------------------------------------------------------------------
# Game selection UI
# ---------------------------------------------------------------------------


def build_game_annotation(p: ProjectInfo) -> str:
    """Build a tag string like '(sound, versioned v4, walkthrough+regtest, seed:2)'."""
    tags = []
    if p.sound:
        tags.append("sound")
    if p.versioned:
        ver = f"versioned {p.current_version}" if p.current_version else "versioned"
        tags.append(ver)
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
    needs_versioned: bool = False,
) -> ProjectInfo:
    """Prompt the user to select a game, filtered by requirements."""
    eligible = projects
    if needs_walkthrough:
        eligible = [p for p in eligible if p.has_walkthrough]
    if needs_regtest:
        eligible = [p for p in eligible if p.has_regtest]
    if needs_versioned:
        eligible = [p for p in eligible if p.versioned and p.compilable_versions]

    if not eligible:
        filters = []
        if needs_walkthrough:
            filters.append("walkthrough")
        if needs_regtest:
            filters.append("regtest")
        if needs_versioned:
            filters.append("versioned")
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
# Version picker UI
# ---------------------------------------------------------------------------


def prompt_versions_checkbox(project: ProjectInfo) -> list[str]:
    """Prompt with checkbox to select compilable versions."""
    choices = []
    for v in project.compilable_versions:
        binary_type = detect_version_binary_type(project.dir, project.name, v)
        label = f"{v}  ({binary_type})"
        if v == project.current_version:
            label += " [current]"
        choices.append({"name": label, "value": v, "enabled": v == project.current_version})

    selected = prompt_or_cancel(
        lambda: inquirer.checkbox(
            message="Select versions to recompile:",
            choices=choices,
            pointer=">",
        ).execute()
    )
    if not selected:
        print("No versions selected.")
        sys.exit(0)
    return selected


def prompt_version_text(project: ProjectInfo) -> str:
    """Prompt for a single version string (text input with default)."""
    default = project.current_version or ""
    return prompt_or_cancel(
        lambda: inquirer.text(
            message="Version:", default=default
        ).execute()
    )


# ---------------------------------------------------------------------------
# Command execution engine
# ---------------------------------------------------------------------------


def preview_commands(commands: list[tuple[str, str | None]]):
    """Print a numbered command preview."""
    print()
    print("Commands to run:")
    for i, (cmd, cwd) in enumerate(commands, 1):
        if cwd:
            print(f"  {i}. (cd {to_posix(cwd)}) {cmd}")
        else:
            print(f"  {i}. {cmd}")
    print()


def execute_commands(commands: list[tuple[str, str | None]]):
    """Execute commands with error handling and continue/abort prompt."""
    total = len(commands)
    for i, (cmd, cwd) in enumerate(commands, 1):
        if total > 1:
            print(f"\n[{i}/{total}] {cmd}")
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


def confirm_and_run(commands: list[tuple[str, str | None]]):
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

# Shared path helpers
def pipeline_cmd(game: str, *args: str) -> str:
    return f'bash "{to_posix(PIPELINE_SH)}" {game} {" ".join(args)}'


def snapshot_cmd(game: str, version: str) -> str:
    return f'bash "{to_posix(SNAPSHOT_SH)}" {game} {version} --update'


def publish_cmd(game: str, message: str = "") -> str:
    cmd = f'bash "{to_posix(PUBLISH_SH)}" {game}'
    if message:
        cmd += f' "{message}"'
    return cmd


# --- Build ---


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
    """Release version (compile + test + snapshot + push)."""
    project = prompt_game(projects)

    if project.versioned:
        version = prompt_version_text(project)
        confirm_and_run(
            [
                (
                    pipeline_cmd(
                        project.name, "--ship", "--version", version, "--force"
                    ),
                    None,
                )
            ]
        )
    else:
        confirm_and_run(
            [
                (
                    pipeline_cmd(
                        project.name, "compile", "test", "push", "--force"
                    ),
                    None,
                )
            ]
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

    wt_script = to_posix(os.path.join(project.dir, "tests", "run-walkthrough.sh"))
    cmd = f'bash "{wt_script}"'
    if seed.strip():
        cmd += f" --seed {seed.strip()}"

    confirm_and_run([(cmd, None)])


def preset_regtests(projects: list[ProjectInfo]):
    """Run regtests."""
    project = prompt_game(projects, needs_regtest=True)

    pattern = prompt_or_cancel(
        lambda: inquirer.text(
            message="Test pattern (blank = all):", default=""
        ).execute()
    )

    rt_script = to_posix(os.path.join(project.dir, "tests", "run-tests.sh"))
    cmd = f'bash "{rt_script}"'
    if pattern.strip():
        cmd += f" {pattern.strip()}"

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

    conf_path = to_posix(os.path.join(project.dir, "tests", "project.conf"))
    find_seeds = to_posix(os.path.join(TESTING_DIR, "find-seeds.sh"))
    cmd = f'bash "{find_seeds}" --config "{conf_path}"'
    if max_seeds.strip():
        cmd += f" --max {max_seeds.strip()}"
    cmd += " --stop" if stop_first else " --no-stop"

    confirm_and_run([(cmd, None)])


# --- Publish & Serve ---


def preset_recompile_versions(projects: list[ProjectInfo]):
    """Recompile frozen versions."""
    project = prompt_game(projects, needs_versioned=True)
    selected = prompt_versions_checkbox(project)

    commands: list[tuple[str, str | None]] = []
    for v in selected:
        commands.append((snapshot_cmd(project.name, v), None))

    confirm_and_run(commands)


def preset_publish(projects: list[ProjectInfo]):
    """Publish game to GitHub Pages."""
    project = prompt_game(projects)

    message = prompt_or_cancel(
        lambda: inquirer.text(
            message="Commit message (blank = default):", default=""
        ).execute()
    )

    confirm_and_run([(publish_cmd(project.name, message.strip()), None)])


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
        exit_code = run_python(f"{DEV_SERVER_PY} --port {port.strip()}")
    else:
        # Simple per-project server
        project = next(p for p in projects if p.name == target)
        posix_dir = to_posix(project.dir)
        cmd = f'python -m http.server {port.strip()} --directory "{posix_dir}"'
        print(f"\nServing {target} at http://localhost:{port.strip()}/")
        print("Press Ctrl-C to stop.\n")
        exit_code = run_command(cmd)

    if exit_code != 0 and exit_code != 130:
        print(f"\nServer exited with code {exit_code}")


# --- Advanced ---


def preset_full_pipeline(projects: list[ProjectInfo]):
    """Full pipeline."""
    project = prompt_game(projects)

    version = ""
    if project.versioned:
        version = prompt_version_text(project)

    message = prompt_or_cancel(
        lambda: inquirer.text(
            message="Commit message (blank = default):", default=""
        ).execute()
    )

    if project.versioned and version:
        cmd = pipeline_cmd(
            project.name, "--ship", "--version", version, "--force"
        )
    else:
        cmd = pipeline_cmd(project.name, "--all", "--force")

    if message.strip():
        cmd += f' --message "{message.strip()}"'

    confirm_and_run([(cmd, None)])


def preset_custom(projects: list[ProjectInfo]):
    """Custom (pick stages)."""
    project = prompt_game(projects)

    all_stages = ["compile", "test", "snapshot", "push"]
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

    version = ""
    if "snapshot" in stages and project.versioned:
        version = prompt_version_text(project)

    message = ""
    if "push" in stages:
        message = prompt_or_cancel(
            lambda: inquirer.text(
                message="Commit message (blank = default):", default=""
            ).execute()
        )

    stage_str = " ".join(stages)
    cmd = pipeline_cmd(project.name, stage_str, "--force")
    if version:
        cmd += f" --version {version}"
    if message.strip():
        cmd += f' --message "{message.strip()}"'

    confirm_and_run([(cmd, None)])


# ---------------------------------------------------------------------------
# Preset registry
# ---------------------------------------------------------------------------

PRESETS = [
    Separator("--- Build ---"),
    {
        "name": "Quick build (compile only)",
        "value": preset_quick_build,
    },
    {
        "name": "Build & test",
        "value": preset_build_test,
    },
    {
        "name": "Release version",
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
        "name": "Recompile frozen versions",
        "value": preset_recompile_versions,
    },
    {
        "name": "Publish to GitHub Pages",
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
