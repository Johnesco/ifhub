# IF Hub

Central hub for Inform 7 authoring, compilation, testing, and web deployment. All Inform 7 projects reference this location for shared tooling, reference docs, and the Parchment web player.

**Live site**: [johnesco.github.io/ifhub](https://johnesco.github.io/ifhub/)

### Online Documentation

- **[IF Hub](https://johnesco.github.io/ifhub/)** — Browse and play all games
- **[Split-Pane Player](https://johnesco.github.io/ifhub/app.html)** — Play with side-by-side source code and walkthrough
- **[Publishing Guide](https://johnesco.github.io/ifhub/importing.html)** — Step-by-step guide for adding a new game to the hub
- **[Dashboard Guide](https://johnesco.github.io/ifhub/dashboard.html)** — Local web GUI for the build pipeline

## Quick Start

```bash
# Create a new project
python tools/new_project.py "My Game" mygame

# Edit the source
# (edit projects/mygame/story.ni)

# Compile and set up web player
python tools/compile.py mygame

# Compile with embedded sound (requires Sounds/*.ogg at project root)
python tools/compile.py mygame --sound

# Play locally (hub + all games at production URLs)
python tools/dev-server.py
# Open http://127.0.0.1:8000/ifhub/app.html

# Run tests
python tools/testing/run_tests.py --config projects/mygame/tests/project.conf

# Publish to GitHub Pages
python tools/publish.py mygame

# Interactive pipeline runner (arrow-key menus)
python tools/run.py
```

## Directory Structure

```
ifhub/
├── README.md              ← You are here
├── CLAUDE.md              ← AI assistant instructions and full conventions
├── reference/             ← Inform 7 language reference docs
├── tools/                 ← Shared scripts (see tools/README.md)
│   ├── compile.py         ← Compile I7 → I6 → Glulx → optional blorb → web player
│   ├── new_project.py     ← Scaffold a new project with build, test, and deploy infra
│   ├── publish.py         ← Publish a project to GitHub Pages
│   ├── pipeline.py        ← Orchestrator: compile → test → snapshot → push
│   ├── snapshot.py        ← Freeze/update version snapshots
│   ├── build_site.py      ← Assemble _site/ for deployment
│   ├── lib/               ← Shared Python library
│   ├── run.py             ← Interactive pipeline runner (pip install InquirerPy)
│   ├── dev-server.py      ← Multi-root dev server (hub + all games)
│   ├── regtest.py         ← Shared RegTest runner
│   ├── interpreters/      ← Native glulxe.exe + dfrotz.exe (built from source in MSYS2)
│   ├── testing/           ← Generic testing framework (walkthroughs, seeds, regtests)
│   └── web/               ← Parchment web player setup (templates, libraries)
├── projects/              ← Game projects (each has its own git repo)
│   ├── dracula/
│   ├── feverdream/
│   ├── sample/
│   └── zork1/
└── ifhub/                 ← IF Hub web player (see ifhub/README.md)
    ├── index.html         ← Landing page
    ├── app.html           ← Split-pane player (game + source viewer)
    ├── games.json         ← Game registry (URLs, sound flags)
    └── cards.json         ← Card metadata for landing page
```

## Projects

| Project | Description | Sound | Pages |
|---------|-------------|-------|-------|
| **[zork1](https://johnesco.github.io/zork1/)** | Zork I — The Great Underground Empire (ZIL-to-I7 translation, 4 versions) | v3+: 25 sounds (blorb) | [Play](https://johnesco.github.io/ifhub/app.html?game=zork1) |
| **[dracula](https://johnesco.github.io/dracula/)** | Dracula's Castle — 1980s BASIC text adventure + Inform 7 translation | — | [Play](https://johnesco.github.io/ifhub/app.html?game=dracula) |
| **[feverdream](https://johnesco.github.io/feverdream/)** | Fever Dream — A Perceptual Horror | blorb | [Play](https://johnesco.github.io/ifhub/app.html?game=feverdream) |
| **[sample](https://johnesco.github.io/sample/)** | Sample — Inform 7 practice game | — | [Play](https://johnesco.github.io/ifhub/app.html?game=sample) |

Each project has its own `story.ni` source file, test suite, web player, and GitHub Pages deployment. The hub serves games in-place — it iframes each game's own pages directly from GitHub Pages.

## Three Game Formats

IF Hub plays games spanning three eras of text adventure technology:

- **ZIL → Z-machine** — Infocom's original language (1980s). Zork I v0 is the unmodified open-source Infocom release, compiled with ZILF to a .z3 binary and run via Parchment's Z-machine interpreter.
- **BASIC → Inform 7** — Dracula's Castle preserves the original 1980s BASIC source with annotations; the playable version is a faithful Inform 7 translation.
- **Inform 7 → Glulx** — A natural-English programming language. Source compiles to Glulx bytecode, optionally packaged with .ogg audio in a Blorb binary. Parchment executes via WASM.

## Tools Overview

All scripts live in `tools/`. See [`tools/README.md`](tools/README.md) for full documentation.

| Script | Purpose |
|--------|---------|
| `compile.py` | Compile a project (I7 → I6 → Glulx → optional blorb → web player → walkthrough) |
| `extract_commands.py` | Extract walkthrough commands from a TRANSCRIPT file or `Test me` in source |
| `register_game.py` | Register a game in IF Hub (adds to `games.json` + `cards.json`) |
| `push_hub.py` | Push hub registry changes (`games.json` + `cards.json`) to GitHub |
| `new_project.py` | Scaffold a new project with build, test, and deploy infrastructure |
| `publish.py` | Publish a project to GitHub Pages (creates repo on first run) |
| `pipeline.py` | Orchestrator: compile → test → snapshot → push |
| `snapshot.py` | Freeze/update version snapshots (recompiles from frozen source) |
| `build_site.py` | Assemble `_site/` from project root + version directories |
| `run.py` | Interactive pipeline runner — arrow-key menus for common tasks |
| `dev-server.py` | Multi-root dev server (serves hub + all games at production URLs) |
| `regtest.py` | Shared RegTest runner for regression testing |

### Testing Framework (`tools/testing/`)

Deterministic walkthrough-based testing with native CLI interpreters built from source:

| Script | Purpose |
|--------|---------|
| `run_walkthrough.py` | Run a walkthrough with RNG seeding and diagnostics |
| `find_seeds.py` | Sweep RNG seeds to find deterministic golden seeds |
| `run_tests.py` | Run RegTest regression tests for a project |

**Interpreters**: `glulxe.exe` (Glulx) and `dfrotz.exe` (Z-machine) built from source in MSYS2 UCRT64. These are gitignored — each developer builds locally with `bash tools/interpreters/build.sh`. Tests auto-detect native interpreters and fall back to WSL.

### Web Player (`tools/web/`)

| File | Purpose |
|------|---------|
| `setup_web.py` | Bootstrap a Parchment web player for any project |
| `generate_pages.py` | Generate `index.html` + `source.html` from templates |
| `play-template.html` | HTML template for player pages |
| `landing-template.html` | Template for project landing pages |
| `source-template.html` | Template for source browser pages |
| `parchment/` | Shared Parchment 2025.1 library files (12 files) |

## Sound (Native Blorb)

Games with sound use native Glk/Blorb — audio is embedded directly in the `.gblorb` binary. Parchment 2025.1 plays sounds via AudioContext when the game issues Glk sound channel calls.

```bash
python tools/compile.py zork1 --sound
```

**Requirements**: Sound declarations in `story.ni` (`Sound of X is the file "Y.ogg"`) and `.ogg` files in `projects/<name>/Sounds/`.

See `reference/sound.md` for the full architecture.

## Compiler

Inform 7 is installed system-wide. CLI compilation uses `-source` and `-o` flags — no `.inform/` IDE bundles needed.

```bash
python tools/compile.py <game-name>                    # standard
python tools/compile.py <game-name> --sound             # with blorb sound
python tools/compile.py <game-name> --source PATH       # alternate story.ni
python tools/compile.py <game-name> --compile-only      # skip web player update
```

## Reference Docs

The `reference/` directory contains Inform 7 language reference:

- **syntax-guide.md** — Core syntax, kinds, properties, rooms, actions
- **text-formatting.md** — Text substitutions and output formatting
- **world-model.md** — Kinds, properties, rooms/regions/backdrops, relations
- **understanding.md** — Understand command, parser tokens, grammar
- **rulebooks.md** — Action processing, rules, going, persuasion, senses
- **activities-phrases.md** — Activities, phrase definitions, control flow
- **sound.md** — Sound architecture, native blorb, Parchment integration
- **parchment-troubleshooting.md** — Web player errors and debugging

## Built With

- [Inform 7](http://inform7.com/) — interactive fiction authoring
- [Parchment](https://github.com/curiousdannii/parchment) — browser-based IF interpreter
- [ZILF](https://foss.heptapod.net/zilf/zilf) — ZIL compiler (for Zork I v0)
- [MSYS2](https://www.msys2.org/) — native interpreter builds (glulxe, frotz)
- [Claude](https://claude.ai/) by [Anthropic](https://www.anthropic.com/) — AI-assisted development
