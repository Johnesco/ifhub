# IF Hub — Registry, Hub UI & Intake API

IF Hub's job is to **easily display games online in a browsable format**. It is a target that engine workspaces ship to — not a producer of game builds.

Game projects live **outside** this repo, each with its own git repo and engine-specific build chain. IF Hub provides:

- **Hub site** (`site/`) — the browsable landing page and split-pane player
- **Registry** (`games-registry.json`, `site/games.json`, `site/cards.json`, `site/hubs.json`)
- **Intake API** (`tools/register_game.py`, `tools/publish.py`, `tools/push_hub.py`) — called by engine workspaces
- **Pipeline orchestrator** (`tools/pipeline.py`) — for in-tree engines (I7, Ink, Rez) whose build tools still live here

## Sharpee is NOT built here

IF Hub does not build Sharpee games. The Sharpee workspace (`/c/code/npmsharpee/`) owns the full build chain. Use its `ship.sh` to build and ship to IF Hub:

```bash
cd /c/code/npmsharpee
./ship.sh <game>                # local build only
./ship.sh <game> hub-local      # build + register with on-disk IF Hub
./ship.sh <game> hub            # build + register + publish + push hub
```

See `/c/code/npmsharpee/CLAUDE.md` for the Sharpee build chain.

## Pipeline (I7, Ink, Rez)

For engines whose build tools still live in IF Hub, the pipeline orchestrates build/test/register/publish/push-hub:

```bash
python tools/pipeline.py <game> compile          # compile only
python tools/pipeline.py <game> compile test      # compile + test
python tools/pipeline.py <game> --ship            # compile + test + register + publish + push hub
```

The pipeline auto-detects the engine from `project.conf` and chains stages. For Sharpee games, the `compile` stage delegates to `npmsharpee/tools/ship.py <game> local`.

**Known gaps:**
- Syncing fork packages to `/c/code/sharpee/*/node_modules/` requires `python tools/sync_fork.py` — not yet integrated into the pipeline stages.

## Directory Structure

```
C:\code\ifhub\
├── CLAUDE.md              ← You are here
├── .claude/skills/        ← bash-pitfalls, kill-servers, serve, web-player-debug
├── reference/             ← I7 syntax, text formatting, world model, sound, CSS overlay, etc.
├── tools/
│   ├── lib/               ← Shared Python modules (paths, output, process, config, web, git, regex)
│   ├── pipeline.py        ← Unified build pipeline orchestrator
│   ├── compile.py         ← I7→I6→Glulx→Blorb→web player compilation
│   ├── jukebox.py         ← Universal game import/publish CLI (I7, Ink, Rez, Z-machine, BASIC)
│   ├── publish.py         ← Publish a project to its own GitHub Pages repo
│   ├── register_game.py   ← Register a game in IF Hub (adds to games.json + cards.json)
│   ├── push_hub.py        ← Push hub registry changes to GitHub
│   ├── new_project.py     ← Create a new project scaffold
│   ├── adapters/          ← Per-engine adapters for jukebox (inform7, ink, rez, etc. — no sharpee; that lives in npmsharpee/tools/)
│   ├── regtest.py         ← Shared RegTest runner
│   ├── testing/           ← Generic testing framework (walkthrough, seeds, regtest, guide gen)
│   ├── interpreters/      ← Native Windows CLI interpreters (glulxe.exe, dfrotz.exe — gitignored)
│   ├── rez/               ← Rez compiler (pre-built binary — gitignored)
│   └── web/               ← Web player setup, templates (per engine), Parchment 2025.1 library
├── workspaces.json        ← Engine workspace roots (convention-based game discovery)
├── games-registry.json    ← Game path overrides + GitHub repo references
└── site/                  ← IF Hub web UI (static site deployed to GitHub Pages)
    ├── index.html         ← Landing page (renders cards from cards.json)
    ├── app.html           ← Split-pane player (game + source viewer)
    ├── games.json          ← Game registry (titles, URLs, engine, tags)
    ├── cards.json          ← Card metadata for landing page
    ├── hubs.json           ← Hub/collection definitions (filter by engine/tag)
    └── themes.js           ← Platform theme system (10 retro themes)
```

## Compiler

Inform 7 is installed system-wide via the GUI installer:

- **I7 compiler**: `C:\Program Files\Inform7IDE\Compilers\inform7.exe`
- **I6 compiler**: `C:\Program Files\Inform7IDE\Compilers\inform6.exe`
- **Internal**: `C:\Program Files\Inform7IDE\Internal`

Do NOT create `.inform/` IDE project bundles — the `-source` and `-o` flags let us compile without them.

## Game Projects (External)

Game projects live **outside** this repo in engine-specific workspaces. Each game is its own git repo with its own GitHub Pages deployment. Each engine workspace has its own CLAUDE.md with engine-specific authoring rules.

### Workspace Layout

```
C:\code\text-games\
├── i7/               ← Inform 7 workspace (each game = own git repo)
├── ink/              ← Ink workspace
├── rez/              ← Rez workspace
├── wwwbasic/         ← WWWBasic workspace
├── applesoft/        ← Applesoft BASIC workspace
├── zmachine/         ← Z-machine workspace
└── sharpee/          ← Sharpee game workspace (each game = own git repo; familyzoo/ holds all tutorial versions)

C:\code\npmsharpee\   ← Sharpee build tooling + fork mirrors only (from-fork/) — NO user games, NO build output
```

### Game Discovery

Three layers control game discovery (later layers override earlier):

1. **`workspaces.json`** (committed) — workspace roots scanned for `ifhub.conf` files (convention-based)
2. **`games-registry.json`** (committed) — explicit path + GitHub repo references (overrides)
3. **`games-local.json`** (gitignored) — per-developer path overrides

All engines build **in-place**: the game directory IS the deploy directory. For Sharpee that means `text-games/sharpee/<game>/browser/` (source at `<game>/src/`, output at `<game>/browser/`).

`games.json` entries include auto-probed URL fields: `walkthroughUrl` (from walkthrough files) and `testsUrl` (from `tests.html` in the deploy directory). Both are set by `build_games.py` when the corresponding file exists.

Tools resolve game names via `paths.project_dir(name)` which checks: registry → workspace scan → legacy `projects/` fallback.

### Project-Local Play Templates

Games with custom `play.html` requirements can provide a `play-template.html` in their project root. Build scripts check for it before falling back to the generic template. This makes `--force` rebuilds safe.

Placeholders substituted: `__TITLE__`, `__BASIC_SOURCE__` (BASIC engines), `__STORY_FILE__`/`__STORY_PATH__` (I7).

## Supported Engines

The hub is engine-agnostic — any game that produces a `play.html` works. The pipeline handles all engines automatically via `ENGINE=` in `project.conf`.

| Engine | Source | Build owner | Tests tab |
|--------|--------|-----------------|-----------|
| `inform7` | `story.ni` | IF Hub pipeline (compile.py) | In progress |
| `sharpee` | npm project at `/c/code/text-games/sharpee/<game>/` (or `/c/code/npmsharpee/from-fork/<game>/` for fork mirrors) | **Sharpee workspace** (`npmsharpee/tools/ship.py`) | Yes |
| `wwwbasic` | `.bas` file | IF Hub pipeline | — |
| `qbjc` | `.bas` → `.js` | IF Hub pipeline | — |
| `applesoft` | `.bas` file | IF Hub pipeline | — |
| `jsdos` | `.jsdos` bundle | IF Hub pipeline | — |
| `ink` | `.ink` file | IF Hub pipeline | — |
| `rez` | `.rez` files | IF Hub pipeline | — |

Each BASIC dialect must be specified explicitly via `ENGINE=` in `project.conf` — there is no generic "basic" fallback.

### Sharpee integration

Sharpee games own their build chain in `/c/code/npmsharpee/`. IF Hub is a **target** they ship to via the intake API:

- `python tools/register_game.py --name <game> --title … --engine sharpee` — updates games.json + cards.json
- `python tools/publish.py <game>` — pushes the game folder to `Johnesco/<game>` Pages repo
- `python tools/push_hub.py -m "msg"` — commits + pushes site/* registry changes

The pipeline's Sharpee `compile` stage delegates to `npmsharpee/tools/ship.py <game> local`. For hub-local or full publishing, run ship.sh from the Sharpee workspace directly.

**Registry:** Sharpee games use a single `path:` field in `games-registry.json` pointing at the game folder. Path can be absolute or relative to ifhub root — games can live anywhere on disk, not just under `npmsharpee/`. Multi-version games (familyzoo) add `entry:` / `binary:` / `subpath:` fields to build distinct targets from one folder. Registration is mandatory: `tools/ship.py` does not scan filesystem, so any game without a registry entry is unknown to the hub.

## Hub Architecture

The hub serves games **in-place** — it iframes each game's own play page directly from the game's GitHub Pages URL. No files are copied into the hub; each game project is the single source of truth for its own assets. All games deploy to `johnesco.github.io/<game>/`.

**Local development:** Use `/serve` to start Portman, `/kill-servers` to stop it. See the serve skill for details.

**CSS overlay theming:** Three tiers — Parchment base → static overlay → dynamic mood system. See `reference/css-overlay.md`.

**Multi-hub collections:** Games can belong to curated collections via `hubs.json` filtering. See `reference/project-guide.md` § Hub Collections.

**Tests pane:** The split-pane player (`app.html`) has a standard Tests frame alongside Source and Walkthrough. Games opt in by placing a `tests.html` file in their browser/deploy directory — `build_games.py` auto-detects it and sets `testsUrl` in `games.json`. When `testsUrl` is present, the IF Hub toolbar shows a checkmark Tests toggle button. All engines use ifplayer's HTML report format via `report_adapter.py` (converts `test-results.json` → ifplayer `TestResult` objects → `report.emit_html()`). The tests pane is theme-aware: `buildTestReportCSS()` in `themes.js` maps IF Hub chrome properties to ifplayer CSS variables, with adaptive pass/fail colors for dark vs light themes.

## New Game Publish Flow

```bash
python tools/new_project.py "Title" game-name    # scaffold
# ... edit story.ni, create walkthrough ...
python tools/pipeline.py game-name --ship         # compile + test + register + publish + push hub
```

`compile.py` auto-generates `index.html` + `source.html` from `story.ni` metadata when they don't exist. The `register` stage reads title/description from `story.ni` — no CLI args needed. All steps are idempotent. No colons in game titles (Windows filename limitation).

**GitHub Pages:** `publish.py` automatically enables Pages (workflow deployment) on every publish. If the repo was created manually before running the pipeline, Pages is still detected and enabled. Do NOT create repos or init git manually — let `publish.py` handle first-time setup end-to-end.

See `reference/project-guide.md` for detailed steps, individual scripts, and pipeline stages.

## Testing

### Test Results Tab

The Tests tab uses ifplayer's HTML report as the universal viewer for all engines. The pipeline: engine test runner → `test-results.json` → `report_adapter.py` → ifplayer HTML (`tests.html`). The adapter converts the engine-agnostic JSON schema into ifplayer's `TestResult` objects and calls `report.emit_html()`, producing the same rich transcript-first viewer that ifplayer produces natively. Features: collapsible test cards, turn-by-turn transcript with room/score tracking, inline assertion match highlighting ("show" buttons), word-level drift diffs. Theme integration: `buildTestReportCSS()` maps all 14 IF Hub themes to ifplayer CSS variables with light/dark adaptive colors.

### Engine-Specific Testing

Testing tools live per-engine at `/c/code/text-games/<engine>/tools/` (e.g., `i7/tools/run_walkthrough.py`). See `reference/engine-testing.md` for per-engine test capabilities.

Key points:
- All test scripts take `--config PATH` pointing to a project's `tests/project.conf`
- Native interpreters (`glulxe.exe`, `dfrotz.exe`) auto-detected; WSL fallback available
- Pipeline test stage auto-syncs walkthrough files between `tests/` and project root

## Inform 7 Authoring Rules

See `reference/syntax-guide.md` for full I7 syntax reference. See `reference/text-formatting.md` for text substitutions. See `reference/verb-help.md` for the verb help system template.

Key rules: first line must be `"Title" by "Author"`. Use `[apostrophe]` not `'` in strings. Use `After printing the banner text` for custom attribution (never `When play begins`). No colons in game titles (Windows filename limitation).

## Windows Notes

All tooling is Python — no bash dependency for build, test, or deploy workflows. Native interpreters (`glulxe.exe`, `dfrotz.exe`) are built via MSYS2 (see `tools/interpreters/build.sh`). Original bash scripts are archived in `tools/archive/bash/` for reference.

## Reference from Other Projects

Other project CLAUDE.md files can reference this hub:
```markdown
For Inform 7 syntax and conventions, see C:\code\ifhub\CLAUDE.md
```

## Reference Docs

| Doc | Contents |
|-----|----------|
| `reference/project-guide.md` | Build, test, publish workflows; pipeline stages; source patterns; hub collections |
| `reference/build-pipeline.md` | Manual I7 compilation steps; web player binary format |
| `reference/css-overlay.md` | Three-tier theming; mood engine; platform theme override |
| `reference/sound.md` | Native blorb sound architecture |
| `reference/syntax-guide.md` | Core Inform 7 syntax and structure |
| `reference/text-formatting.md` | Text substitutions and output formatting |
| `reference/sharpee-author-guide.md` | Sharpee authoring: stories, objects, rooms, NPCs, testing |
| `reference/parchment-troubleshooting.md` | Web player errors, sound gotchas, binary format |

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
