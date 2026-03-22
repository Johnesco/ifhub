#!/usr/bin/env python3
"""Synth Lab -- Procedural Ambient Noise & Music Maker.

Usage:
    pip install flask
    python tools/synth.py [--port 5001]

Browser-based synthesizer for creating ambient soundscapes, drones,
and sound effects. Exports .ogg (Vorbis) via FFmpeg.

Hierarchy:
    Source (atom)    — oscillator, noise, or sample
    Voice (molecule) — source + filter + gain + LFO
    Generator (compound) — named group of voices = a recognizable sound
    Scene (ecosystem)    — mix of generators + globals = exportable soundscape
"""

import shutil
import subprocess
import sys
import threading
import time
import webbrowser

try:
    from flask import Flask, Response, jsonify, request
except ImportError:
    print("Missing dependency: Flask")
    print()
    print("  pip install flask")
    print()
    sys.exit(1)

# ---------------------------------------------------------------------------
# FFmpeg detection
# ---------------------------------------------------------------------------

FFMPEG = shutil.which("ffmpeg")
if not FFMPEG:
    print("WARNING: ffmpeg not found on PATH. Export to .ogg will not work.")
    print("Install FFmpeg: https://ffmpeg.org/download.html")

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


@app.route("/worklet/noise-processor.js")
def noise_worklet():
    return Response(NOISE_PROCESSOR_JS, mimetype="application/javascript")


@app.route("/api/convert", methods=["POST"])
def api_convert():
    """Convert WAV blob to Ogg Vorbis and return as download."""
    if not FFMPEG:
        return jsonify({"ok": False, "error": "ffmpeg not found on PATH"}), 500

    wav_data = request.files.get("wav")
    filename = request.form.get("filename", "sound.ogg")

    if not wav_data:
        return jsonify({"ok": False, "error": "No WAV data provided"}), 400
    if not filename.endswith(".ogg"):
        filename += ".ogg"

    try:
        proc = subprocess.run(
            [FFMPEG, "-y", "-i", "pipe:0",
             "-c:a", "libvorbis", "-q:a", "4", "-ar", "48000",
             "-f", "ogg", "pipe:1"],
            input=wav_data.read(),
            capture_output=True,
            timeout=60,
        )
        if proc.returncode != 0:
            return jsonify({
                "ok": False,
                "error": f"ffmpeg failed: {proc.stderr.decode(errors='replace')[:500]}"
            }), 500

        return Response(
            proc.stdout,
            mimetype="audio/ogg",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "ffmpeg timed out"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# AudioWorklet: Noise Processor
# ---------------------------------------------------------------------------

NOISE_PROCESSOR_JS = """
class NoiseProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    this.color = 'white';
    this.pinkRows = new Float64Array(16).fill(0);
    this.pinkRunning = 0;
    this.pinkIndex = 0;
    this.brownLast = 0;
    this.port.onmessage = (e) => {
      if (e.data.color) this.color = e.data.color;
    };
  }

  process(inputs, outputs, parameters) {
    const output = outputs[0];
    for (let ch = 0; ch < output.length; ch++) {
      const buf = output[ch];
      for (let i = 0; i < buf.length; i++) buf[i] = this._sample();
    }
    return true;
  }

  _sample() {
    switch (this.color) {
      case 'pink': return this._pink();
      case 'brown': return this._brown();
      default: return Math.random() * 2 - 1;
    }
  }

  _pink() {
    const idx = this.pinkIndex++;
    const lastIdx = idx - 1;
    for (let i = 0; i < 16; i++) {
      if ((idx & (1 << i)) !== (lastIdx & (1 << i))) {
        const oldVal = this.pinkRows[i];
        const newVal = Math.random() * 2 - 1;
        this.pinkRunning += newVal - oldVal;
        this.pinkRows[i] = newVal;
      }
    }
    return (this.pinkRunning + Math.random() * 2 - 1) / 8;
  }

  _brown() {
    const white = Math.random() * 2 - 1;
    this.brownLast = (this.brownLast + (0.02 * white)) / 1.02;
    return this.brownLast * 3.5;
  }
}
registerProcessor('noise-processor', NoiseProcessor);
"""

# ---------------------------------------------------------------------------
# HTML / CSS / JS
# ---------------------------------------------------------------------------

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Synth Lab</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0e1117;
  --bg-sidebar: #0b0e14;
  --bg-card: #151922;
  --bg-voice: #1a1f2b;
  --bg-selected: #1a2030;
  --border: #1e2535;
  --border-accent: #2a3548;
  --text: #c8cdd8;
  --text-muted: #7b8598;
  --text-dim: #4a5468;
  --accent: #6eb5ff;
  --accent-hover: #8ec8ff;
  --heading: #94a3ba;
  --terminal-bg: #080b10;
  --green: #5cb890;
  --red: #e05565;
  --yellow: #d4a843;
  --orange: #d08050;
  --muted-bg: #12151c;
  --solo-color: #d4a843;
  --slider-track: #1e2535;
  --slider-thumb: #6eb5ff;
}

html, body { height: 100%; overflow: hidden; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  display: flex;
  font-size: 13px;
}

/* --- Sidebar --- */
.sidebar {
  width: 250px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  padding: 14px 10px;
  flex-shrink: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.sidebar h1 {
  color: var(--accent);
  font-size: 1.15em;
  font-weight: 600;
  letter-spacing: 0.03em;
  border-bottom: 1px solid var(--border);
  padding-bottom: 8px;
}
.sidebar h2 {
  color: var(--heading);
  font-size: 0.72em;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 600;
  margin-bottom: 3px;
}
.sidebar-section { display: flex; flex-direction: column; gap: 3px; }

/* Project controls */
.project-controls { display: flex; flex-direction: column; gap: 5px; }
.project-name-input {
  background: var(--bg-card);
  color: var(--text);
  border: 1px solid var(--border-accent);
  padding: 5px 7px;
  border-radius: 4px;
  font-family: inherit;
  font-size: 0.88em;
  width: 100%;
}
.project-btn-row { display: flex; gap: 3px; flex-wrap: wrap; }
.saved-projects { display: flex; flex-direction: column; gap: 1px; max-height: 100px; overflow-y: auto; }
.saved-project-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 3px 7px; border-radius: 3px; font-size: 0.82em;
  color: var(--text-muted); cursor: pointer; transition: background 0.1s;
}
.saved-project-item:hover { background: var(--bg-selected); color: var(--text); }
.saved-project-item .del { color: var(--text-dim); cursor: pointer; padding: 0 3px; font-size: 1.1em; }
.saved-project-item .del:hover { color: var(--red); }

/* Preset tree */
.preset-list { display: flex; flex-direction: column; gap: 1px; }
.preset-item { border-radius: 4px; overflow: hidden; }
.preset-header {
  display: flex; align-items: center; padding: 4px 7px; cursor: pointer;
  font-size: 0.82em; color: var(--text-muted); transition: background 0.1s; gap: 5px;
}
.preset-header:hover { background: var(--bg-selected); color: var(--text); }
.preset-header .arrow { font-size: 0.65em; transition: transform 0.15s; color: var(--text-dim); width: 10px; }
.preset-item.expanded .preset-header .arrow { transform: rotate(90deg); }
.preset-header .name { flex: 1; }
.preset-header .add-all {
  color: var(--accent); font-size: 0.72em; font-weight: 600;
  opacity: 0; transition: opacity 0.1s; padding: 1px 5px;
  border: 1px solid var(--accent); border-radius: 3px;
}
.preset-header:hover .add-all { opacity: 1; }
.preset-gens { display: none; padding: 0 3px 4px 16px; flex-direction: column; gap: 2px; }
.preset-item.expanded .preset-gens { display: flex; }
.preset-gen-row {
  display: flex; align-items: center; gap: 5px; font-size: 0.78em;
  color: var(--text-dim); padding: 2px 5px; border-radius: 3px;
  cursor: pointer; transition: background 0.1s;
}
.preset-gen-row:hover { background: var(--bg-selected); color: var(--text-muted); }
.preset-gen-row .add-one { color: var(--green); font-weight: bold; }

/* Generator library */
.gen-lib-item {
  display: flex; align-items: center; gap: 5px; padding: 3px 7px;
  border-radius: 3px; font-size: 0.82em; color: var(--text-muted);
  cursor: pointer; transition: background 0.1s;
}
.gen-lib-item:hover { background: var(--bg-selected); color: var(--text); }
.gen-lib-item .add-one { color: var(--green); font-weight: bold; }
.gen-lib-item .del { color: var(--text-dim); cursor: pointer; padding: 0 3px; margin-left: auto; }
.gen-lib-item .del:hover { color: var(--red); }

/* SFX files */
.sfx-list { display: flex; flex-direction: column; gap: 2px; }
.sfx-item { display: flex; align-items: center; gap: 5px; padding: 3px 7px; border-radius: 3px; font-size: 0.78em; color: var(--text-muted); }
.sfx-item .name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sfx-item .play-sfx {
  background: none; border: 1px solid var(--border-accent); color: var(--green);
  width: 22px; height: 20px; border-radius: 3px; cursor: pointer; font-size: 0.85em;
  display: flex; align-items: center; justify-content: center;
}
.sfx-item .play-sfx:hover { background: var(--bg-selected); border-color: var(--green); }
.sfx-item .remove-sfx { background: none; border: none; color: var(--text-dim); cursor: pointer; font-size: 1em; padding: 0 2px; }
.sfx-item .remove-sfx:hover { color: var(--red); }

/* Buttons */
.btn-small {
  background: none; border: 1px solid var(--border-accent); color: var(--text-muted);
  padding: 3px 7px; border-radius: 4px; cursor: pointer; font-family: inherit;
  font-size: 0.72em; transition: all 0.1s; white-space: nowrap;
}
.btn-small:hover { background: var(--bg-selected); color: var(--accent); border-color: var(--accent); }

/* Main */
.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.content { flex: 1; display: flex; overflow: hidden; }

/* Generator panel */
.gen-panel {
  flex: 1; overflow-y: auto; padding: 12px;
  display: flex; flex-direction: column; gap: 10px;
}
.gen-toolbar { display: flex; gap: 5px; align-items: center; flex-wrap: wrap; }
.gen-toolbar h3 { color: var(--heading); font-size: 0.78em; text-transform: uppercase; letter-spacing: 0.06em; margin-right: 6px; }

/* Generator card */
.generator-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}
.generator-card.muted { opacity: 0.45; }
.generator-card.soloed { border-color: var(--solo-color); }

.gen-header {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 10px;
  border-bottom: 1px solid var(--border);
  background: rgba(255,255,255,0.015);
}
.gen-collapse {
  cursor: pointer; color: var(--text-dim); font-size: 0.7em;
  width: 14px; transition: transform 0.15s; user-select: none;
}
.generator-card.collapsed .gen-collapse { transform: rotate(-90deg); }
.gen-name-input {
  background: transparent; border: none; color: var(--heading);
  font-family: inherit; font-size: 0.9em; font-weight: 500;
  width: 0; flex: 1; min-width: 60px;
  padding: 2px 4px; border-radius: 3px;
}
.gen-name-input:focus { background: var(--bg); outline: 1px solid var(--border-accent); }

.gen-btn {
  background: none; border: 1px solid var(--border); color: var(--text-dim);
  width: 24px; height: 22px; border-radius: 3px; cursor: pointer;
  font-size: 0.7em; font-weight: 700; display: flex;
  align-items: center; justify-content: center; font-family: inherit;
}
.gen-btn:hover { border-color: var(--text-muted); color: var(--text-muted); }
.gen-btn.mute-active { background: var(--red); color: var(--bg); border-color: var(--red); }
.gen-btn.solo-active { background: var(--solo-color); color: var(--bg); border-color: var(--solo-color); }

.gen-gain-slider {
  width: 70px; -webkit-appearance: none; appearance: none;
  height: 3px; background: var(--slider-track); border-radius: 2px; outline: none;
}
.gen-gain-slider::-webkit-slider-thumb {
  -webkit-appearance: none; appearance: none;
  width: 10px; height: 10px; background: var(--slider-thumb); border-radius: 50%; cursor: pointer;
}
.gen-gain-slider::-moz-range-thumb {
  width: 10px; height: 10px; background: var(--slider-thumb); border-radius: 50%; cursor: pointer; border: none;
}
.gen-gain-val { color: var(--text-dim); font-size: 0.75em; width: 30px; font-variant-numeric: tabular-nums; }

.gen-remove { background: none; border: 1px solid var(--border); color: var(--text-dim);
  width: 22px; height: 22px; border-radius: 3px; cursor: pointer; font-size: 0.9em;
  display: flex; align-items: center; justify-content: center;
}
.gen-remove:hover { border-color: var(--red); color: var(--red); }
.gen-save-lib { background: none; border: 1px solid var(--border); color: var(--text-dim);
  width: 22px; height: 22px; border-radius: 3px; cursor: pointer; font-size: 0.7em;
  display: flex; align-items: center; justify-content: center; title: "Save to library";
}
.gen-save-lib:hover { border-color: var(--green); color: var(--green); }

/* Voices inside generator */
.gen-voices { padding: 6px 8px 8px 8px; display: flex; flex-direction: column; gap: 6px; }
.generator-card.collapsed .gen-voices { display: none; }

.voice-card {
  background: var(--bg-voice);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 8px 10px;
}
.voice-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;
}
.voice-header select {
  background: var(--bg); color: var(--text); border: 1px solid var(--border-accent);
  padding: 2px 5px; border-radius: 3px; font-family: inherit; font-size: 0.82em;
}
.voice-remove {
  background: none; border: 1px solid var(--border); color: var(--text-dim);
  width: 20px; height: 20px; border-radius: 3px; cursor: pointer; font-size: 0.8em;
  display: flex; align-items: center; justify-content: center;
}
.voice-remove:hover { border-color: var(--red); color: var(--red); }

.add-voice-btn {
  background: none; border: 1px dashed var(--border-accent); color: var(--text-dim);
  padding: 4px; border-radius: 4px; cursor: pointer; font-family: inherit;
  font-size: 0.78em; text-align: center; transition: all 0.1s;
}
.add-voice-btn:hover { border-color: var(--accent); color: var(--accent); }

.add-gen-btn {
  background: var(--bg-card); border: 1px dashed var(--border-accent);
  color: var(--text-muted); padding: 10px; border-radius: 6px; cursor: pointer;
  font-family: inherit; font-size: 0.85em; text-align: center; transition: all 0.1s;
}
.add-gen-btn:hover { border-color: var(--accent); color: var(--accent); background: var(--bg-selected); }

/* Voice params */
.param-row { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.param-row label { width: 60px; color: var(--text-muted); font-size: 0.78em; text-align: right; flex-shrink: 0; }
.param-row input[type="range"] {
  flex: 1; -webkit-appearance: none; appearance: none;
  height: 3px; background: var(--slider-track); border-radius: 2px; outline: none;
}
.param-row input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none; appearance: none;
  width: 10px; height: 10px; background: var(--slider-thumb); border-radius: 50%; cursor: pointer;
}
.param-row input[type="range"]::-moz-range-thumb {
  width: 10px; height: 10px; background: var(--slider-thumb); border-radius: 50%; cursor: pointer; border: none;
}
.param-row .value { width: 55px; color: var(--text-dim); font-size: 0.78em; flex-shrink: 0; font-variant-numeric: tabular-nums; }
.param-row select {
  background: var(--bg); color: var(--text); border: 1px solid var(--border-accent);
  padding: 2px 5px; border-radius: 3px; font-family: inherit; font-size: 0.82em;
}
.lfo-section { margin-top: 4px; padding-top: 4px; border-top: 1px solid var(--border); }
.lfo-section .section-label { color: var(--text-dim); font-size: 0.68em; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 3px; font-weight: 600; }

/* Right panel */
.right-panel { width: 270px; border-left: 1px solid var(--border); display: flex; flex-direction: column; flex-shrink: 0; }
.viz-section { padding: 8px 10px; border-bottom: 1px solid var(--border); }
.viz-section h3 { color: var(--text-dim); font-size: 0.68em; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 3px; font-weight: 600; }
.viz-section canvas { width: 100%; height: 50px; background: var(--terminal-bg); border-radius: 4px; display: block; }
.globals-section { padding: 8px 10px; border-bottom: 1px solid var(--border); display: flex; flex-direction: column; gap: 3px; }
.globals-section h3 { color: var(--text-dim); font-size: 0.68em; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 1px; font-weight: 600; }
.transport { padding: 8px 10px; display: flex; flex-direction: column; gap: 5px; }
.transport h3 { color: var(--text-dim); font-size: 0.68em; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 1px; font-weight: 600; }
.transport-buttons { display: flex; gap: 5px; flex-wrap: wrap; }
.btn {
  background: var(--bg-card); border: 1px solid var(--border-accent); color: var(--text);
  padding: 6px 12px; border-radius: 4px; cursor: pointer; font-family: inherit;
  font-size: 0.82em; transition: all 0.1s;
}
.btn:hover { background: var(--bg-selected); border-color: var(--accent); color: var(--accent); }
.btn.active { background: var(--accent); color: var(--bg); border-color: var(--accent); }
.btn.primary { border-color: var(--green); color: var(--green); }
.btn.primary:hover { background: var(--green); color: var(--bg); }
.btn.danger { border-color: var(--red); color: var(--red); }
.btn.danger:hover { background: var(--red); color: var(--bg); }
.export-section {
  padding: 8px 10px; border-top: 1px solid var(--border);
  display: flex; flex-direction: column; gap: 5px; margin-top: auto;
}
.export-section h3 { color: var(--text-dim); font-size: 0.68em; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
.export-row { display: flex; gap: 5px; align-items: center; }
.export-row input {
  flex: 1; background: var(--bg-card); color: var(--text); border: 1px solid var(--border-accent);
  padding: 4px 7px; border-radius: 4px; font-family: inherit; font-size: 0.82em;
}
.status-msg { font-size: 0.78em; padding: 2px 0; min-height: 1.1em; }
.status-msg.ok { color: var(--green); }
.status-msg.err { color: var(--red); }
.status-msg.working { color: var(--yellow); }

.toast {
  position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%) translateY(50px);
  background: var(--bg-card); border: 1px solid var(--green); color: var(--green);
  padding: 6px 16px; border-radius: 6px; font-size: 0.82em;
  opacity: 0; transition: transform 0.2s ease, opacity 0.2s ease;
  pointer-events: none; z-index: 100;
}
.toast.show { transform: translateX(-50%) translateY(0); opacity: 1; }
.hidden-input { display: none; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-accent); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-dim); }
</style>
</head>
<body>

<div class="sidebar">
  <h1>Synth Lab</h1>

  <div class="sidebar-section">
    <h2>Scene</h2>
    <div class="project-controls">
      <input type="text" class="project-name-input" id="project-name" placeholder="Untitled" value="Untitled">
      <div class="project-btn-row">
        <button class="btn-small" id="project-new">New</button>
        <button class="btn-small" id="project-save">Save</button>
        <button class="btn-small" id="project-export-json">Export</button>
        <button class="btn-small" id="project-import-json">Import</button>
      </div>
      <div class="saved-projects" id="saved-projects"></div>
    </div>
    <input type="file" class="hidden-input" id="import-json-input" accept=".json">
  </div>

  <div class="sidebar-section">
    <h2>Ambient Scenes</h2>
    <div class="preset-list" id="ambient-presets"></div>
  </div>
  <div class="sidebar-section">
    <h2>Effect Generators</h2>
    <div class="preset-list" id="sfx-presets"></div>
  </div>
  <div class="sidebar-section">
    <h2>Custom Scenes</h2>
    <div class="preset-list" id="custom-presets"></div>
    <button class="btn-small" id="save-preset-btn" style="margin-top:3px">Save Scene as Preset</button>
  </div>

  <div class="sidebar-section">
    <h2>Generator Library</h2>
    <div id="gen-library"></div>
  </div>

  <div class="sidebar-section" style="margin-top:auto">
    <h2>Sound Files</h2>
    <div class="sfx-list" id="sfx-files"></div>
    <button class="btn-small" id="import-sfx-btn" style="margin-top:3px">Import Audio</button>
    <input type="file" class="hidden-input" id="sfx-file-input" accept="audio/*" multiple>
  </div>
</div>

<div class="main">
  <div class="content">
    <div class="gen-panel" id="gen-panel">
      <div class="gen-toolbar">
        <h3>Generators</h3>
        <button class="btn-small" id="clear-all-btn">Clear All</button>
      </div>
      <button class="add-gen-btn" id="add-gen-btn">+ Add Generator</button>
    </div>

    <div class="right-panel">
      <div class="viz-section">
        <h3>Waveform</h3>
        <canvas id="waveform-canvas" width="250" height="50"></canvas>
      </div>
      <div class="viz-section">
        <h3>Spectrum</h3>
        <canvas id="spectrum-canvas" width="250" height="50"></canvas>
      </div>
      <div class="globals-section">
        <h3>Globals</h3>
        <div class="param-row"><label>Duration</label><input type="range" id="g-duration" min="1" max="120" value="30" step="1"><span class="value" id="g-duration-val">30s</span></div>
        <div class="param-row"><label>Fade In</label><input type="range" id="g-fade-in" min="0" max="5" value="1" step="0.1"><span class="value" id="g-fade-in-val">1.0s</span></div>
        <div class="param-row"><label>Fade Out</label><input type="range" id="g-fade-out" min="0" max="5" value="1" step="0.1"><span class="value" id="g-fade-out-val">1.0s</span></div>
        <div class="param-row"><label>Reverb</label><input type="range" id="g-reverb" min="0" max="1" value="0.2" step="0.01"><span class="value" id="g-reverb-val">0.20</span></div>
        <div class="param-row"><label>Master</label><input type="range" id="g-master" min="0" max="1" value="0.7" step="0.01"><span class="value" id="g-master-val">0.70</span></div>
      </div>
      <div class="transport">
        <h3>Transport</h3>
        <div class="transport-buttons">
          <button class="btn primary" id="play-btn">Play</button>
          <button class="btn danger" id="stop-btn">Stop</button>
          <button class="btn" id="loop-btn">Loop</button>
        </div>
      </div>
      <div class="export-section">
        <h3>Download</h3>
        <div class="export-row"><input type="text" id="export-filename" placeholder="filename.ogg" value="sound.ogg"></div>
        <div class="transport-buttons">
          <button class="btn primary" id="download-ogg-btn">Download .ogg</button>
          <button class="btn" id="download-wav-btn">Download .wav</button>
        </div>
        <div class="status-msg" id="export-status"></div>
      </div>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const SynthLab = (() => {

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let audioCtx = null, masterGain = null, compressor = null;
let reverbNode = null, reverbGain = null, dryGain = null, analyser = null;
let isPlaying = false, isLooping = false, workletReady = false;
let activeGens = []; // { genGain, voiceNodes: [] }

let generators = [];
let genIdCounter = 0, voiceIdCounter = 0;
let globals = { duration: 30, fadeIn: 1.0, fadeOut: 1.0, reverb: 0.2, master: 0.7 };
let sfxFiles = [];

// ---------------------------------------------------------------------------
// Toast
// ---------------------------------------------------------------------------
let toastTimer = null;
function showToast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2000);
}

// ---------------------------------------------------------------------------
// AudioContext
// ---------------------------------------------------------------------------
async function ensureCtx() {
  if (audioCtx) return;
  audioCtx = new AudioContext({ sampleRate: 48000 });
  try { await audioCtx.audioWorklet.addModule('/worklet/noise-processor.js'); workletReady = true; } catch(e) {}

  analyser = audioCtx.createAnalyser();
  analyser.fftSize = 2048;
  compressor = audioCtx.createDynamicsCompressor();
  compressor.threshold.value = -12; compressor.ratio.value = 4; compressor.knee.value = 10;
  masterGain = audioCtx.createGain();
  masterGain.gain.value = globals.master;
  dryGain = audioCtx.createGain();
  dryGain.gain.value = 1 - globals.reverb;
  reverbGain = audioCtx.createGain();
  reverbGain.gain.value = globals.reverb;
  reverbNode = audioCtx.createConvolver();
  reverbNode.buffer = makeReverbIR(audioCtx, 2.5, 0.8);

  dryGain.connect(compressor);
  reverbNode.connect(reverbGain);
  reverbGain.connect(compressor);
  compressor.connect(analyser);
  analyser.connect(masterGain);
  masterGain.connect(audioCtx.destination);
}

function makeReverbIR(ctx, dur, decay) {
  const len = ctx.sampleRate * dur;
  const buf = ctx.createBuffer(2, len, ctx.sampleRate);
  for (let ch = 0; ch < 2; ch++) {
    const d = buf.getChannelData(ch);
    for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, decay * 3);
  }
  return buf;
}

// ---------------------------------------------------------------------------
// Voice node creation
// ---------------------------------------------------------------------------
function createVoiceNodes(voice) {
  const n = { source: null, filter: null, gain: null, lfo: null, lfoGain: null,
              _partials: null, _noiseSource: null, _isPassive: false,
              _burstInterval: null, _crackleInterval: null };

  n.gain = audioCtx.createGain();
  n.gain.gain.value = voice.gain;
  n.filter = audioCtx.createBiquadFilter();
  n.filter.type = voice.filterType;
  n.filter.frequency.value = voice.filterFreq;
  n.filter.Q.value = voice.filterQ;

  switch (voice.type) {
    case 'noise':
      if (workletReady) {
        n.source = new AudioWorkletNode(audioCtx, 'noise-processor');
        n.source.port.postMessage({ color: voice.noiseColor });
      } else { n.source = noiseFallback(audioCtx, voice.noiseColor); }
      break;
    case 'tone':
      n.source = audioCtx.createOscillator();
      n.source.type = voice.waveform;
      n.source.frequency.value = voice.frequency;
      n.source.detune.value = voice.detune;
      n.source.start();
      break;
    case 'harmonic': {
      const partials = voice.partials || [1,2,3,4,5];
      const merger = audioCtx.createGain();
      merger.gain.value = 1 / partials.length;
      n._partials = [];
      partials.forEach((p, i) => {
        const osc = audioCtx.createOscillator();
        osc.type = voice.waveform || 'sine';
        osc.frequency.value = (voice.frequency || 110) * p;
        const pg = audioCtx.createGain();
        pg.gain.value = 1 / (i + 1);
        osc.connect(pg); pg.connect(merger); osc.start();
        n._partials.push({ osc, gain: pg });
      });
      n.source = merger; n._isPassive = true;
      break;
    }
    case 'impulse': {
      const ns = workletReady ? new AudioWorkletNode(audioCtx, 'noise-processor') : noiseFallback(audioCtx, 'white');
      if (workletReady) ns.port.postMessage({ color: 'white' });
      const bg = audioCtx.createGain(); bg.gain.value = 0;
      ns.connect(bg);
      n.source = bg; n._noiseSource = ns; n._isPassive = true;
      const rate = voice.impulseRate || 2, decay = voice.impulseDecay || 0.1;
      n._burstInterval = setInterval(() => {
        const now = audioCtx.currentTime;
        bg.gain.cancelScheduledValues(now);
        bg.gain.setValueAtTime(1, now);
        bg.gain.exponentialRampToValueAtTime(0.001, now + decay);
      }, 1000 / rate);
      break;
    }
    case 'crackle': {
      const ns2 = workletReady ? new AudioWorkletNode(audioCtx, 'noise-processor') : noiseFallback(audioCtx, 'white');
      if (workletReady) ns2.port.postMessage({ color: 'white' });
      const cg = audioCtx.createGain(); cg.gain.value = 0;
      ns2.connect(cg);
      n.source = cg; n._noiseSource = ns2; n._isPassive = true;
      const dens = voice.crackleDensity || 8;
      n._crackleInterval = setInterval(() => {
        if (Math.random() < dens / 30) {
          const now = audioCtx.currentTime;
          cg.gain.cancelScheduledValues(now);
          cg.gain.setValueAtTime(0.8, now);
          cg.gain.exponentialRampToValueAtTime(0.001, now + 0.02);
        }
      }, 33);
      break;
    }
  }

  if (n.source) n.source.connect(n.filter);
  n.filter.connect(n.gain);
  // NOTE: caller connects n.gain -> generator gain node

  // LFO
  if (voice.lfoRate > 0 && voice.lfoDepth > 0) {
    n.lfo = audioCtx.createOscillator();
    n.lfo.frequency.value = voice.lfoRate;
    n.lfoGain = audioCtx.createGain();
    let target;
    switch (voice.lfoTarget) {
      case 'frequency': target = n.filter.frequency; n.lfoGain.gain.value = voice.lfoDepth * voice.filterFreq; break;
      case 'filter': target = n.filter.frequency; n.lfoGain.gain.value = voice.lfoDepth * voice.filterFreq; break;
      default: target = n.gain.gain; n.lfoGain.gain.value = voice.lfoDepth * voice.gain;
    }
    n.lfo.connect(n.lfoGain); n.lfoGain.connect(target); n.lfo.start();
  }
  return n;
}

function noiseFallback(ctx, color) {
  const bs = 4096;
  const proc = ctx.createScriptProcessor(bs, 0, 1);
  let bl = 0, pr = new Float64Array(16).fill(0), prun = 0, pidx = 0;
  proc.onaudioprocess = (e) => {
    const out = e.outputBuffer.getChannelData(0);
    for (let i = 0; i < bs; i++) {
      if (color === 'brown') { bl = (bl + 0.02*(Math.random()*2-1))/1.02; out[i]=bl*3.5; }
      else if (color === 'pink') {
        const idx = pidx++, li = idx-1;
        for (let j=0;j<16;j++) if((idx&(1<<j))!==(li&(1<<j))){ prun+=Math.random()*2-1-pr[j]; pr[j]=Math.random()*2-1; }
        out[i]=(prun+Math.random()*2-1)/8;
      } else out[i]=Math.random()*2-1;
    }
  };
  return proc;
}

function destroyVoiceNodes(n) {
  if (n._burstInterval) clearInterval(n._burstInterval);
  if (n._crackleInterval) clearInterval(n._crackleInterval);
  if (n._partials) n._partials.forEach(p => { try{p.osc.stop();}catch(e){} });
  if (n.lfo) try{n.lfo.stop();}catch(e){}
  if (n.source && !n._isPassive) try{n.source.stop();}catch(e){}
  if (n._noiseSource) try{n._noiseSource.disconnect();}catch(e){}
  ['source','filter','gain','lfo','lfoGain'].forEach(k => { if(n[k]) try{n[k].disconnect();}catch(e){} });
}

// ---------------------------------------------------------------------------
// Generator-level audio
// ---------------------------------------------------------------------------
function shouldGenPlay(gen) {
  const anySoloed = generators.some(g => g.solo);
  if (anySoloed) return gen.solo && !gen.muted;
  return !gen.muted;
}

function createGenAudio(gen) {
  const gg = audioCtx.createGain();
  gg.gain.value = shouldGenPlay(gen) ? gen.gain : 0;
  gg.connect(dryGain);
  gg.connect(reverbNode);

  const voiceNodes = gen.voices.map(v => {
    const vn = createVoiceNodes(v);
    vn.gain.connect(gg);
    return vn;
  });
  return { genGain: gg, voiceNodes };
}

function updateMuteSoloState() {
  generators.forEach((gen, i) => {
    if (i < activeGens.length && activeGens[i]) {
      activeGens[i].genGain.gain.value = shouldGenPlay(gen) ? gen.gain : 0;
    }
  });
  renderGenerators(); // update visual state
}

// ---------------------------------------------------------------------------
// Playback
// ---------------------------------------------------------------------------
async function play() {
  if (isPlaying) stop();
  await ensureCtx();
  if (audioCtx.state === 'suspended') await audioCtx.resume();
  activeGens = generators.map(g => createGenAudio(g));
  isPlaying = true;
  updateTransportUI();
  startViz();
}

function stop() {
  activeGens.forEach(ag => {
    ag.voiceNodes.forEach(destroyVoiceNodes);
    try { ag.genGain.disconnect(); } catch(e) {}
  });
  activeGens = [];
  isPlaying = false;
  updateTransportUI();
}

function toggleLoop() { isLooping = !isLooping; updateTransportUI(); }

// SFX playback
async function playSfx(sfx) {
  await ensureCtx();
  if (audioCtx.state === 'suspended') await audioCtx.resume();
  const src = audioCtx.createBufferSource();
  src.buffer = sfx.buffer;
  src.connect(dryGain); src.connect(reverbNode);
  src.start();
  if (!isPlaying) startViz();
}

// ---------------------------------------------------------------------------
// Visualization
// ---------------------------------------------------------------------------
let vizFrame = null;
function startViz() {
  if (vizFrame) return;
  const wc = document.getElementById('waveform-canvas'), sc = document.getElementById('spectrum-canvas');
  const wCtx = wc.getContext('2d'), sCtx = sc.getContext('2d');
  const bufLen = analyser.frequencyBinCount;
  const tBuf = new Uint8Array(bufLen), fBuf = new Uint8Array(bufLen);

  function draw() {
    vizFrame = requestAnimationFrame(draw);
    analyser.getByteTimeDomainData(tBuf);
    wCtx.fillStyle = '#080b10'; wCtx.fillRect(0, 0, wc.width, wc.height);
    wCtx.lineWidth = 1.5; wCtx.strokeStyle = '#6eb5ff'; wCtx.beginPath();
    const sl = wc.width / bufLen;
    for (let i = 0; i < bufLen; i++) {
      const y = (tBuf[i] / 128.0) * wc.height / 2;
      i === 0 ? wCtx.moveTo(0, y) : wCtx.lineTo(i * sl, y);
    }
    wCtx.stroke();

    analyser.getByteFrequencyData(fBuf);
    sCtx.fillStyle = '#080b10'; sCtx.fillRect(0, 0, sc.width, sc.height);
    const bw = sc.width / (bufLen / 4);
    for (let i = 0; i < bufLen / 4; i++) {
      const h = (fBuf[i] / 255) * sc.height;
      sCtx.fillStyle = `hsl(${200+fBuf[i]/4}, ${40+fBuf[i]/5}%, ${15+fBuf[i]/5}%)`;
      sCtx.fillRect(i * bw, sc.height - h, bw - 1, h);
    }

    if (!isPlaying) {
      let silent = true;
      for (let i = 0; i < bufLen; i++) if (Math.abs(tBuf[i]-128) > 2) { silent = false; break; }
      if (silent) {
        cancelAnimationFrame(vizFrame); vizFrame = null;
        wCtx.fillStyle = '#080b10'; wCtx.fillRect(0, 0, wc.width, wc.height);
        sCtx.fillStyle = '#080b10'; sCtx.fillRect(0, 0, sc.width, sc.height);
      }
    }
  }
  draw();
}

// ---------------------------------------------------------------------------
// Offline render
// ---------------------------------------------------------------------------
async function renderToBuffer() {
  const sr = 48000, dur = globals.duration, extra = globals.fadeOut;
  const offCtx = new OfflineAudioContext(2, sr * (dur + extra), sr);
  let owk = false;
  try { await offCtx.audioWorklet.addModule('/worklet/noise-processor.js'); owk = true; } catch(e) {}

  const oMaster = offCtx.createGain(); oMaster.gain.value = globals.master;
  const oComp = offCtx.createDynamicsCompressor(); oComp.threshold.value = -12; oComp.ratio.value = 4;
  const oDry = offCtx.createGain(); oDry.gain.value = 1 - globals.reverb;
  const oRevG = offCtx.createGain(); oRevG.gain.value = globals.reverb;
  const oRev = offCtx.createConvolver(); oRev.buffer = makeReverbIR(offCtx, 2.5, 0.8);

  oDry.connect(oComp); oRev.connect(oRevG); oRevG.connect(oComp);
  oComp.connect(oMaster); oMaster.connect(offCtx.destination);

  for (const gen of generators) {
    if (!shouldGenPlay(gen)) continue;
    const gg = offCtx.createGain(); gg.gain.value = gen.gain;
    gg.connect(oDry); gg.connect(oRev);

    for (const voice of gen.voices) {
      const n = createVoiceNodesOffline(offCtx, voice, owk);
      if (n.source) n.source.connect(n.filter);
      n.filter.connect(n.gain);
      n.gain.connect(gg);
      if (voice.lfoRate > 0 && voice.lfoDepth > 0) {
        const lfo = offCtx.createOscillator(); lfo.frequency.value = voice.lfoRate;
        const lg = offCtx.createGain();
        let t;
        switch (voice.lfoTarget) {
          case 'frequency': case 'filter': t = n.filter.frequency; lg.gain.value = voice.lfoDepth * voice.filterFreq; break;
          default: t = n.gain.gain; lg.gain.value = voice.lfoDepth * voice.gain;
        }
        lfo.connect(lg); lg.connect(t); lfo.start();
      }
    }
  }

  const fi = globals.fadeIn, fo = globals.fadeOut;
  oMaster.gain.setValueAtTime(0, 0);
  oMaster.gain.linearRampToValueAtTime(globals.master, fi);
  oMaster.gain.setValueAtTime(globals.master, dur - fo);
  oMaster.gain.linearRampToValueAtTime(0, dur);
  oMaster.gain.setValueAtTime(0, dur);
  oMaster.gain.linearRampToValueAtTime(globals.master, dur + fi);

  const rendered = await offCtx.startRendering();
  const mainSamples = dur * sr, fadeSamples = Math.floor(fo * sr);
  if (fadeSamples > 0 && fadeSamples < mainSamples) {
    for (let ch = 0; ch < rendered.numberOfChannels; ch++) {
      const d = rendered.getChannelData(ch);
      for (let i = 0; i < fadeSamples; i++) {
        const t = i / fadeSamples;
        d[i] = d[i] * t + d[mainSamples + i] * (1 - t);
      }
    }
  }
  const final = new AudioBuffer({ numberOfChannels: 2, length: mainSamples, sampleRate: sr });
  for (let ch = 0; ch < 2; ch++) final.copyToChannel(rendered.getChannelData(ch).slice(0, mainSamples), ch);
  return final;
}

function createVoiceNodesOffline(ctx, voice, hasWk) {
  const n = { source: null, filter: null, gain: null };
  n.gain = ctx.createGain(); n.gain.gain.value = voice.gain;
  n.filter = ctx.createBiquadFilter(); n.filter.type = voice.filterType;
  n.filter.frequency.value = voice.filterFreq; n.filter.Q.value = voice.filterQ;

  switch (voice.type) {
    case 'noise':
      if (hasWk) {
        n.source = new AudioWorkletNode(ctx, 'noise-processor');
        n.source.port.postMessage({ color: voice.noiseColor });
      } else {
        const len = ctx.length, buf = ctx.createBuffer(1, len, ctx.sampleRate), d = buf.getChannelData(0);
        let br = 0;
        for (let i = 0; i < len; i++) {
          if (voice.noiseColor === 'brown') { br = (br + 0.02*(Math.random()*2-1))/1.02; d[i]=br*3.5; }
          else d[i] = Math.random()*2-1;
        }
        const s = ctx.createBufferSource(); s.buffer = buf; s.start(); n.source = s;
      }
      break;
    case 'tone':
      n.source = ctx.createOscillator(); n.source.type = voice.waveform;
      n.source.frequency.value = voice.frequency; n.source.detune.value = voice.detune;
      n.source.start(); break;
    case 'harmonic': {
      const ps = voice.partials || [1,2,3,4,5], bf = voice.frequency || 110;
      const m = ctx.createGain(); m.gain.value = 1/ps.length;
      ps.forEach((p,i) => {
        const o = ctx.createOscillator(); o.type = voice.waveform||'sine';
        o.frequency.value = bf*p;
        const pg = ctx.createGain(); pg.gain.value = 1/(i+1);
        o.connect(pg); pg.connect(m); o.start();
      });
      n.source = m; break;
    }
    case 'impulse': {
      const len = ctx.length, buf = ctx.createBuffer(1, len, ctx.sampleRate), d = buf.getChannelData(0);
      const rate = voice.impulseRate||2, decay = voice.impulseDecay||0.1;
      const interval = ctx.sampleRate/rate, ds = decay*ctx.sampleRate;
      for (let pos = 0; pos < len; pos += interval) {
        const st = Math.floor(pos);
        for (let i = 0; i < ds && st+i < len; i++) d[st+i] += (Math.random()*2-1)*Math.exp(-i/(ds/5));
      }
      const s = ctx.createBufferSource(); s.buffer = buf; s.start(); n.source = s; break;
    }
    case 'crackle': {
      const len = ctx.length, buf = ctx.createBuffer(1, len, ctx.sampleRate), d = buf.getChannelData(0);
      const dens = voice.crackleDensity || 8;
      for (let i = 0; i < len; i++) {
        if (Math.random() < dens/(ctx.sampleRate*0.5)) {
          d[i] = (Math.random()*2-1)*0.8;
          const dl = Math.min(ctx.sampleRate*0.02, len-i);
          for (let j = 1; j < dl; j++) d[i+j] += d[i]*Math.exp(-j/(dl/3));
        }
      }
      const s = ctx.createBufferSource(); s.buffer = buf; s.start(); n.source = s; break;
    }
  }
  return n;
}

// ---------------------------------------------------------------------------
// WAV encoding
// ---------------------------------------------------------------------------
function bufToWav(buffer) {
  const nc = buffer.numberOfChannels, sr = buffer.sampleRate, len = buffer.length;
  const ba = nc * 2, ds = len * ba, total = 44 + ds;
  const ab = new ArrayBuffer(total), v = new DataView(ab);
  function ws(o,s) { for(let i=0;i<s.length;i++) v.setUint8(o+i,s.charCodeAt(i)); }
  ws(0,'RIFF'); v.setUint32(4,total-8,true); ws(8,'WAVE');
  ws(12,'fmt '); v.setUint32(16,16,true); v.setUint16(20,1,true);
  v.setUint16(22,nc,true); v.setUint32(24,sr,true); v.setUint32(28,sr*ba,true);
  v.setUint16(32,ba,true); v.setUint16(34,16,true);
  ws(36,'data'); v.setUint32(40,ds,true);
  const chs = []; for(let c=0;c<nc;c++) chs.push(buffer.getChannelData(c));
  let off = 44;
  for(let i=0;i<len;i++) for(let c=0;c<nc;c++) {
    let s = Math.max(-1,Math.min(1,chs[c][i]));
    v.setInt16(off, s<0?s*0x8000:s*0x7FFF, true); off+=2;
  }
  return new Blob([ab], { type: 'audio/wav' });
}

// ---------------------------------------------------------------------------
// Download
// ---------------------------------------------------------------------------
async function downloadAudio(fmt) {
  const statusEl = document.getElementById('export-status');
  const fn = document.getElementById('export-filename').value.trim() || 'sound.ogg';
  const allVoices = generators.reduce((a,g) => a + g.voices.length, 0);
  if (allVoices === 0) { statusEl.textContent = 'No voices to render'; statusEl.className = 'status-msg err'; return; }

  statusEl.textContent = 'Rendering...'; statusEl.className = 'status-msg working';
  try {
    const buf = await renderToBuffer();
    const wav = bufToWav(buf);
    if (fmt === 'wav') {
      dl(wav, fn.replace(/\.ogg$/, '.wav'));
      statusEl.textContent = 'Downloaded .wav'; statusEl.className = 'status-msg ok'; return;
    }
    statusEl.textContent = 'Converting to Ogg Vorbis...';
    const fd = new FormData();
    fd.append('wav', wav, 'render.wav');
    fd.append('filename', fn.endsWith('.ogg') ? fn : fn + '.ogg');
    const r = await fetch('/api/convert', { method: 'POST', body: fd });
    if (!r.ok) { const e = await r.json(); throw new Error(e.error || 'Failed'); }
    const blob = await r.blob();
    dl(blob, fn.endsWith('.ogg') ? fn : fn + '.ogg');
    statusEl.textContent = 'Downloaded .ogg'; statusEl.className = 'status-msg ok';
  } catch(e) { statusEl.textContent = 'Error: ' + e.message; statusEl.className = 'status-msg err'; }
}

function dl(blob, name) {
  const u = URL.createObjectURL(blob), a = document.createElement('a');
  a.href = u; a.download = name; a.click(); URL.revokeObjectURL(u);
}

// ---------------------------------------------------------------------------
// Data model: Voices & Generators
// ---------------------------------------------------------------------------
function makeVoice(type = 'noise') {
  const id = ++voiceIdCounter;
  const base = { id, type, gain: 0.5, filterType: 'lowpass', filterFreq: 2000, filterQ: 1, lfoRate: 0, lfoDepth: 0, lfoTarget: 'gain' };
  switch (type) {
    case 'noise': return { ...base, noiseColor: 'brown', filterFreq: 800 };
    case 'tone': return { ...base, waveform: 'sine', frequency: 180, detune: 0 };
    case 'harmonic': return { ...base, waveform: 'sine', frequency: 110, partials: [1,2,3,4,5] };
    case 'impulse': return { ...base, impulseRate: 2, impulseDecay: 0.1, filterFreq: 1000 };
    case 'crackle': return { ...base, crackleDensity: 8, filterFreq: 4000 };
    default: return base;
  }
}

function makeGenerator(name = 'New Generator', voiceDefs = []) {
  const gen = { id: ++genIdCounter, name, gain: 1.0, muted: false, solo: false, collapsed: false, voices: [] };
  if (voiceDefs.length > 0) {
    gen.voices = voiceDefs.map(vd => ({ ...makeVoice(vd.type), ...vd, id: ++voiceIdCounter }));
  } else {
    gen.voices.push(makeVoice('noise'));
  }
  return gen;
}

// ---------------------------------------------------------------------------
// Presets (structured as generators)
// ---------------------------------------------------------------------------
const PRESETS = {
  ambient: [
    { name: 'forest', generators: [
        { name: 'Wind', gain: 1.0, voices: [
            { type: 'noise', noiseColor: 'brown', filterType: 'lowpass', filterFreq: 800, filterQ: 1, gain: 0.4, lfoRate: 0.15, lfoDepth: 0.3, lfoTarget: 'filter' },
            { type: 'noise', noiseColor: 'pink', filterType: 'bandpass', filterFreq: 3000, filterQ: 0.8, gain: 0.15, lfoRate: 0.2, lfoDepth: 0.2, lfoTarget: 'gain' },
        ]},
        { name: 'Ambience', gain: 1.0, voices: [
            { type: 'tone', waveform: 'sine', frequency: 180, detune: 0, filterType: 'lowpass', filterFreq: 300, filterQ: 1, gain: 0.08, lfoRate: 0.05, lfoDepth: 0.3, lfoTarget: 'gain' },
        ]},
      ], globals: { duration: 90, fadeIn: 2, fadeOut: 2, reverb: 0.25, master: 0.7 } },
    { name: 'cave', generators: [
        { name: 'Depths', gain: 1.0, voices: [
            { type: 'noise', noiseColor: 'brown', filterType: 'lowpass', filterFreq: 400, filterQ: 1.5, gain: 0.5, lfoRate: 0.08, lfoDepth: 0.15, lfoTarget: 'filter' },
        ]},
        { name: 'Drips', gain: 1.0, voices: [
            { type: 'impulse', impulseRate: 0.5, impulseDecay: 0.3, filterType: 'bandpass', filterFreq: 2000, filterQ: 3, gain: 0.2, lfoRate: 0, lfoDepth: 0, lfoTarget: 'gain' },
        ]},
        { name: 'Resonance', gain: 1.0, voices: [
            { type: 'tone', waveform: 'sine', frequency: 80, detune: 0, filterType: 'lowpass', filterFreq: 200, filterQ: 1, gain: 0.12, lfoRate: 0.03, lfoDepth: 0.4, lfoTarget: 'gain' },
        ]},
      ], globals: { duration: 90, fadeIn: 3, fadeOut: 3, reverb: 0.6, master: 0.65 } },
    { name: 'water', generators: [
        { name: 'Flow', gain: 1.0, voices: [
            { type: 'noise', noiseColor: 'pink', filterType: 'bandpass', filterFreq: 400, filterQ: 1.5, gain: 0.45, lfoRate: 0.3, lfoDepth: 0.4, lfoTarget: 'filter' },
            { type: 'noise', noiseColor: 'brown', filterType: 'lowpass', filterFreq: 1000, filterQ: 0.7, gain: 0.25, lfoRate: 0.15, lfoDepth: 0.2, lfoTarget: 'gain' },
        ]},
        { name: 'Bubbles', gain: 1.0, voices: [
            { type: 'crackle', crackleDensity: 12, filterType: 'highpass', filterFreq: 1500, filterQ: 1, gain: 0.1, lfoRate: 0, lfoDepth: 0, lfoTarget: 'gain' },
        ]},
      ], globals: { duration: 90, fadeIn: 2, fadeOut: 2, reverb: 0.3, master: 0.7 } },
    { name: 'rapids', generators: [
        { name: 'Rush', gain: 1.0, voices: [
            { type: 'noise', noiseColor: 'white', filterType: 'bandpass', filterFreq: 1000, filterQ: 0.5, gain: 0.5, lfoRate: 2, lfoDepth: 0.3, lfoTarget: 'filter' },
            { type: 'noise', noiseColor: 'brown', filterType: 'highpass', filterFreq: 100, filterQ: 0.5, gain: 0.35, lfoRate: 0.5, lfoDepth: 0.2, lfoTarget: 'gain' },
        ]},
      ], globals: { duration: 60, fadeIn: 1.5, fadeOut: 1.5, reverb: 0.2, master: 0.65 } },
    { name: 'mine', generators: [
        { name: 'Earth', gain: 1.0, voices: [
            { type: 'noise', noiseColor: 'brown', filterType: 'lowpass', filterFreq: 200, filterQ: 2, gain: 0.5, lfoRate: 0.05, lfoDepth: 0.2, lfoTarget: 'filter' },
        ]},
        { name: 'Clanks', gain: 1.0, voices: [
            { type: 'impulse', impulseRate: 0.3, impulseDecay: 0.5, filterType: 'bandpass', filterFreq: 800, filterQ: 5, gain: 0.15, lfoRate: 0, lfoDepth: 0, lfoTarget: 'gain' },
        ]},
        { name: 'Hum', gain: 1.0, voices: [
            { type: 'tone', waveform: 'square', frequency: 60, detune: 0, filterType: 'lowpass', filterFreq: 150, filterQ: 1, gain: 0.1, lfoRate: 0.02, lfoDepth: 0.5, lfoTarget: 'gain' },
        ]},
      ], globals: { duration: 90, fadeIn: 3, fadeOut: 3, reverb: 0.5, master: 0.6 } },
    { name: 'machinery', generators: [
        { name: 'Engine', gain: 1.0, voices: [
            { type: 'tone', waveform: 'sawtooth', frequency: 120, detune: 0, filterType: 'lowpass', filterFreq: 500, filterQ: 2, gain: 0.2, lfoRate: 4, lfoDepth: 0.3, lfoTarget: 'gain' },
            { type: 'tone', waveform: 'square', frequency: 60, detune: 0, filterType: 'lowpass', filterFreq: 300, filterQ: 1, gain: 0.15, lfoRate: 2, lfoDepth: 0.5, lfoTarget: 'gain' },
        ]},
        { name: 'Rumble', gain: 1.0, voices: [
            { type: 'noise', noiseColor: 'brown', filterType: 'lowpass', filterFreq: 500, filterQ: 1, gain: 0.25, lfoRate: 0.1, lfoDepth: 0.15, lfoTarget: 'filter' },
        ]},
      ], globals: { duration: 60, fadeIn: 1, fadeOut: 1, reverb: 0.15, master: 0.6 } },
    { name: 'hades', generators: [
        { name: 'Drone', gain: 1.0, voices: [
            { type: 'tone', waveform: 'sine', frequency: 40, detune: 0, filterType: 'lowpass', filterFreq: 200, filterQ: 1, gain: 0.35, lfoRate: 0.04, lfoDepth: 0.6, lfoTarget: 'gain' },
            { type: 'tone', waveform: 'sine', frequency: 67, detune: 0, filterType: 'lowpass', filterFreq: 200, filterQ: 1, gain: 0.25, lfoRate: 0.06, lfoDepth: 0.4, lfoTarget: 'gain' },
        ]},
        { name: 'Abyss', gain: 1.0, voices: [
            { type: 'noise', noiseColor: 'brown', filterType: 'lowpass', filterFreq: 300, filterQ: 1.5, gain: 0.3, lfoRate: 0.03, lfoDepth: 0.3, lfoTarget: 'filter' },
        ]},
      ], globals: { duration: 120, fadeIn: 4, fadeOut: 4, reverb: 0.5, master: 0.65 } },
    { name: 'drone-horror', generators: [
        { name: 'Dissonance', gain: 1.0, voices: [
            { type: 'tone', waveform: 'sine', frequency: 55, detune: 0, filterType: 'lowpass', filterFreq: 400, filterQ: 1, gain: 0.3, lfoRate: 0.05, lfoDepth: 0.3, lfoTarget: 'gain' },
            { type: 'tone', waveform: 'sine', frequency: 82, detune: 15, filterType: 'lowpass', filterFreq: 400, filterQ: 1, gain: 0.25, lfoRate: 0.07, lfoDepth: 0.25, lfoTarget: 'gain' },
            { type: 'tone', waveform: 'sawtooth', frequency: 110, detune: -10, filterType: 'lowpass', filterFreq: 600, filterQ: 2, gain: 0.15, lfoRate: 0.1, lfoDepth: 0.4, lfoTarget: 'filter' },
        ]},
        { name: 'Darkness', gain: 1.0, voices: [
            { type: 'noise', noiseColor: 'brown', filterType: 'lowpass', filterFreq: 250, filterQ: 1, gain: 0.15, lfoRate: 0.02, lfoDepth: 0.2, lfoTarget: 'gain' },
        ]},
      ], globals: { duration: 120, fadeIn: 4, fadeOut: 4, reverb: 0.4, master: 0.6 } },
    { name: 'house', generators: [
        { name: 'Room Tone', gain: 1.0, voices: [
            { type: 'noise', noiseColor: 'brown', filterType: 'lowpass', filterFreq: 600, filterQ: 0.5, gain: 0.08, lfoRate: 0.05, lfoDepth: 0.1, lfoTarget: 'gain' },
            { type: 'noise', noiseColor: 'pink', filterType: 'bandpass', filterFreq: 2000, filterQ: 0.5, gain: 0.04, lfoRate: 0.1, lfoDepth: 0.15, lfoTarget: 'gain' },
        ]},
      ], globals: { duration: 60, fadeIn: 2, fadeOut: 2, reverb: 0.15, master: 0.5 } },
  ],
  sfx: [
    { name: 'footsteps', generators: [{ name: 'Steps', gain: 1.0, voices: [{ type: 'impulse', impulseRate: 4, impulseDecay: 0.05, filterType: 'lowpass', filterFreq: 400, filterQ: 2, gain: 0.7, lfoRate: 0, lfoDepth: 0, lfoTarget: 'gain' }] }], globals: { duration: 1, fadeIn: 0, fadeOut: 0.1, reverb: 0.1, master: 0.8 } },
    { name: 'creak', generators: [{ name: 'Creak', gain: 1.0, voices: [
        { type: 'tone', waveform: 'sine', frequency: 300, detune: 0, filterType: 'bandpass', filterFreq: 500, filterQ: 5, gain: 0.5, lfoRate: 8, lfoDepth: 0.8, lfoTarget: 'frequency' },
        { type: 'noise', noiseColor: 'white', filterType: 'bandpass', filterFreq: 600, filterQ: 3, gain: 0.15, lfoRate: 0, lfoDepth: 0, lfoTarget: 'gain' },
    ] }], globals: { duration: 1.5, fadeIn: 0.05, fadeOut: 0.3, reverb: 0.2, master: 0.7 } },
    { name: 'sword', generators: [{ name: 'Strike', gain: 1.0, voices: [
        { type: 'noise', noiseColor: 'white', filterType: 'highpass', filterFreq: 2000, filterQ: 1, gain: 0.7, lfoRate: 0, lfoDepth: 0, lfoTarget: 'gain' },
        { type: 'tone', waveform: 'sine', frequency: 800, detune: 0, filterType: 'lowpass', filterFreq: 2000, filterQ: 1, gain: 0.3, lfoRate: 15, lfoDepth: 0.5, lfoTarget: 'frequency' },
    ] }], globals: { duration: 2, fadeIn: 0.01, fadeOut: 0.5, reverb: 0.15, master: 0.8 } },
    { name: 'bell', generators: [{ name: 'Bell', gain: 1.0, voices: [{ type: 'harmonic', waveform: 'sine', frequency: 440, partials: [1,2,3,4,5.5], filterType: 'lowpass', filterFreq: 6000, filterQ: 0.5, gain: 0.5, lfoRate: 0, lfoDepth: 0, lfoTarget: 'gain' }] }], globals: { duration: 3, fadeIn: 0.01, fadeOut: 1.5, reverb: 0.5, master: 0.7 } },
    { name: 'heartbeat', generators: [{ name: 'Pulse', gain: 1.0, voices: [{ type: 'tone', waveform: 'sine', frequency: 60, detune: 0, filterType: 'lowpass', filterFreq: 150, filterQ: 2, gain: 0.7, lfoRate: 0, lfoDepth: 0, lfoTarget: 'gain' }] }], globals: { duration: 2, fadeIn: 0, fadeOut: 0.2, reverb: 0.1, master: 0.8 } },
    { name: 'glass', generators: [{ name: 'Shatter', gain: 1.0, voices: [
        { type: 'noise', noiseColor: 'white', filterType: 'bandpass', filterFreq: 4500, filterQ: 2, gain: 0.6, lfoRate: 0, lfoDepth: 0, lfoTarget: 'gain' },
        { type: 'harmonic', waveform: 'sine', frequency: 2200, partials: [1,1.5,2.3,3.1], filterType: 'highpass', filterFreq: 1500, filterQ: 1, gain: 0.3, lfoRate: 0, lfoDepth: 0, lfoTarget: 'gain' },
    ] }], globals: { duration: 1, fadeIn: 0.01, fadeOut: 0.5, reverb: 0.3, master: 0.75 } },
    { name: 'match', generators: [{ name: 'Ignite', gain: 1.0, voices: [
        { type: 'noise', noiseColor: 'white', filterType: 'highpass', filterFreq: 4000, filterQ: 1, gain: 0.6, lfoRate: 0, lfoDepth: 0, lfoTarget: 'gain' },
        { type: 'noise', noiseColor: 'pink', filterType: 'lowpass', filterFreq: 2000, filterQ: 0.5, gain: 0.15, lfoRate: 0, lfoDepth: 0, lfoTarget: 'gain' },
    ] }], globals: { duration: 1, fadeIn: 0.01, fadeOut: 0.3, reverb: 0.1, master: 0.7 } },
    { name: 'grue', generators: [{ name: 'Grue', gain: 1.0, voices: [
        { type: 'tone', waveform: 'sine', frequency: 40, detune: 0, filterType: 'lowpass', filterFreq: 200, filterQ: 3, gain: 0.6, lfoRate: 0.5, lfoDepth: 0.8, lfoTarget: 'gain' },
        { type: 'noise', noiseColor: 'brown', filterType: 'lowpass', filterFreq: 300, filterQ: 2, gain: 0.4, lfoRate: 0, lfoDepth: 0, lfoTarget: 'gain' },
    ] }], globals: { duration: 3, fadeIn: 0.1, fadeOut: 1, reverb: 0.4, master: 0.75 } },
  ],
};

// ---------------------------------------------------------------------------
// Custom presets & generator library (localStorage)
// ---------------------------------------------------------------------------
function getCustomPresets() { try{return JSON.parse(localStorage.getItem('synthlab-presets')||'[]');}catch{return[];} }
function saveCustomPreset(name) {
  const p = { name, generators: generators.map(serializeGen), globals: {...globals} };
  const list = getCustomPresets();
  const idx = list.findIndex(x => x.name === name);
  if (idx >= 0) list[idx] = p; else list.push(p);
  localStorage.setItem('synthlab-presets', JSON.stringify(list));
  renderPresets(); showToast('Scene saved: ' + name);
}
function deleteCustomPreset(name) {
  localStorage.setItem('synthlab-presets', JSON.stringify(getCustomPresets().filter(p => p.name !== name)));
  renderPresets();
}

function getGenLibrary() { try{return JSON.parse(localStorage.getItem('synthlab-gen-lib')||'[]');}catch{return[];} }
function saveGenToLibrary(gen) {
  const entry = serializeGen(gen);
  const lib = getGenLibrary();
  const idx = lib.findIndex(g => g.name === entry.name);
  if (idx >= 0) lib[idx] = entry; else lib.push(entry);
  localStorage.setItem('synthlab-gen-lib', JSON.stringify(lib));
  renderGenLibrary(); showToast('Generator saved: ' + entry.name);
}
function deleteGenFromLibrary(name) {
  localStorage.setItem('synthlab-gen-lib', JSON.stringify(getGenLibrary().filter(g => g.name !== name)));
  renderGenLibrary();
}

function serializeGen(gen) {
  return { name: gen.name, gain: gen.gain, voices: gen.voices.map(v => { const c={...v}; delete c.id; return c; }) };
}

// ---------------------------------------------------------------------------
// Additive loading
// ---------------------------------------------------------------------------
function addPresetGenerators(preset) {
  for (const gd of preset.generators) addGeneratorDef(gd);
  if (isPlaying) { stop(); play(); }
  showToast(`Added ${preset.generators.length} generator(s) from "${preset.name}"`);
}

function addGeneratorDef(gd) {
  const gen = makeGenerator(gd.name, gd.voices);
  gen.gain = gd.gain ?? 1.0;
  generators.push(gen);
  renderGenerators();
}

function describeVoice(v) {
  switch (v.type) {
    case 'noise': return `${v.noiseColor} noise ${v.filterType} ${fHz(v.filterFreq)}`;
    case 'tone': return `${v.waveform} ${fHz(v.frequency)}`;
    case 'harmonic': return `harmonic ${fHz(v.frequency)}`;
    case 'impulse': return `impulse ${v.impulseRate}Hz`;
    case 'crackle': return `crackle d${v.crackleDensity}`;
    default: return v.type;
  }
}
function fHz(v) { return v >= 1000 ? (v/1000).toFixed(1)+'kHz' : Math.round(v)+'Hz'; }

// ---------------------------------------------------------------------------
// Scene (project) save/load
// ---------------------------------------------------------------------------
function getSceneList() { try{return JSON.parse(localStorage.getItem('synthlab-scene-list')||'[]');}catch{return[];} }
function saveScene() {
  const name = document.getElementById('project-name').value.trim() || 'Untitled';
  const scene = { name, generators: generators.map(serializeGen), globals: {...globals} };
  localStorage.setItem('synthlab-scene-' + name, JSON.stringify(scene));
  const list = getSceneList();
  if (!list.includes(name)) { list.push(name); localStorage.setItem('synthlab-scene-list', JSON.stringify(list)); }
  renderSavedScenes(); showToast('Scene saved: ' + name);
}
function loadScene(name) {
  try {
    const d = JSON.parse(localStorage.getItem('synthlab-scene-' + name));
    if (!d) return;
    if (isPlaying) stop();
    document.getElementById('project-name').value = d.name || name;
    generators = (d.generators || []).map(gd => { const g = makeGenerator(gd.name, gd.voices); g.gain = gd.gain ?? 1.0; return g; });
    if (d.globals) { Object.assign(globals, d.globals); syncGlobalsUI(); }
    renderGenerators(); showToast('Loaded: ' + name);
  } catch(e) { console.error(e); }
}
function deleteScene(name) {
  localStorage.removeItem('synthlab-scene-' + name);
  localStorage.setItem('synthlab-scene-list', JSON.stringify(getSceneList().filter(n => n !== name)));
  renderSavedScenes();
}
function newScene() {
  if (isPlaying) stop();
  generators = []; globals = { duration: 30, fadeIn: 1.0, fadeOut: 1.0, reverb: 0.2, master: 0.7 };
  document.getElementById('project-name').value = 'Untitled';
  syncGlobalsUI(); renderGenerators();
}
function exportSceneJSON() {
  const name = document.getElementById('project-name').value.trim() || 'Untitled';
  const scene = { name, generators: generators.map(serializeGen), globals: {...globals} };
  dl(new Blob([JSON.stringify(scene, null, 2)], { type: 'application/json' }), name.replace(/\s+/g, '-').toLowerCase() + '.json');
}
function importSceneJSON(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const d = JSON.parse(e.target.result);
      if (isPlaying) stop();
      document.getElementById('project-name').value = d.name || 'Imported';
      generators = (d.generators || []).map(gd => { const g = makeGenerator(gd.name, gd.voices); g.gain = gd.gain ?? 1.0; return g; });
      if (d.globals) { Object.assign(globals, d.globals); syncGlobalsUI(); }
      renderGenerators(); showToast('Imported: ' + (d.name || file.name));
    } catch(err) { alert('Invalid file: ' + err.message); }
  };
  reader.readAsText(file);
}

// SFX file import
async function importSfxFiles(files) {
  await ensureCtx();
  for (const f of files) {
    try {
      const ab = await f.arrayBuffer();
      const buf = await audioCtx.decodeAudioData(ab);
      sfxFiles.push({ name: f.name, buffer: buf });
    } catch(e) { showToast('Failed: ' + f.name); }
  }
  renderSfxFiles();
  if (sfxFiles.length > 0) showToast(`Loaded ${files.length} file(s)`);
}
function removeSfx(i) { sfxFiles.splice(i, 1); renderSfxFiles(); }

// ---------------------------------------------------------------------------
// UI Rendering
// ---------------------------------------------------------------------------
function renderPresets() {
  renderPresetList('ambient-presets', PRESETS.ambient);
  renderPresetList('sfx-presets', PRESETS.sfx);
  const cel = document.getElementById('custom-presets'); cel.innerHTML = '';
  for (const p of getCustomPresets()) cel.appendChild(makePresetItem(p, true));
}

function renderPresetList(id, presets) {
  const el = document.getElementById(id); el.innerHTML = '';
  for (const p of presets) el.appendChild(makePresetItem(p, false));
}

function makePresetItem(preset, isCustom) {
  const item = document.createElement('div'); item.className = 'preset-item';
  const header = document.createElement('div'); header.className = 'preset-header';
  const arrow = document.createElement('span'); arrow.className = 'arrow'; arrow.textContent = '\u25b6';
  const name = document.createElement('span'); name.className = 'name'; name.textContent = preset.name;
  const addAll = document.createElement('span'); addAll.className = 'add-all'; addAll.textContent = '+ All';
  addAll.onclick = (e) => { e.stopPropagation(); addPresetGenerators(preset); };
  header.appendChild(arrow); header.appendChild(name); header.appendChild(addAll);
  if (isCustom) {
    const del = document.createElement('span');
    del.textContent = '\u00d7'; del.style.cssText = 'color:var(--text-dim);cursor:pointer;padding:0 3px;font-size:1.1em';
    del.onclick = (e) => { e.stopPropagation(); deleteCustomPreset(preset.name); };
    header.appendChild(del);
  }
  header.onclick = () => item.classList.toggle('expanded');

  const gens = document.createElement('div'); gens.className = 'preset-gens';
  for (const gd of (preset.generators || [])) {
    const row = document.createElement('div'); row.className = 'preset-gen-row';
    row.onclick = () => { addGeneratorDef(gd); if(isPlaying){stop();play();} showToast('Added: '+gd.name); };
    const plus = document.createElement('span'); plus.className = 'add-one'; plus.textContent = '+';
    const desc = document.createElement('span');
    desc.textContent = gd.name + ' (' + gd.voices.length + (gd.voices.length === 1 ? ' voice)' : ' voices)');
    row.appendChild(plus); row.appendChild(desc);
    gens.appendChild(row);
  }
  item.appendChild(header); item.appendChild(gens);
  return item;
}

function renderSavedScenes() {
  const el = document.getElementById('saved-projects'); el.innerHTML = '';
  for (const name of getSceneList()) {
    const row = document.createElement('div'); row.className = 'saved-project-item';
    const ns = document.createElement('span'); ns.textContent = name; ns.style.flex = '1'; ns.style.cursor = 'pointer';
    ns.onclick = () => loadScene(name);
    const del = document.createElement('span'); del.className = 'del'; del.textContent = '\u00d7';
    del.onclick = (e) => { e.stopPropagation(); deleteScene(name); };
    row.appendChild(ns); row.appendChild(del); el.appendChild(row);
  }
}

function renderGenLibrary() {
  const el = document.getElementById('gen-library'); el.innerHTML = '';
  const lib = getGenLibrary();
  if (lib.length === 0) {
    el.innerHTML = '<div style="font-size:0.78em;color:var(--text-dim);padding:2px 7px">No saved generators</div>';
    return;
  }
  for (const gd of lib) {
    const row = document.createElement('div'); row.className = 'gen-lib-item';
    const plus = document.createElement('span'); plus.className = 'add-one'; plus.textContent = '+';
    const name = document.createElement('span'); name.textContent = gd.name; name.style.flex = '1';
    const del = document.createElement('span'); del.className = 'del'; del.textContent = '\u00d7';
    del.onclick = (e) => { e.stopPropagation(); deleteGenFromLibrary(gd.name); };
    row.onclick = () => { addGeneratorDef(gd); if(isPlaying){stop();play();} showToast('Added: '+gd.name); };
    row.appendChild(plus); row.appendChild(name); row.appendChild(del);
    el.appendChild(row);
  }
}

function renderSfxFiles() {
  const el = document.getElementById('sfx-files'); el.innerHTML = '';
  if (sfxFiles.length === 0) {
    el.innerHTML = '<div style="font-size:0.78em;color:var(--text-dim);padding:2px 7px">No files loaded</div>';
    return;
  }
  sfxFiles.forEach((sfx, i) => {
    const row = document.createElement('div'); row.className = 'sfx-item';
    const name = document.createElement('span'); name.className = 'name'; name.textContent = sfx.name;
    const pb = document.createElement('button'); pb.className = 'play-sfx'; pb.textContent = '\u25b6'; pb.onclick = () => playSfx(sfx);
    const rb = document.createElement('button'); rb.className = 'remove-sfx'; rb.textContent = '\u00d7'; rb.onclick = () => removeSfx(i);
    row.appendChild(name); row.appendChild(pb); row.appendChild(rb); el.appendChild(row);
  });
}

// ---------------------------------------------------------------------------
// Generator & Voice cards
// ---------------------------------------------------------------------------
function renderGenerators() {
  const panel = document.getElementById('gen-panel');
  panel.querySelectorAll('.generator-card').forEach(el => el.remove());
  const addBtn = document.getElementById('add-gen-btn');
  for (const gen of generators) panel.insertBefore(createGenCard(gen), addBtn);
}

function createGenCard(gen) {
  const card = document.createElement('div');
  card.className = 'generator-card' + (gen.muted ? ' muted' : '') + (gen.solo ? ' soloed' : '') + (gen.collapsed ? ' collapsed' : '');

  // Header
  const header = document.createElement('div'); header.className = 'gen-header';
  const collapse = document.createElement('span'); collapse.className = 'gen-collapse'; collapse.textContent = '\u25bc';
  collapse.onclick = () => { gen.collapsed = !gen.collapsed; card.classList.toggle('collapsed'); };
  const nameInput = document.createElement('input'); nameInput.className = 'gen-name-input';
  nameInput.value = gen.name; nameInput.onchange = () => { gen.name = nameInput.value; };

  const muteBtn = document.createElement('button'); muteBtn.className = 'gen-btn' + (gen.muted ? ' mute-active' : '');
  muteBtn.textContent = 'M'; muteBtn.title = 'Mute';
  muteBtn.onclick = () => { gen.muted = !gen.muted; updateMuteSoloState(); };

  const soloBtn = document.createElement('button'); soloBtn.className = 'gen-btn' + (gen.solo ? ' solo-active' : '');
  soloBtn.textContent = 'S'; soloBtn.title = 'Solo';
  soloBtn.onclick = () => { gen.solo = !gen.solo; updateMuteSoloState(); };

  const gainSlider = document.createElement('input'); gainSlider.className = 'gen-gain-slider';
  gainSlider.type = 'range'; gainSlider.min = 0; gainSlider.max = 1; gainSlider.step = 0.01; gainSlider.value = gen.gain;
  const gainVal = document.createElement('span'); gainVal.className = 'gen-gain-val'; gainVal.textContent = gen.gain.toFixed(2);
  gainSlider.oninput = () => {
    gen.gain = parseFloat(gainSlider.value); gainVal.textContent = gen.gain.toFixed(2);
    const idx = generators.indexOf(gen);
    if (idx >= 0 && idx < activeGens.length && activeGens[idx] && shouldGenPlay(gen)) {
      activeGens[idx].genGain.gain.value = gen.gain;
    }
  };

  const saveLib = document.createElement('button'); saveLib.className = 'gen-save-lib';
  saveLib.textContent = '\u2b07'; saveLib.title = 'Save to library';
  saveLib.onclick = () => saveGenToLibrary(gen);

  const removeBtn = document.createElement('button'); removeBtn.className = 'gen-remove';
  removeBtn.textContent = '\u00d7'; removeBtn.title = 'Remove';
  removeBtn.onclick = () => {
    generators = generators.filter(g => g.id !== gen.id);
    renderGenerators();
    if (isPlaying) { stop(); play(); }
  };

  header.appendChild(collapse); header.appendChild(nameInput);
  header.appendChild(muteBtn); header.appendChild(soloBtn);
  header.appendChild(gainSlider); header.appendChild(gainVal);
  header.appendChild(saveLib); header.appendChild(removeBtn);
  card.appendChild(header);

  // Voices
  const voicesDiv = document.createElement('div'); voicesDiv.className = 'gen-voices';
  for (const voice of gen.voices) voicesDiv.appendChild(createVoiceCard(gen, voice));
  const addVoiceBtn = document.createElement('button'); addVoiceBtn.className = 'add-voice-btn';
  addVoiceBtn.textContent = '+ Add Voice';
  addVoiceBtn.onclick = () => { gen.voices.push(makeVoice('noise')); renderGenerators(); if(isPlaying){stop();play();} };
  voicesDiv.appendChild(addVoiceBtn);
  card.appendChild(voicesDiv);

  return card;
}

function createVoiceCard(gen, voice) {
  const card = document.createElement('div'); card.className = 'voice-card';
  const header = document.createElement('div'); header.className = 'voice-header';
  const typeSelect = document.createElement('select');
  for (const t of ['noise','tone','harmonic','impulse','crackle']) {
    const opt = document.createElement('option'); opt.value = t; opt.textContent = t; opt.selected = t === voice.type;
    typeSelect.appendChild(opt);
  }
  typeSelect.onchange = () => {
    const idx = gen.voices.indexOf(voice);
    gen.voices[idx] = { ...makeVoice(typeSelect.value), gain: voice.gain, id: voice.id };
    renderGenerators(); if(isPlaying){stop();play();}
  };
  const removeBtn = document.createElement('button'); removeBtn.className = 'voice-remove';
  removeBtn.textContent = '\u00d7';
  removeBtn.onclick = () => {
    gen.voices = gen.voices.filter(v => v.id !== voice.id);
    renderGenerators(); if(isPlaying){stop();play();}
  };
  header.appendChild(typeSelect); header.appendChild(removeBtn);
  card.appendChild(header);

  // Type-specific params
  switch (voice.type) {
    case 'noise':
      card.appendChild(mkSelect('Color', ['white','pink','brown'], voice.noiseColor, v => { voice.noiseColor=v; if(isPlaying){stop();play();} }));
      break;
    case 'tone':
      card.appendChild(mkSelect('Wave', ['sine','square','sawtooth','triangle'], voice.waveform, v => { voice.waveform=v; if(isPlaying){stop();play();} }));
      card.appendChild(mkSlider('Freq', voice.frequency, 20, 2000, 1, 'Hz', v => { voice.frequency=v; updateVoiceParam(gen,voice); }));
      card.appendChild(mkSlider('Detune', voice.detune, -100, 100, 1, 'ct', v => { voice.detune=v; updateVoiceParam(gen,voice); }));
      break;
    case 'harmonic':
      card.appendChild(mkSelect('Wave', ['sine','square','sawtooth','triangle'], voice.waveform, v => { voice.waveform=v; if(isPlaying){stop();play();} }));
      card.appendChild(mkSlider('Base Freq', voice.frequency, 20, 1000, 1, 'Hz', v => { voice.frequency=v; if(isPlaying){stop();play();} }));
      break;
    case 'impulse':
      card.appendChild(mkSlider('Rate', voice.impulseRate, 0.1, 20, 0.1, 'Hz', v => { voice.impulseRate=v; if(isPlaying){stop();play();} }));
      card.appendChild(mkSlider('Decay', voice.impulseDecay, 0.01, 1, 0.01, 's', v => { voice.impulseDecay=v; if(isPlaying){stop();play();} }));
      break;
    case 'crackle':
      card.appendChild(mkSlider('Density', voice.crackleDensity, 1, 30, 1, '', v => { voice.crackleDensity=v; if(isPlaying){stop();play();} }));
      break;
  }

  // Common filter + gain
  card.appendChild(mkSelect('Filter', ['lowpass','highpass','bandpass','notch','allpass'], voice.filterType, v => { voice.filterType=v; updateVoiceParam(gen,voice); }));
  card.appendChild(mkSlider('Freq', voice.filterFreq, 20, 20000, 1, 'Hz', v => { voice.filterFreq=v; updateVoiceParam(gen,voice); }));
  card.appendChild(mkSlider('Q', voice.filterQ, 0.1, 20, 0.1, '', v => { voice.filterQ=v; updateVoiceParam(gen,voice); }));
  card.appendChild(mkSlider('Gain', voice.gain, 0, 1, 0.01, '', v => { voice.gain=v; updateVoiceParam(gen,voice); }));

  // LFO
  const lfo = document.createElement('div'); lfo.className = 'lfo-section';
  const ll = document.createElement('div'); ll.className = 'section-label'; ll.textContent = 'LFO';
  lfo.appendChild(ll);
  lfo.appendChild(mkSlider('Rate', voice.lfoRate, 0, 20, 0.01, 'Hz', v => { voice.lfoRate=v; if(isPlaying){stop();play();} }));
  lfo.appendChild(mkSlider('Depth', voice.lfoDepth, 0, 1, 0.01, '', v => { voice.lfoDepth=v; if(isPlaying){stop();play();} }));
  lfo.appendChild(mkSelect('Target', ['gain','frequency','filter'], voice.lfoTarget, v => { voice.lfoTarget=v; if(isPlaying){stop();play();} }));
  card.appendChild(lfo);

  return card;
}

function updateVoiceParam(gen, voice) {
  const gi = generators.indexOf(gen);
  if (gi < 0 || gi >= activeGens.length || !isPlaying) return;
  const vi = gen.voices.indexOf(voice);
  const vn = activeGens[gi]?.voiceNodes[vi];
  if (!vn) return;
  if (vn.filter) { vn.filter.type = voice.filterType; vn.filter.frequency.value = voice.filterFreq; vn.filter.Q.value = voice.filterQ; }
  if (vn.gain) vn.gain.gain.value = voice.gain;
  if (vn.source && voice.type === 'tone') { try { vn.source.frequency.value = voice.frequency; vn.source.detune.value = voice.detune; } catch(e){} }
}

function mkSlider(label, value, min, max, step, unit, onChange) {
  const row = document.createElement('div'); row.className = 'param-row';
  const lbl = document.createElement('label'); lbl.textContent = label;
  const inp = document.createElement('input'); inp.type = 'range'; inp.min = min; inp.max = max; inp.step = step; inp.value = value;
  const val = document.createElement('span'); val.className = 'value'; val.textContent = fmtVal(value, unit);
  inp.oninput = () => { const v = parseFloat(inp.value); val.textContent = fmtVal(v, unit); onChange(v); };
  row.appendChild(lbl); row.appendChild(inp); row.appendChild(val);
  return row;
}

function mkSelect(label, options, value, onChange) {
  const row = document.createElement('div'); row.className = 'param-row';
  const lbl = document.createElement('label'); lbl.textContent = label;
  const sel = document.createElement('select');
  for (const o of options) { const opt = document.createElement('option'); opt.value = o; opt.textContent = o; opt.selected = o === value; sel.appendChild(opt); }
  sel.onchange = () => onChange(sel.value);
  row.appendChild(lbl); row.appendChild(sel);
  return row;
}

function fmtVal(v, u) {
  if (u === 'Hz' && v >= 1000) return (v/1000).toFixed(1) + 'k';
  if (typeof v === 'number') {
    if (Number.isInteger(v) || Math.abs(v) >= 100) return v + (u ? ' '+u : '');
    return v.toFixed(2) + (u ? ' '+u : '');
  }
  return v + (u ? ' '+u : '');
}

// ---------------------------------------------------------------------------
// Globals
// ---------------------------------------------------------------------------
function syncGlobalsUI() {
  for (const [id, val, u] of [['g-duration',globals.duration,'s'],['g-fade-in',globals.fadeIn,'s'],['g-fade-out',globals.fadeOut,'s'],['g-reverb',globals.reverb,''],['g-master',globals.master,'']]) {
    const s = document.getElementById(id), ve = document.getElementById(id+'-val');
    if(s) s.value = val;
    if(ve) ve.textContent = u === 's' ? parseFloat(val).toFixed(1)+'s' : parseFloat(val).toFixed(2);
  }
}
function bindGlobals() {
  for (const [id, key, u] of [['g-duration','duration','s'],['g-fade-in','fadeIn','s'],['g-fade-out','fadeOut','s'],['g-reverb','reverb',''],['g-master','master','']]) {
    const s = document.getElementById(id), ve = document.getElementById(id+'-val');
    s.oninput = () => {
      const v = parseFloat(s.value); globals[key] = v;
      ve.textContent = u === 's' ? v.toFixed(1)+'s' : v.toFixed(2);
      if (key === 'master' && masterGain) masterGain.gain.value = v;
      if (key === 'reverb') { if(reverbGain) reverbGain.gain.value = v; if(dryGain) dryGain.gain.value = 1-v; }
    };
  }
}
function updateTransportUI() {
  const pb = document.getElementById('play-btn'), lb = document.getElementById('loop-btn');
  pb.textContent = isPlaying ? 'Playing...' : 'Play';
  pb.classList.toggle('active', isPlaying);
  lb.classList.toggle('active', isLooping);
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
function init() {
  renderPresets(); renderSavedScenes(); renderGenLibrary(); renderSfxFiles();
  bindGlobals(); syncGlobalsUI(); renderGenerators();

  document.getElementById('play-btn').onclick = () => { if(isPlaying) stop(); else play(); };
  document.getElementById('stop-btn').onclick = stop;
  document.getElementById('loop-btn').onclick = toggleLoop;
  document.getElementById('add-gen-btn').onclick = () => { generators.push(makeGenerator()); renderGenerators(); };
  document.getElementById('clear-all-btn').onclick = () => { if(generators.length===0) return; if(isPlaying) stop(); generators=[]; renderGenerators(); showToast('Cleared'); };
  document.getElementById('save-preset-btn').onclick = () => { const n=prompt('Scene name:'); if(n&&n.trim()) saveCustomPreset(n.trim()); };

  document.getElementById('project-new').onclick = newScene;
  document.getElementById('project-save').onclick = saveScene;
  document.getElementById('project-export-json').onclick = exportSceneJSON;
  document.getElementById('project-import-json').onclick = () => document.getElementById('import-json-input').click();
  document.getElementById('import-json-input').onchange = (e) => { if(e.target.files[0]) importSceneJSON(e.target.files[0]); e.target.value=''; };

  document.getElementById('import-sfx-btn').onclick = () => document.getElementById('sfx-file-input').click();
  document.getElementById('sfx-file-input').onchange = (e) => { if(e.target.files.length>0) importSfxFiles(e.target.files); e.target.value=''; };

  document.getElementById('download-ogg-btn').onclick = () => downloadAudio('ogg');
  document.getElementById('download-wav-btn').onclick = () => downloadAudio('wav');

  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
    if (e.code === 'Space') { e.preventDefault(); if(isPlaying) stop(); else play(); }
    if (e.code === 'Escape' && isPlaying) stop();
    if (e.code === 'KeyS' && (e.ctrlKey||e.metaKey)) { e.preventDefault(); saveScene(); }
  });

  updateTransportUI();
}

return { init };
})();

document.addEventListener('DOMContentLoaded', SynthLab.init);
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    port = 5001
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--port" and i < len(sys.argv) - 1:
            port = int(sys.argv[i + 1])

    url = f"http://127.0.0.1:{port}"
    print()
    print("  Synth Lab")
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
