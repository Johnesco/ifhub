# IF Hub — Tools, Hub UI & Game Registry

IF Hub is the shared tooling, web hub, and game registry for interactive fiction projects.
Game projects live **outside** this repo at `/c/code/text-games/<game>/`, each with its own git repo.
IF Hub provides the build pipeline, dashboard, web player setup, and the hub web UI that aggregates all games.

## Pipeline First

**All building, registering, and publishing MUST go through the pipeline.** Never run individual scripts manually (compile.py, register_game.py, publish.py, setup_web.py, etc.) — use the pipeline instead:

```bash
python tools/pipeline.py <game> compile          # compile only
python tools/pipeline.py <game> compile test      # compile + test
python tools/pipeline.py <game> --ship            # compile + test + register + publish + push hub
```

The pipeline auto-detects the engine from `project.conf`, chains all steps in order, handles staleness checks, and ensures nothing is missed. If a step is missing from the pipeline, **fix the pipeline** — don't work around it with manual commands.

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
│   ├── compile_sharpee.py ← Build Sharpee game + import into IF Hub
│   ├── publish.py         ← Publish a project to its own GitHub Pages repo
│   ├── register_game.py   ← Register a game in IF Hub (adds to games.json + cards.json)
│   ├── push_hub.py        ← Push hub registry changes to GitHub
│   ├── new_project.py     ← Create a new project scaffold
│   ├── regtest.py         ← Shared RegTest runner
│   ├── testing/           ← Generic testing framework (walkthrough, seeds, regtest, guide gen)
│   ├── interpreters/      ← Native Windows CLI interpreters (glulxe.exe, dfrotz.exe — gitignored)
│   ├── rez/               ← Rez compiler (pre-built binary — gitignored)
│   └── web/               ← Web player setup, templates (per engine), Parchment 2025.1 library
├── games-registry.json    ← Game path registry (maps game names to local paths + repos)
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

Game projects live **outside** this repo at `/c/code/text-games/<game>/`. Each game is its own git repo with its own GitHub Pages deployment.

### Game Registry

Two files control game discovery (resolution: local overrides defaults):

- **`games-registry.json`** (committed) — default paths + GitHub repo references
- **`games-local.json`** (gitignored) — per-developer path overrides

Tools resolve game names via `paths.project_dir(name)` which checks: local → defaults → legacy `projects/` fallback.

### Project-Local Play Templates

Games with custom `play.html` requirements can provide a `play-template.html` in their project root. Build scripts check for it before falling back to the generic template. This makes `--force` rebuilds safe.

Placeholders substituted: `__TITLE__`, `__BASIC_SOURCE__` (BASIC engines), `__STORY_FILE__`/`__STORY_PATH__` (I7).

## Supported Engines

The hub is engine-agnostic — any game that produces a `play.html` works. The pipeline handles all engines automatically via `ENGINE=` in `project.conf`.

| Engine | Source | Pipeline handles |
|--------|--------|-----------------|
| `inform7` | `story.ni` | Compile I7→I6→Glulx→web player |
| `sharpee` | `src/index.ts` (npm project at `/c/code/sharpee/<game>/`) | `npx sharpee build-browser` + import |
| `wwwbasic` | `.bas` file | Embed source in play template |
| `qbjc` | `.bas` → `.js` | Pre-compile + template |
| `applesoft` | `.bas` file | jsbasic template |
| `jsdos` | `.jsdos` bundle | DOSBox template |
| `ink` | `.ink` file | ink.js runtime |
| `rez` | `.rez` files | Rez compiler |

Each BASIC dialect must be specified explicitly via `ENGINE=` in `project.conf` — there is no generic "basic" fallback.

**Sharpee workspace:** Games at `/c/code/sharpee/<game>/` (npm projects). Engine fork at `/c/code/fork/sharpee/` (engine contributions only — never modify during game dev). See `reference/sharpee-author-guide.md`.

## Hub Architecture

The hub serves games **in-place** — it iframes each game's own play page directly from the game's GitHub Pages URL. No files are copied into the hub; each game project is the single source of truth for its own assets. All games deploy to `johnesco.github.io/<game>/`.

**Local development:** Use `/serve` to start Portman, `/kill-servers` to stop it. See the serve skill for details.

**CSS overlay theming:** Three tiers — Parchment base → static overlay → dynamic mood system. See `reference/css-overlay.md`.

**Multi-hub collections:** Games can belong to curated collections via `hubs.json` filtering. See `reference/project-guide.md` § Hub Collections.

## New Game Publish Flow

```bash
python tools/new_project.py "Title" game-name    # scaffold
# ... edit story.ni, create walkthrough ...
python tools/pipeline.py game-name --ship         # compile + test + register + publish + push hub
```

`compile.py` auto-generates `index.html` + `source.html` from `story.ni` metadata when they don't exist. The `register` stage reads title/description from `story.ni` — no CLI args needed. All steps are idempotent. No colons in game titles (Windows filename limitation).

See `reference/project-guide.md` for detailed steps, individual scripts, and pipeline stages.

## Testing

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
