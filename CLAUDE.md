# Inform 7 Central Hub

This folder is the single home for all Inform 7 authoring, compilation, and testing.
Any project under `C:\code\` that needs to generate, edit, or build Inform 7 source references this location.

## Directory Structure

```
C:\code\ifhub\
├── CLAUDE.md              ← You are here
├── .claude/skills/
│   ├── bash-pitfalls/     ← Triggered on *.sh edits (legacy bash scripts)
│   ├── kill-servers/      ← Kill dev/dashboard servers
│   ├── serve/             ← Start dev-server or dashboard
│   └── web-player-debug/  ← Triggered on play.html, *.ulx.js, parchment/** edits
├── reference/
│   ├── syntax-guide.md    ← Core Inform 7 syntax and structure
│   ├── text-formatting.md ← Text substitutions and output formatting
│   ├── world-model.md     ← Advanced kinds, properties, rooms/regions/backdrops, relations
│   ├── understanding.md   ← Understand command, parser tokens, and grammar
│   ├── lists.md           ← List operations, sorting, and iteration
│   ├── extensions.md      ← Extension system: including, authoring, versioning
│   ├── descriptions-adaptive-text.md ← Descriptions, quantifiers, adaptive text, dynamic change
│   ├── rulebooks.md       ← Action processing order, rules, going, persuasion, senses
│   ├── activities-phrases.md ← Activities, phrase definitions, control flow, decisions
│   ├── project-guide.md   ← Build, test, publish workflows (referenced by all project CLAUDE.md files)
│   ├── sound.md           ← Sound architecture: native blorb, decision record
│   ├── sound-overlay/     ← Archived JS overlay system (replaced by native blorb)
│   ├── css-overlay.md     ← CSS overlay system: three-tier theming architecture for play.html
│   ├── glk-styling.md    ← Glk text styles, colors, images, windows, hyperlinks (Emglken/AsyncGlk stack)
│   ├── parchment-troubleshooting.md ← Web player errors, sound gotchas, binary format
│   ├── windows-pitfalls.md ← Git Bash grep/subshell issues, MSYS2 interpreter build
│   ├── writing-with-inform.md ← OFFICIAL: Complete Inform 7 manual (25K lines, 27 chapters, ~500 examples)
│   ├── recipe-book.md      ← OFFICIAL: Problem-oriented companion (patterns by effect)
│   ├── inform7-contents.txt ← Table of contents for official docs
│   ├── inform7-handbook-v3.pdf ← Jim Aikin's Handbook v3.0 (community guide, current for 10.1.2)
│   └── inform7-for-programmers.pdf ← Ron Newcomb's guide (I7 explained for programmers)
├── tools/
│   ├── lib/               ← Shared Python library modules
│   │   ├── paths.py            ← Path resolution, compiler paths, project dirs
│   │   ├── output.py           ← Terminal colors (ANSI), status prefixes
│   │   ├── process.py          ← Subprocess wrappers (run, run_interpreter)
│   │   ├── config.py           ← project.conf parser (ProjectConfig dataclass)
│   │   ├── web.py              ← Web player utilities (base64, templates, validation)
│   │   ├── git.py              ← Git/GitHub operations
│   │   └── regex.py            ← PCRE pattern utilities (\K conversion)
│   ├── build_site.py      ← Assemble _site/ for deployment (legacy — zork1 only)
│   ├── snapshot.py        ← Freeze/update version snapshots (legacy — zork1 only)
│   ├── compile.py         ← I7→I6→Glulx→Blorb→web player compilation
│   ├── pipeline.py        ← Unified build pipeline orchestrator
│   ├── publish.py         ← Publish a project to its own GitHub Pages repo
│   ├── run.py             ← Interactive pipeline runner (Python CLI with arrow-key menus)
│   ├── dashboard.py       ← Flask web GUI for build pipeline (http://127.0.0.1:5000)
│   ├── regtest.py         ← Shared RegTest runner (used by all project test suites)
│   ├── validate_web.py    ← Post-build web player validation (7 checks)
│   ├── generate_blurb.py  ← Generate .blurb from story.ni sound declarations
│   ├── extract_commands.py ← Extract walkthrough commands from transcript or story.ni
│   ├── register_game.py   ← Register a game in IF Hub (adds to games.json + cards.json)
│   ├── push_hub.py        ← Push hub registry changes (games.json + cards.json) to GitHub
│   ├── new_project.py     ← Create a new project scaffold
│   ├── interpreters/      ← Native Windows CLI interpreters (built locally)
│   │   ├── build.sh            ← MSYS2 build script (clones + compiles from source)
│   │   ├── glulxe.exe          ← Glulx interpreter (gitignored, built by build.sh)
│   │   └── dfrotz.exe          ← Z-machine interpreter (gitignored, built by build.sh)
│   ├── testing/           ← Generic testing framework
│   │   ├── run_walkthrough.py  ← Walkthrough runner (config-driven)
│   │   ├── find_seeds.py       ← RNG seed sweeper (config-driven)
│   │   ├── run_tests.py        ← RegTest wrapper (config-driven)
│   │   └── generate-guide.py   ← Walkthrough guide generator
│   ├── dev-server.py      ← Multi-root dev server (serves hub + all games at production URLs)
│   ├── archive/bash/      ← Archived original bash scripts (reference only)
│   └── web/               ← Web player setup
│       ├── setup_web.py        ← Bootstrap a Parchment web player for any project
│       ├── setup_basic.py      ← Bootstrap a BASIC web player (wwwbasic, qbjc, applesoft, jsdos)
│       ├── generate_pages.py   ← Generate index.html + source.html from templates
│       ├── play-template.html  ← HTML template (__TITLE__, __STORY_FILE__ placeholders)
│       ├── landing-template.html ← Landing page template (ifhub:* meta tags + __PLACEHOLDER__ values)
│       ├── source-template.html  ← Source browser template (syntax-highlighted viewer)
│       ├── templates/          ← Play template library (one per engine)
│       │   ├── play-mood.html       ← Mood-enabled Parchment template (palette transitions)
│       │   ├── play-parchment.html  ← Inform 7 / Z-machine (Parchment)
│       │   ├── play-wwwbasic.html   ← GW-BASIC (Google wwwBASIC)
│       │   ├── play-qbjc.html       ← QBasic/GW-BASIC (qbjc + xterm.js)
│       │   ├── play-applesoft.html  ← Apple II (jsbasic)
│       │   └── play-jsdos.html      ← DOS (js-dos / DOSBox)
│       └── parchment/          ← Shared Parchment 2025.1 library (copy, don't symlink)
│           ├── jquery.min.js   ← jQuery
│           ├── main.js         ← Parchment game loader
│           ├── main.css        ← Layout styling
│           ├── parchment.js    ← Parchment engine
│           ├── parchment.css   ← Engine styling
│           ├── quixe.js        ← Quixe interpreter (JS Glulx)
│           ├── glulxe.js       ← Glulxe interpreter (WASM)
│           ├── ie.js           ← IE compatibility (loaded with nomodule)
│           ├── bocfel.js       ← Z-machine interpreter
│           ├── resourcemap.js  ← Resource mapping (images/sounds)
│           ├── zvm.js          ← Z-machine VM
│           ├── waiting.gif     ← Loading indicator
│           └── mood-engine.js  ← Shared mood palette engine (copied to projects by --mood)
├── projects/              ← Game projects
│   ├── dracula/           ← Dracula: Inform 7 Edition
│   ├── feverdream/        ← Fever Dream
│   ├── sample/            ← Sample practice game
│   └── zork1/             ← Zork I: Inform 7 Edition
│       ├── v0/, v1/, ...  ← Frozen version snapshots (legacy, zork1 only)
│       ├── lib/parchment/ ← Parchment engine + latest game binary
│       └── index.html     ← Landing page (+ play.html, source.html, etc.)
└── ifhub/                 ← IF Hub web player
    ├── index.html         ← Landing page (reads cards.json, renders cards with Source/Walkthrough links)
    ├── app.html           ← Split-pane player (game + source viewer)
    ├── play.html          ← Shared player page (standalone use)
    ├── themes.js          ← Platform theme system (10 retro themes)
    ├── importing.html     ← Guide for adding new games to the hub
    ├── games.json         ← Game registry (titles, URLs, engine, tags, sourceBrowser)
    ├── cards.json         ← Card metadata for landing page (engine, tags, versions)
    ├── hubs.json          ← Hub/collection definitions (filter by engine/tag)
    └── lib/parchment/     ← Hub's OWN Parchment copy (separate from tools/web/)
```

## Compiler

Inform 7 is installed system-wide via the GUI installer:

- **IDE**: `C:\Program Files\Inform7IDE\Inform.exe`
- **I7 compiler**: `C:\Program Files\Inform7IDE\Compilers\inform7.exe`
- **I6 compiler**: `C:\Program Files\Inform7IDE\Compilers\inform6.exe`
- **Internal**: `C:\Program Files\Inform7IDE\Internal`

CLI compilation — compile directly from `story.ni`, no `.inform` bundle needed:
```bash
# Standard compilation (no sound):
python /c/code/ifhub/tools/compile.py <game-name>

# With native blorb sound (embeds .ogg audio in .gblorb):
python /c/code/ifhub/tools/compile.py <game-name> --sound

# Compile from alternate source (e.g., a frozen version snapshot):
python /c/code/ifhub/tools/compile.py <game-name> --source <path/to/story.ni> --compile-only
```

For manual compilation steps, see `reference/build-pipeline.md`. Do NOT create `.inform/` IDE project bundles — the `-source` and `-o` flags let us compile without them.

## Testing

### Shared Tools
- `tools/regtest.py` — RegTest runner, used by all projects
- `tools/testing/` — Generic testing framework (walkthrough runner, seed sweeper, RegTest wrapper)

### Interpreters

**Native Windows** (preferred — no WSL needed):
- **glulxe.exe** (Glulx): `tools/interpreters/glulxe.exe` — built from source via MSYS2
- **dfrotz.exe** (Z-machine): `tools/interpreters/dfrotz.exe` — built from source via MSYS2
- Build with: `bash tools/interpreters/build.sh` (requires MSYS2 UCRT64 with gcc + make)
- These are gitignored — each developer builds locally

**WSL fallback** (used when native interpreters are not available):
- **glulxe** (Glulx): `~/glulxe/glulxe` — for Inform 7 compiled games
- **dfrotz** (Z-machine): `~/frotz-install/usr/games/dfrotz` — for ZIL compiled games

The test framework auto-detects native interpreters via `project.conf` platform detection. If `tools/interpreters/glulxe.exe` exists and is executable on Git Bash/MSYS, it is used directly. Otherwise, tests fall back to WSL with health checks.

### Testing Framework (`tools/testing/`)

The testing framework provides three reusable Python scripts driven by a per-project `project.conf`:

| Script | Purpose |
|---|---|
| `run_walkthrough.py` | Runs a walkthrough through an interpreter with RNG seeding and diagnostics |
| `find_seeds.py` | Sweeps RNG seeds to find ones where the walkthrough achieves a passing score |
| `run_tests.py` | Wraps `regtest.py` with project-specific engine/game/test file |
| `generate-guide.py` | Generates rich `walkthrough-guide.txt` from walkthrough commands + transcript (item pickups, combat, containers, stages, NPC interactions; auto-detects sound prompt; preserves hand-written guides) |

All three test scripts require `--config PATH` pointing to a project's `tests/project.conf`. The config file defines:

- Engine paths, seed flags, and game file paths (primary + optional alternate)
- Score extraction regex patterns and pass threshold
- Diagnostic grep patterns (deaths, won-flag)
- RegTest file, engine, and game paths

Config files are parsed by `tools/lib/config.py` which extracts key=value pairs via regex (no bash sourcing needed).

#### Adding Testing to a New Project

1. Create `<name>/tests/project.conf` (see `projects/zork1/tests/project.conf` as a template)
2. Add walkthrough data files (`tests/inform7/walkthrough.txt`), seeds.conf, and regtest files as needed
3. Run tests using the framework directly with `--config`:

```bash
# Walkthrough
python tools/testing/run_walkthrough.py --config projects/<name>/tests/project.conf --seed 5

# Seed sweep
python tools/testing/find_seeds.py --config projects/<name>/tests/project.conf

# Regtests
python tools/testing/run_tests.py --config projects/<name>/tests/project.conf
```

No per-project wrapper scripts needed — all projects use the same framework scripts with `--config`.

### Per-Project Tests
Each project has a `tests/` subfolder with project-specific config, data, and wrapper scripts.
The `project.conf` file centralizes all project-specific paths and patterns.

## Build Pipeline (`tools/pipeline.py`)

A thin orchestrator that chains existing scripts in order with error handling. Every existing script continues to work standalone.

### Usage

```bash
# Default: compile only (fast dev iteration)
python /c/code/ifhub/tools/pipeline.py zork1

# Compile + test
python /c/code/ifhub/tools/pipeline.py zork1 compile test

# Full pipeline (local only)
python /c/code/ifhub/tools/pipeline.py zork1 --all       # compile test push

# Ship: compile + test + register + publish + push hub
python /c/code/ifhub/tools/pipeline.py zork1 --ship

# Resume after failure
python /c/code/ifhub/tools/pipeline.py zork1 --continue

# Other flags
#   --force         Skip staleness checks
#   --dry-run       Show what would happen
#   --message "msg" Commit message for push/publish stage
```

### Pipeline Stages

| Stage | What it does | Calls |
|-------|-------------|-------|
| **compile** | I7 → I6 → Glulx → Blorb(if sound) → web player + pages | `compile.py` (auto-generates `index.html` + `source.html` if missing) |
| **test** | Walkthrough + regtest + guide regen + sync to web root | `run_walkthrough.py`, `generate-guide.py`, `run_tests.py` |
| **register** | Add to `games.json` + `cards.json` (idempotent, reads metadata from `story.ni`) | `register_game.py` |
| **publish** | Push project to its own GitHub Pages repo | `publish.py` |
| **push-hub** | Commit + push hub registry changes | `push_hub.py` |
| **push** | Stage all ifhub changes, show summary, prompt before commit/push | `git` |

Default with no stages = `compile` only. `--ship` = compile test register publish push-hub. Stages are reordered to pipeline order automatically.

### Project Capability Detection

The pipeline reads `PIPELINE_*` fields from `tests/project.conf`:

```bash
PIPELINE_SOUND=true                 # compile with --sound
PIPELINE_HUB_ID="zork1"            # game ID in games.json
PIPELINE_TESTS="walkthrough,regtest"  # available test types
```

Projects without these fields get fallback inference from the filesystem (e.g., `Sounds/` directory = sound enabled).

### Walkthrough File Sync

Each project has walkthrough data in two places:
- **`tests/inform7/`** — canonical source, generated by the test framework
- **Project root** — served by `walkthrough.html` on GitHub Pages

The pipeline's test stage keeps them in sync automatically:
1. `run_walkthrough.py` generates `walkthrough_output.txt` and copies it to the web root via `--copy-output`
2. `generate-guide.py` regenerates `walkthrough-guide.txt` from the walkthrough + transcript
3. The guide is copied to the web root alongside the transcript

**When editing manually** (outside the pipeline): after running the walkthrough test, always regenerate the guide and copy both files to the project root:
```bash
# After running walkthrough test:
python tools/testing/generate-guide.py \
    --walkthrough projects/<game>/tests/inform7/walkthrough.txt \
    --transcript projects/<game>/tests/inform7/walkthrough_output.txt \
    -o projects/<game>/tests/inform7/walkthrough-guide.txt
cp projects/<game>/tests/inform7/walkthrough_output.txt projects/<game>/
cp projects/<game>/tests/inform7/walkthrough-guide.txt projects/<game>/
```

### Staleness Detection

Pipeline writes `.pipeline-state` (gitignored) after each stage. Source/binary hashes are compared to skip redundant work. Use `--force` to override.

## Web Player (`tools/web/`)

Parchment 2025.1 is a browser-based Glulx interpreter that plays `.ulx` and `.gblorb` games in any modern browser. The shared library files (12 files) live in `tools/web/parchment/` — each project gets its own copy.

### Adding a Web Player to a New Project

Use the setup script:
```bash
# Standard (no sound embedded):
python /c/code/ifhub/tools/web/setup_web.py \
    --title "My Game" \
    --ulx /path/to/game.ulx \
    --out /path/to/project

# With native blorb sound:
python /c/code/ifhub/tools/web/setup_web.py \
    --title "My Game" \
    --blorb /path/to/game.gblorb \
    --out /path/to/project

# With mood palette system:
python /c/code/ifhub/tools/web/setup_web.py \
    --title "My Game" \
    --ulx /path/to/game.ulx \
    --out /path/to/project \
    --mood
```

This creates:
```
project/
├── play.html                  ← Ready-to-serve player page
└── lib/parchment/
    ├── jquery.min.js          ← jQuery
    ├── main.js                ← Parchment loader
    ├── main.css               ← Layout styling
    ├── parchment.js           ← Parchment engine
    ├── parchment.css          ← Engine styling
    ├── quixe.js               ← Quixe interpreter (JS Glulx)
    ├── glulxe.js              ← Glulxe interpreter (WASM)
    ├── ie.js                  ← IE compatibility (nomodule)
    ├── bocfel.js              ← Z-machine interpreter
    ├── resourcemap.js         ← Resource mapping
    ├── zvm.js                 ← Z-machine VM
    ├── waiting.gif            ← Loading indicator
    └── game.ulx.js            ← Base64-encoded game binary (or .gblorb.js)
```

To serve locally:
```bash
python -m http.server 8000 --directory project
# then open http://localhost:8000/play.html
```

After recompiling the game, update the web binary:
```bash
B64=$(base64 -w 0 game.ulx) && echo "processBase64Zcode('${B64}')" > web/lib/parchment/game.ulx.js
```

### Sound

Compile with `--sound` to embed `.ogg` audio in a `.gblorb` binary. See `reference/sound.md` for full architecture and gotchas.

### IF Hub — Serve-in-Place Architecture

The hub at `ifhub/` serves games **in-place** — it iframes each game's own play page directly from the game's GitHub Pages URL. No files are copied into the hub; each game project is the single source of truth for its own assets.

**How it works:**
- `games.json` contains URL-based fields (`playUrl`, `sourceUrl`, `walkthroughUrl`, `landingUrl`) pointing to each game's own pages
- `app.html` loads `iframe.src = game.playUrl` — one line, no file construction
- Source viewer fetches `game.sourceUrl` (same origin on GitHub Pages = works)
- All games deploy to `johnesco.github.io/<game>/`, so same-origin iframes and fetch work freely

**Adding a new game:**
1. **Enable GitHub Pages** on the game repo — `publish.py` does this automatically (workflow deployment via GitHub Actions)
2. Add an entry to `games.json` with `id`, `title`, and URL fields
3. Add card metadata to `cards.json`
4. Verify `johnesco.github.io/<game>/play.html` loads before adding to the hub

**Local development:**
```bash
python tools/dev-server.py [--port 8000]
# Maps /ifhub/* → ifhub/, /<game>/* → projects/<game>/
# Open http://127.0.0.1:8000/ifhub/app.html
```

### Multi-Hub Collections

The hub supports curated collections via query-param filtering. A game can belong to multiple collections. The default URL (no params) shows all games.

**Files:**
- `hubs.json` — Hub definitions with filter criteria (`engine` match, `tag` includes, or both for AND logic)
- `cards.json` / `games.json` — Each entry has `engine` (string: `inform7`, `ink`, `basic`) and `tags` (string array)

**How it works:**
- `index.html` fetches `cards.json` + `hubs.json`, parses `?hub=X`, renders a hub bar, filters cards
- `app.html` fetches `games.json` + `hubs.json`, filters the dropdown when `?hub=X` is present
- Hub links are `<a href="?hub=X">` — statically shareable URLs
- Play buttons pass `&hub=X` to `app.html` to maintain the filtered context

**Adding a new hub:** Edit `hubs.json`:
```json
{ "id": "my-hub", "title": "My Collection", "description": "Description.", "filter": { "tag": "my-tag" } }
```

**Adding a game to a hub:** Add the matching `engine` or tag to the game's entry in `cards.json` and `games.json`.

**Registration with engine/tags:**
```bash
python tools/register_game.py --name game-id --title "Title" --engine ink --tags "horror,classic"
```

### CSS Overlay Theming

Each game's `play.html` layers custom CSS on top of Parchment's base styles. Three tiers: Parchment base → static overlay (all projects) → dynamic mood system (zork1 v3, feverdream, seasons). The shared mood engine (`tools/web/parchment/mood-engine.js`) provides room detection, palette transitions, and hooks for game-specific effects. See `reference/css-overlay.md` for full authoring guide.

**Platform theme override:** When a platform theme is selected in the hub's style dropdown, `app.html` directly injects `<style id="ifhub-theme-override">` into all same-origin iframes (game, source, walkthrough) via `contentDocument`. Engine-specific CSS builders (`buildParchmentCSS`, `buildInkCSS`, `buildBasicCSS`, `buildChromeCSS`) target the correct selectors for each page type. Games with `overlayLabel` in `games.json` are exempt from direct injection — they receive `ifhub:applyTheme` / `ifhub:restoreOverlay` via postMessage so their own listener can coordinate `body.platform-theme-active` to suppress visual effects while the mood engine continues running. Non-overlay game `play.html` files do not need a theme listener script.

**Adding mood theming to a new project:**
1. Copy `tools/web/templates/play-mood.html` → `projects/<game>/play-template.html`
2. Add palettes, room zones, and CSS effects
3. Add `MoodEngine.init({...})` in a `<script>` block
4. Build: `python tools/compile.py <game> --force` (auto-detects mood-engine.js in template)

### Troubleshooting

For Parchment errors ("Error loading story 200", "Error loading engine: 404"), sound gotchas, `.ulx.js` format issues, and MutationObserver quirks, see `reference/parchment-troubleshooting.md`.

## Multi-Engine BASIC Support (`tools/web/setup_basic.py`)

The hub is engine-agnostic — any game that can produce a self-contained `play.html` works in the iframe player. A template library at `tools/web/templates/` provides ready-made player pages for multiple engines:

| Template | Engine | Dialect | Status |
|---|---|---|---|
| `play-parchment.html` | Parchment 2025.1 | Inform 7 / Z-machine | Production |
| `play-wwwbasic.html` | Google wwwBASIC | GW-BASIC (INPUT-based only) | Production |
| `play-qbjc.html` | qbjc + xterm.js | QBasic + GW-BASIC (GOTO, INKEY$) | Template ready |
| `play-applesoft.html` | jsbasic | Apple II Applesoft BASIC | Template ready |
| `play-jsdos.html` | js-dos (DOSBox) | Any DOS program | Template ready |

### Adding a BASIC Game

```bash
# GW-BASIC via wwwBASIC (embed .bas source inline):
python /c/code/ifhub/tools/web/setup_basic.py \
    --engine wwwbasic --title "My Game" \
    --source path/to/game.bas --out path/to/project

# QBasic via qbjc (pre-compile .bas -> .js first):
# Step 1: npm install -g qbjc && qbjc game.bas -o game.js
# Step 2:
python /c/code/ifhub/tools/web/setup_basic.py \
    --engine qbjc --title "My Game" \
    --compiled path/to/game.js --out path/to/project

# DOS via js-dos (create .jsdos bundle first):
python /c/code/ifhub/tools/web/setup_basic.py \
    --engine jsdos --title "My Game" \
    --bundle path/to/game.jsdos --out path/to/project
```

Options: `--version-label "v0 — Original BASIC"`, `--back-href "./"`, `--force`.

After generating `play.html`, register and publish like any other game:
```bash
python tools/register_game.py --name <id> --title "Game Title"
python tools/publish.py <id>
python tools/push_hub.py <id>
```

### Engine Selection Guide

| If the game... | Use engine | Why |
|---|---|---|
| Uses INPUT/LINE INPUT only | `wwwbasic` | Simplest, already proven (dracula v0) |
| Uses INKEY$, SCREEN, or structured QBasic | `qbjc` | Compiles to JS, handles real-time I/O |
| Is Apple II Applesoft BASIC | `applesoft` | Authentic green-screen look |
| Won't run in any JS interpreter | `jsdos` | Runs real DOS + real BASIC interpreter |
| Is Inform 7 / Z-machine | `parchment` | Use `setup_web.py` (not `setup_basic.py`) |
| Is a Sharpee game | `sharpee` | TypeScript IF engine, CSS variable theming |

### Sharpee Games (`tools/web/setup_sharpee.py`)

[Sharpee](https://sharpee.net/) is a TypeScript-based parser IF engine. Games build to a `dist/web/` directory containing `index.html` + `styles.css` + `{game}.js`. The hub integrates via CSS custom property injection — Sharpee already uses `--theme-*` variables.

```bash
# From a Sharpee build output:
python /c/code/ifhub/tools/web/setup_sharpee.py \
    --title "My Game" --dist path/to/dist/web/game/ --out path/to/project

# Register and publish:
python tools/register_game.py --name game-id --title "My Game" --engine sharpee
python tools/publish.py game-id
```

The setup script copies the dist files, renames `index.html` → `play.html`, and injects the IF Hub theme listener (maps hub themes to Sharpee's `--theme-*` CSS variables).

### Other Formats (No Engine Needed)

Games in these formats are already self-contained HTML — just create `play.html` manually and register:
- **Twine** — Export as single HTML file
- **Ink/Inkle** — ink.js runtime + JSON story
- **ChoiceScript** — Build to HTML
- **Custom JS / static HTML fiction** — Already browser-native

## New Game Publish Flow

End-to-end steps from `story.ni` to a fully deployed game on IF Hub. See `reference/project-guide.md` for detailed instructions and command examples.

**Streamlined flow** (after writing the game):
```bash
python tools/new_project.py "Title" game-name    # scaffold
# ... edit story.ni, create walkthrough ...
python tools/pipeline.py game-name --ship         # compile + test + register + publish + push hub
```

`compile.py` auto-generates `index.html` + `source.html` from `story.ni` metadata when they don't exist. The `register` stage reads title/description from `story.ni` — no CLI args needed. All steps are idempotent.

**Individual scripts** (still work standalone):

| Step | Script | What it produces |
|------|--------|-----------------|
| Scaffold | `tools/new_project.py` | Project directory with source, tests, CI, CLAUDE.md |
| Compile | `tools/compile.py` | `.ulx`, `play.html`, `walkthrough.html`, `index.html`, `source.html`, transcript, guide |
| Extract commands | `tools/extract_commands.py` | `walkthrough.txt` from transcript or source |
| Generate pages | `tools/web/generate_pages.py` | `index.html`, `source.html` (manual override) |
| Register | `tools/register_game.py` | `games.json` + `cards.json` entries |
| Publish | `tools/publish.py` | GitHub repo + Pages deployment |
| Push hub | `tools/push_hub.py` | Commits + pushes hub registry to GitHub |

No colons in game titles (Windows filename limitation — use dashes instead).

## Projects

Each Inform 7 project lives under `C:\code\ifhub\projects\`.

- Each project gets its own subfolder (e.g., `projects/zork1/`, `projects/sample/`)
- Do NOT create `.inform` bundles — compile directly using `-source` and `-o` flags
- The `story.ni` in each project subfolder is the **single source of truth** for that project
- Other repos (like `C:\code\resume\writing\`) may contain **read-only snapshots** of source for display — those are NOT for compilation or editing
- When a project compiles, the output (.ulx, .ulx.js) is used by the project's own web player

### Versioning (Legacy — zork1 only)

The `vN/` directory model (frozen snapshots with `snapshot.py` and `build_site.py`) is deployed legacy for zork1 and dracula. New projects should not use versioning — flat layout with a single `story.ni` is the standard. See `projects/zork1/CLAUDE.md` for the versioning workflow if maintaining those projects.

### Standard Project Layout

Every project follows this baseline structure. Each has a `CLAUDE.md` that references `reference/project-guide.md` for shared workflows.

```
projects/<game>/
├── CLAUDE.md              ← Project guide (points to hub for shared docs)
├── story.ni               ← Source of truth (Inform 7 source)
├── <game>.ulx             ← Compiled Glulx binary (gitignored)
├── .github/workflows/deploy-pages.yml ← GitHub Actions workflow for Pages
├── index.html             ← Landing page
├── play.html              ← Parchment player (CSS overlay theming)
├── source.html            ← Source browser
├── walkthrough.html       ← Walkthrough viewer
├── walkthrough.txt        ← Raw walkthrough commands (copy from tests/)
├── walkthrough-guide.txt  ← Annotated guide (copy from tests/)
├── walkthrough_output.txt ← Game transcript (copy from tests/)
├── lib/parchment/         ← Parchment engine + <game>.ulx.js (base64 binary)
└── tests/
    ├── project.conf       ← Project-specific test + pipeline configuration
    ├── seeds.conf         ← Golden seeds for deterministic testing
    └── inform7/           ← Canonical walkthrough data
        ├── walkthrough.txt
        ├── walkthrough-guide.txt
        └── walkthrough_output.txt
```

Optional additions per project:
- `Sounds/` + `<game>.gblorb` + `<game>.blurb` — sound projects (zork1, feverdream)
- `v0/`, `v1/`, etc. — version snapshots (legacy — zork1, dracula only)
- `<game>.regtest` — projects with regression test suites (zork1, sample)
- `README.md` — public-facing description (zork1, dracula)

### Known Projects

| Project | Sound | CSS Effects | Tests |
|---|---|---|---|
| zork1 | blorb (v3+) | Mood palettes, CRT, tree, egg, sword (v3) | walkthrough, regtest, scenarios |
| dracula | No | Static dark theme | walkthrough |
| feverdream | blorb | Mood palettes, monitor, glass, fungus, spray | walkthrough (scoreless) |
| sample | No | Static dark theme | walkthrough, regtest |

All projects have `CLAUDE.md` referencing `reference/project-guide.md`, plus `project.conf` for the shared testing framework. See `reference/css-overlay.md` for the play.html theming architecture.

Games with `overlayLabel` in `games.json` (zork1 v3+, feverdream, seasons) show an overlay toggle in the hub's style dropdown.

## Key Rules for Generating story.ni Files

### File Format
- Inform 7 source files are plain text with a `.ni` extension
- The file is traditionally named `story.ni`
- First line must be the title and author: `"Title" by "Author Name"`
- Use natural English syntax — Inform 7 reads like prose, not code

### Organization
- Use `Part`, `Chapter`, `Section` headings to organize (in that hierarchy order)
- Parts are top-level, Chapters nest inside Parts, Sections inside Chapters

### Special Characters in Text
Inform 7 does NOT allow literal special characters in `say` strings. Use substitutions:
- `[apostrophe]` for `'` inside strings
- `[quotation mark]` for `"` inside strings
- `[bracket]` and `[close bracket]` for `[` and `]`
- Never use curly quotes or smart quotes

### Text Output Formatting
See `reference/text-formatting.md` for complete list. Key ones:
- `[paragraph break]` — blank line between paragraphs
- `[line break]` — newline without blank line
- `[bold type]` / `[roman type]` — toggle bold on/off
- `[italic type]` / `[roman type]` — toggle italic on/off
- `[fixed letter spacing]` / `[variable letter spacing]` — monospace on/off

### Long Text Pattern
For long passages, break `say` statements into multiple sequential `say` calls within a `To say` phrase:
```inform7
To say my-long-text:
    say "First paragraph.[paragraph break]";
    say "Second paragraph.[paragraph break]";
    say "Third paragraph."
```
Then invoke with `say "[my-long-text]"` — note the name is hyphenated, not spaced.

### IF Banner Convention

The startup banner uniquely identifies every build. The compiler auto-generates:
```
Title
Subtitle by Author
Release N / Serial number YYMMDD / Inform 7 v10.1.2 / D
```

**A. Required bibliographic fields:**
```inform7
"Title" by "Author"

The story headline is "A Subtitle".
The story genre is "Genre".
The release number is N.
The story creation year is YYYY.
The story description is "Brief description."
```

**B. Release number = version number:**
- Versioned projects: v1→1, v2→2, v3→3
- Non-versioned: sequential (1, 2, 3...)
- Never encode dates or other data in the release number

**C. Serial number = build fingerprint:**
- Auto-generated by compiler (YYMMDD compilation date) — never hardcode
- "Release 3 / Serial number 260308" = v3, compiled March 8, 2026

**D. Custom attribution uses `After printing the banner text`:**
```inform7
After printing the banner text:
    say "Custom lines here[paragraph break]".
```
Never use `When play begins: say "banner..."` — it creates a double header.

**E. Build tracing:** Title + Release + Serial uniquely identifies any binary's source and build date.

### Common Patterns
See `reference/syntax-guide.md` for full reference. Quick hits:
- Kinds: `A widget is a kind of thing.`
- Properties: `A widget has text called the label.`
- Rooms: `The Kitchen is a room. "Description here."`
- Actions: `Instead of pushing the button: say "Click."`
- Custom actions: `Requesting help is an action out of world applying to nothing.`
- Understand: `Understand "help" as requesting help.`

### Verb Help System

A reusable source template at `tools/verb-help-template.ni` that reduces guess-the-verb frustration. Copy the Chapter into any `story.ni` to get:
- **Enhanced parser errors** — actionable messages instead of cryptic defaults
- **VERBS command** — categorized list of available verbs
- **HELP command** — brief orientation for parser IF newcomers
- **~35 synonym mappings** — covers the most common guess-the-verb failures (inspect→examine, grab→take, etc.)
- **USE verb handler** — redirects the most common unrecognized verb to specific verbs

See `reference/verb-help.md` for the full authoring guide. Piloted on `projects/sample/`.

### Testing
- Inform 7 compiles to Glulx (.ulx) or Z-machine (.z8)
- Web playable via Quixe (Glulx interpreter in JS)
- Always test: rooms are reachable, actions respond, text renders properly

## Windows Notes

All tooling is Python — no bash dependency for build, test, or deploy workflows. Native interpreters (`glulxe.exe`, `dfrotz.exe`) are built via MSYS2 (see `tools/interpreters/build.sh`). Original bash scripts are archived in `tools/archive/bash/` for reference.

## Reference from Other Projects

Other project CLAUDE.md files can reference this hub:
```markdown
For Inform 7 syntax and conventions, see C:\code\ifhub\CLAUDE.md
```

<!-- SDLC WORKFLOW — Source: https://github.com/Johnesco/sdlc-baseline -->

## Instructions for Claude

> Full SDLC details (roles, 7-step workflow, board columns, automations, commit/branch conventions, severity matrix, idea-to-ship cycle) are in `docs/sdlc/`. The key rules are summarized below.

**The most important rule: Claude cannot QA its own work.** The Verify column is always human-owned.

### When Making Changes
1. **Ticket first** — Create a GitHub Issue before any code. Add to project board: `gh project item-add 3 --owner Johnesco --url [ISSUE_URL]`
2. **Read before editing** — Always read files before modifying them
3. **Follow existing patterns** — Match the coding style already in use
4. **Keep it simple** — Avoid over-engineering

### Maintaining Documentation

**UPDATE the project spec** (`docs/functional-spec.md`) when you:
- Add, modify, or remove any feature
- Fix a bug that changes observable behavior
- Change data formats or API contracts
- Alter UI behavior, states, or interactions

**UPDATE CLAUDE.md** when you:
- Add new features or pages
- Change the file structure
- Modify architectural patterns
- Make significant design decisions

**UPDATE README.md** when changes affect:
- Public-facing feature descriptions
- Setup or usage instructions
- Project overview

A change without a corresponding documentation update is considered **incomplete**.

### Commit Convention

```
#XX: description
```

Where `XX` is the GitHub Issue number. Use `Fixes #XX` in PR body for auto-close. Branch naming: `[type]/[short-description]` (feature/, fix/, docs/, task/, spike/).

### Project Board Reference

- **Board URL:** https://github.com/users/Johnesco/projects/3
- **Project number:** 3
- **Owner:** Johnesco
- **Add issue to board:** `gh project item-add 3 --owner Johnesco --url [ISSUE_URL]`

<!-- END SDLC WORKFLOW -->
