#!/usr/bin/env python3
"""IF Hub Dashboard -- Local web GUI for the build pipeline.

Usage:
    pip install flask
    python tools/dashboard.py [--port 5000]

Opens a browser-based dashboard for managing IF Hub game projects.
Matches the IF Hub dark-gold theme.
"""

import glob as _glob_mod
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from dataclasses import dataclass, field

try:
    from flask import Flask, Response, jsonify, request
except ImportError:
    print("Missing dependency: Flask")
    print()
    print("  pip install flask")
    print()
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
I7_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECTS_DIR = os.path.join(I7_ROOT, "projects")
COMPILE_PY = os.path.join(SCRIPT_DIR, "compile.py")
EXTRACT_COMMANDS_PY = os.path.join(SCRIPT_DIR, "extract_commands.py")
GENERATE_PAGES_PY = os.path.join(SCRIPT_DIR, "web", "generate_pages.py")
REGISTER_GAME_PY = os.path.join(SCRIPT_DIR, "register_game.py")
UNREGISTER_GAME_PY = os.path.join(SCRIPT_DIR, "unregister_game.py")
PUBLISH_PY = os.path.join(SCRIPT_DIR, "publish.py")
PIPELINE_PY = os.path.join(SCRIPT_DIR, "pipeline.py")
NEW_PROJECT_PY = os.path.join(SCRIPT_DIR, "new_project.py")
PUSH_HUB_PY = os.path.join(SCRIPT_DIR, "push_hub.py")
SETUP_BASIC_PY = os.path.join(SCRIPT_DIR, "web", "setup_basic.py")
SETUP_INK_PY = os.path.join(SCRIPT_DIR, "web", "setup_ink.py")
SETUP_SHARPEE_PY = os.path.join(SCRIPT_DIR, "web", "setup_sharpee.py")
TESTING_DIR = os.path.join(SCRIPT_DIR, "testing")

sys.path.insert(0, SCRIPT_DIR)
from lib import config as _libconfig  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def py_cmd(*args):
    """Build a Python subprocess command list."""
    return [sys.executable, *args]


# ---------------------------------------------------------------------------
# Project Discovery
# ---------------------------------------------------------------------------


@dataclass
class ProjectInfo:
    name: str
    dir: str
    engine: str = "unknown"        # inform7, wwwbasic, qbjc, applesoft, jsdos, twine, unknown
    source_file: str = ""          # primary source filename (story.ni, game.bas, etc.)
    sound: bool = False
    hub_id: str = ""
    has_source: bool = False
    has_walkthrough: bool = False
    has_regtest: bool = False
    has_test_me: bool = False
    has_play_html: bool = False
    has_binary: bool = False       # .ulx, .gblorb, .js compiled output, etc.
    has_index: bool = False
    has_source_html: bool = False
    has_git: bool = False
    registered: bool = False
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


def load_registered_ids():
    """Return set of game IDs currently in games.json."""
    games_path = os.path.join(I7_ROOT, "ifhub", "games.json")
    try:
        with open(games_path, "r", encoding="utf-8") as f:
            return {g["id"] for g in json.load(f)}
    except (OSError, json.JSONDecodeError):
        return set()


def load_projects():
    registered_ids = load_registered_ids()
    projects = []
    for name in sorted(os.listdir(PROJECTS_DIR)):
        project_dir = os.path.join(PROJECTS_DIR, name)
        if not os.path.isdir(project_dir):
            continue

        # Parse config fields via shared library
        fields = _libconfig.parse_conf_fields(project_dir)

        engine = _libconfig.detect_engine(project_dir, fields)
        source_file = _libconfig.detect_source_file(project_dir, engine, fields)
        source_path = os.path.join(project_dir, source_file) if source_file else ""
        has_source = bool(source_file) and os.path.isfile(source_path)
        has_play = os.path.isfile(os.path.join(project_dir, "play.html"))

        sound = fields.get("PIPELINE_SOUND", "").lower() == "true"
        if not sound and os.path.isdir(os.path.join(project_dir, "Sounds")):
            sound = True

        has_walkthrough = os.path.isfile(
            os.path.join(project_dir, "tests", "inform7", "walkthrough.txt")
        )
        has_regtest = bool(_glob_mod.glob(
            os.path.join(project_dir, "tests", "*.regtest")
        ))

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

        # Detect compiled binaries (engine-appropriate)
        dir_files = os.listdir(project_dir)
        if engine == "inform7":
            has_binary = any(
                f.endswith((".ulx", ".gblorb"))
                for f in dir_files
                if os.path.isfile(os.path.join(project_dir, f))
            )
        else:
            # For non-I7: play.html IS the compiled output, or look for .js bundles
            has_binary = has_play

        has_index = os.path.isfile(os.path.join(project_dir, "index.html"))
        has_source_html = os.path.isfile(os.path.join(project_dir, "source.html"))
        has_git = os.path.isdir(os.path.join(project_dir, ".git"))
        is_registered = (name in registered_ids
                         or fields.get("PIPELINE_HUB_ID", "") in registered_ids
                         or any(rid.startswith(name) for rid in registered_ids))

        # --- Pipeline state enrichment ---
        state_file = os.path.join(project_dir, ".pipeline-state")
        pipeline_state = {}
        try:
            if os.path.isfile(state_file):
                with open(state_file, "r", encoding="utf-8") as f:
                    pipeline_state = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

        # Source mtime
        source_mt = 0.0
        if has_source and source_path:
            try:
                source_mt = os.path.getmtime(source_path)
            except OSError:
                pass

        # Find binary file for details
        binary_name_str = ""
        binary_sz = 0
        binary_mt = 0.0
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
        compile_stale = True
        if has_source and source_path:
            try:
                cur_hash = hashlib.md5(open(source_path, "rb").read()).hexdigest()
                saved = pipeline_state.get("STAGE_COMPILE_SOURCE_HASH", "")
                if saved and saved == cur_hash:
                    compile_stale = False
            except OSError:
                pass

        test_stale = True
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
        engine_spec = _libconfig.get_engine_spec(engine)
        has_cli_tests = engine_spec.has_cli_tests if engine_spec else False
        is_buildable = engine in ("inform7", "wwwbasic", "qbjc", "applesoft",
                                  "bwbasic", "basic", "ink", "jsdos")

        stage_status = {}

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
                hub_id=fields.get("PIPELINE_HUB_ID", name),
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


# ---------------------------------------------------------------------------
# Command Builders
# ---------------------------------------------------------------------------


def compile_cmd(game, sound=False, force=False):
    cmd = py_cmd(COMPILE_PY, game)
    if sound:
        cmd.append("--sound")
    if force:
        cmd.append("--force")
    return cmd


def extract_commands_cmd(source_path, output_path):
    return py_cmd(EXTRACT_COMMANDS_PY, "--from-source", source_path, "-o", output_path)


def generate_pages_cmd(title, meta, description, out_dir, force=False, source_file=""):
    cmd = py_cmd(GENERATE_PAGES_PY,
                 "--title", title, "--meta", meta,
                 "--description", description, "--out", out_dir)
    if source_file:
        cmd.extend(["--source-file", source_file])
    if force:
        cmd.append("--force")
    return cmd


def register_game_cmd(name, title, meta, description, sound="", engine="", tags=""):
    cmd = py_cmd(REGISTER_GAME_PY,
                 "--name", name, "--title", title,
                 "--meta", meta, "--description", description)
    if sound:
        cmd.extend(["--sound", sound])
    if engine:
        cmd.extend(["--engine", engine])
    if tags:
        cmd.extend(["--tags", tags])
    return cmd


def publish_cmd(game, message=""):
    cmd = py_cmd(PUBLISH_PY, game)
    if message:
        cmd.append(message)
    return cmd


def pipeline_cmd(game, *stages):
    return py_cmd(PIPELINE_PY, game, *stages)


def new_project_cmd(title, name, engine="inform7"):
    cmd = py_cmd(NEW_PROJECT_PY, title, name)
    if engine != "inform7":
        cmd.extend(["--engine", engine])
    return cmd


def unregister_game_cmd(name):
    return py_cmd(UNREGISTER_GAME_PY, name)


def push_hub_cmd(game):
    return py_cmd(PUSH_HUB_PY, game)


# ---------------------------------------------------------------------------
# Job Management
# ---------------------------------------------------------------------------


@dataclass
class Job:
    id: str
    commands: list
    status: str = "running"  # running | done | error
    exit_code: int = 0
    log: list = field(default_factory=list)
    process: subprocess.Popen = None


jobs: dict[str, Job] = {}


def fmt_cmd(cmd):
    """Format a command list as a readable string for display."""
    if isinstance(cmd, list):
        return " ".join(cmd)
    return cmd


def run_job(job_id, commands):
    """Run commands sequentially, appending output to job.log."""
    job = jobs[job_id]

    for i, cmd in enumerate(commands):
        if len(commands) > 1:
            header = f"\n--- [{i + 1}/{len(commands)}] {fmt_cmd(cmd)} ---\n"
            job.log.append(header)

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            job.process = proc

            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                job.log.append(line)

            proc.wait()

            if proc.returncode != 0:
                job.log.append(f"\n[FAILED] Exit code {proc.returncode}\n")
                job.status = "error"
                job.exit_code = proc.returncode
                break

        except Exception as e:
            job.log.append(f"\n[ERROR] {e}\n")
            job.status = "error"
            job.exit_code = 1
            break
    else:
        job.status = "done"

    if job.status == "running":
        job.status = "done"


PIPELINE_STEPS = ["build", "test", "package", "register", "publish"]


def _basic_compile_cmd(project, force=False):
    """Build a setup_basic.py command for a BASIC engine project."""
    engine = project.engine
    if engine == "basic":
        engine = "wwwbasic"  # default BASIC engine
    title = project.name.replace("-", " ").replace("_", " ").title()
    cmd = py_cmd(SETUP_BASIC_PY, "--engine", engine, "--title", title,
                 "--out", project.dir)
    if project.source_file:
        source_path = os.path.join(project.dir, project.source_file)
        if os.path.isfile(source_path):
            if engine == "jsdos":
                cmd.extend(["--bundle", source_path])
            else:
                cmd.extend(["--source", source_path])
    if force:
        cmd.append("--force")
    return cmd


def _step_commands(step, project, data):
    """Return commands for a single pipeline step, or [] if not applicable."""
    game = project.name
    engine = project.engine
    is_i7 = engine == "inform7"
    engine_spec = _libconfig.get_engine_spec(engine)
    is_basic = engine_spec.is_basic if engine_spec else False
    force = data.get("force", False)
    title = data.get("title", game.replace("-", " ").replace("_", " ").title())
    meta = data.get("meta", "An Interactive Fiction")
    desc = data.get("description", "An interactive fiction game.")

    is_ink = engine == "ink"

    if step == "build":
        if is_i7:
            cmds = []
            # Auto-extract walkthrough from Test me blocks if none exists yet
            if project.has_test_me and not project.has_walkthrough:
                walk_dir = os.path.join(project.dir, "tests", "inform7")
                walk_file = os.path.join(walk_dir, "walkthrough.txt")
                os.makedirs(walk_dir, exist_ok=True)
                cmds.append(extract_commands_cmd(
                    os.path.join(project.dir, "story.ni"), walk_file
                ))
            cmds.append(compile_cmd(game, data.get("sound", project.sound), force=force))
            return cmds
        if is_basic or engine == "jsdos":
            return [_basic_compile_cmd(project, force=force)]
        if is_ink:
            cmd = py_cmd(SETUP_INK_PY, "--title", title, "--out", project.dir)
            if project.source_file:
                cmd.extend(["--ink", os.path.join(project.dir, project.source_file)])
            if force:
                cmd.append("--force")
            return [cmd]
        if engine == "sharpee":
            cmd = py_cmd(SETUP_SHARPEE_PY, "--title", title, "--out", project.dir)
            if force:
                cmd.append("--force")
            return [cmd]
        return []

    if step == "test":
        if not (engine_spec and engine_spec.has_cli_tests):
            return []
        cmds = []
        conf = os.path.join(project.dir, "tests", "project.conf")
        if project.has_walkthrough:
            cmds.append(py_cmd(os.path.join(TESTING_DIR, "run_walkthrough.py"), "--config", conf))
        if project.has_regtest:
            cmds.append(py_cmd(os.path.join(TESTING_DIR, "run_tests.py"), "--config", conf))
        return cmds

    if step == "package":
        return [generate_pages_cmd(title, meta, desc, project.dir, force=force,
                                   source_file=project.source_file)]

    if step == "register":
        sound_type = "blorb" if data.get("sound", project.sound) else ""
        return [register_game_cmd(game, title, meta, desc, sound_type, engine=engine), push_hub_cmd(game)]

    if step == "publish":
        message = data.get("message", "")
        if not message:
            message = f"Publish {game}"
        return [publish_cmd(game, message)]

    return []


def build_commands(task, project, data):
    """Build command list for a task. Returns list or error string."""
    # Individual pipeline steps
    if task in PIPELINE_STEPS:
        cmds = _step_commands(task, project, data)
        if not cmds:
            return f"Step '{task}' not applicable for engine: {project.engine}"
        return cmds

    # Chain: run from a step through to the end
    if task == "run-from":
        from_step = data.get("from", "build")
        try:
            idx = PIPELINE_STEPS.index(from_step)
        except ValueError:
            return f"Unknown step: {from_step}"
        cmds = []
        for step in PIPELINE_STEPS[idx:]:
            cmds.extend(_step_commands(step, project, data))
        return cmds if cmds else f"No applicable steps from '{from_step}'"

    # Special tasks (not pipeline steps)
    if task == "publish-update":
        message = data.get("message", "")
        return [publish_cmd(project.name, message)]

    if task == "unregister":
        return [unregister_game_cmd(project.name), push_hub_cmd(project.name)]

    return f"Unknown task: {task}"


# ---------------------------------------------------------------------------
# Flask App
# ---------------------------------------------------------------------------

app = Flask(__name__)


@app.route("/")
def index():
    return HTML_PAGE


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/api/projects")
def api_projects():
    projects = load_projects()
    return jsonify(
        [
            {
                "name": p.name,
                "engine": p.engine,
                "sourceFile": p.source_file,
                "sound": p.sound,
                "hubId": p.hub_id,
                "hasSource": p.has_source,
                "hasWalkthrough": p.has_walkthrough,
                "hasRegtest": p.has_regtest,
                "hasTestMe": p.has_test_me,
                "hasPlayHtml": p.has_play_html,
                "hasBinary": p.has_binary,
                "hasIndex": p.has_index,
                "hasSourceHtml": p.has_source_html,
                "hasGit": p.has_git,
                "registered": p.registered,
                "binaryName": p.binary_name,
                "binarySize": p.binary_size,
                "binaryMtime": p.binary_mtime,
                "sourceMtime": p.source_mtime,
                "compileStale": p.compile_stale,
                "testStale": p.test_stale,
                "failedStage": p.failed_stage,
                "stageStatus": p.stage_status,
            }
            for p in projects
        ]
    )


@app.route("/api/create", methods=["POST"])
def api_create():
    """Create a new project by calling new_project.py, optionally with custom source."""
    data = request.json
    name = data.get("name", "").strip()
    source = data.get("source", "").strip()
    engine = data.get("engine", "inform7").strip()

    if not name:
        return jsonify({"error": "Game name is required"}), 400
    if not re.match(r"^[a-z0-9]([a-z0-9_-]*[a-z0-9])?$", name):
        return jsonify(
            {"error": "Name must be lowercase alphanumeric (hyphens/underscores ok)"}
        ), 400

    project_dir = os.path.join(PROJECTS_DIR, name)

    if os.path.isdir(project_dir):
        return jsonify({"error": f"Project '{name}' already exists"}), 409

    # Extract title from source (or use the game name as fallback)
    title = name.replace("-", " ").replace("_", " ").title()
    if source and engine == "inform7":
        first_line = source.split("\n")[0].strip()
        if not first_line.startswith('"'):
            return jsonify(
                {"error": 'Source must start with "Title" by "Author"'}
            ), 400
        m = re.match(r'^"([^"]+)"', first_line)
        if m:
            title = m.group(1)

    # Scaffold project via new_project.py (creates tests, config, etc.)
    result = subprocess.run(
        new_project_cmd(title, name, engine),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return jsonify({"error": f"new_project.py failed: {result.stderr}"}), 500

    # If custom source was provided, overwrite the starter source file
    if source:
        # Determine the source file name for this engine
        spec = _libconfig.get_engine_spec(engine)
        if engine == "inform7":
            source_file = "story.ni"
        elif spec:
            source_file = name.replace("-", "_") + spec.source_extensions[0]
        else:
            source_file = "story.ni"
        source_path = os.path.join(project_dir, source_file)
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(source if source.endswith("\n") else source + "\n")

    return jsonify({"name": name, "dir": project_dir})


@app.route("/api/run", methods=["POST"])
def api_run():
    data = request.json
    task = data.get("task")
    game = data.get("game")

    projects = load_projects()
    project = next((p for p in projects if p.name == game), None)
    if not project:
        return jsonify({"error": f"Project not found: {game}"}), 404

    commands = build_commands(task, project, data)
    if isinstance(commands, str):
        return jsonify({"error": commands}), 400

    job_id = str(uuid.uuid4())[:8]
    job = Job(id=job_id, commands=commands)
    jobs[job_id] = job

    thread = threading.Thread(
        target=run_job, args=(job_id, commands), daemon=True
    )
    thread.start()

    return jsonify({"jobId": job_id, "commands": [fmt_cmd(c) for c in commands]})


@app.route("/api/stream/<job_id>")
def api_stream(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    def generate():
        pos = 0
        try:
            while True:
                # Yield any new log lines
                while pos < len(job.log):
                    yield f"data: {json.dumps({'line': job.log[pos]})}\n\n"
                    pos += 1

                if job.status != "running":
                    yield (
                        f"event: done\n"
                        f"data: {json.dumps({'status': job.status, 'exitCode': job.exit_code})}\n\n"
                    )
                    return

                time.sleep(0.05)
        except GeneratorExit:
            pass

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/stop/<job_id>", methods=["POST"])
def api_stop(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    if job.process and job.process.poll() is None:
        job.process.terminate()
        job.status = "error"
        job.exit_code = 130
        job.log.append("\n[STOPPED]\n")
    return jsonify({"status": "stopped"})


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IF Hub Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0a0908;
  --bg-sidebar: #0d0b09;
  --bg-card: #111;
  --bg-selected: #1a1610;
  --border: #1e1a14;
  --border-accent: #3a3020;
  --text: #d4c5a9;
  --text-muted: #aa9966;
  --text-dim: #665a40;
  --accent: #e8d090;
  --accent-hover: #ffe8a0;
  --heading: #c4b48a;
  --terminal-bg: #050403;
  --green: #6a9f55;
  --red: #c44;
  --yellow: #c4a32e;
}

html, body { height: 100%; }

body {
  font-family: Georgia, "Times New Roman", serif;
  background: var(--bg);
  color: var(--text);
  display: flex;
}

/* --- Sidebar --- */

.sidebar {
  width: 260px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  padding: 20px 14px;
  flex-shrink: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.sidebar h1 {
  color: var(--accent);
  font-size: 1.3em;
  letter-spacing: 1px;
}

.sidebar-sub {
  color: var(--text-muted);
  font-size: 0.85em;
  font-style: italic;
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border);
}

.proj-item {
  padding: 9px 11px;
  margin-bottom: 3px;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.1s;
}

.proj-item:hover { background: var(--bg-selected); }

.proj-item.sel {
  background: var(--bg-selected);
  border-color: var(--accent);
}

.proj-name {
  font-weight: bold;
  font-size: 0.92em;
  display: flex;
  align-items: center;
  gap: 7px;
}

.dot {
  display: inline-block;
  width: 7px; height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-g { background: var(--green); }
.dot-y { background: var(--yellow); }
.dot-r { background: var(--red); }

.proj-tags {
  font-size: 0.75em;
  color: var(--text-dim);
  margin-top: 2px;
  padding-left: 14px;
}

/* --- Main --- */

main {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
}

.welcome {
  color: var(--text-dim);
  padding-top: 80px;
  text-align: center;
}

.welcome h2 { color: var(--heading); margin-bottom: 8px; }

#panel { display: none; }

.panel-head h2 {
  color: var(--accent);
  font-size: 1.25em;
  margin-bottom: 3px;
}

.panel-tags {
  color: var(--text-muted);
  font-size: 0.85em;
  margin-bottom: 22px;
}

/* --- Sections --- */

section { margin-bottom: 18px; }

section h3 {
  color: var(--heading);
  font-size: 0.95em;
  margin-bottom: 10px;
}

details summary {
  cursor: pointer;
  list-style: none;
  user-select: none;
}

details summary::-webkit-details-marker { display: none; }

details summary h3::before {
  content: "\25B6\00a0";
  font-size: 0.7em;
  vertical-align: 1px;
}

details[open] summary h3::before {
  content: "\25BC\00a0";
}

details[open] summary { margin-bottom: 12px; }

/* --- Buttons --- */

.btn-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

button {
  padding: 7px 16px;
  font-family: Georgia, serif;
  font-size: 0.88em;
  border: 1px solid var(--border-accent);
  background: var(--bg-selected);
  color: var(--text);
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s;
}

button:hover:not(:disabled) {
  background: #2a2418;
  border-color: var(--text-muted);
}

button:disabled { opacity: 0.35; cursor: default; }

button.primary {
  background: var(--accent);
  color: var(--bg);
  border-color: var(--accent);
  font-weight: bold;
}

button.primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

/* --- Form --- */

.form-grid {
  display: grid;
  grid-template-columns: 90px 1fr;
  gap: 8px 12px;
  align-items: center;
  margin-bottom: 14px;
  max-width: 480px;
}

.form-grid label {
  color: var(--text-muted);
  font-size: 0.85em;
  text-align: right;
}

.form-grid input[type="text"] {
  width: 100%;
  padding: 7px 10px;
  background: var(--bg-selected);
  border: 1px solid var(--border-accent);
  color: var(--text);
  font-family: Georgia, serif;
  font-size: 0.88em;
  border-radius: 4px;
}

.form-grid input[type="text"]:focus {
  outline: none;
  border-color: var(--text-muted);
}

.form-check {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 14px;
}

.form-check input { accent-color: var(--accent); }
.form-check span { color: var(--text-muted); font-size: 0.85em; }

/* --- Output --- */

.output-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.output-bar h3 { margin-bottom: 0; }

#job-status {
  font-size: 0.82em;
  flex: 1;
}

.st-run { color: var(--yellow); }
.st-done { color: var(--green); }
.st-err { color: var(--red); }

.output-btns { display: flex; gap: 6px; }

#term {
  background: var(--terminal-bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 12px 14px;
  font-family: Consolas, Monaco, "Courier New", monospace;
  font-size: 12.5px;
  line-height: 1.5;
  height: 420px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
  color: #b0a080;
}

#term::-webkit-scrollbar { width: 8px; }
#term::-webkit-scrollbar-track { background: var(--terminal-bg); }
#term::-webkit-scrollbar-thumb { background: var(--border-accent); border-radius: 4px; }

/* --- Pipeline Steps --- */

.step {
  border: 1px solid var(--border);
  border-left: 3px solid var(--text-dim);
  border-radius: 4px;
  padding: 10px 14px;
  margin-bottom: 0;
}

.step-off { opacity: 0.35; }

.step-border-done { border-left-color: var(--green); }
.step-border-stale { border-left-color: var(--yellow); }
.step-border-failed { border-left-color: var(--red); }
.step-border-blocked { border-left-color: var(--red); opacity: 0.6; }
.step-border-notrun { border-left-color: var(--text-dim); }
.step-border-na { border-left-color: var(--border); }

.step-force-active { border-color: var(--yellow); border-left-color: var(--yellow); }

.step-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.step-num {
  color: var(--text-dim);
  font-size: 0.85em;
  min-width: 16px;
  padding-top: 1px;
}

.step-info { flex: 1; }

.step-name {
  font-weight: bold;
  font-size: 0.9em;
}

.step-desc {
  color: var(--text-dim);
  font-size: 0.78em;
  margin-top: 1px;
}

.step-artifact {
  color: var(--text-muted);
  font-size: 0.76em;
  margin-top: 4px;
}

.step-artifact-warn {
  color: var(--yellow);
  font-size: 0.76em;
  margin-top: 4px;
}

.step-skip-hint {
  color: var(--text-dim);
  font-size: 0.74em;
  font-style: italic;
  margin-top: 3px;
}

.badge {
  font-size: 0.72em;
  font-weight: bold;
  padding: 1px 7px;
  border-radius: 3px;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.badge-done { background: var(--green); color: #111; }
.badge-stale { background: var(--yellow); color: #111; }
.badge-failed { background: var(--red); color: #fff; }
.badge-notrun { background: var(--border-accent); color: var(--text-dim); }
.badge-na { background: var(--border); color: var(--text-dim); }
.badge-blocked { background: #522; color: #c88; }

.step-status {
  font-size: 0.78em;
  white-space: nowrap;
  padding-top: 2px;
}

.step-sep { color: var(--text-dim); }
.ck { color: var(--green); }
.xk { color: var(--text-dim); }

.step-connector {
  text-align: center;
  color: var(--text-dim);
  font-size: 0.7em;
  line-height: 1;
  margin: 2px 0;
}

.step-connector-done { color: var(--green); }

.step-btns {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  padding-left: 26px;
  align-items: center;
}

.step-btns-spacer { flex: 1; }

.force-label {
  font-size: 0.76em;
  color: var(--text-dim);
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.force-label input { cursor: pointer; }

.btn-chain {
  font-size: 0.82em;
  color: var(--text-muted);
  border-style: dashed;
}

.force-all-link {
  font-size: 0.78em;
  color: var(--text-dim);
  cursor: pointer;
  text-decoration: underline;
  margin-bottom: 6px;
  display: inline-block;
}

.force-all-link:hover { color: var(--text-muted); }

/* --- New Game --- */

.new-game-btn {
  margin-top: 16px;
  width: 100%;
  padding: 9px 16px;
  font-weight: bold;
  border-style: dashed;
}

.name-hint {
  font-size: 0.78em;
  color: var(--text-dim);
  margin: -2px 0 16px 102px;
}

.source-area {
  margin-top: 8px;
}

.source-area > label {
  display: block;
  color: var(--text-muted);
  font-size: 0.85em;
  margin-bottom: 6px;
}

.source-area textarea {
  width: 100%;
  max-width: 600px;
  height: 220px;
  padding: 10px 12px;
  background: var(--bg-selected);
  border: 1px solid var(--border-accent);
  color: var(--text);
  font-family: Consolas, Monaco, "Courier New", monospace;
  font-size: 12.5px;
  line-height: 1.5;
  border-radius: 4px;
  resize: vertical;
}

.source-area textarea:focus {
  outline: none;
  border-color: var(--text-muted);
}

.source-hint {
  font-size: 0.78em;
  color: var(--text-dim);
  margin-top: 6px;
}
</style>
</head>
<body>

<aside class="sidebar">
  <h1>IF Hub</h1>
  <div class="sidebar-sub">Dashboard</div>
  <div id="proj-list"></div>
  <button class="new-game-btn" onclick="showCreate()">+ New Game</button>
</aside>

<main>
  <div id="welcome" class="welcome">
    <h2>IF Hub Dashboard</h2>
    <p>Select a project from the sidebar, or create a new one.</p>
  </div>

  <div id="create-panel" style="display:none">
    <div class="panel-head">
      <h2>New Game</h2>
      <div class="panel-tags">Create a new project</div>
    </div>

    <section>
      <div class="form-grid">
        <label for="c-name">Name</label>
        <input id="c-name" type="text" placeholder="my-game">
      </div>
      <div class="name-hint">Lowercase, alphanumeric, hyphens ok. Becomes the project folder and URL.</div>

      <div class="form-grid" style="margin-top:10px">
        <label for="c-engine">Engine</label>
        <select id="c-engine" onchange="onEngineChange()">
          <option value="inform7">Inform 7</option>
          <option value="ink">Ink</option>
          <option value="wwwbasic">wwwBASIC (GW-BASIC)</option>
          <option value="qbjc">qbjc (QBasic)</option>
          <option value="applesoft">Applesoft BASIC</option>
          <option value="bwbasic">bwBASIC (GW-BASIC)</option>
          <option value="jsdos">DOS (js-dos)</option>
          <option value="twine">Twine</option>
          <option value="sharpee">Sharpee</option>
        </select>
      </div>

      <div class="source-area">
        <label for="c-source" id="c-source-label">Source code (story.ni)</label>
        <textarea id="c-source" placeholder='"My Game" by "Author Name"

The Foyer is a room. "You stand in a grand foyer."'></textarea>
        <div class="source-hint" id="c-source-hint">
          Paste your Inform 7 source here, or leave empty for a starter template.
        </div>
      </div>

      <div class="btn-row" style="margin-top:14px">
        <button class="primary" onclick="createGame()">Create Project</button>
        <button onclick="hideCreate()">Cancel</button>
      </div>
    </section>

    <section>
      <div class="output-bar">
        <h3>Output</h3>
        <span id="create-status"></span>
      </div>
      <pre id="create-term" style="height:200px;background:var(--terminal-bg);border:1px solid var(--border);border-radius:4px;padding:12px 14px;font-family:Consolas,Monaco,monospace;font-size:12.5px;line-height:1.5;overflow-y:auto;white-space:pre-wrap;word-break:break-all;color:#b0a080"></pre>
    </section>
  </div>

  <div id="panel">
    <div class="panel-head">
      <h2 id="p-name"></h2>
      <div class="panel-tags" id="p-tags"></div>
    </div>

    <section>
      <details id="meta-section">
        <summary><h3>Metadata</h3></summary>
        <div class="form-grid">
          <label for="f-title">Title</label>
          <input id="f-title" type="text">
          <label for="f-meta">Subtitle</label>
          <input id="f-meta" type="text" value="An Interactive Fiction">
          <label for="f-desc">Description</label>
          <input id="f-desc" type="text" value="An interactive fiction game.">
        </div>
        <div class="form-check">
          <input id="f-sound" type="checkbox">
          <span>Sound (blorb)</span>
        </div>
      </details>
    </section>

    <section>
      <h3>Pipeline</h3>
      <span class="force-all-link" onclick="toggleForceAll()">Force all steps</span>
      <div id="steps"></div>
    </section>

    <section>
      <details>
        <summary><h3>Quick Actions</h3></summary>
        <div class="btn-row">
          <button id="btn-pubup" onclick="pubUpdate()">Publish Update</button>
          <button onclick="unregister()">Unregister</button>
        </div>
      </details>
    </section>

    <section>
      <div class="output-bar">
        <h3>Output</h3>
        <span id="job-status"></span>
        <div class="output-btns">
          <button id="btn-stop" onclick="stopJob()" disabled>Stop</button>
          <button onclick="clr()">Clear</button>
        </div>
      </div>
      <pre id="term"></pre>
    </section>
  </div>
</main>

<script>
let projects = [];
let sel = null;
let curJob = null;
let evtSrc = null;

const ENGINE_LABELS = {
  inform7: 'Inform 7', wwwbasic: 'wwwBASIC', qbjc: 'QBasic',
  applesoft: 'Applesoft', bwbasic: 'bwBASIC', jsdos: 'DOS', basic: 'BASIC',
  twine: 'Twine', ink: 'Ink', sharpee: 'Sharpee', unknown: 'Unknown',
};

const BASIC_ENGINES = ['wwwbasic', 'qbjc', 'applesoft', 'bwbasic', 'basic'];
const BUILDABLE = ['inform7', 'wwwbasic', 'qbjc', 'applesoft', 'bwbasic', 'basic', 'ink', 'jsdos', 'sharpee'];

const STEPS = [
  {
    id: 'build', name: 'Build',
    desc: p => p.engine === 'inform7'
      ? 'Compile I7 source \u2192 binary + web player'
      : p.engine === 'ink'
        ? 'Compile .ink \u2192 JSON + web player'
        : BASIC_ENGINES.includes(p.engine)
          ? 'Generate web player from source'
          : p.engine === 'jsdos'
            ? 'Generate web player from .jsdos bundle'
            : 'Compile source',
    checks: p => [
      { ok: p.hasBinary, t: p.hasBinary ? 'binary' : 'no binary' },
      { ok: p.hasPlayHtml, t: p.hasPlayHtml ? 'play.html' : 'no play.html' },
    ],
    enabled: p => BUILDABLE.includes(p.engine),
  },
  {
    id: 'test', name: 'Test',
    desc: () => 'Run walkthrough + regression tests',
    checks: p => {
      const s = [];
      if (p.hasWalkthrough) s.push({ ok: true, t: 'walkthrough' });
      if (p.hasRegtest) s.push({ ok: true, t: 'regtest' });
      if (!s.length) s.push({ ok: false, t: 'no tests configured' });
      return s;
    },
    enabled: p => (p.engine === 'inform7' || p.engine === 'zmachine') && (p.hasWalkthrough || p.hasRegtest),
  },
  {
    id: 'package', name: 'Package',
    desc: () => 'Generate landing page + source browser',
    checks: p => [
      { ok: p.hasIndex, t: p.hasIndex ? 'index.html' : 'no index.html' },
      { ok: p.hasSourceHtml, t: p.hasSourceHtml ? 'source.html' : 'no source.html' },
    ],
    enabled: () => true,
  },
  {
    id: 'register', name: 'Register',
    desc: () => 'Add to IF Hub registry + push changes',
    checks: p => [
      { ok: p.registered, t: p.registered ? 'registered' : 'not registered' },
    ],
    enabled: () => true,
  },
  {
    id: 'publish', name: 'Publish',
    desc: p => p.hasGit ? 'Push changes to GitHub Pages' : 'Create GitHub repo + enable Pages',
    checks: p => [
      { ok: p.hasGit, t: p.hasGit ? 'git repo' : 'no repo' },
    ],
    enabled: () => true,
  },
];

async function load() {
  const r = await fetch('/api/projects');
  projects = await r.json();
  renderList();
  // Re-render steps if a project is selected
  if (sel) {
    const p = projects.find(x => x.name === sel);
    if (p) renderSteps(p);
  }
}

function renderList() {
  const el = document.getElementById('proj-list');
  el.innerHTML = '';
  projects.forEach(p => {
    const tags = [ENGINE_LABELS[p.engine] || p.engine];
    if (p.sound) tags.push('sound');
    if (p.hasWalkthrough) tags.push('walkthrough');
    if (p.hasRegtest) tags.push('regtest');

    let dc = 'dot-r';
    if (p.registered) dc = 'dot-g';
    else if (p.hasPlayHtml) dc = 'dot-y';

    const d = document.createElement('div');
    d.className = 'proj-item' + (sel === p.name ? ' sel' : '');
    d.onclick = () => pick(p.name);
    d.innerHTML =
      '<div class="proj-name"><span class="dot ' + dc + '"></span>' + p.name + '</div>' +
      (tags.length ? '<div class="proj-tags">' + tags.join(' &middot; ') + '</div>' : '');
    el.appendChild(d);
  });
}

function fmtSize(bytes) {
  if (bytes <= 0) return '';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function fmtRelTime(epoch) {
  if (!epoch) return '';
  const diff = (Date.now() / 1000) - epoch;
  if (diff < 60) return 'just now';
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
  if (diff < 172800) return 'yesterday';
  const d = new Date(epoch * 1000);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

const BADGE_MAP = {
  'done':    { label: 'DONE',    cls: 'badge-done' },
  'stale':   { label: 'STALE',   cls: 'badge-stale' },
  'failed':  { label: 'FAILED',  cls: 'badge-failed' },
  'not-run': { label: '\u2014',  cls: 'badge-notrun' },
  'n/a':     { label: 'N/A',     cls: 'badge-na' },
  'blocked': { label: 'BLOCKED', cls: 'badge-blocked' },
};

function renderSteps(p) {
  const el = document.getElementById('steps');
  el.innerHTML = '';
  const ss = p.stageStatus || {};

  STEPS.forEach((s, i) => {
    const on = s.enabled(p);
    const checks = s.checks(p);
    const isLast = i === STEPS.length - 1;
    const status = ss[s.id] || 'not-run';
    const badge = BADGE_MAP[status] || BADGE_MAP['not-run'];

    // Connector between cards
    if (i > 0) {
      const prevStatus = ss[STEPS[i - 1].id] || 'not-run';
      const conn = document.createElement('div');
      conn.className = 'step-connector' + (prevStatus === 'done' ? ' step-connector-done' : '');
      conn.textContent = '\u25BC';
      el.appendChild(conn);
    }

    // Check indicators
    const checksHtml = checks.map(x =>
      '<span class="' + (x.ok ? 'ck' : 'xk') + '">' +
      (x.ok ? '\u2713 ' : '\u2717 ') + x.t + '</span>'
    ).join(' <span class="step-sep">\u00b7</span> ');

    // Artifact detail line
    let artifactHtml = '';
    if (s.id === 'build' && p.binaryName && p.binarySize) {
      artifactHtml = '<div class="step-artifact">' +
        p.binaryName + ' \u00b7 ' + fmtSize(p.binarySize) +
        ' \u00b7 compiled ' + fmtRelTime(p.binaryMtime) + '</div>';
    }
    if (s.id === 'test' && status !== 'n/a' && p.testStale && p.hasBinary) {
      artifactHtml = '<div class="step-artifact-warn">\u26A0 Binary changed since last test</div>';
    }

    // Skip hint
    let skipHtml = '';
    if (status === 'done') {
      skipHtml = '<div class="step-skip-hint">Will skip (unchanged)</div>';
    }

    // Buttons
    let btns = '<button ' + (on ? '' : 'disabled ') +
      'onclick="runStep(\'' + s.id + '\')">' + s.name + '</button>';
    if (!isLast) {
      btns += ' <button ' + (on ? '' : 'disabled ') +
        'onclick="runFrom(\'' + s.id + '\')" class="btn-chain">' +
        s.name + ' \u2192 Publish</button>';
    }

    // Per-step force checkbox (only for done/stale)
    let forceHtml = '';
    if (status === 'done' || status === 'stale') {
      forceHtml = '<span class="step-btns-spacer"></span>' +
        '<label class="force-label">' +
        '<input type="checkbox" id="force-' + s.id + '" onchange="onForceToggle(\'' + s.id + '\')">' +
        ' Force re-run</label>';
    }

    const borderCls = 'step-border-' + status.replace('-', '');
    const div = document.createElement('div');
    div.className = 'step' + (on ? '' : ' step-off') + ' ' + borderCls;
    div.id = 'step-card-' + s.id;
    div.innerHTML =
      '<div class="step-head">' +
        '<span class="step-num">' + (i + 1) + '</span>' +
        '<div class="step-info">' +
          '<div class="step-name">' + s.name + '</div>' +
          '<div class="step-desc">' + s.desc(p) + '</div>' +
          artifactHtml +
          '<div class="step-status">' + checksHtml + '</div>' +
          skipHtml +
        '</div>' +
        '<span class="badge ' + badge.cls + '">' + badge.label + '</span>' +
      '</div>' +
      '<div class="step-btns">' + btns + forceHtml + '</div>';
    el.appendChild(div);
  });
}

function onForceToggle(stepId) {
  const cb = document.getElementById('force-' + stepId);
  const card = document.getElementById('step-card-' + stepId);
  if (!cb || !card) return;
  if (cb.checked) {
    card.classList.add('step-force-active');
    // Hide skip hint when forcing
    const hint = card.querySelector('.step-skip-hint');
    if (hint) hint.style.display = 'none';
  } else {
    card.classList.remove('step-force-active');
    const hint = card.querySelector('.step-skip-hint');
    if (hint) hint.style.display = '';
  }
}

function toggleForceAll() {
  const boxes = document.querySelectorAll('[id^="force-"]');
  const allChecked = Array.from(boxes).every(b => b.checked);
  boxes.forEach(b => { b.checked = !allChecked; onForceToggle(b.id.replace('force-', '')); });
}

function pick(name) {
  sel = name;
  const p = projects.find(x => x.name === name);
  if (!p) return;

  document.getElementById('welcome').style.display = 'none';
  document.getElementById('create-panel').style.display = 'none';
  document.getElementById('panel').style.display = 'block';
  document.getElementById('p-name').textContent = p.name;

  const info = [ENGINE_LABELS[p.engine] || p.engine];
  if (p.sourceFile) info.push(p.sourceFile);
  if (p.hasPlayHtml) info.push('Web player');
  if (p.hasBinary) info.push('Compiled');
  if (p.sound) info.push('Sound (blorb)');
  if (p.hasGit) info.push('Git repo');
  document.getElementById('p-tags').textContent = info.join(' \u00b7 ');

  // Pre-fill metadata form
  document.getElementById('f-title').value =
    name.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  document.getElementById('f-sound').checked = p.sound;

  // Publish Update button
  document.getElementById('btn-pubup').disabled = !p.hasGit;

  renderSteps(p);
  renderList();
}

function fd(stepId) {
  const base = {
    title: document.getElementById('f-title').value,
    meta: document.getElementById('f-meta').value,
    description: document.getElementById('f-desc').value,
    sound: document.getElementById('f-sound').checked,
  };
  // Per-step force: check the step's own checkbox
  if (stepId) {
    const cb = document.getElementById('force-' + stepId);
    if (cb && cb.checked) base.force = true;
  }
  return base;
}

function runStep(step) { run(step, fd(step)); }

function runFrom(step) {
  const data = fd(step);
  data.from = step;
  // Collect force from all steps in the chain
  const idx = STEPS.findIndex(s => s.id === step);
  for (let i = idx; i < STEPS.length; i++) {
    const cb = document.getElementById('force-' + STEPS[i].id);
    if (cb && cb.checked) { data.force = true; break; }
  }
  run('run-from', data);
}

async function run(task, extra) {
  if (!sel) return;
  const body = { task: task, game: sel, ...(extra || {}) };

  clr();
  setSt('st-run', 'Running...');

  const r = await fetch('/api/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await r.json();

  if (data.error) {
    out('[ERROR] ' + data.error + '\n');
    setSt('st-err', 'Error');
    return;
  }

  curJob = data.jobId;
  document.getElementById('btn-stop').disabled = false;

  data.commands.forEach(c => out('$ ' + c + '\n'));
  out('\n');

  if (evtSrc) evtSrc.close();
  evtSrc = new EventSource('/api/stream/' + data.jobId);

  evtSrc.onmessage = e => {
    const d = JSON.parse(e.data);
    if (d.line) out(d.line);
  };

  evtSrc.addEventListener('done', e => {
    const d = JSON.parse(e.data);
    evtSrc.close();
    evtSrc = null;
    curJob = null;
    document.getElementById('btn-stop').disabled = true;
    if (d.status === 'done') {
      setSt('st-done', 'Done');
    } else {
      setSt('st-err', 'Failed (exit code ' + d.exitCode + ')');
    }
    load();
  });

  evtSrc.onerror = () => {
    if (evtSrc) evtSrc.close();
    evtSrc = null;
    document.getElementById('btn-stop').disabled = true;
  };
}

function unregister() {
  if (!sel) return;
  if (!confirm('Remove ' + sel + ' from IF Hub?\n\nThe game repo and Pages site will NOT be deleted.')) return;
  run('unregister');
}

function pubUpdate() {
  const msg = prompt('Commit message (blank = default):');
  if (msg === null) return;
  run('publish-update', { message: msg });
}

async function stopJob() {
  if (!curJob) return;
  await fetch('/api/stop/' + curJob, { method: 'POST' });
}

function out(text) {
  const t = document.getElementById('term');
  t.textContent += text.replace(/\x1b\[[0-9;]*m/g, '');
  t.scrollTop = t.scrollHeight;
}

function clr() {
  document.getElementById('term').textContent = '';
  setSt('', '');
}

function setSt(cls, text) {
  const el = document.getElementById('job-status');
  el.className = cls;
  el.textContent = text;
}

const ENGINE_META = {
  inform7:   { label: 'Inform 7',  file: 'story.ni',  hint: 'Paste your Inform 7 source here, or leave empty for a starter template.', placeholder: '"My Game" by "Author Name"\\n\\nThe Foyer is a room. "You stand in a grand foyer."' },
  ink:       { label: 'Ink',       file: '.ink',       hint: 'Paste your Ink source here, or leave empty for a starter template.', placeholder: '=== start ===\\nYou stand at a crossroads.\\n\\n+ [Go north] -> north' },
  wwwbasic:  { label: 'wwwBASIC',  file: '.bas',       hint: 'Paste your GW-BASIC source here, or leave empty for a starter template.', placeholder: '10 PRINT "Hello, World!"\\n20 END' },
  qbjc:      { label: 'qbjc',      file: '.bas',       hint: 'Paste your QBasic source here, or leave empty for a starter template.', placeholder: 'PRINT "Hello, World!"\\nEND' },
  applesoft: { label: 'Applesoft', file: '.bas',       hint: 'Paste your Applesoft BASIC source here, or leave empty for a starter template.', placeholder: '10 PRINT "HELLO, WORLD!"\\n20 END' },
  bwbasic:   { label: 'bwBASIC',  file: '.bas',       hint: 'Paste your GW-BASIC source here, or leave empty for a starter template.', placeholder: '10 PRINT "Hello, World!"\\n20 END' },
  jsdos:     { label: 'DOS',      file: '.jsdos',     hint: 'A .jsdos bundle is required. Create one with js-dos tools.', placeholder: '' },
  twine:     { label: 'Twine',     file: '.tw',        hint: 'Paste your Twee source here, or leave empty for a starter template.', placeholder: ':: Start\\nYou stand at a crossroads.\\n\\n[[Go north->North]]' },
  sharpee:   { label: 'Sharpee',  file: '.ts',        hint: 'Sharpee games are built from a TypeScript monorepo. Place the dist/web/ output here.', placeholder: '' },
};

function onEngineChange() {
  const engine = document.getElementById('c-engine').value;
  const meta = ENGINE_META[engine] || ENGINE_META.inform7;
  const name = document.getElementById('c-name').value.trim();
  const fileLabel = engine === 'inform7' ? meta.file : (name ? name.replace(/-/g,'_') + meta.file : '*' + meta.file);
  document.getElementById('c-source-label').textContent = 'Source code (' + fileLabel + ')';
  document.getElementById('c-source-hint').textContent = meta.hint;
  document.getElementById('c-source').placeholder = meta.placeholder;
}

function showCreate() {
  sel = null;
  document.getElementById('welcome').style.display = 'none';
  document.getElementById('panel').style.display = 'none';
  document.getElementById('create-panel').style.display = 'block';
  document.getElementById('c-name').value = '';
  document.getElementById('c-source').value = '';
  document.getElementById('c-engine').value = 'inform7';
  document.getElementById('create-term').textContent = '';
  document.getElementById('create-status').textContent = '';
  document.getElementById('create-status').className = '';
  onEngineChange();
  renderList();
}

function hideCreate() {
  document.getElementById('create-panel').style.display = 'none';
  document.getElementById('welcome').style.display = 'block';
}

async function createGame() {
  const name = document.getElementById('c-name').value.trim();
  const source = document.getElementById('c-source').value;
  const engine = document.getElementById('c-engine').value;
  const cTerm = document.getElementById('create-term');
  const cSt = document.getElementById('create-status');

  if (!name) { alert('Enter a game name.'); return; }

  cTerm.textContent = '';
  cSt.className = 'st-run';
  cSt.textContent = 'Creating...';

  const engineLabel = (ENGINE_META[engine] || {}).label || engine;
  cTerm.textContent += 'Creating projects/' + name + '/ [' + engineLabel + ']...\n';

  const r = await fetch('/api/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, source, engine }),
  });
  const data = await r.json();

  if (data.error) {
    cTerm.textContent += '[ERROR] ' + data.error + '\n';
    cSt.className = 'st-err';
    cSt.textContent = 'Error';
    return;
  }

  cTerm.textContent += 'Created: ' + data.dir + '\n';
  cTerm.textContent += 'Refreshing project list...\n';

  await load();

  cSt.className = 'st-done';
  cSt.textContent = 'Done';

  setTimeout(() => {
    hideCreate();
    pick(name);
  }, 500);
}

load();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    port = 5000
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--port" and i < len(sys.argv) - 1:
            port = int(sys.argv[i + 1])

    url = f"http://127.0.0.1:{port}"
    print()
    print("  IF Hub Dashboard")
    print(f"  {url}")
    print("  Press Ctrl-C to stop.")
    print()

    # Open browser after a short delay (so server is ready)
    threading.Thread(
        target=lambda: (time.sleep(1), webbrowser.open(url)),
        daemon=True,
    ).start()

    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
