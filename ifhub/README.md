# IF Hub

**[Play online](https://johnesco.github.io/ifhub/)** | **[Source on GitHub](https://github.com/Johnesco/ifhub)**

IF Hub is a browser-based player for interactive fiction. Pick a game, play it online, and read the source code side by side — all in one interface. No downloads, no plugins, no server.

## Games

| Game | Format | Sound | Links |
|------|--------|-------|-------|
| **Zork I** (v0–v3 + current) | ZIL → Z-machine, Inform 7 → Glulx | v3+: native blorb | [Play](https://johnesco.github.io/zork1/) · [Hub](https://johnesco.github.io/ifhub/app.html?game=zork1) |
| **Dracula's Castle** | BASIC (original) + Inform 7 (translation) | — | [Play](https://johnesco.github.io/dracula/) · [Hub](https://johnesco.github.io/ifhub/app.html?game=dracula) |
| **Fever Dream** | Inform 7 → Glulx | native blorb | [Hub](https://johnesco.github.io/ifhub/app.html?game=feverdream) |
| **Sample** | Inform 7 → Glulx | — | [Play](https://johnesco.github.io/sample/) · [Hub](https://johnesco.github.io/ifhub/app.html?game=sample) |

## Three Eras of Interactive Fiction

IF Hub plays games spanning three decades of text adventure technology. The same virtual machines that ran on 1980s home computers now execute in your browser via [Parchment](https://github.com/curiousdannii/parchment), a JavaScript interpreter framework.

### ZIL → Z-machine (1980s)

Infocom wrote their games in ZIL (Zork Implementation Language), a Lisp dialect that compiled to Z-machine bytecode. Zork I v0 is the unmodified [open-source Infocom release](https://github.com/historicalsource/zork1), compiled with [ZILF](https://foss.heptapod.net/zilf/zilf) (a modern open-source ZIL compiler) to a .z3 binary. Parchment runs it via its Z-machine interpreter (bocfel compiled to WebAssembly). The ZIL source browser lets you read all ten original Infocom source files with syntax highlighting and annotations explaining the game engine.

### BASIC → Inform 7 (1980s → present)

Dracula's Castle is a type-in BASIC text adventure from the early 1980s — part of a wave of vampire castle games that flourished on home microcomputers. The original BASIC source is preserved with line-by-line annotations. The playable version is a faithful translation to Inform 7 that preserves the original map, puzzles, objects, and real-time clock while taking advantage of Inform 7's built-in world model.

### Inform 7 → Glulx (present)

Most games here are written in [Inform 7](http://inform7.com/), a programming language created by Graham Nelson that reads like natural English. Inform 7 source compiles through two stages — first to Inform 6 (a C-like intermediate language), then to [Glulx](https://www.eblong.com/zarf/glulx/) bytecode. Parchment executes Glulx via Emglken, a WebAssembly build of the reference interpreter. Games with sound embed .ogg audio files in a [Blorb](https://www.eblong.com/zarf/blorb/) package (.gblorb) that Parchment plays through the Web Audio API.

## Architecture

### Serve-in-Place

Each game is its own GitHub Pages site. The hub doesn't copy or generate any game files — it references each game by URL.

- `games.json` stores URL paths (`playUrl`, `sourceUrl`, `walkthroughUrl`)
- `app.html` loads games in iframes: `iframe.src = game.playUrl`
- Source viewer fetches `game.sourceUrl` directly (same-origin on GitHub Pages)
- Sound controls communicate with game iframes via `postMessage`

### Split-Pane Player (`app.html`)

The primary interface. A resizable two-pane layout with the game on the left and source/walkthrough on the right:

- **Game selector** — dropdown populated from `games.json`
- **Source viewer** — syntax-highlighted Inform 7 with outline navigation and search; iframe mode for ZIL and BASIC source browsers
- **Walkthrough viewer** — annotated guides with Commands, Game Text, and Replay modes
- **Sound controls** — mute and volume (shown only for sound-enabled games)

### Source Browsers

Every game has a source browser with syntax highlighting:

- **Inform 7** — built-in viewer with Part/Chapter/Section navigation, search, and line numbers
- **ZIL** — standalone browser covering all ten Infocom source files with annotations
- **BASIC** — annotated listing with toggle between original code and commentary

### Toolchain

The entire pipeline runs from the command line on Windows:

```
story.ni → Inform 7 compiler → story.i6 → Inform 6 compiler → game.ulx
         → (optional) generate_blurb.py → inblorb → game.gblorb
         → base64 encode → game.ulx.js (or .gblorb.js)
         → setup_web.py → play.html + lib/parchment/
```

Testing uses native CLI interpreters ([glulxe](https://github.com/erkyrath/glulxe) and [frotz](https://gitlab.com/DavidGriffith/frotz)) built from source in MSYS2. A deterministic seed system ensures reproducible walkthroughs — the same RNG seed produces the same combat outcomes, NPC behavior, and random events every run.

### Registry Files

| File | Drives | Fields |
|------|--------|--------|
| `games.json` | `app.html` game selector, source viewer, walkthrough viewer | `id`, `playUrl`, `sourceUrl`, `walkthroughUrl`, `sound`, `sourceBrowser` |
| `cards.json` | `index.html` landing page cards | `id`, `base`, `title`, `meta`, `description`, `versions` |

## Local Development

```bash
# Serve hub + all games at production-equivalent URLs
python tools/dev-server.py
# Open http://127.0.0.1:8000/ifhub/app.html
```

## Adding a Game

All steps are scripted — see [importing.html](https://johnesco.github.io/ifhub/importing.html) for the full guide.

```bash
python tools/compile.py mygame                          # compile + web player + walkthrough
python tools/extract_commands.py --from-source story.ni  # extract walkthrough from source
python tools/compile.py mygame                          # recompile with walkthrough
python tools/web/generate_pages.py --title "..." --out . # landing page + source browser
python tools/register_game.py --name mygame --title "..."  # add to games.json + cards.json
python tools/publish.py mygame                          # deploy to GitHub Pages
```

## Built With

- [Inform 7](http://inform7.com/) — interactive fiction authoring
- [Parchment](https://github.com/curiousdannii/parchment) — browser-based IF interpreter
- [ZILF](https://foss.heptapod.net/zilf/zilf) — ZIL compiler (for Zork I v0)
- [Claude](https://claude.ai/) by [Anthropic](https://www.anthropic.com/) — AI-assisted development
