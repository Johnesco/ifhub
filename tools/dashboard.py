#!/usr/bin/env python3
"""IF Hub Dashboard -- Local web GUI for the build pipeline.

Usage:
    pip install flask
    python tools/dashboard.py [--port 5000]

Opens a browser-based dashboard for managing IF Hub game projects.
Matrix table view with artifact-based state model and converging DAG detail.
"""

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
# Shared library imports
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from lib import config as _libconfig  # noqa: E402
from lib import paths  # noqa: E402
from lib.projects import ProjectInfo, ArtifactStatus, load_projects  # noqa: E402
from lib.config import extract_story_metadata  # noqa: E402

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

PIPELINE_PY = str(paths.TOOLS_DIR / "pipeline.py")
PUBLISH_PY = str(paths.TOOLS_DIR / "publish.py")
REGISTER_GAME_PY = str(paths.TOOLS_DIR / "register_game.py")
UNREGISTER_GAME_PY = str(paths.TOOLS_DIR / "unregister_game.py")
PUSH_HUB_PY = str(paths.TOOLS_DIR / "push_hub.py")
NEW_PROJECT_PY = str(paths.TOOLS_DIR / "new_project.py")
GENERATE_PAGES_PY = str(paths.WEB_DIR / "generate_pages.py")
COMPILE_SHARPEE_PY = str(paths.TOOLS_DIR / "compile_sharpee.py")
COMPILE_REZ_PY = str(paths.TOOLS_DIR / "compile_rez.py")
SETUP_BASIC_PY = str(paths.WEB_DIR / "setup_basic.py")
SETUP_INK_PY = str(paths.WEB_DIR / "setup_ink.py")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def py_cmd(*args):
    """Build a Python subprocess command list."""
    return [sys.executable, *args]


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


# ---------------------------------------------------------------------------
# Action command builders
# ---------------------------------------------------------------------------

# Pipeline steps: compile → publish → register
PIPELINE_ORDER = ["compile", "publish", "register"]
STEP_TO_ARTIFACT = {"compile": "compile", "publish": "published", "register": "registered"}


def _compile_commands(project, data):
    """Compile step: engine-specific build."""
    game = project.name
    force = data.get("force", False)
    cmd = py_cmd(PIPELINE_PY, game, "compile")
    if force:
        cmd.append("--force")
    return [cmd]


def _publish_commands(project, data):
    """Publish step: push to GitHub Pages."""
    message = data.get("message", "")
    cmd = py_cmd(PUBLISH_PY, project.name)
    if message:
        cmd.append(message)
    return [cmd]


def _register_commands(project, data):
    """Build commands for the 'register' action."""
    title = data.get("title", project.name.replace("-", " ").replace("_", " ").title())
    meta = data.get("meta", "An Interactive Fiction")
    desc = data.get("description", "An interactive fiction game.")
    sound_type = "blorb" if data.get("sound", project.sound) else ""
    engine = project.engine

    reg_cmd = py_cmd(REGISTER_GAME_PY,
                     "--name", project.name, "--title", title,
                     "--meta", meta, "--description", desc)
    if sound_type:
        reg_cmd.extend(["--sound", sound_type])
    if engine and engine != "unknown":
        reg_cmd.extend(["--engine", engine])

    return [reg_cmd, py_cmd(PUSH_HUB_PY, project.name)]


STEP_HANDLERS = {
    "compile": _compile_commands,
    "publish": _publish_commands,
    "register": _register_commands,
}


def _run_to_commands(project, data):
    """Run all pipeline steps up to and including target, skipping what's current."""
    target = data.get("target", "register")
    force = data.get("force", False)

    if target not in PIPELINE_ORDER:
        return f"Unknown target step: {target}"

    idx = PIPELINE_ORDER.index(target)
    steps = PIPELINE_ORDER[:idx + 1]

    cmds = []
    for step in steps:
        art_key = STEP_TO_ARTIFACT[step]
        art = project.artifacts.get(art_key)

        if art and art.status == ArtifactStatus.NA:
            continue
        if not force and art and art.status == ArtifactStatus.PRESENT:
            continue

        handler = STEP_HANDLERS.get(step)
        if handler:
            step_cmds = handler(project, data)
            if step_cmds:
                cmds.extend(step_cmds)

    return cmds or None


def _ship_all_commands(project, data):
    """Ship-all runs publish + register only (no compile/test)."""
    data = dict(data, target="register")
    return _run_to_commands(project, data)


def _unregister_commands(project, data):
    """Build commands for the 'unregister' action."""
    return [py_cmd(UNREGISTER_GAME_PY, project.name), py_cmd(PUSH_HUB_PY, project.name)]


ACTION_HANDLERS = {
    **STEP_HANDLERS,
    "run-to": _run_to_commands,
    "ship-all": _ship_all_commands,
    "unregister": _unregister_commands,
}


def build_commands(task, project, data):
    """Build command list for a task. Returns list, None, or error string."""
    handler = ACTION_HANDLERS.get(task)
    if not handler:
        return f"Unknown task: {task}"
    result = handler(project, data)
    if result is None:
        return "Nothing to do — all artifacts are current."
    if not result:
        return f"Action '{task}' not applicable for engine: {project.engine}"
    return result


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
    result = []
    for p in projects:
        arts = {}
        for key, a in p.artifacts.items():
            arts[key] = {
                "status": a.status.value,
                "path": a.path,
                "size": a.size,
                "mtime": a.mtime,
                "detail": a.detail,
            }
        # Extract story metadata for form pre-fill
        meta = extract_story_metadata(p.dir)
        result.append({
            "name": p.name,
            "dir": p.dir,
            "engine": p.engine,
            "sourceFile": p.source_file,
            "sound": p.sound,
            "hubId": p.hub_id,
            "overallStatus": p.overall_status,
            "artifacts": arts,
            "title": meta.get("title", ""),
            "meta": meta.get("meta", "An Interactive Fiction"),
            "description": meta.get("description", "An interactive fiction game."),
            "compileScripts": p.compile_scripts,
        })
    return jsonify(result)


def _resolve_file_path(game, filetype):
    """Resolve a file path for a game + filetype. Returns (path, error)."""
    from lib.projects import walkthrough_path as _wt_path
    projects = load_projects()
    project = next((p for p in projects if p.name == game), None)
    if not project:
        return None, f"Project not found: {game}"

    if filetype == "source":
        if not project.source_file:
            return None, "No source file detected"
        return os.path.join(project.dir, project.source_file), None
    elif filetype == "walkthrough":
        return _wt_path(project.dir), None
    else:
        return None, f"Unknown file type: {filetype}"


@app.route("/api/file/<game>/<filetype>")
def api_file_read(game, filetype):
    """Read a project file. Types: source, walkthrough."""
    path, err = _resolve_file_path(game, filetype)
    if err:
        return jsonify({"error": err}), 400

    content = ""
    exists = os.path.isfile(path)
    if exists:
        try:
            content = open(path, "r", encoding="utf-8").read()
        except OSError as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"content": content, "path": path, "exists": exists})


@app.route("/api/file/<game>/<filetype>", methods=["POST"])
def api_file_write(game, filetype):
    """Write a project file before running a step."""
    data = request.json
    content = data.get("content", "")

    path, err = _resolve_file_path(game, filetype)
    if err:
        return jsonify({"error": err}), 400

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content if content.endswith("\n") else content + "\n")
    except OSError as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"path": path, "written": True})


@app.route("/api/create", methods=["POST"])
def api_create():
    """Create a new project."""
    data = request.json
    name = data.get("name", "").strip()
    source = data.get("source", "").strip()
    engine = data.get("engine", "inform7").strip()

    if not name:
        return jsonify({"error": "Game name is required"}), 400
    if not re.match(r"^[a-z0-9]([a-z0-9_-]*[a-z0-9])?$", name):
        return jsonify({"error": "Name must be lowercase alphanumeric (hyphens/underscores ok)"}), 400

    # Extract title from source (or use the game name as fallback)
    title = name.replace("-", " ").replace("_", " ").title()
    if source and engine == "inform7":
        first_line = source.split("\n")[0].strip()
        if not first_line.startswith('"'):
            return jsonify({"error": 'Source must start with "Title" by "Author"'}), 400
        m = re.match(r'^"([^"]+)"', first_line)
        if m:
            title = m.group(1)

    cmd = py_cmd(NEW_PROJECT_PY, title, name)
    if engine != "inform7":
        cmd.extend(["--engine", engine])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return jsonify({"error": f"new_project.py failed: {result.stderr}"}), 500

    # If custom source was provided, overwrite the starter source file
    if source:
        spec = _libconfig.get_engine_spec(engine)
        if engine == "inform7":
            source_file = "story.ni"
        elif spec:
            source_file = name.replace("-", "_") + spec.source_extensions[0]
        else:
            source_file = "story.ni"

        project_dir = str(paths.new_project_dir(engine, name))
        source_path = os.path.join(project_dir, source_file)
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(source if source.endswith("\n") else source + "\n")

    return jsonify({"name": name})


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

    thread = threading.Thread(target=run_job, args=(job_id, commands), daemon=True)
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
# HTML — Preact SPA (no build step, CDN imports via htm tagged templates)
# ---------------------------------------------------------------------------

_HTML_FILE = os.path.join(SCRIPT_DIR, "dashboard.html")
if os.path.isfile(_HTML_FILE):
    HTML_PAGE = open(_HTML_FILE, "r", encoding="utf-8").read()
else:
    HTML_PAGE = "<html><body><h1>Missing dashboard.html</h1></body></html>"


_UNUSED_INLINE_HTML = r"""<!DOCTYPE html>

/* Header */
header { padding:14px 24px; border-bottom:1px solid var(--border); display:flex; align-items:center; gap:16px; background:var(--bg-card); }
header h1 { color:var(--accent); font-size:1.15em; font-weight:600; }
header .sub { color:var(--text-muted); font-size:.82em; }
header .spacer { flex:1; }
.hdr-btn { padding:6px 14px; font-size:.82em; border:1px solid var(--border-accent); background:transparent; color:var(--text-muted); border-radius:6px; cursor:pointer; font-family:inherit; transition:all .12s; }
.hdr-btn:hover { background:var(--bg-hover); border-color:var(--accent); color:var(--text); }

/* Matrix Table */
.matrix { width:100%; border-collapse:collapse; table-layout:fixed; }
.matrix th { text-align:left; padding:10px 12px; font-size:.72em; font-weight:600; color:var(--text-dim); text-transform:uppercase; letter-spacing:.8px; border-bottom:1px solid var(--border); position:sticky; top:0; background:var(--bg); z-index:2; }
.matrix td { padding:10px 12px; font-size:.86em; border-bottom:1px solid var(--border); vertical-align:middle; }
.col-game { width:22%; } .col-engine { width:8%; } .col-status { width:10%; } .col-actions { width:18%; }
.matrix tbody tr { cursor:pointer; transition:background .08s; }
.matrix tbody tr:hover { background:var(--bg-hover); }
.matrix tbody tr.row-sel { background:var(--bg-sel); }
.game-name { color:var(--text); font-weight:600; text-decoration:none; }
.game-name:hover { color:var(--accent); }
.engine-tag { font-size:.72em; color:var(--text-muted); background:var(--bg); border:1px solid var(--border); border-radius:4px; padding:2px 7px; white-space:nowrap; font-weight:500; }

/* Badges */
.badge { display:inline-block; font-size:.68em; font-weight:600; padding:3px 8px; border-radius:4px; letter-spacing:.3px; cursor:pointer; white-space:nowrap; transition:all .1s; text-transform:uppercase; }
.badge:hover { filter:brightness(1.2); }
.badge-present { background:var(--green-dim); color:var(--green); border:1px solid rgba(52,211,153,.2); }
.badge-missing { background:rgba(85,91,112,.15); color:var(--text-dim); border:1px solid var(--border); }
.badge-stale   { background:var(--yellow-dim); color:var(--yellow); border:1px solid rgba(251,191,36,.2); }
.badge-failed  { background:var(--red-dim); color:var(--red); border:1px solid rgba(248,113,113,.2); }
.badge-na      { background:transparent; color:var(--text-dim); border:1px solid var(--border); font-weight:normal; opacity:.5; }

/* Buttons */
.btn { padding:5px 12px; font-family:inherit; font-size:.8em; border:1px solid var(--border-accent); background:var(--bg-card); color:var(--text); border-radius:6px; cursor:pointer; white-space:nowrap; transition:all .1s; }
.btn:hover { background:var(--bg-sel); border-color:var(--accent); }
.btn:disabled { opacity:.3; cursor:default; }
.btn-primary { background:var(--accent); color:#fff; border-color:var(--accent); font-weight:600; }
.btn-primary:hover { background:var(--accent-hover); }
.force-label { font-size:.72em; color:var(--text-dim); display:flex; align-items:center; gap:3px; cursor:pointer; }

/* Expanded row */
.expanded-row td { padding:0!important; border-bottom:2px solid var(--accent); }
.expanded-content { background:var(--bg-expanded); padding:20px 28px; display:flex; gap:28px; }
.expanded-left { flex:0 0 340px; }
.expanded-right { flex:1; min-width:0; }

/* DAG */
.dag { display:flex; flex-direction:column; align-items:stretch; max-width:340px; }
.dag-node { border:1px solid var(--border); border-left:3px solid var(--text-dim); border-radius:6px; padding:10px 14px; background:var(--bg-card); }
.dag-node-present { border-left-color:var(--green); }
.dag-node-missing { border-left-color:var(--text-dim); }
.dag-node-stale   { border-left-color:var(--yellow); }
.dag-node-failed  { border-left-color:var(--red); }
.dag-node-na      { border-left-color:var(--border); opacity:.35; }
.dag-node-running { border-left-color:var(--accent); background:repeating-linear-gradient(-45deg,var(--bg-card),var(--bg-card) 8px,rgba(108,158,255,.06) 8px,rgba(108,158,255,.06) 16px); background-size:200% 100%; animation:stripe-scroll .8s linear infinite; }
@keyframes stripe-scroll { 0%{background-position:0 0} 100%{background-position:22.6px 0} }
.only-link { font-size:.7em; color:var(--text-dim); cursor:pointer; text-decoration:underline; margin-left:4px; }
.only-link:hover { color:var(--text-muted); }
.node-head { display:flex; align-items:center; gap:8px; margin-bottom:3px; }
.node-name { font-weight:600; font-size:.88em; }
.node-badge { font-size:.65em; font-weight:600; padding:2px 7px; border-radius:4px; margin-left:auto; text-transform:uppercase; }
.node-detail { font-size:.76em; color:var(--text-muted); margin-bottom:6px; }
.node-detail a { color:var(--blue); text-decoration:none; }
.node-detail a:hover { text-decoration:underline; }
.node-btns { display:flex; gap:6px; align-items:center; }
.node-btns .spacer { flex:1; }

/* DAG connectors */
.dag-connector { display:flex; align-items:stretch; height:28px; position:relative; }
.conn-straight { width:2px; background:var(--line); margin:0 auto; position:relative; }
.conn-straight::after { content:''; position:absolute; bottom:-4px; left:50%; transform:translateX(-50%); border:5px solid transparent; border-top-color:var(--line); }
.conn-branch { position:relative; height:28px; width:100%; }
.conn-fork::before { content:''; position:absolute; top:0; left:50%; width:2px; height:50%; background:var(--line); transform:translateX(-50%); }
.conn-fork::after { content:''; position:absolute; top:50%; left:15%; right:15%; height:2px; background:var(--line); }
.conn-fork-left, .conn-fork-right { position:absolute; top:50%; width:2px; height:50%; background:var(--line); }
.conn-fork-left { left:15%; } .conn-fork-right { right:15%; }
.conn-fork-left::after, .conn-fork-right::after { content:''; position:absolute; bottom:-4px; left:50%; transform:translateX(-50%); border:4px solid transparent; border-top-color:var(--line); }
.conn-merge::after { content:''; position:absolute; bottom:0; left:15%; right:15%; height:2px; background:var(--line); }
.conn-merge::before { content:''; position:absolute; bottom:0; left:50%; width:2px; height:50%; background:var(--line); transform:translateX(-50%); }
.conn-merge-left, .conn-merge-right { position:absolute; top:0; width:2px; height:50%; background:var(--line); }
.conn-merge-left { left:15%; } .conn-merge-right { right:15%; }
.conn-merge-down { position:absolute; bottom:-4px; left:50%; transform:translateX(-50%); border:5px solid transparent; border-top-color:var(--line); }
.dag-row { display:flex; gap:12px; }
.dag-row > .dag-node { flex:1; min-width:0; }

/* Metadata form */
.meta-form { display:grid; grid-template-columns:auto 1fr; gap:6px 10px; align-items:center; margin-bottom:12px; padding:12px 14px; background:var(--bg-card); border:1px solid var(--border); border-radius:6px; }
.meta-form label { font-size:.76em; color:var(--text-dim); text-align:right; font-weight:500; }
.meta-form input[type="text"] { padding:5px 8px; background:var(--bg); border:1px solid var(--border); color:var(--text); font-family:inherit; font-size:.82em; border-radius:4px; }
.meta-form input[type="text"]:focus { outline:none; border-color:var(--accent); }
.meta-form .chk { grid-column:2; display:flex; align-items:center; gap:5px; font-size:.76em; color:var(--text-dim); }
.meta-form .chk input { accent-color:var(--accent); }

/* Terminal */
.output-bar { display:flex; align-items:center; gap:12px; margin-bottom:6px; }
.output-bar h4 { font-size:.82em; color:var(--heading); font-weight:600; }
.job-status { font-size:.76em; flex:1; }
.st-run { color:var(--yellow); } .st-done { color:var(--green); } .st-err { color:var(--red); }
.output-btns { display:flex; gap:6px; }
.term { background:var(--term-bg); border:1px solid var(--border); border-radius:6px; padding:10px 12px; font-family:"SF Mono","Cascadia Code",Consolas,monospace; font-size:12px; line-height:1.6; height:300px; overflow-y:auto; white-space:pre-wrap; word-break:break-all; color:var(--text-muted); }
.term::-webkit-scrollbar { width:6px; } .term::-webkit-scrollbar-track { background:transparent; } .term::-webkit-scrollbar-thumb { background:var(--border); border-radius:3px; }

/* Modal */
.overlay { display:none; position:fixed; inset:0; background:rgba(0,0,0,.55); backdrop-filter:blur(4px); z-index:100; justify-content:center; align-items:center; }
.overlay.show { display:flex; }
.modal { background:var(--bg-card); border:1px solid var(--border-accent); border-radius:10px; padding:24px; width:480px; max-height:80vh; overflow-y:auto; box-shadow:0 20px 60px rgba(0,0,0,.4); }
.modal h2 { color:var(--accent); font-size:1.05em; margin-bottom:14px; font-weight:600; }
.modal .form-row { display:flex; align-items:center; gap:10px; margin-bottom:10px; }
.modal .form-row label { font-size:.82em; color:var(--text-muted); min-width:60px; text-align:right; }
.modal .form-row input, .modal .form-row select { flex:1; padding:7px 10px; background:var(--bg); border:1px solid var(--border); color:var(--text); font-family:inherit; font-size:.85em; border-radius:6px; }
.modal .form-row input:focus, .modal .form-row select:focus { outline:none; border-color:var(--accent); }
.modal textarea { width:100%; height:160px; padding:10px; background:var(--bg); border:1px solid var(--border); color:var(--text); font-family:"SF Mono",Consolas,monospace; font-size:12px; border-radius:6px; resize:vertical; margin-top:8px; }
.modal textarea:focus { outline:none; border-color:var(--accent); }
.modal .btn-row { display:flex; gap:8px; margin-top:14px; }

main { height:calc(100vh - 51px); overflow-y:auto; }
</style>
</head>
<body>
<script type="module">
import { h, render, Fragment } from 'https://esm.sh/preact@10.25.4';
import { useState, useEffect, useRef, useCallback, useMemo } from 'https://esm.sh/preact@10.25.4/hooks';
import htm from 'https://esm.sh/htm@3.1.1';
const html = htm.bind(h);

/* ── Helpers ── */
const ENG = {inform7:'I7',zmachine:'Z',ink:'Ink',wwwbasic:'wwwBASIC',qbjc:'qbjc',applesoft:'Apple',bwbasic:'bwBASIC',jsdos:'DOS',twine:'Twine',sharpee:'Sharpee',rez:'Rez',unknown:'?'};
const BLBL = {present:'DONE',missing:'\u2014',stale:'STALE',failed:'FAIL','n/a':'n/a'};
const BCLS = {present:'badge-present',missing:'badge-missing',stale:'badge-stale',failed:'badge-failed','n/a':'badge-na'};
const NCLS = {present:'dag-node-present',missing:'dag-node-missing',stale:'dag-node-stale',failed:'dag-node-failed','n/a':'dag-node-na'};

function fileUrl(p){if(!p)return'';p=p.replace(/\\/g,'/');if(!p.startsWith('/'))p='/'+p;return'file://'+p;}
function esc(s){return(s||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');}

/* ── Badge ── */
function Badge({status,detail,onClick}){
  const label=BLBL[status]||status, cls=BCLS[status]||'badge-missing';
  return html`<span class="badge ${cls}" title=${detail||''} onClick=${e=>{e.stopPropagation();onClick&&onClick();}}>${label}</span>`;
}

/* ── DAG Node ── */
function DagNode({name,detail,linkUrl,status,running,onRunTo,onRunOnly}){
  const ncls = running ? 'dag-node-running' : (NCLS[status]||'dag-node-missing');
  const bLabel=BLBL[status]||status, bCls=BCLS[status]||'badge-missing';
  const forceRef=useRef(null);

  const parts=(detail||'').split(' \u00b7 ');
  const detailEl = linkUrl && parts.length>0
    ? html`<div class="node-detail"><a href=${linkUrl} onClick=${e=>e.stopPropagation()}>${parts[0]}</a>${parts.length>1?' \u00b7 '+parts.slice(1).join(' \u00b7 '):''}</div>`
    : detail ? html`<div class="node-detail">${detail}</div>` : null;

  return html`<div class="dag-node ${ncls}">
    <div class="node-head">
      <span class="node-name">${name}</span>
      <span class="node-badge ${bCls}">${bLabel}</span>
    </div>
    ${detailEl}
    ${onRunTo && html`<div class="node-btns">
      <button class="btn" onClick=${e=>{e.stopPropagation();onRunTo(forceRef.current?.checked);}}>${name}</button>
      ${onRunOnly && html`<a class="only-link" onClick=${e=>{e.stopPropagation();onRunOnly(forceRef.current?.checked);}}>only</a>`}
      <span class="spacer" />
      <label class="force-label" onClick=${e=>e.stopPropagation()}><input type="checkbox" ref=${forceRef} /> Force</label>
    </div>`}
  </div>`;
}

/* ── Connector ── */
function Conn({type,style}){
  if(type==='straight') return html`<div class="dag-connector" style=${style}><div class="conn-straight" /></div>`;
  if(type==='fork') return html`<div class="dag-connector"><div class="conn-branch conn-fork"><div class="conn-fork-left"/><div class="conn-fork-right"/></div></div>`;
  if(type==='merge') return html`<div class="dag-connector"><div class="conn-branch conn-merge"><div class="conn-merge-left"/><div class="conn-merge-right"/><div class="conn-merge-down"/></div></div>`;
  return null;
}

/* ── Terminal — persistent, never unmounted while expanded ── */
function Terminal({game}){
  const termRef=useRef(null);
  const [status,setStatus]=useState({cls:'',text:''});
  const [running,setRunning]=useState(false);

  // Expose imperative API via window so run() can drive it
  useEffect(()=>{
    const api={
      clear(){if(termRef.current)termRef.current.textContent='';setStatus({cls:'',text:''});},
      append(text){if(termRef.current){termRef.current.textContent+=text;termRef.current.scrollTop=termRef.current.scrollHeight;}},
      setStatus(cls,text){setStatus({cls,text});},
      setRunning(v){setRunning(v);},
    };
    window.__term=window.__term||{};
    window.__term[game]=api;
    return ()=>{if(window.__term)delete window.__term[game];};
  },[game]);

  const stop=useCallback(async()=>{
    if(window.__curJob){await fetch('/api/stop/'+window.__curJob,{method:'POST'});}
  },[]);

  const clear=useCallback(()=>{
    if(termRef.current)termRef.current.textContent='';
    setStatus({cls:'',text:''});
  },[]);

  return html`<div>
    <div class="output-bar">
      <h4>Output</h4>
      <span class="job-status ${status.cls}">${status.text}</span>
      <div class="output-btns">
        <button class="btn" disabled=${!running} onClick=${stop}>Stop</button>
        <button class="btn" onClick=${clear}>Clear</button>
      </div>
    </div>
    <pre class="term" ref=${termRef} />
  </div>`;
}

/* ── DAG panel ── */
function DAG({project,onAction,runningSteps}){
  const a=project.artifacts, hasTests=a.tests&&a.tests.status!=='n/a';
  const rs=runningSteps||[];
  // onRunTo: run all steps up to this one; onRunOnly: run just this step
  const runTo=(step,force)=>onAction('run-to',project,force,{target:step});
  const runOnly=(step,force)=>onAction(step,project,force);

  return html`<div class="dag">
    <${DagNode} name="Source" detail=${project.sourceFile||'n/a'} linkUrl=${project.sourceFile?fileUrl(project.dir+'/'+project.sourceFile):''} status="present" />
    <${Conn} type="fork" />
    <div class="dag-row">
      <${DagNode} name="Build" detail=${a.build.detail} linkUrl=${a.build.path?fileUrl(a.build.path):''} status=${a.build.status} running=${rs.includes('build')} onRunTo=${f=>runTo('build',f)} onRunOnly=${f=>runOnly('build',f)} />
      <${DagNode} name="Pages" detail=${a.pages.detail} linkUrl=${a.pages.path?fileUrl(a.pages.path):''} status=${a.pages.status} running=${rs.includes('pages')} onRunTo=${f=>runTo('pages',f)} onRunOnly=${f=>runOnly('pages',f)} />
    </div>
    ${hasTests && html`<${Fragment}>
      <${Conn} type="straight" style=${{}} />
      <div class="dag-row">
        <${DagNode} name="Tests" detail=${a.tests.detail} status=${a.tests.status} running=${rs.includes('test')} onRunTo=${f=>runTo('test',f)} onRunOnly=${f=>runOnly('test',f)} />
        <div />
      </div>
    </${Fragment}>`}
    <${Conn} type="merge" />
    <${DagNode} name="Ship" detail=${a.shipped.detail} status=${a.shipped.status} running=${rs.includes('ship')} onRunTo=${f=>runTo('ship',f)} onRunOnly=${f=>runOnly('ship',f)} />
    <${Conn} type="straight" />
    <${DagNode} name="Register" detail=${a.registered.detail} status=${a.registered.status} running=${rs.includes('register')} onRunTo=${f=>runTo('register',f)} onRunOnly=${f=>runOnly('register',f)} />
    <${Conn} type="straight" />
    <button class="btn btn-primary" style=${{width:'100%',marginTop:'4px'}} onClick=${e=>{e.stopPropagation();runTo('register',false);}}>Ship All</button>
  </div>`;
}

/* ── Meta form ── */
function MetaForm({project,formRef}){
  const p=project;
  const t=p.title||p.name.replace(/[-_]/g,' ').replace(/\b\w/g,c=>c.toUpperCase());
  const m=p.meta||'An Interactive Fiction';
  const d=p.description||'An interactive fiction game.';
  return html`<div class="meta-form" ref=${formRef}>
    <label>Title</label><input type="text" name="title" defaultValue=${t} />
    <label>Sub</label><input type="text" name="meta" defaultValue=${m} />
    <label>Desc</label><input type="text" name="description" defaultValue=${d} />
    <span class="chk"><input type="checkbox" name="sound" defaultChecked=${p.sound} /> Sound</span>
  </div>`;
}

/* ── Expanded row content ── */
function ExpandedContent({project,onAction,runningSteps}){
  const formRef=useRef(null);

  const handleAction=useCallback((action,proj,force,extra)=>{
    const form=formRef.current;
    const meta={};
    if(form){
      meta.title=form.querySelector('[name=title]')?.value||'';
      meta.meta=form.querySelector('[name=meta]')?.value||'';
      meta.description=form.querySelector('[name=description]')?.value||'';
      meta.sound=form.querySelector('[name=sound]')?.checked||false;
    }
    onAction(action,proj.name,force,{...meta,...(extra||{})});
  },[onAction]);

  return html`<div class="expanded-content">
    <div class="expanded-left">
      <${DAG} project=${project} onAction=${handleAction} runningSteps=${runningSteps} />
    </div>
    <div class="expanded-right">
      <${MetaForm} project=${project} formRef=${formRef} />
      <${Terminal} game=${project.name} key=${project.name} />
    </div>
  </div>`;
}

/* ── Pipeline step order (mirrors backend PIPELINE_ORDER) ── */
const STEPS=['build','pages','test','ship','register'];

/* ── Main App ── */
function App(){
  const [projects,setProjects]=useState([]);
  const [expanded,setExpanded]=useState(null);
  const [showModal,setShowModal]=useState(false);
  const [runningSteps,setRunningSteps]=useState([]);  // steps currently executing

  const fetchProjects=useCallback(async()=>{
    const r=await fetch('/api/projects');
    setProjects(await r.json());
  },[]);

  useEffect(()=>{fetchProjects();},[]);

  // Compute which pipeline steps a task will touch (for the running animation)
  const computeRunningSteps=useCallback((action,meta,game)=>{
    if(action==='run-to'||action==='ship-all'){
      const target=meta?.target||'register';
      const idx=STEPS.indexOf(target);
      return idx>=0?STEPS.slice(0,idx+1):[target];
    }
    return [action];
  },[]);

  const runTask=useCallback(async(action,game,force,meta)=>{
    setExpanded(game);
    await new Promise(r=>setTimeout(r,60));

    // Show running animation on affected steps
    const steps=computeRunningSteps(action,meta,game);
    setRunningSteps(steps);

    const api=window.__term&&window.__term[game];
    if(api){api.clear();api.setRunning(true);api.setStatus('job-status st-run','Running...');}

    const body={task:action,game,force:!!force,...(meta||{})};
    const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data=await r.json();

    if(data.error){
      if(api){api.append('[ERROR] '+data.error+'\n');api.setStatus('job-status st-err','Error');api.setRunning(false);}
      setRunningSteps([]);
      return;
    }

    window.__curJob=data.jobId;
    if(api)data.commands.forEach(c=>api.append('$ '+c+'\n'));
    if(api)api.append('\n');

    const es=new EventSource('/api/stream/'+data.jobId);

    es.onmessage=e=>{
      const d=JSON.parse(e.data);
      if(d.line&&api)api.append(d.line.replace(/\x1b\[[0-9;]*m/g,''));
    };

    es.addEventListener('done',e=>{
      const d=JSON.parse(e.data);
      es.close();window.__curJob=null;
      setRunningSteps([]);
      if(api){
        api.setRunning(false);
        if(d.status==='done')api.setStatus('job-status st-done','Done');
        else api.setStatus('job-status st-err','Failed (exit '+d.exitCode+')');
      }
      fetchProjects();
    });

    es.onerror=()=>{es.close();window.__curJob=null;setRunningSteps([]);if(api)api.setRunning(false);};
  },[fetchProjects,computeRunningSteps]);

  const shipAll=useCallback((game,force,meta)=>{
    runTask('run-to',game,force,{...(meta||{}),target:'register'});
  },[runTask]);

  const badgeClick=useCallback((action,game)=>{
    const p=projects.find(x=>x.name===game);
    const meta=p?{title:p.title,meta:p.meta,description:p.description,sound:p.sound}:{};
    runTask(action,game,false,meta);
  },[projects,runTask]);

  const toggleRow=useCallback(name=>{
    setExpanded(prev=>prev===name?null:name);
  },[]);

  return html`<div>
    <header>
      <h1>IF Hub</h1>
      <span class="sub">Dashboard</span>
      <span class="spacer" />
      <button class="hdr-btn" onClick=${()=>setShowModal(true)}>+ New Game</button>
      <button class="hdr-btn" onClick=${fetchProjects}>Refresh</button>
    </header>
    <main>
      <table class="matrix">
        <thead><tr>
          <th class="col-game">Game</th><th class="col-engine">Engine</th>
          <th class="col-status">Build</th><th class="col-status">Pages</th>
          <th class="col-status">Tests</th><th class="col-status">Ship</th>
          <th class="col-status">Hub</th><th class="col-actions">Actions</th>
        </tr></thead>
        <tbody>
          ${projects.map(p=>{
            const a=p.artifacts;
            const isExp=expanded===p.name;
            return html`<${Fragment} key=${p.name}>
              <tr class=${isExp?'row-sel':''} onClick=${e=>{if(!e.target.closest('.badge,.btn,.force-label'))toggleRow(p.name);}}>
                <td><a class="game-name" href=${fileUrl(p.dir)} title=${p.dir} onClick=${e=>e.stopPropagation()}>${p.name}</a></td>
                <td><span class="engine-tag">${ENG[p.engine]||p.engine}</span></td>
                <td><${Badge} status=${a.build.status} detail=${a.build.detail} onClick=${()=>badgeClick('build',p.name)} /></td>
                <td><${Badge} status=${a.pages.status} detail=${a.pages.detail} onClick=${()=>badgeClick('pages',p.name)} /></td>
                <td><${Badge} status=${a.tests.status} detail=${a.tests.detail} onClick=${()=>badgeClick('test',p.name)} /></td>
                <td><${Badge} status=${a.shipped.status} detail=${a.shipped.detail} onClick=${()=>badgeClick('ship',p.name)} /></td>
                <td><${Badge} status=${a.registered.status} detail=${a.registered.detail} onClick=${()=>badgeClick('register',p.name)} /></td>
                <td>
                  <button class="btn btn-primary" disabled=${p.overallStatus==='ready'} onClick=${e=>{e.stopPropagation();shipAll(p.name);}}>Ship All</button>
                  ${' '}<label class="force-label" onClick=${e=>e.stopPropagation()}><input type="checkbox" id=${'force-row-'+p.name} /> Force</label>
                </td>
              </tr>
              ${isExp && html`<tr class="expanded-row"><td colSpan="8">
                <${ExpandedContent} project=${p} onAction=${runTask} runningSteps=${runningSteps} />
              </td></tr>`}
            </${Fragment}>`;
          })}
        </tbody>
      </table>
    </main>
    ${showModal && html`<${CreateModal} onClose=${()=>setShowModal(false)} onCreated=${async(name)=>{await fetchProjects();setExpanded(name);}} />`}
  </div>`;
}

/* ── Create modal ── */
function CreateModal({onClose,onCreated}){
  const [name,setName]=useState('');
  const [engine,setEngine]=useState('inform7');
  const [source,setSource]=useState('');

  const create=async()=>{
    if(!name.trim()){alert('Enter a game name.');return;}
    const r=await fetch('/api/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:name.trim(),source,engine})});
    const data=await r.json();
    if(data.error){alert(data.error);return;}
    onClose();
    onCreated(name.trim());
  };

  return html`<div class="overlay show" onClick=${e=>{if(e.target===e.currentTarget)onClose();}}>
    <div class="modal">
      <h2>New Game</h2>
      <div class="form-row"><label>Name</label><input type="text" value=${name} onInput=${e=>setName(e.target.value)} placeholder="my-game" /></div>
      <div class="form-row"><label>Engine</label><select value=${engine} onChange=${e=>setEngine(e.target.value)}>
        <option value="inform7">Inform 7</option><option value="ink">Ink</option>
        <option value="wwwbasic">wwwBASIC</option><option value="qbjc">qbjc</option>
        <option value="applesoft">Applesoft</option><option value="sharpee">Sharpee</option>
        <option value="rez">Rez</option>
      </select></div>
      <label style="font-size:.82em;color:var(--text-muted)">Source (optional)</label>
      <textarea value=${source} onInput=${e=>setSource(e.target.value)} placeholder="Paste source code or leave blank..." />
      <div class="btn-row">
        <button class="btn btn-primary" onClick=${create}>Create</button>
        <button class="btn" onClick=${onClose}>Cancel</button>
      </div>
    </div>
  </div>`;
}

/* ── Mount ── */
render(html`<${App} />`, document.body);
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

    threading.Thread(
        target=lambda: (time.sleep(1), webbrowser.open(url)),
        daemon=True,
    ).start()

    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
