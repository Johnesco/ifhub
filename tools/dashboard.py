#!/usr/bin/env python3
"""IF Hub Dashboard -- Local web GUI for the build pipeline.

Usage:
    pip install flask
    python tools/dashboard.py [--port 5000]

Opens a browser-based dashboard for managing IF Hub game projects.
Matches the IF Hub dark-gold theme.
"""

import json
import os
import re
import shutil
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
COMPILE_SH = os.path.join(SCRIPT_DIR, "compile.sh")
EXTRACT_COMMANDS_SH = os.path.join(SCRIPT_DIR, "extract-commands.sh")
GENERATE_PAGES_SH = os.path.join(SCRIPT_DIR, "web", "generate-pages.sh")
REGISTER_GAME_SH = os.path.join(SCRIPT_DIR, "register-game.sh")
PUBLISH_SH = os.path.join(SCRIPT_DIR, "publish.sh")
PIPELINE_SH = os.path.join(SCRIPT_DIR, "pipeline.sh")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def to_posix(path):
    """Convert Windows path to MSYS2/Git Bash posix form."""
    path = path.replace("\\", "/")
    m = re.match(r"^([A-Za-z]):/", path)
    if m:
        path = "/" + m.group(1).lower() + "/" + path[3:]
    return path


def find_bash():
    git_bash = r"C:\Program Files\Git\bin\bash.exe"
    if os.path.isfile(git_bash):
        return git_bash
    found = shutil.which("bash")
    if found:
        return found
    return "bash"


# ---------------------------------------------------------------------------
# Project Discovery
# ---------------------------------------------------------------------------


@dataclass
class ProjectInfo:
    name: str
    dir: str
    sound: bool = False
    versioned: bool = False
    current_version: str = ""
    hub_id: str = ""
    has_walkthrough: bool = False
    has_regtest: bool = False
    has_test_me: bool = False
    has_play_html: bool = False
    has_ulx: bool = False
    has_git: bool = False


def load_projects():
    projects = []
    for name in sorted(os.listdir(PROJECTS_DIR)):
        project_dir = os.path.join(PROJECTS_DIR, name)
        if not os.path.isdir(project_dir):
            continue
        story_path = os.path.join(project_dir, "story.ni")
        if not os.path.isfile(story_path):
            continue

        conf_path = os.path.join(project_dir, "tests", "project.conf")
        fields = {}
        try:
            with open(conf_path, "r", encoding="utf-8") as f:
                for line in f:
                    m = re.match(
                        r'^(PIPELINE_\w+)=["\']?(.*?)["\']?\s*$', line.strip()
                    )
                    if m:
                        fields[m.group(1)] = m.group(2)
        except OSError:
            pass

        sound = fields.get("PIPELINE_SOUND", "").lower() == "true"
        if not sound and os.path.isdir(os.path.join(project_dir, "Sounds")):
            sound = True

        versioned = fields.get("PIPELINE_VERSIONED", "").lower() == "true"
        if not versioned:
            for entry in os.listdir(project_dir):
                if re.match(r"^v\d+$", entry) and os.path.isdir(
                    os.path.join(project_dir, entry)
                ):
                    versioned = True
                    break

        has_walkthrough = os.path.isfile(
            os.path.join(project_dir, "tests", "run-walkthrough.sh")
        )
        has_regtest = os.path.isfile(
            os.path.join(project_dir, "tests", "run-tests.sh")
        )

        has_test_me = False
        try:
            with open(story_path, "r", encoding="utf-8") as f:
                has_test_me = bool(
                    re.search(r"Test\s+\w+\s+with", f.read(), re.IGNORECASE)
                )
        except OSError:
            pass

        has_play = os.path.isfile(
            os.path.join(project_dir, "play.html")
        ) or os.path.isfile(os.path.join(project_dir, "web", "play.html"))

        has_ulx = any(
            f.endswith((".ulx", ".gblorb"))
            for f in os.listdir(project_dir)
            if os.path.isfile(os.path.join(project_dir, f))
        )

        projects.append(
            ProjectInfo(
                name=name,
                dir=project_dir,
                sound=sound,
                versioned=versioned,
                current_version=fields.get("PIPELINE_CURRENT_VERSION", ""),
                hub_id=fields.get("PIPELINE_HUB_ID", name),
                has_walkthrough=has_walkthrough,
                has_regtest=has_regtest,
                has_test_me=has_test_me,
                has_play_html=has_play,
                has_ulx=has_ulx,
                has_git=os.path.isdir(os.path.join(project_dir, ".git")),
            )
        )
    return projects


# ---------------------------------------------------------------------------
# Command Builders
# ---------------------------------------------------------------------------


def compile_cmd(game, sound=False):
    cmd = f'bash "{to_posix(COMPILE_SH)}" {game}'
    if sound:
        cmd += " --sound"
    return cmd


def extract_commands_cmd(source_path, output_path):
    return (
        f'bash "{to_posix(EXTRACT_COMMANDS_SH)}" --from-source '
        f'"{to_posix(source_path)}" -o "{to_posix(output_path)}"'
    )


def generate_pages_cmd(title, meta, description, out_dir):
    return (
        f'bash "{to_posix(GENERATE_PAGES_SH)}" '
        f'--title "{title}" --meta "{meta}" --description "{description}" '
        f'--out "{to_posix(out_dir)}"'
    )


def register_game_cmd(name, title, meta, description, sound=""):
    cmd = (
        f'bash "{to_posix(REGISTER_GAME_SH)}" '
        f'--name {name} --title "{title}" --meta "{meta}" '
        f'--description "{description}"'
    )
    if sound:
        cmd += f" --sound {sound}"
    return cmd


def publish_cmd(game, message=""):
    cmd = f'bash "{to_posix(PUBLISH_SH)}" {game}'
    if message:
        cmd += f' "{message}"'
    return cmd


def pipeline_cmd(game, *stages):
    return f'bash "{to_posix(PIPELINE_SH)}" {game} {" ".join(stages)}'


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


def run_job(job_id, commands):
    """Run commands sequentially, appending output to job.log."""
    job = jobs[job_id]
    bash = find_bash()

    for i, cmd in enumerate(commands):
        if len(commands) > 1:
            header = f"\n--- [{i + 1}/{len(commands)}] {cmd} ---\n"
            job.log.append(header)

        try:
            proc = subprocess.Popen(
                [bash, "-c", cmd],
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


def build_commands(task, project, data):
    """Build command list for a task. Returns list or error string."""
    game = project.name

    if task == "compile":
        return [compile_cmd(game, project.sound)]

    if task == "build-test":
        return [pipeline_cmd(game, "compile", "test", "--force")]

    if task == "publish-new":
        title = data.get("title", "")
        meta = data.get("meta", "An Interactive Fiction")
        desc = data.get("description", "An interactive fiction game.")
        sound = data.get("sound", project.sound)

        cmds = []
        if project.has_test_me:
            walk_dir = to_posix(
                os.path.join(project.dir, "tests", "inform7")
            )
            walk_file = os.path.join(
                project.dir, "tests", "inform7", "walkthrough.txt"
            )
            cmds.append(f'mkdir -p "{walk_dir}"')
            cmds.append(
                extract_commands_cmd(
                    os.path.join(project.dir, "story.ni"), walk_file
                )
            )

        cmds.append(compile_cmd(game, sound))
        cmds.append(generate_pages_cmd(title, meta, desc, project.dir))
        sound_type = "blorb" if sound else ""
        cmds.append(
            register_game_cmd(game, title, meta, desc, sound_type)
        )
        cmds.append(publish_cmd(game, f"Initial publish: {title}"))
        # Push hub changes (games.json + cards.json) so the live hub sees the new game
        hub_dir = to_posix(os.path.join(I7_ROOT, "ifhub"))
        ifhub_root = to_posix(I7_ROOT)
        cmds.append(
            f'cd "{ifhub_root}" && '
            f'git add ifhub/games.json ifhub/cards.json && '
            f'git diff --cached --quiet || '
            f'git commit -m "Register {game} in IF Hub" && git push'
        )
        return cmds

    if task == "publish-update":
        message = data.get("message", "")
        return [publish_cmd(game, message)]

    if task == "extract-walkthrough":
        walk_dir = to_posix(
            os.path.join(project.dir, "tests", "inform7")
        )
        walk_file = os.path.join(
            project.dir, "tests", "inform7", "walkthrough.txt"
        )
        return [
            f'mkdir -p "{walk_dir}"',
            extract_commands_cmd(
                os.path.join(project.dir, "story.ni"), walk_file
            ),
        ]

    if task == "generate-pages":
        title = data.get("title", "")
        meta = data.get("meta", "An Interactive Fiction")
        desc = data.get("description", "An interactive fiction game.")
        return [generate_pages_cmd(title, meta, desc, project.dir)]

    if task == "register":
        title = data.get("title", "")
        meta = data.get("meta", "An Interactive Fiction")
        desc = data.get("description", "An interactive fiction game.")
        sound = data.get("sound", project.sound)
        sound_type = "blorb" if sound else ""
        return [register_game_cmd(game, title, meta, desc, sound_type)]

    if task == "test-walkthrough":
        wt = to_posix(
            os.path.join(project.dir, "tests", "run-walkthrough.sh")
        )
        return [f'bash "{wt}"']

    if task == "test-regtest":
        rt = to_posix(
            os.path.join(project.dir, "tests", "run-tests.sh")
        )
        return [f'bash "{rt}"']

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
                "sound": p.sound,
                "versioned": p.versioned,
                "currentVersion": p.current_version,
                "hubId": p.hub_id,
                "hasWalkthrough": p.has_walkthrough,
                "hasRegtest": p.has_regtest,
                "hasTestMe": p.has_test_me,
                "hasPlayHtml": p.has_play_html,
                "hasUlx": p.has_ulx,
                "hasGit": p.has_git,
            }
            for p in projects
        ]
    )


@app.route("/api/create", methods=["POST"])
def api_create():
    """Create a new project from a game name + source code."""
    data = request.json
    name = data.get("name", "").strip()
    source = data.get("source", "").strip()

    if not name:
        return jsonify({"error": "Game name is required"}), 400
    if not re.match(r"^[a-z0-9]([a-z0-9_-]*[a-z0-9])?$", name):
        return jsonify(
            {"error": "Name must be lowercase alphanumeric (hyphens/underscores ok)"}
        ), 400

    project_dir = os.path.join(PROJECTS_DIR, name)
    story_path = os.path.join(project_dir, "story.ni")

    if os.path.isfile(story_path):
        return jsonify({"error": f"Project '{name}' already exists"}), 409

    if not source:
        return jsonify({"error": "Source code is required"}), 400

    # Validate first line looks like Inform 7
    first_line = source.split("\n")[0].strip()
    if not first_line.startswith('"'):
        return jsonify(
            {"error": 'Source must start with "Title" by "Author"'}
        ), 400

    os.makedirs(project_dir, exist_ok=True)
    with open(story_path, "w", encoding="utf-8") as f:
        f.write(source)
        if not source.endswith("\n"):
            f.write("\n")

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

    return jsonify({"jobId": job_id, "commands": commands})


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
.dot-x { background: #444; }

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
      <div class="panel-tags">Create a new Inform 7 project</div>
    </div>

    <section>
      <div class="form-grid">
        <label for="c-name">Name</label>
        <input id="c-name" type="text" placeholder="my-game">
      </div>
      <div class="name-hint">Lowercase, alphanumeric, hyphens ok. Becomes the project folder and URL.</div>

      <div class="source-area">
        <label for="c-source">Source code (story.ni)</label>
        <textarea id="c-source" placeholder='"My Game" by "Author Name"

The Foyer is a room. "You stand in a grand foyer."'></textarea>
        <div class="source-hint">
          Paste your Inform 7 source here, or leave empty if you already placed
          a story.ni in projects/&lt;name&gt;/.
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
      <h3>Quick Actions</h3>
      <div class="btn-row">
        <button onclick="run('compile')">Compile</button>
        <button onclick="run('build-test')">Build &amp; Test</button>
        <button id="btn-pubup" onclick="pubUpdate()">Publish Update</button>
      </div>
    </section>

    <section>
      <details id="pub-section">
        <summary><h3>Publish New Game</h3></summary>
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
        <button class="primary" onclick="pubNew()">Publish New Game</button>
      </details>
    </section>

    <section>
      <details>
        <summary><h3>More Tools</h3></summary>
        <div class="btn-row">
          <button onclick="run('extract-walkthrough')">Extract Walkthrough</button>
          <button onclick="run('generate-pages',fd())">Generate Pages</button>
          <button onclick="run('register',fd())">Register in Hub</button>
        </div>
        <div class="btn-row" style="margin-top:4px">
          <button id="btn-wt" onclick="run('test-walkthrough')">Run Walkthrough</button>
          <button id="btn-rt" onclick="run('test-regtest')">Run Regtests</button>
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

async function load() {
  const r = await fetch('/api/projects');
  projects = await r.json();
  renderList();
}

function renderList() {
  const el = document.getElementById('proj-list');
  el.innerHTML = '';
  projects.forEach(p => {
    const tags = [];
    if (p.sound) tags.push('sound');
    if (p.versioned) tags.push('versioned' + (p.currentVersion ? ' ' + p.currentVersion : ''));
    if (p.hasTestMe) tags.push('Test me');
    if (p.hasWalkthrough) tags.push('walkthrough');
    if (p.hasRegtest) tags.push('regtest');

    let dc = 'dot-x';
    if (p.hasPlayHtml) dc = 'dot-g';
    else if (p.hasUlx) dc = 'dot-y';

    const d = document.createElement('div');
    d.className = 'proj-item' + (sel === p.name ? ' sel' : '');
    d.onclick = () => pick(p.name);
    d.innerHTML =
      '<div class="proj-name"><span class="dot ' + dc + '"></span>' + p.name + '</div>' +
      (tags.length ? '<div class="proj-tags">' + tags.join(' &middot; ') + '</div>' : '');
    el.appendChild(d);
  });
}

function pick(name) {
  sel = name;
  const p = projects.find(x => x.name === name);
  if (!p) return;

  document.getElementById('welcome').style.display = 'none';
  document.getElementById('panel').style.display = 'block';
  document.getElementById('p-name').textContent = p.name;

  const info = [];
  if (p.hasPlayHtml) info.push('Web player');
  if (p.hasUlx) info.push('Compiled');
  if (p.sound) info.push('Sound (blorb)');
  if (p.versioned) info.push('Versioned' + (p.currentVersion ? ': ' + p.currentVersion : ''));
  if (p.hasGit) info.push('Git repo');
  document.getElementById('p-tags').textContent = info.join(' \u00b7 ') || 'Source only';

  // Pre-fill form
  document.getElementById('f-title').value =
    name.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  document.getElementById('f-sound').checked = p.sound;

  // Enable/disable buttons
  document.getElementById('btn-wt').disabled = !p.hasWalkthrough;
  document.getElementById('btn-rt').disabled = !p.hasRegtest;
  document.getElementById('btn-pubup').disabled = !p.hasGit;

  renderList();
}

function fd() {
  return {
    title: document.getElementById('f-title').value,
    meta: document.getElementById('f-meta').value,
    description: document.getElementById('f-desc').value,
    sound: document.getElementById('f-sound').checked,
  };
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

  // Show commands
  data.commands.forEach(c => out('$ ' + c + '\n'));
  out('\n');

  // Start SSE
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
    load(); // refresh project status
  });

  evtSrc.onerror = () => {
    if (evtSrc) evtSrc.close();
    evtSrc = null;
    document.getElementById('btn-stop').disabled = true;
  };
}

function pubNew() { run('publish-new', fd()); }

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
  // Strip ANSI escape codes
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

function showCreate() {
  sel = null;
  document.getElementById('welcome').style.display = 'none';
  document.getElementById('panel').style.display = 'none';
  document.getElementById('create-panel').style.display = 'block';
  document.getElementById('c-name').value = '';
  document.getElementById('c-source').value = '';
  document.getElementById('create-term').textContent = '';
  document.getElementById('create-status').textContent = '';
  document.getElementById('create-status').className = '';
  renderList();
}

function hideCreate() {
  document.getElementById('create-panel').style.display = 'none';
  document.getElementById('welcome').style.display = 'block';
}

async function createGame() {
  const name = document.getElementById('c-name').value.trim();
  const source = document.getElementById('c-source').value;
  const cTerm = document.getElementById('create-term');
  const cSt = document.getElementById('create-status');

  if (!name) { alert('Enter a game name.'); return; }

  cTerm.textContent = '';
  cSt.className = 'st-run';
  cSt.textContent = 'Creating...';

  // If source is empty, check if story.ni already exists
  if (!source.trim()) {
    cTerm.textContent += 'No source pasted -- checking for existing story.ni...\n';
    // Try to load projects and see if it exists
    await load();
    const existing = projects.find(p => p.name === name);
    if (existing) {
      cTerm.textContent += 'Found existing project: ' + name + '\n';
      cSt.className = 'st-done';
      cSt.textContent = 'Ready';
      hideCreate();
      pick(name);
      return;
    } else {
      cTerm.textContent += 'No story.ni found at projects/' + name + '/story.ni\n';
      cSt.className = 'st-err';
      cSt.textContent = 'Error';
      return;
    }
  }

  // Create via API
  cTerm.textContent += 'Creating projects/' + name + '/story.ni...\n';

  const r = await fetch('/api/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, source }),
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

  // Switch to the new project
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
