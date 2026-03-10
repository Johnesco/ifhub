# IF Hub — Web Player for Inform 7 Games

A standalone static site that serves multiple Inform 7 games through a single browser interface with source viewer.

## Project Structure

```
ifhub/
├── CLAUDE.md              ← You are here
├── index.html             ← Landing page (reads cards.json, renders game cards with Source/Walkthrough links)
├── app.html               ← Split-pane player (game iframe + source viewer + walkthrough)
├── play.html              ← Shared Parchment player (standalone use; has version-gated CSS effects for zork1 v3+)
├── importing.html         ← Guide for adding new games to the hub
├── games.json             ← Game registry (id, title, URLs, sound flag, sourceBrowser)
├── cards.json             ← Card metadata for landing page (title, description, versions)
└── lib/parchment/         ← Shared Parchment JS libraries (checked in)
```

## Serve-in-Place Architecture

The hub serves games **in-place** — `app.html` iframes each game's own play page directly from the game's GitHub Pages URL. No files are copied into the hub.

- `games.json` uses URL-based fields: `playUrl`, `sourceUrl`, `walkthroughUrl`, `landingUrl`
- `app.html` loads `iframe.src = game.playUrl` — one line, no file construction
- Source viewer fetches `game.sourceUrl` (same origin on GitHub Pages); when `sourceBrowser: true`, loads an iframe instead
- All games deploy to `johnesco.github.io/<game>/`, so same-origin iframes and fetch work

### Current Games

| ID | Source Mode | Sound |
|----|-------------|-------|
| `zork1-v0` through `zork1-v3`, `zork1` (current) | v0: sourceBrowser (ZIL), v1–v3: raw .ni | v3+: blorb |
| `dracula-v0`, `dracula` (current) | v0: sourceBrowser (BASIC), current: raw .ni | No |
| `feverdream` | raw .ni | blorb |
| `sample` | sourceBrowser | No |

## Running Locally

```bash
python tools/dev-server.py [--port 8000]
# Maps /ifhub/* → ifhub/, /<game>/* → projects/<game>/
# Open http://127.0.0.1:8000/ifhub/app.html
```

## Adding a New Game

1. **Enable GitHub Pages** on the game repo (required — the hub iframes pages directly from `johnesco.github.io/<game>/`)
   - Settings → Pages → Source: "Deploy from a branch", Branch: `main` (or `master`), Path: `/ (root)`
   - Or via CLI: `gh api repos/Johnesco/<game>/pages -X POST --input - <<< '{"build_type":"legacy","source":{"branch":"main","path":"/"}}'`
2. Add a game entry to `games.json` with id, title, and URL fields (`playUrl`, `sourceUrl`, `walkthroughUrl`, `landingUrl`)
3. Add card metadata to `cards.json`
4. Verify the game's play page loads at `johnesco.github.io/<game>/play.html` before adding to the hub

## Hosting on the Web

Pure static site — no server-side logic. Deployed to GitHub Pages from the repo directly. Each game is served from its own repo's GitHub Pages.

## Relation to Game Repos

- Each game project lives under `C:\code\ifhub\projects\` with its own repo and build process
- Game repos are never modified by this project — ifhub only reads from them
- The hub iframes game pages and fetches source files — no copying
- Game projects have their own GitHub Pages sites (landing pages, play pages, source)
- For shared Inform 7 tooling and references, see `C:\code\ifhub\CLAUDE.md`

## CSS Overlay System

All games use a three-tier CSS overlay architecture. Full documentation in `C:\code\ifhub\reference\css-overlay.md`.

- **Tier 1**: Parchment base (`parchment.css` + `main.css`) — shared library
- **Tier 2**: Static overlay — inline `<style>` in each game's `play.html` (dark theme, CSS variables, layout)
- **Tier 3**: Dynamic mood system — Houdini `@property` + MutationObserver JS (zork1 v3, feverdream only)

The shared `play.html` version-gates Tier 3 effects for Zork I. When the binary path matches `zork1-v(\d+)` with version >= 3, it adds `body.zork1-enhanced` and activates mood palettes + effects. Other games get Tier 2 static theming only.

### MutationObserver Input Detection

Parchment in WASM mode (Emglken) does **not** wrap user input in `.Input` CSS class spans. Event detection tracks the previous buffer node's text (`lastNodeText`) instead of querying `.BufferWindow .Input` elements.
