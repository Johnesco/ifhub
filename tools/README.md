# Tools

Shared scripts for compiling, testing, and deploying Inform 7 projects.

## Project Lifecycle Scripts

These are the main scripts you'll use day-to-day. All take a `<game-name>` argument matching a directory under `projects/`.

### `new_project.py` — Create a New Project

Scaffolds a complete project with source, tests, CI, and documentation.

```bash
python tools/new_project.py "Game Title" game-name
```

Creates:
- `story.ni` — Starter Inform 7 source
- `CLAUDE.md` — Project guide
- `.gitignore` — Build output, IDE files
- `.github/workflows/deploy-pages.yml` — GitHub Pages deployment
- `tests/` — Full test suite (project.conf, starter regtest, walkthrough)

### `compile.py` — Compile a Project

Runs the full compilation pipeline and optionally updates the web player.

```bash
python tools/compile.py <game-name>                          # standard compile (ULX)
python tools/compile.py <game-name> --sound                  # with embedded blorb sound
python tools/compile.py <game-name> --source PATH            # compile from alternate story.ni
python tools/compile.py <game-name> --compile-only           # skip web player update
python tools/compile.py <game-name> --source PATH --compile-only --sound  # all flags combined
```

**Options:**
| Flag | Purpose |
|------|---------|
| `--sound` | Embed `.ogg` audio in a `.gblorb` binary |
| `--source PATH` | Use this `story.ni` instead of the project's own |
| `--compile-only` | Skip the web player update step (`setup_web.py` + `validate_web.py`) |

Steps (standard):
1. Inform 7 → Inform 6 (via `inform7.exe`)
2. Inform 6 → Glulx (via `inform6.exe`)
3. Clean up intermediate `.i6` file
4. Update web player (copies Parchment libs, base64-encodes `.ulx`) — skipped with `--compile-only`

Additional steps with `--sound`:
3. Generate `.blurb` manifest from sound declarations in `story.ni`
4. Build `.gblorb` blorb with embedded audio (via `inblorb`)
5. Clean up intermediates
6. Update web player (base64-encodes `.gblorb` instead of `.ulx`) — skipped with `--compile-only`

**Pre-flight checks** (run before expensive compilation):
- Rejects titles with colons (`:`) — invalid filenames on Windows
- Rejects `--sound` if `Sounds/` directory is missing at project root

Output: `projects/<name>/<name>.ulx` (+ `.gblorb` with `--sound`) and `projects/<name>/web/play.html` (unless `--compile-only`)

### `publish.py` — Publish to GitHub Pages

Publishes a project to GitHub Pages. On first run, creates the GitHub repo and enables Pages. On subsequent runs, commits and pushes changes.

```bash
python tools/publish.py <game-name>
python tools/publish.py <game-name> "commit message"
```

Publishes to: `johnesco.github.io/<game-name>/`

### `build_site.py` — Assemble Site for Deployment

Assembles a deployable `_site/` directory from `web/` + version snapshots. Used by projects with multiple playable versions (like zork1).

```bash
python tools/build_site.py <game-name>
```

Copies `web/*` into `_site/`, then overlays each `vN/` directory as `_site/vN/`. Serve locally with `python -m http.server 8000 --directory _site`.

### `snapshot.py` — Freeze a Version Snapshot

Creates or updates a frozen version snapshot in `<version>/` at the project root.

```bash
# Create new version (copies from previous version's template)
python tools/snapshot.py <game-name> v3

# Update existing version (recompile from frozen source, re-encode binary)
python tools/snapshot.py <game-name> v3 --update
```

**New version** creates:
- `story.ni` — Frozen copy of current source
- `lib/parchment/<name>.ulx.js` or `<name>.gblorb.js` — Base64-encoded binary (prefers `.gblorb` if it exists)
- Template files (player pages, libs) copied from previous version (excludes `*.ulx.js`, `*.gblorb.js`, `*.z3.js`)

**Update mode** (`--update`):
- **Never overwrites frozen source** — compiles from the version's own `story.ni`
- Auto-detects binary type (`.gblorb` vs `.ulx`) from existing web files
- Recompiles via `compile.py --source <version>/story.ni --compile-only` (adds `--sound` for gblorb)
- Re-encodes the compiled binary into `lib/parchment/`
- Copies walkthrough command files (`walkthrough.txt`, `walkthrough-guide.txt`) from `tests/inform7/` if present
- Does **not** overwrite `walkthrough_output.txt` — that's version-specific game output

Versions without a `story.ni` (e.g., ZIL-only v0) will error on `--update`.

---

## Testing Framework (`testing/`)

A config-driven framework for testing Inform 7 games. Each project defines a `tests/project.conf` with engine paths, score patterns, and diagnostic settings. The framework scripts read this config and do the rest.

### Configuration (`project.conf`)

A bash-sourceable file defining project-specific settings. Key variables:

| Variable | Purpose |
|----------|---------|
| `PROJECT_NAME` | Display name for output |
| `PRIMARY_ENGINE_PATH` | Path to Glulx interpreter |
| `PRIMARY_ENGINE_SEED_FLAG` | Flag for RNG seeding (e.g., `--rngseed`) |
| `PRIMARY_GAME_PATH` | Path to compiled `.ulx` file |
| `PRIMARY_WALKTHROUGH` | Path to walkthrough command file |
| `SCORE_REGEX` | Perl regex to extract final score |
| `PASS_THRESHOLD` | Minimum score for a passing run |
| `DEATH_PATTERNS` | Grep pattern for death detection |
| `REGTEST_FILE` | Path to `.regtest` file |
| `REGTEST_ENGINE` | Interpreter for RegTest |
| `REGTEST_GAME` | Game file for RegTest |

Optional: `ALT_*` variants for alternate engines (e.g., dfrotz for ZIL testing), and a `diagnostics_extra()` function for project-specific output.

### `run_walkthrough.py` — Walkthrough Runner

Runs a walkthrough through an interpreter with optional RNG seeding, extracts score and diagnostics, and reports pass/fail.

```bash
python tools/testing/run_walkthrough.py --config tests/project.conf
python tools/testing/run_walkthrough.py --config tests/project.conf --alt         # alternate engine
python tools/testing/run_walkthrough.py --config tests/project.conf --seed 42     # override seed
python tools/testing/run_walkthrough.py --config tests/project.conf --no-seed     # true randomness
python tools/testing/run_walkthrough.py --config tests/project.conf --diff        # compare vs baseline
python tools/testing/run_walkthrough.py --config tests/project.conf --quiet       # exit code only
python tools/testing/run_walkthrough.py --config tests/project.conf --no-save     # don't save output
```

Output includes: engine info, seed, score, death count, error counts, score changes, endgame status, and pass/fail result. Saves transcript to the output file configured in `project.conf`.

**Golden seeds**: The script auto-loads a golden seed from `tests/seeds.conf` if available. It also checks the binary hash to warn about stale seeds after recompilation.

### `find_seeds.py` — RNG Seed Sweeper

Sweeps RNG seeds (1 to N) to find ones where the walkthrough achieves a passing score. Reports statistics and recommends a golden seed.

```bash
python tools/testing/find_seeds.py --config tests/project.conf               # default range (1-200)
python tools/testing/find_seeds.py --config tests/project.conf --max 500     # extended range
python tools/testing/find_seeds.py --config tests/project.conf --alt         # alternate engine
python tools/testing/find_seeds.py --config tests/project.conf --no-stop     # find all passing seeds
```

On success, outputs a `seeds.conf` line ready to paste:
```
glulxe:42:a1b2c3d4:2026-02-28
```

Format: `engine:seed:binary_hash_prefix:date`

### `run_tests.py` — RegTest Wrapper

Runs RegTest regression tests using the project's configured engine, game, and test file.

```bash
python tools/testing/run_tests.py --config tests/project.conf              # run all tests
python tools/testing/run_tests.py --config tests/project.conf -v           # verbose
python tools/testing/run_tests.py --config tests/project.conf -l           # list tests
python tools/testing/run_tests.py --config tests/project.conf cellar       # run specific test
python tools/testing/run_tests.py --config tests/project.conf -v --vital cellar  # stop on first error
```

Pass-through args go directly to `regtest.py`.

### Adding Testing to a New Project

`new_project.py` sets up `project.conf` automatically. To set up manually:

1. Create `tests/project.conf` (see any existing project for a template)
2. Add walkthrough commands, seeds.conf, and regtest scenarios as needed
3. Run tests using the framework directly with `--config`

---

## RegTest Runner (`regtest.py`)

Andrew Plotkin's RegTest (v1.13) — a regression testing tool for interactive fiction. Reads `.regtest` files containing named test scenarios with commands and expected output patterns.

```bash
python3 tools/regtest.py -i "glulxe -q" -g game.ulx tests/game.regtest
python3 tools/regtest.py -i "glulxe -q" -g game.ulx tests/game.regtest -v       # verbose
python3 tools/regtest.py -i "glulxe -q" -g game.ulx tests/game.regtest -l       # list tests
python3 tools/regtest.py -i "glulxe -q" -g game.ulx tests/game.regtest smoke    # run one test
```

Normally invoked via `run_tests.py` rather than directly.

---

## Web Player Setup (`web/`)

Sets up a Parchment-based browser player for Inform 7 games.

### `setup_web.py` — Bootstrap Web Player

Creates a ready-to-serve web player directory with all required Parchment files and the base64-encoded game binary.

```bash
# Standard (naked ULX binary, no sound)
python tools/web/setup_web.py --title "My Game" --ulx path/to/game.ulx --out path/to/web

# With embedded sound (gblorb binary)
python tools/web/setup_web.py --title "My Game" --blorb path/to/game.gblorb --out path/to/web
```

Creates:
```
web/
├── play.html                ← Browser-playable game page (cache-busted)
└── lib/parchment/
    ├── jquery.min.js        ← jQuery
    ├── parchment.js         ← Parchment engine (AudioContext sound support)
    ├── parchment.css        ← Engine styling
    ├── main.js              ← AsyncGlk standalone (NO sound — do not load this)
    ├── main.css             ← Layout styling
    ├── quixe.js             ← Quixe interpreter (JS Glulx)
    ├── glulxe.js            ← Glulxe interpreter (WASM)
    ├── bocfel.js            ← Z-machine interpreter
    ├── zvm.js               ← ZVM interpreter
    ├── ie.js                ← IE compatibility shim
    ├── resourcemap.js       ← Blorb resource map (images/sound)
    ├── waiting.gif          ← Loading animation
    └── game.gblorb.js       ← Base64-encoded game binary
```

**Post-generation validation**: Warns if the generated `play.html` loads `main.js` instead of `parchment.js` (which would silently disable sound).

**Cache-busting**: All `.js` and `.css` references get `?v=<timestamp>` appended to prevent stale browser cache after rebuilds.

Normally invoked by `compile.py` rather than directly.

### `play-template.html`

HTML template with `__TITLE__` and `__STORY_FILE__` placeholders, filled by `setup_web.py`. Must load `parchment.js` (not `main.js`) and must include `story_name` in `parchment_options`.

### `generate_pages.py` — Generate Landing and Source Pages

Generates `index.html` (landing page) and `source.html` (syntax-highlighted source browser) from templates.

```bash
python tools/web/generate_pages.py --title "My Game" --meta "Subtitle" --description "Description" --out path/to/project
```

### `parchment/`

12 shared Parchment 2025.1 library files. Copied (not symlinked) to each project's `web/lib/parchment/` directory.

**Critical distinction**: `parchment.js` has full sound support (AudioContext, Glk sound channels). `main.js` has only stub sound functions that throw errors. Always load `parchment.js` in play pages.

---

## Project-Specific Scripts

Some projects add custom scripts beyond the standard testing framework:

### Zork1-Specific

| Script | Purpose |
|--------|---------|
| `tests/run-scenario.py` | Generate full transcripts from regtest scenarios |
| `tests/extract-scenario-commands.py` | Parse regtest files into flat command lists |

---

## Typical Workflows

### New game from scratch
```bash
python tools/new_project.py "My Game" mygame
# Edit projects/mygame/story.ni
python tools/compile.py mygame
python tools/testing/run_tests.py --config projects/mygame/tests/project.conf
python tools/publish.py mygame
```

### Edit → compile → test cycle
```bash
# Edit projects/<name>/story.ni
python tools/compile.py <name>
python tools/testing/run_walkthrough.py --config projects/<name>/tests/project.conf --no-seed --no-save
python tools/testing/run_tests.py --config projects/<name>/tests/project.conf
```

### Create a version snapshot
```bash
python tools/compile.py zork1
python tools/snapshot.py zork1 v3
python tools/build_site.py zork1
python -m http.server 8000 --directory projects/zork1/_site  # preview
```

### Recompile a frozen version from its own source
```bash
python tools/snapshot.py zork1 v1 --update      # recompiles from v1's story.ni
python tools/snapshot.py zork1 v3 --update      # auto-detects --sound for gblorb versions
```
