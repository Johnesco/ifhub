# Publishing a game to IF Hub

IF Hub is a receive-only display. A game is written, built, and tested in its engine workspace; the hub receives a finished folder and puts it online. This page is the contract between the two.

## 1. The game folder

Every game is a folder that is its own git repo and is published to `https://johnesco.github.io/<game>/`. The hub can receive it when it contains:

| File | Required | Notes |
|---|---|---|
| `ifhub.conf` | yes | flat `key = value` lines, see below |
| `play.html` | yes | a self-contained web player. Everything it loads must be in the folder (`lib/parchment/`, `theme-listener.js`, the story data) or on a public CDN |
| source file | no | the raw file named by `source =`. The hub highlights it in the source pane (Inform 7, Rez, Ink, BASIC). A game with a multi-file or custom source view ships its own `source.html` and sets `sourceBrowser = yes` |
| `walkthrough.txt` | no | one command per line, at the game root. Optional companions next to it: `walkthrough_output.txt` (transcript) and `walkthrough-guide.txt` (annotated guide). The hub renders them in its own walkthrough viewer |
| `tests.html` | no | any self-contained test report page. When present the hub shows a Tests tab. Inform 7 games get one from ifPlayer |
| `index.html` | generated | the game's landing page, the only file the hub writes into the folder. `tools/ship.py` writes it when missing; `--refresh-pages` rewrites it |

### ifhub.conf

```ini
engine = inform7                 # inform7 | zmachine | ink | rez | wwwbasic | applesoft
title = Babel Fish Puzzle from HHGG
author = An Homage To Adams and Meretzky
description = One or two sentences for the card.
tags = classic, puzzle           # hubs.json filters on these
source = story.ni                # shown in the source pane
sourceLabel = babel.ni           # optional label for the source toolbar
walkthrough = walkthrough.txt    # optional
sound = blorb                    # optional: game has embedded audio
hub = yes                        # ship.py sets this; the game is listed only when it is yes
```

Versioned games add `versionOf = <base>`, `versionLabel = ...`, `versionPrimary = yes` on the current one. See `reference/multi-version-guide.md`.

The hub reads nothing else. Anything engine-specific (test configs, compiler settings) is the workspace's business.

## 2. Build in the workspace

Each engine workspace under `C:/code/text-games/` has a `tools/build.py` that turns source into the folder above. Run it with a game folder name or a path.

| Engine | Command | What it does |
|---|---|---|
| Inform 7 | `python C:/code/text-games/i7/tools/build.py <game>` | I7 → I6 → Glulx (or .gblorb with sound), Parchment player into `lib/parchment/`, walkthrough + regtests + ifPlayer tests, `tests.html`. `--no-test`, `--compile-only`, `--force` |
| Z-machine | `python C:/code/text-games/i7/tools/build.py <game>` | same workspace as Inform 7 (`engine = zmachine` in ifhub.conf): wraps the `.z3/.z5` (or an already encoded `.js`) named by `binary =` in Parchment. No compile, no tests |
| Ink | `python C:/code/text-games/ink/tools/build.py <game>` | compiles the `.ink` with inklecate when Inky is installed, otherwise uses the committed `.json`; ink.js player with the story inlined; copies `theme-listener.js` |
| Rez | `python C:/code/text-games/rez/tools/build.py <game>` | `rez compile` from the game root (compiler: `rez` on PATH or `rez/tools/bin/rez_windows.exe`), then `dist/index.html` → `play.html` with the theme listener. `--no-compile` reuses `dist/` |
| BASIC (wwwbasic, applesoft, bwbasic, qbjc, jsdos) | `python C:/code/text-games/basic/tools/build.py <game>` | inlines the `.BAS` named by `source =` into the dialect's player template; `engine =` in ifhub.conf picks the dialect |

`--force` overwrites an existing `play.html`. Games with a hand-tuned player keep a `play-template.html` in their folder; the build scripts prefer it over the generic template, which makes `--force` safe.

Preview any game locally with `python -m http.server 8000 --directory <game>`, or run `python tools/serve.py` in the hub and open `http://127.0.0.1:8892/ifhub/app.html?game=<game>` to see it inside the hub.

## 3. Ship to the hub

From the hub repo:

```bash
python tools/ship.py <game>                   # full: verify, wrapper pages, register, publish, push hub
python tools/ship.py <game> --local           # register only; preview the hub on disk
python tools/ship.py <game> --refresh-pages   # rewrite index.html from the current template
python tools/ship.py <game> --clean-wrappers  # delete source.html / walkthrough.html an older hub generated
python tools/ship.py <game> --message "msg"   # commit message for the game repo
python tools/ship.py <game> --unlist          # hide the game (hub = no) and push the registry
```

Steps, in order:

1. **Contract check** — `ifhub.conf` with `engine` and `title`, `play.html` present, `source =` (if given) exists.
2. **Landing page** — `index.html` via `tools/web/generate_pages.py` when missing. Source and walkthrough views are not files in the game folder; the hub renders them from the raw source and the walkthrough txt files.
3. **Register** — sets `hub = yes` in `ifhub.conf` and runs `tools/build_games.py`, which regenerates `site/games.json` and `site/cards.json` from every `ifhub.conf` under the `workspaces.json` roots. Title, author (the card subtitle), description, tags, and version fields come from the conf; URL fields (`sourceUrl`, `walkthroughUrl`, `testsUrl`, `landingUrl`) are only emitted when the file exists.
4. **Publish** — `tools/publish.py` commits everything in the game folder and pushes to `Johnesco/<game>`; on first use it creates the repo, adds the Pages workflow, and enables Pages.
5. **Push hub** — `tools/push_hub.py` regenerates the registry once more, commits `site/games.json`, `cards.json`, `hubs.json`, and pushes. The hub redeploys from `master`.

`--local` stops after step 3. Steps 4 and 5 are the only ones that touch GitHub.

## 4. Snapshots and versions

Publish whenever the game is worth showing; `ship.py` is idempotent. To keep an older state visible next to the current one, give it its own folder and repo (`zork1-v1`, `zork1-v2`, ...) and mark the group with `versionOf` / `versionPrimary` in `ifhub.conf`; the landing page for the group is generated by `tools/build_landing.py`. A plain git tag in the game repo is enough when the old state does not need to stay playable.

## 5. Adding an engine

1. Make a workspace `C:/code/text-games/<engine>/` and add its root to `workspaces.json`.
2. Give it `tools/build.py <game>` that produces the folder in section 1. Copy `theme-listener.js` from an existing workspace into the player so hub themes apply.
3. Add a highlighter for the engine's source to `site/app.html` (Inform 7, Rez, Ink and BASIC exist), or have games ship their own `source.html` and set `sourceBrowser = yes`.
4. Add a `<engine>/CLAUDE.md` with the authoring rules, and a row to the table in section 2.

The hub itself does not need to know the engine name; `build_games.py` copies whatever `engine =` says into `games.json`, and `hubs.json` can filter on it.

## 6. Where things live

| Thing | Location |
|---|---|
| Engine workspaces and game repos | `C:/code/text-games/<engine>/<game>/` (each game its own repo). Workspaces: `i7` (Inform 7 + Z-machine), `ink`, `rez`, `basic` (all BASIC dialects) |
| Workspace tooling | `C:/code/text-games/<engine>/tools/` — each engine folder is a git repo (branch `main`) holding only `tools/`, `CLAUDE.md`, and for I7 `reference/`; the game folders inside it are ignored because each game is its own repo. Remotes: `Johnesco/inform7-workspace`, `ink-workspace`, `rez-workspace`, `basic-workspace` |
| Inform 7 language references, interpreters, test framework | `C:/code/text-games/i7/reference/`, `i7/tools/interpreters/`, `i7/tools/` |
| ifPlayer (I7 test runner and report format) | `C:/code/text-games/ifPlayer/` — repo `Johnesco/ifplayer` |
| Local preview server | `tools/serve.py` in the hub: `site/` at `/ifhub/`, every game folder at `/<game>/`, one port |
| The hub | `C:/code/ifhub/` — repo `Johnesco/ifhub`, site deployed from `site/` |
