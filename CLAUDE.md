# Inform 7 Central Hub

This folder is the single home for all Inform 7 authoring, compilation, and testing.
Any project under `C:\code\` that needs to generate, edit, or build Inform 7 source references this location.

## Directory Structure

```
C:\code\ifhub\
├── CLAUDE.md              ← You are here
├── .claude/skills/
│   ├── bash-pitfalls/     ← Triggered on *.sh, project.conf, tools/** edits
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
│   ├── sound.md           ← Sound architecture: native blorb, decision record
│   ├── sound-overlay/     ← Archived JS overlay system (replaced by native blorb)
│   ├── css-overlay.md     ← CSS overlay system: three-tier theming architecture for play.html
│   ├── glk-styling.md    ← Glk text styles, colors, images, windows, hyperlinks (Emglken/AsyncGlk stack)
│   ├── parchment-troubleshooting.md ← Web player errors, sound gotchas, binary format
│   └── windows-pitfalls.md ← Git Bash grep/subshell issues, MSYS2 interpreter build
├── tools/
│   ├── build-site.sh      ← Assemble _site/ from flat project layout for deployment
│   ├── snapshot.sh        ← Freeze/update version snapshots (recompiles from frozen source)
│   ├── run.py             ← Interactive pipeline runner (Python CLI with arrow-key menus)
│   ├── regtest.py         ← Shared RegTest runner (used by all project test suites)
│   ├── interpreters/      ← Native Windows CLI interpreters (built locally)
│   │   ├── build.sh            ← MSYS2 build script (clones + compiles from source)
│   │   ├── glulxe.exe          ← Glulx interpreter (gitignored, built by build.sh)
│   │   └── dfrotz.exe          ← Z-machine interpreter (gitignored, built by build.sh)
│   ├── testing/           ← Generic testing framework
│   │   ├── run-walkthrough.sh  ← Walkthrough runner (config-driven)
│   │   ├── find-seeds.sh       ← RNG seed sweeper (config-driven)
│   │   ├── run-tests.sh        ← RegTest wrapper (config-driven)
│   │   ├── pcre_grep.py        ← Portable grep -oP replacement (Python re)
│   │   └── wsl-check.sh        ← WSL health check and path conversion
│   ├── dev-server.py      ← Multi-root dev server (serves hub + all games at production URLs)
│   ├── validate-web.sh    ← Post-build web player validation (7 checks)
│   ├── generate-blurb.sh  ← Generate .blurb from story.ni sound declarations
│   ├── extract-commands.sh ← Extract walkthrough commands from transcript or story.ni
│   ├── register-game.sh   ← Register a game in IF Hub (adds to games.json + cards.json)
│   ├── push-hub.sh        ← Push hub registry changes (games.json + cards.json) to GitHub
│   ├── publish.sh         ← Publish a project to its own GitHub Pages repo
│   └── web/               ← Web player setup
│       ├── setup-web.sh        ← Bootstrap a Parchment web player for any project
│       ├── generate-pages.sh   ← Generate index.html + source.html from templates
│       ├── play-template.html  ← HTML template (__TITLE__, __STORY_FILE__ placeholders)
│       ├── landing-template.html ← Landing page template (ifhub:* meta tags + __PLACEHOLDER__ values)
│       ├── source-template.html  ← Source browser template (syntax-highlighted viewer)
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
│           └── waiting.gif     ← Loading indicator
├── projects/              ← Game projects
│   ├── dracula/           ← Dracula: Inform 7 Edition
│   ├── feverdream/        ← Fever Dream
│   ├── sample/            ← Sample practice game
│   └── zork1/             ← Zork I: Inform 7 Edition
│       ├── v0/, v1/, ...  ← Frozen version snapshots (flat layout)
│       ├── lib/parchment/ ← Parchment engine + latest game binary
│       └── index.html     ← Landing page (+ play.html, source.html, etc.)
└── ifhub/                 ← IF Hub web player
    ├── index.html         ← Landing page (reads cards.json, renders cards with Source/Walkthrough links)
    ├── app.html           ← Split-pane player (game + source viewer)
    ├── play.html          ← Shared player page (standalone use)
    ├── importing.html     ← Guide for adding new games to the hub
    ├── games.json         ← Game registry (titles, URLs, sound flags, sourceBrowser)
    ├── cards.json         ← Card metadata for landing page
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
bash /c/code/ifhub/tools/compile.sh <game-name>

# With native blorb sound (embeds .ogg audio in .gblorb):
bash /c/code/ifhub/tools/compile.sh <game-name> --sound

# Compile from alternate source (e.g., a frozen version snapshot):
bash /c/code/ifhub/tools/compile.sh <game-name> --source <path/to/story.ni> --compile-only
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

The testing framework provides three reusable scripts driven by a per-project `project.conf`:

| Script | Purpose |
|---|---|
| `run-walkthrough.sh` | Runs a walkthrough through an interpreter with RNG seeding and diagnostics |
| `find-seeds.sh` | Sweeps RNG seeds to find ones where the walkthrough achieves a passing score |
| `run-tests.sh` | Wraps `regtest.py` with project-specific engine/game/test file |
| `generate-guide.py` | Generates rich `walkthrough-guide.txt` from walkthrough commands + transcript (item pickups, combat, containers, stages, NPC interactions; auto-detects sound prompt; preserves hand-written guides) |
| `pcre_grep.py` | Portable `grep -oP` replacement using Python `re` (Git Bash lacks PCRE grep) |
| `wsl-check.sh` | WSL health check (`check_wsl_health`) and path conversion (`gitbash_to_wsl_path`) |

All three test scripts require `--config PATH` pointing to a project's `tests/project.conf`. The config file is a bash-sourceable file that defines:

- Platform detection (native Windows vs WSL interpreter paths)
- Engine paths, seed flags, and game file paths (primary + optional alternate)
- Score extraction regex patterns and pass threshold
- Diagnostic grep patterns (deaths, won-flag)
- RegTest file, engine, and game paths
- Optional `diagnostics_extra()` function for project-specific output

#### Adding Testing to a New Project

1. Create `<name>/tests/project.conf` (see `projects/zork1/tests/project.conf` as a template)
2. Create thin wrapper scripts in `<name>/tests/` that delegate to `tools/testing/`:
   ```bash
   #!/bin/bash
   SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
   PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
   # Platform-aware ifhub root
   if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
       I7_ROOT="/c/code/ifhub"
   else
       I7_ROOT="/mnt/c/code/ifhub"
   fi
   exec bash "$I7_ROOT/tools/testing/run-walkthrough.sh" --config "$SCRIPT_DIR/project.conf" "$@"
   ```
3. Add walkthrough data files, seeds.conf, and regtest files as needed

#### Generic vs Project Scripts

- **Generic** (`tools/testing/*.sh`): Use `--config` + `--alt` flags. Engine-agnostic.
- **Project wrappers** (`<name>/tests/*.sh`): Pre-configure `--config`, translate legacy flags (e.g., `--zil` → `--alt`).

Both invocation styles work:
```bash
# Via project wrapper — native (Git Bash, if interpreters built)
bash tests/run-walkthrough.sh --zil --seed 3

# Via project wrapper — WSL fallback (if no native interpreters)
wsl -e bash tests/run-walkthrough.sh --zil --seed 3

# Via generic framework directly
bash tools/testing/run-walkthrough.sh --config projects/zork1/tests/project.conf --alt --seed 3
```

### Per-Project Tests
Each project has a `tests/` subfolder with project-specific config, data, and wrapper scripts.
The `project.conf` file centralizes all project-specific paths and patterns.

## Build Pipeline (`tools/pipeline.sh`)

A thin orchestrator that chains existing scripts in order with error handling. Every existing script continues to work standalone.

### Usage

```bash
# Default: compile only (fast dev iteration)
bash /c/code/ifhub/tools/pipeline.sh zork1

# Compile + test
bash /c/code/ifhub/tools/pipeline.sh zork1 compile test

# Full pipeline (no snapshot)
bash /c/code/ifhub/tools/pipeline.sh zork1 --all       # compile test push

# Version release
bash /c/code/ifhub/tools/pipeline.sh zork1 --ship --version v4   # compile test snapshot push

# Resume after failure
bash /c/code/ifhub/tools/pipeline.sh zork1 --continue

# Other flags
#   --force         Skip staleness checks
#   --dry-run       Show what would happen
#   --message "msg" Commit message for push stage
```

### Pipeline Stages

| Stage | What it does | Calls |
|-------|-------------|-------|
| **compile** | I7 → I6 → Glulx → Blorb(if sound) → web player | `compile.sh` |
| **test** | Walkthrough + regtest + guide regen + sync to web root | `run-walkthrough.sh`, `generate-guide.py`, `run-tests.sh` |
| **snapshot** | Sync root source to `vN/`, recompile from it | `snapshot.sh` (requires `--version`) |
| **push** | Stage changes, show summary, prompt before commit/push | `git` |

Default with no stages = `compile` only. Stages are reordered to pipeline order automatically.

### Project Capability Detection

The pipeline reads `PIPELINE_*` fields from `tests/project.conf`:

```bash
PIPELINE_SOUND=true                 # compile with --sound
PIPELINE_VERSIONED=true             # has version directories (v0/, v1/, etc.)
PIPELINE_CURRENT_VERSION="v4"       # default --version for snapshot
PIPELINE_HUB_ID="zork1-v4"         # game ID in games.json
PIPELINE_TESTS="walkthrough,regtest"  # available test types
```

Projects without these fields get fallback inference from the filesystem (e.g., `Sounds/` directory = sound enabled).

### Walkthrough File Sync

Each project has walkthrough data in two places:
- **`tests/inform7/`** — canonical source, generated by the test framework
- **Project root** — served by `walkthrough.html` on GitHub Pages

The pipeline's test stage keeps them in sync automatically:
1. `run-walkthrough.sh` generates `walkthrough_output.txt` and copies it to the web root via `--copy-output`
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
bash /c/code/ifhub/tools/web/setup-web.sh \
    --title "My Game" \
    --ulx /path/to/game.ulx \
    --out /path/to/project/web

# With native blorb sound:
bash /c/code/ifhub/tools/web/setup-web.sh \
    --title "My Game" \
    --blorb /path/to/game.gblorb \
    --out /path/to/project/web
```

This creates:
```
project/web/
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
1. **Enable GitHub Pages** on the game repo — `publish.sh` does this automatically (workflow deployment via GitHub Actions)
2. Add an entry to `games.json` with `id`, `title`, and URL fields
3. Add card metadata to `cards.json`
4. Verify `johnesco.github.io/<game>/play.html` loads before adding to the hub

**Local development:**
```bash
python tools/dev-server.py [--port 8000]
# Maps /ifhub/* → ifhub/, /<game>/* → projects/<game>/
# Open http://127.0.0.1:8000/ifhub/app.html
```

### CSS Overlay Theming

Each game's `play.html` layers custom CSS on top of Parchment's base styles. Three tiers: Parchment base → static overlay (all projects) → dynamic mood system (zork1 v4, feverdream). See `reference/css-overlay.md` for full architecture.

### Troubleshooting

For Parchment errors ("Error loading story 200", "Error loading engine: 404"), sound gotchas, `.ulx.js` format issues, and MutationObserver quirks, see `reference/parchment-troubleshooting.md`.

## New Game Publish Flow

End-to-end steps to go from a `story.ni` file to a fully deployed game on IF Hub. Every step uses a script — no manual file creation.

### Step 1: Write the game

Create `projects/<name>/story.ni` (or use an existing source file). The first line must be `"Title" by "Author"`. No colons in the title (Windows filename limitation — use dashes instead).

### Step 2: First compile

```bash
bash /c/code/ifhub/tools/compile.sh <name>
```

Generates: `<name>.ulx`, `play.html`, `walkthrough.html`, Parchment libraries. If `tests/inform7/walkthrough.txt` exists, also generates the transcript and guide automatically.

### Step 3: Create the walkthrough

Play the game and record a transcript using one of these methods:

**A. From a TRANSCRIPT file** (preferred — works in Parchment, IDE, or any interpreter):
1. Play the game and type `TRANSCRIPT` at the prompt to start recording
2. Play through to completion
3. Save/download the transcript file
4. Extract commands:
```bash
mkdir -p projects/<name>/tests/inform7
bash /c/code/ifhub/tools/extract-commands.sh transcript.txt \
    -o projects/<name>/tests/inform7/walkthrough.txt
```

**B. From `Test me` in source** (for games with built-in test commands):
```bash
mkdir -p projects/<name>/tests/inform7
bash /c/code/ifhub/tools/extract-commands.sh --from-source projects/<name>/story.ni \
    -o projects/<name>/tests/inform7/walkthrough.txt
```

**C. Manual** (for short games): Write commands directly into `projects/<name>/tests/inform7/walkthrough.txt`, one per line.

### Step 4: Recompile (with walkthrough)

```bash
bash /c/code/ifhub/tools/compile.sh <name>
```

Now that `tests/inform7/walkthrough.txt` exists, compile.sh automatically:
- Runs the commands through `glulxe.exe` → generates `walkthrough_output.txt`
- Runs `generate-guide.py` → generates `walkthrough-guide.txt`
- Copies all walkthrough files to the web root

### Step 5: Generate landing page + source browser

```bash
bash /c/code/ifhub/tools/web/generate-pages.sh \
    --title "Game Title" \
    --meta "Subtitle" \
    --description "Game description" \
    --out projects/<name>
```

Generates: `index.html` (landing page with Play/Source/Walkthrough links), `source.html` (syntax-highlighted source browser).

### Step 6: Register in IF Hub

```bash
bash /c/code/ifhub/tools/register-game.sh \
    --name <name> \
    --title "Game Title" \
    --meta "Subtitle" \
    --description "Game description"
```

Adds entries to `ifhub/games.json` and `ifhub/cards.json`. Prints a reminder to run `publish.sh`.

### Step 7: Publish to GitHub Pages

```bash
bash /c/code/ifhub/tools/publish.sh <name>
```

First run: creates `Johnesco/<name>` GitHub repo, pushes all files, enables GitHub Pages (workflow deployment via GitHub Actions). If no workflow file exists, publish.sh auto-generates one. Subsequent runs: commits and pushes changes.

### Step 8: Push hub changes

```bash
bash /c/code/ifhub/tools/push-hub.sh <name>
```

Stages `games.json` and `cards.json`, commits, and pushes. Skips if no changes.

### Quick reference

| Step | Script | What it produces |
|------|--------|-----------------|
| Compile | `tools/compile.sh` | `.ulx`, `play.html`, `walkthrough.html`, transcript, guide |
| Extract commands | `tools/extract-commands.sh` | `walkthrough.txt` from transcript or source |
| Generate pages | `tools/web/generate-pages.sh` | `index.html`, `source.html` |
| Register | `tools/register-game.sh` | `games.json` + `cards.json` entries |
| Publish | `tools/publish.sh` | GitHub repo + Pages deployment |
| Push hub | `tools/push-hub.sh` | Commits + pushes hub registry to GitHub |

## Projects

Each Inform 7 project lives under `C:\code\ifhub\projects\`.

- Each project gets its own subfolder (e.g., `projects/zork1/`, `projects/sample/`)
- Do NOT create `.inform` bundles — compile directly using `-source` and `-o` flags
- The `story.ni` in each project subfolder is the **single source of truth** for that project
- Other repos (like `C:\code\resume\writing\`) may contain **read-only snapshots** of source for display — those are NOT for compilation or editing
- When a project compiles, the output (.ulx, .ulx.js) is used by the project's own web player

### Version Snapshots (opt-in)

Projects with multiple playable milestones store frozen snapshots in `vN/` directories at the project root (flat layout). Tools: `snapshot.sh` (freeze/update), `build-site.sh` (assemble `_site/` for local preview). GitHub Actions assembles `_site/` from site-level files + version directories. The `_site/` directory is gitignored. `snapshot.sh --update` recompiles from the version's own frozen `story.ni` (never overwrites it) and auto-detects `.gblorb` vs `.ulx` binary type.

### Standard Project Layout

Every project follows this baseline structure. Each has a `CLAUDE.md` with project-specific details.

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
    ├── run-walkthrough.sh ← Thin wrapper → tools/testing/run-walkthrough.sh
    ├── find-seeds.sh      ← Thin wrapper → tools/testing/find-seeds.sh
    ├── seeds.conf         ← Golden seeds for deterministic testing
    └── inform7/           ← Canonical walkthrough data
        ├── walkthrough.txt
        ├── walkthrough-guide.txt
        └── walkthrough_output.txt
```

Optional additions per project:
- `Sounds/` + `<game>.gblorb` + `<game>.blurb` — sound projects (zork1, feverdream)
- `v0/`, `v1/`, etc. — versioned projects with frozen snapshots (zork1, dracula)
- `run-tests.sh` + `<game>.regtest` — projects with regression test suites (zork1, sample)
- `README.md` — public-facing description (zork1, dracula)

### Known Projects

| Project | Sound | Versions | CSS Effects | Tests |
|---|---|---|---|---|
| zork1 | blorb (v3+) | v0–v4 | Mood palettes, CRT, tree, egg, sword (v4) | walkthrough, regtest, scenarios |
| dracula | No | v0 (BASIC) | Static dark theme | walkthrough |
| feverdream | blorb | None | Mood palettes, monitor, glass, fungus, spray | walkthrough (scoreless) |
| sample | No | None | Static dark theme | walkthrough, regtest |

All projects have `CLAUDE.md`, `project.conf`, and delegate to the shared testing framework. See `reference/css-overlay.md` for the play.html theming architecture.

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
- Versioned projects: v1→1, v2→2, v3→3, v4→4
- Non-versioned: sequential (1, 2, 3...)
- Never encode dates or other data in the release number

**C. Serial number = build fingerprint:**
- Auto-generated by compiler (YYMMDD compilation date) — never hardcode
- "Release 4 / Serial number 260304" = v4, compiled March 4, 2026

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

### Testing
- Inform 7 compiles to Glulx (.ulx) or Z-machine (.z8)
- Web playable via Quixe (Glulx interpreter in JS)
- Always test: rooms are reachable, actions respond, text renders properly

## Windows / Git Bash Pitfalls

Key pitfalls: no `grep -oP` (use `pcre_grep.py` or `grep -E`), pipe-to-`while read` loses variables (use `mapfile`), native interpreters require MSYS2 build. See `reference/windows-pitfalls.md` for full details and examples.

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
