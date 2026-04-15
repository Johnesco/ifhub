# Project Guide — Build, Test, and Publish

Canonical reference for all IF Hub project workflows. Every project CLAUDE.md should link here instead of duplicating these instructions.

## Quick Reference

**Streamlined flow** (scaffold → write → ship):
```bash
python tools/new_project.py "Title" game-name    # scaffold
# ... edit story.ni, create walkthrough ...
python tools/pipeline.py game-name --ship         # compile + test + register + publish + push hub
```

**Individual scripts** (all still work standalone):

| Step | Script | What it produces |
|------|--------|-----------------|
| Compile (I7) | `tools/compile.py <name>` | `.ulx`, `play.html`, `walkthrough.html`, `index.html`, `source.html`, transcript, guide |
| Compile (Sharpee) | `tools/compile_sharpee.py <name>` | `play.html`, `*.js` bundle, `styles.css`, `theme-listener.js` |
| Extract commands | `tools/extract_commands.py` | `walkthrough.txt` from transcript or source |
| Generate pages | `tools/web/generate_pages.py` | `index.html`, `source.html` (manual override) |
| Register | `tools/register_game.py` | `games.json` + `cards.json` entries |
| Publish | `tools/publish.py <name>` | GitHub repo + Pages deployment |
| Push hub | `tools/push_hub.py <name>` | Commits + pushes hub registry to GitHub |

## Building

### Inform 7 (compile.py)

```bash
# Standard compilation (no sound):
python /c/code/ifhub/tools/compile.py <name>

# With native blorb sound (embeds .ogg audio in .gblorb):
python /c/code/ifhub/tools/compile.py <name> --sound

# Compile from alternate source (e.g., a frozen version snapshot):
python /c/code/ifhub/tools/compile.py <name> --source <path/to/story.ni> --compile-only
```

If `tests/inform7/walkthrough.txt` exists, compile.py automatically runs the walkthrough, generates the transcript and guide, and copies all walkthrough files to the web root. It also auto-generates `index.html` and `source.html` from `story.ni` metadata if they don't exist.

### Sharpee (built outside IF Hub)

Sharpee builds are owned by the **`/c/code/npmsharpee/`** workspace, not IF Hub. IF Hub is the *target* a Sharpee game ships to via the intake API. The game is authored, built, and tested **in-place inside its own folder**, then registered/published into IF Hub from there.

Game source lives in:
- `/c/code/text-games/sharpee/<game>/` — user-authored games
- `/c/code/npmsharpee/from-fork/<game>/` — pristine upstream mirrors

Each game folder builds **in-place** into `<game>/browser/` (or `<game>/browser/<subpath>/` for multi-version projects). The `browser/` directory IS the deployable artifact: `play.html`, the bundled `*.js`, `styles.css`, plus `source.html` and `walkthrough.html` (rendered from IF Hub's shared `tools/web/source-template.html` and `walkthrough-template.html`).

**Build + ship a Sharpee game** (run from `/c/code/npmsharpee/`):

```bash
./ship.sh <game>                  # build only — open <game>/browser/play.html
./ship.sh <game> hub-local        # build + register with on-disk IF Hub
./ship.sh <game> hub              # build + register + publish + push hub registry
```

`ship.sh` orchestrates `tools/build.py` (esbuild + transcript tests + asset install) and the IF Hub intake scripts (`register_game.py`, `publish.py`, `push_hub.py`). It does NOT use `tests/project.conf`; Sharpee config is declared in `<game>/ifhub.conf` plus per-version overrides in IF Hub's `games-registry.json` (e.g. `entry`, `binary`, `subpath`, `walkthrough` for multi-version projects).

**Scaffolding a new Sharpee game:**
```bash
cd /c/code/text-games/sharpee
npx @sharpee/sharpee init <game-name> -y
cd <game-name> && npx @sharpee/sharpee init-browser && npm install
# Add an ifhub.conf next to package.json (title, source, walkthrough, tags)
# Add a registry entry to /c/code/ifhub/games-registry.json
cd /c/code/npmsharpee && ./ship.sh <game-name> hub-local
```

For details on the npmsharpee build chain and authoring conventions see `/c/code/npmsharpee/CLAUDE.md` and `reference/sharpee-author-guide.md`.

### Pipeline (all engines)

```bash
# Default: compile only (fast dev iteration)
python /c/code/ifhub/tools/pipeline.py <name>

# Compile + test
python /c/code/ifhub/tools/pipeline.py <name> compile test

# Full pipeline (local only)
python /c/code/ifhub/tools/pipeline.py <name> --all       # compile test push

# Ship: compile + test + register + publish + push hub
python /c/code/ifhub/tools/pipeline.py <name> --ship

# Resume after failure
python /c/code/ifhub/tools/pipeline.py <name> --continue

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

### Capability Detection

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
python tools/testing/generate-guide.py \
    --walkthrough <game>/tests/inform7/walkthrough.txt \
    --transcript <game>/tests/inform7/walkthrough_output.txt \
    -o <game>/tests/inform7/walkthrough-guide.txt
cp <game>/tests/inform7/walkthrough_output.txt <game>/
cp <game>/tests/inform7/walkthrough-guide.txt <game>/
```

### Staleness Detection

Pipeline writes `.pipeline-state` (gitignored) after each stage. Source/binary hashes are compared to skip redundant work. Use `--force` to override.

### Source Location Patterns

Source lives where the engine's toolchain naturally expects it. Web deliverables land in the game's own directory.

| Engine | Source location | Config pointer | Compile wrapper |
|--------|----------------|----------------|-----------------|
| I7 | `<game>/story.ni` | — (in-project) | `compile.py` |
| Rez | `<game>/src/*.rez` | Optional `REZ_DIR` for external | `compile_rez.py` |
| wwwbasic | `<game>/*.bas` | `SOURCE=<file>` in project.conf | `setup_basic.py` (via pipeline) |
| applesoft | `<game>/*.bas` | `SOURCE=<file>` in project.conf | `setup_basic.py` (via pipeline) |
| Ink | `<game>/*.ink` | `SOURCE=<file>` in project.conf | `setup_ink.py` (via pipeline) |
| Sharpee | `text-games/sharpee/<game>/` or `npmsharpee/from-fork/<game>/` | `<game>/ifhub.conf` + `games-registry.json` | `npmsharpee/tools/ship.sh` (in-place build to `<game>/browser/`) |

Each BASIC dialect (wwwbasic, qbjc, applesoft, bwbasic) must be specified explicitly via `ENGINE=` in `project.conf` — there is no generic "basic" fallback.

## Testing

Tests use the shared framework at `C:\code\ifhub\tools\testing\`. Platform detection in `project.conf` auto-selects native `glulxe.exe` (Git Bash) or WSL `glulxe` (Linux).

```bash
# Run walkthrough
python /c/code/ifhub/tools/testing/run_walkthrough.py --config tests/project.conf

# Run walkthrough without seed (first time or no golden seeds)
python /c/code/ifhub/tools/testing/run_walkthrough.py --config tests/project.conf --no-seed --no-save

# Run regression tests
python /c/code/ifhub/tools/testing/run_tests.py --config tests/project.conf

# Find golden seeds
python /c/code/ifhub/tools/testing/find_seeds.py --config tests/project.conf

# Or via pipeline
python /c/code/ifhub/tools/pipeline.py <name> compile test
```

### Interpreters

- **Native Windows** (preferred): `tools/interpreters/glulxe.exe` + `dfrotz.exe` — built via MSYS2, auto-detected by `project.conf`
- **WSL fallback**: `~/glulxe/glulxe` + `~/frotz-install/usr/games/dfrotz`

### Sharpee Testing

Sharpee uses its own transcript-based test system (`@sharpee/transcript-tester`). Tests live in the game folder (same folder that holds `src/` and `browser/`), not in IF Hub.

```bash
cd /c/code/text-games/sharpee/<game>     # or /c/code/npmsharpee/from-fork/<game>

# Build + run all transcript tests:
npx sharpee build --test

# Interactive play (REPL with debug commands):
npx transcript-test --play

# Run specific transcript file:
npx transcript-test walkthroughs/wt-01.transcript
```

`./ship.sh <game>` (from `/c/code/npmsharpee/`) runs the transcript tests automatically as part of the build; the single walkthrough selected via the rules in `sharpee_adapter.pick_walkthrough()` is used to generate `walkthrough.html` alongside `play.html`.

Transcript files use `> command` / `[OK: contains "text"]` assertions. See `/c/code/fork/sharpee/docs/testing/README.md` for the full format spec.

## Creating a Walkthrough

Three methods to create `tests/inform7/walkthrough.txt`:

**A. From a TRANSCRIPT file** (preferred):
1. Play the game and type `TRANSCRIPT` to start recording
2. Play through to completion
3. Extract commands:
```bash
mkdir -p ../text-games/i7/<name>/tests/inform7
python /c/code/ifhub/tools/extract_commands.py transcript.txt \
    -o ../text-games/i7/<name>/tests/inform7/walkthrough.txt
```

**B. From `Test me` in source** (for games with built-in test commands):
```bash
python /c/code/ifhub/tools/extract_commands.py --from-source ../text-games/i7/<name>/story.ni \
    -o ../text-games/i7/<name>/tests/inform7/walkthrough.txt
```

**C. Manual** (for short games): Write commands directly into the file, one per line.

After creating the walkthrough, recompile — `compile.py` automatically generates the transcript and guide.

## Generate Pages

```bash
python /c/code/ifhub/tools/web/generate_pages.py \
    --title "Game Title" \
    --meta "Subtitle" \
    --description "Game description" \
    --out ../text-games/i7/<name>
```

Generates `index.html` (landing page with Play/Source/Walkthrough links) and `source.html` (syntax-highlighted source browser).

## Register in IF Hub

```bash
python /c/code/ifhub/tools/register_game.py \
    --name <name> \
    --title "Game Title" \
    --meta "Subtitle" \
    --description "Game description"
```

Adds entries to `ifhub/games.json` and `ifhub/cards.json`.

## Publish to GitHub Pages

```bash
python /c/code/ifhub/tools/publish.py <name>
```

First run: creates `Johnesco/<name>` GitHub repo, pushes all files, enables GitHub Pages (workflow deployment via GitHub Actions). Subsequent runs: commits, pushes, and verifies Pages is enabled (catches repos created outside the first-time flow).

## Push Hub Changes

```bash
python /c/code/ifhub/tools/push_hub.py <name>
```

Stages `games.json` and `cards.json`, commits, and pushes. Skips if no changes.

## Play Locally

```bash
# Multi-root dev server (serves hub + all games at production URLs)
python /c/code/ifhub/tools/dev-server.py [--port 8000]
# Open http://127.0.0.1:8000/<name>/play.html

# Or simple server from project directory
python -m http.server 8000 --directory ../text-games/i7/<name>
# Open http://localhost:8000/play.html
```

## Shared Resources

| Resource | Location |
|----------|----------|
| Hub CLAUDE.md | `C:\code\ifhub\CLAUDE.md` |
| Syntax reference | `C:\code\ifhub\reference\syntax-guide.md` |
| Text formatting | `C:\code\ifhub\reference\text-formatting.md` |
| Sound architecture | `C:\code\ifhub\reference\sound.md` |
| CSS overlay theming | `C:\code\ifhub\reference\css-overlay.md` |
| Glk styling | `C:\code\ifhub\reference\glk-styling.md` |
| Testing framework | `C:\code\ifhub\tools\testing\` |
| Web player setup | `C:\code\ifhub\tools\web\` |
| Native interpreters | `C:\code\ifhub\tools\interpreters\` |
| RegTest runner | `C:\code\ifhub\tools\regtest.py` |
| Sharpee build + import | `C:\code\ifhub\tools\compile_sharpee.py` |
| Pipeline orchestrator | `C:\code\ifhub\tools\pipeline.py` |
| Parchment troubleshooting | `C:\code\ifhub\reference\parchment-troubleshooting.md` |

## Hub Collections

The hub supports curated collections via query-param filtering. A game can belong to multiple collections.

**Files:**
- `hubs.json` — Hub definitions with filter criteria (`engine` match, `tag` includes, or both for AND logic)
- `cards.json` / `games.json` — Each entry has `engine` (string) and `tags` (string array)

**How it works:**
- `index.html` and `app.html` fetch `hubs.json`, parse `?hub=X`, and filter games
- Hub links are `<a href="?hub=X">` — statically shareable URLs
- Play buttons pass `&hub=X` to `app.html` to maintain the filtered context

**Adding a new hub:** Edit `hubs.json`:
```json
{ "id": "my-hub", "title": "My Collection", "description": "Description.", "filter": { "tag": "my-tag" } }
```

**Registration with engine/tags:**
```bash
python tools/register_game.py --name game-id --title "Title" --engine ink --tags "horror,classic"
```

## Key Rules

- `story.ni` is the single source of truth for each Inform 7 project
- Sharpee game source lives in `/c/code/sharpee/<game>/`, not in the ifhub projects directory
- Do NOT create `.inform/` IDE bundles — compile directly using `-source` and `-o` flags
- For Inform 7 syntax and conventions, see `C:\code\ifhub\CLAUDE.md`
- The hub serves games in-place via iframe from each game's own GitHub Pages URL
