# IF Hub — Web Player for Inform 7 Games

A standalone static site that serves multiple Inform 7 games through a single browser interface with source viewer.

## Project Structure

```
ifhub/
├── CLAUDE.md              ← You are here
├── index.html             ← Landing page (reads cards.json, renders game cards)
├── app.html               ← Player UI (game selector, source viewer, tabs)
├── play.html              ← Shared Parchment player (standalone use; has version-gated CSS effects for zork1 v4+)
├── games.json             ← Game registry (id, title, URLs, sound flag)
├── cards.json             ← Card metadata for landing page
└── lib/parchment/         ← Shared Parchment JS libraries (checked in)
```

## Serve-in-Place Architecture

The hub serves games **in-place** — `app.html` iframes each game's own play page directly from the game's GitHub Pages URL. No files are copied into the hub.

- `games.json` uses URL-based fields: `playUrl`, `sourceUrl`, `walkthroughUrl`, `landingUrl`
- `app.html` loads `iframe.src = game.playUrl` — one line, no file construction
- Source viewer fetches `game.sourceUrl` (same origin on GitHub Pages)
- All games deploy to `johnesco.github.io/<game>/`, so same-origin iframes and fetch work

## Running Locally

```bash
python tools/dev-server.py [--port 8000]
# Maps /ifhub/* → ifhub/, /<game>/* → projects/<game>/
# Open http://127.0.0.1:8000/ifhub/app.html
```

## Adding a New Game

1. Add a game entry to `games.json` with id, title, and URL fields (`playUrl`, `sourceUrl`, `walkthroughUrl`, `landingUrl`)
2. Add card metadata to `cards.json`
3. Ensure the game repo deploys to GitHub Pages

## Hosting on the Web

Pure static site — no server-side logic. Deployed to GitHub Pages from the repo directly. Each game is served from its own repo's GitHub Pages.

## Relation to Game Repos

- Each game project lives under `C:\code\ifhub\projects\` with its own repo and build process
- Game repos are never modified by this project — ifhub only reads from them
- The hub iframes game pages and fetches source files — no copying
- Game projects have their own GitHub Pages sites (landing pages, play pages, source)
- For shared Inform 7 tooling and references, see `C:\code\ifhub\CLAUDE.md`

## CSS Mood Theming (Zork1 v4+)

The shared `play.html` includes version-gated CSS atmospheric effects for Zork I v4 and later. When the binary path matches `zork1-v(\d+)` with version >= 4 (or no version number, meaning current/latest), the page adds `body.zork1-enhanced` and activates: zone-reactive mood palettes, CRT terminal intro, reversed status bar, Up a Tree effects (canopy glow, falling leaves), egg taken golden explosion, larger fonts (19px/17px), text fade-in, and synchronized color transitions.

The Zork1 v4 game repo has its own hand-crafted `play.html` with all effects baked in (no version gating needed).

### MutationObserver Input Detection

Parchment in WASM mode (Emglken) does **not** wrap user input in `.Input` CSS class spans. The egg flash detection tracks the previous buffer node's text (`lastNodeText`) instead of querying `.BufferWindow .Input` elements. This is because the user's command (e.g., "take egg") appears as a regular added node immediately before the game response ("Taken.") in the DOM mutation sequence.
