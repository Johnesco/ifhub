# IF Hub — where finished games get published

IF Hub is **receive-only**. It displays a game, its source, and its walkthrough (plus a test report when the game ships one). It does not build, compile, or test games. Every engine has its own workspace under `C:\code\text-games\<engine>\` with a `tools/build.py`; the hub takes the folder that produces and puts it online.

- Live site: https://johnesco.github.io/ifhub/ — deployed from `site/` by GitHub Actions on every push to `master` that touches `site/**`.
- Each game is its own git repo, published to `https://johnesco.github.io/<game>/`. The hub iframes it from there; nothing is copied into the hub.
- This is a personal showcase for getting games in front of people quickly, not a product.

## The contract

A game folder that IF Hub can receive contains:

| File | Required | What it is for |
|---|---|---|
| `ifhub.conf` | yes | `engine`, `title`, `description`, `tags`, `source`, `walkthrough`, `sound`, and `hub = yes` to be listed |
| `play.html` | yes | self-contained web player, with the libs it needs (`lib/parchment/`, `theme-listener.js`, ...) |
| source file | no | the raw file named by `source =`; the hub highlights it (Inform 7, Rez, Ink, BASIC). `sourceBrowser = yes` means the game ships its own `source.html` |
| `walkthrough.txt`, `walkthrough_output.txt`, `walkthrough-guide.txt` | no | at the game root; the hub renders them in `site/walkthrough.html` |
| `tests.html` | no | a test report page; its presence turns on the Tests tab |
| `index.html` | generated | the game's landing page, the only file `tools/ship.py` writes into a game folder |

Full details, per-engine build commands, and how to add an engine: `docs/publishing.md`.

## Commands

```bash
# In the engine workspace: build, test, and lay out the game folder
python C:/code/text-games/i7/tools/build.py <game>          # I7 and Z-machine; other workspaces: ink, rez, basic

# In the hub: put the folder online and list it
python tools/ship.py <game>              # verify contract, wrapper pages, register, publish to Pages, push hub
python tools/ship.py <game> --local      # register only (local preview)
python tools/ship.py <game> --refresh-pages   # rewrite the landing page from the current template
python tools/ship.py <game> --clean-wrappers  # delete source.html / walkthrough.html an older hub generated
python tools/ship.py <game> --unlist          # hide a game from the hub (hub = no) and push the registry

# Maintenance
python tools/build_games.py              # regenerate site/games.json + site/cards.json from every ifhub.conf
python tools/check_links.py [--fix]      # verify every URL in the registry resolves on disk
python tools/build_landing.py --all      # regenerate landing pages for versioned groups (zork1)
```

## Layout

```
ifhub/
├── CLAUDE.md, README.md
├── workspaces.json          ← roots scanned for game folders: ../text-games/<engine>
├── site/                    ← the static hub: index.html (cards), app.html (split-pane player),
│                              walkthrough.html (walkthrough viewer), themes.js, games.json, cards.json, hubs.json
├── tools/
│   ├── ship.py              ← intake: contract check → landing page → register → publish → push hub
│   ├── build_games.py       ← every ifhub.conf → games.json + cards.json (idempotent)
│   ├── publish.py           ← push a game folder to Johnesco/<game> and enable Pages
│   ├── push_hub.py          ← commit + push site/games.json, cards.json, hubs.json
│   ├── check_links.py, build_landing.py
│   ├── web/                 ← landing-page generator + templates (single game, versioned group)
│   └── lib/                 ← paths, git, output, process, web (template substitution)
├── docs/                    ← publishing.md (the contract), functional-spec.md (site behaviour), sdlc/
├── reference/               ← css-overlay.md (theming), multi-version-guide.md (versioned games)
└── .claude/                 ← skills: serve, kill-servers (Portman local preview); launch.json: hub-site
```

**Game discovery:** `build_games.py` scans each root in `workspaces.json` for subfolders containing an `ifhub.conf`. A game is listed when its conf says `hub = yes`; `ship.py <game> --unlist` sets it back to `no`. Card text (title, subtitle from `author`, description) comes from the same conf, so nothing in `games.json` or `cards.json` is hand-maintained.

## Hub behaviour worth knowing

- `site/app.html` is the split-pane player: game, source, walkthrough, and tests panes. Source is fetched raw and highlighted in the hub (Inform 7, Rez, Ink, BASIC; games with `sourceBrowser = yes` are iframed instead); walkthroughs render in `site/walkthrough.html?game=<id>` from the game's txt files; 15 platform themes from `themes.js`; collections from `hubs.json` (filter by engine or tag, switched client-side). Theming reaches into game pages through `theme-listener.js` (each workspace ships a copy) and `ifhub:applyTheme` messages. See `reference/css-overlay.md`.
- Versioned games (zork1 v0..v3, dracula): `versionOf` / `versionPrimary` in `ifhub.conf` collapse a group into one card. See `reference/multi-version-guide.md`.
- Local preview: `/serve` starts Portman (port 9000) and registers the site plus every game folder; `/kill-servers` stops it.

## Engine workspaces (outside this repo)

| Workspace | Build command | Notes |
|---|---|---|
| `text-games/i7/` | `tools/build.py <game>` | Inform 7: compile, walkthrough + regtests + ifPlayer tests, Parchment player, tests.html. Z-machine stories (`engine = zmachine`, e.g. zork1-v0) live here too and are wrapped in the same player. I7 language references in `i7/reference/`; native interpreters in `i7/tools/interpreters/` |
| `text-games/ink/` | `tools/build.py <game>` | compiles with inklecate when installed, else uses the committed .json |
| `text-games/rez/` | `tools/build.py <game>` | Rez compiler in `rez/tools/bin/`; dist → play.html |
| `text-games/basic/` | `tools/build.py <game>` | every BASIC dialect (wwwbasic, applesoft, bwbasic, qbjc, jsdos); `engine =` in ifhub.conf picks the player template; bwBASIC runtime in `basic/tools` |

Each workspace has its own `CLAUDE.md` with authoring rules and is a git repo that holds only the tooling (GitHub: `Johnesco/inform7-workspace`, `ink-workspace`, `rez-workspace`, `basic-workspace`); the game folders inside it are ignored because every game is its own repo. Sharpee (Chord) is not integrated yet; when it is, it gets a workspace and a `build.py` like the others.

## Instructions for Claude

> Full SDLC details are in `docs/sdlc/`. The key rules:

**Claude cannot QA its own work.** The Verify column is always human-owned.

1. **Ticket first** — create a GitHub Issue before code, then `gh project item-add 3 --owner Johnesco --url [ISSUE_URL]`
2. **Read before editing.** Follow existing patterns. Keep it simple.
3. **Docs are part of done** — update `docs/functional-spec.md` for behaviour or data-format changes, this file for structure changes, `README.md` for public-facing changes, `docs/publishing.md` when the contract or a build command changes.
4. **Commits:** `#XX: description`. Branches: `[type]/[short-description]` (feature/, fix/, docs/, task/, spike/). `Fixes #XX` in the PR body.
5. **Never do game work in this repo.** Compiling, testing, and scaffolding belong in the engine workspaces.

Board: https://github.com/users/Johnesco/projects/3 (project 3, owner Johnesco).
