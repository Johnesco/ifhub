# IF Hub — Architecture Guide

IF Hub is a static site that serves multiple Inform 7 games through a unified browser interface with source viewer, walkthrough viewer, and centralized sound controls.

**Live site**: Deployed to GitHub Pages from this directory.
**Local preview**: `python tools/dev-server.py` (from the ifhub root)

---

## Table of Contents

- [Directory Structure](#directory-structure)
- [How It Works](#how-it-works)
- [Game Registry (games.json)](#game-registry-gamesjson)
- [Sound System](#sound-system)
- [Adding a New Game](#adding-a-new-game)
- [Adding Sound to a Game](#adding-sound-to-a-game)
- [File Reference](#file-reference)

---

## Directory Structure

```
ifhub/
├── README.md                ← This file
├── CLAUDE.md                ← AI assistant instructions
│
├── index.html               ← Landing page (reads cards.json, renders game cards)
├── app.html                 ← Main player UI (game selector, source viewer, sound controls)
├── play.html                ← Shared Parchment player (standalone use)
├── importing.html           ← Documentation/import page
│
├── games.json               ← Game registry — URLs, metadata, sound flags
├── cards.json               ← Card metadata for landing page
│
└── lib/
    └── parchment/           ← Shared Parchment interpreter libraries
        ├── jquery.min.js    ← DOM library
        ├── main.js          ← Parchment game loader
        ├── main.css         ← Layout styling
        ├── parchment.js     ← Engine variant
        ├── parchment.css    ← Engine styling
        ├── quixe.js         ← Quixe interpreter (JS Glulx)
        └── glulxe.js        ← Glulxe interpreter (WASM Glulx)
```

### Current Games

| Game ID | Title | Sound | Play URL |
|---------|-------|-------|----------|
| `zork1-v0` | Zork I (v0 — Original ZIL) | No | `/zork1/v0/play.html` |
| `zork1-v1` | Zork I (v1 — The Port) | No | `/zork1/v1/play.html` |
| `zork1-v2` | Zork I (v2 — Bug Fixes) | No | `/zork1/v2/play.html` |
| `zork1-v3` | Zork I (v3 — Sound) | Yes | `/zork1/v3/play.html` |
| `zork1-v4` | Zork I (v4 — Current) | Yes | `/zork1/v4/play.html` |
| `dracula` | Dracula's Castle | No | `/dracula/play.html` |
| `feverdream` | Fever Dream | Yes | `/feverdream/play.html` |
| `sample` | Sample | No | `/sample/play.html` |

---

## How It Works

### Serve-in-Place Architecture

The hub serves games **in-place** — it iframes each game's own play page directly from the game's GitHub Pages URL. No files are copied into the hub; each game project is the single source of truth for its own assets.

- `games.json` uses URL-based fields (`playUrl`, `sourceUrl`, `walkthroughUrl`, `landingUrl`)
- `app.html` loads `iframe.src = game.playUrl` — one line, no construction
- Source viewer fetches `game.sourceUrl` (same origin on GitHub Pages = works)
- All repos deploy to `johnesco.github.io/*`, so same-origin iframes and fetch work freely

### Main Hub (app.html)

`app.html` is the full-featured interface:
- **Game selector dropdown** — switches between all registered games
- **Source viewer tab** — fetches the game's `story.ni` from its `sourceUrl` with syntax highlighting
- **Walkthrough viewer tab** — iframes the game's walkthrough page from its `walkthroughUrl`
- **Centralized sound controls** — mute button + volume slider (visible only for sound-enabled games)
- **Game player** — an iframe loading the game's own play page via `playUrl`

### Shared Parchment Library

The hub maintains its own Parchment library at `lib/parchment/` for the standalone `play.html`. Each game project also has its own Parchment copy — the hub's copy is separate.

---

## Game Registry (games.json)

Every game must have an entry in `games.json`. This file drives:
- The game selector in `app.html`
- Sound control visibility (the `"sound": "blorb"` flag)

Card metadata for the landing page is maintained in `cards.json`.

### Schema

```json
{
  "id": "mygame",
  "title": "My Game",
  "sourceLabel": "mygame.ni",
  "playUrl": "/mygame/play.html",
  "sourceUrl": "/mygame/story.ni",
  "walkthroughUrl": "/mygame/walkthrough.html",
  "landingUrl": "/mygame/",
  "sound": "blorb",
  "versionLabel": "v1 — Description"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier (e.g., `"zork1-v4"`, `"sample"`). |
| `title` | Yes | Display name in the game selector dropdown. |
| `sourceLabel` | No | Label for the source viewer tab. |
| `playUrl` | Yes | Absolute URL path to the game's play page. |
| `sourceUrl` | Yes | Absolute URL path to source file or source browser page. |
| `walkthroughUrl` | No | Absolute URL path to walkthrough HTML page. |
| `landingUrl` | No | Absolute URL path to game's landing page. |
| `sound` | No | Set to `"blorb"` for native Glk sound. Shows controls in app.html. |
| `sourceBrowser` | No | Set to `true` if source is an HTML page (loaded in iframe instead of fetched as text). |
| `versionLabel` | No | Shown in the game selector for versioned games (e.g., "v1 — The Port"). |

---

## Sound System

Sound-enabled games use **native Glk/blorb sound** via Parchment 2025.1. Audio files (`.ogg`) are embedded in the game binary (`.gblorb`) and played by the interpreter via AudioContext and Glk sound channels. No external JavaScript overlay is needed.

For details on the blorb pipeline (`compile.sh --sound`, `generate-blurb.sh`, `setup-web.sh --blorb`), see `reference/sound.md`.

---

## Adding a New Game

### Prerequisites

The game must already be compiled and have a web player set up in its project directory. See `C:\code\ifhub\CLAUDE.md` for compiler paths and `tools/web/setup-web.sh` for web player setup. The game project must be deployed to GitHub Pages.

### Steps

1. **Ensure the game has the 4 standard pages**: `play.html`, `source.html` (or `story.ni`), `walkthrough.html`, `index.html`

2. **Deploy the game repo to GitHub Pages** at `johnesco.github.io/<game>/`

3. **Add to `games.json`** with URL fields:
   ```json
   {
     "id": "mygame",
     "title": "My Game",
     "sourceLabel": "mygame.ni",
     "playUrl": "/mygame/play.html",
     "sourceUrl": "/mygame/story.ni",
     "walkthroughUrl": "/mygame/walkthrough.html",
     "landingUrl": "/mygame/"
   }
   ```

4. **Add card metadata to `cards.json`**

5. **Commit and push**

---

## Adding Sound to a Game

Use native Glk/blorb sound. See `reference/sound.md` for the full pipeline.

1. Add `.ogg` sound files to `projects/mygame/Sounds/`
2. Add sound declarations to `story.ni`: `Sound of X is the file "Y.ogg".`
3. Compile with `bash tools/compile.sh mygame --sound`
4. Set `"sound": "blorb"` in `games.json`

---

## File Reference

### Hub-Level Files

| File | Purpose | When to Edit |
|------|---------|-------------|
| `index.html` | Landing page — reads `cards.json`, renders game cards | Changing landing page layout or static content |
| `app.html` | Main player UI with game selector, source viewer, sound controls | Changing the player UI, adding features |
| `play.html` | Parchment player (standalone use) | Changing how standalone games load |
| `games.json` | Game registry with URL fields | Adding/removing games, enabling sound |
| `cards.json` | Card metadata for landing page | Adding/removing games |

### Source of Truth

| What | Location | Consumed By |
|------|----------|-------------|
| Parchment interpreter | `ifhub/lib/parchment/` | `play.html` (standalone) |
| Game source | `projects/<game>/story.ni` | Served from game repo, fetched by `app.html` |
| Game binary | `projects/<game>/lib/parchment/<game>.ulx.js` | Served from game repo |
| Game metadata | `games.json` | `app.html` |
| Card metadata | `cards.json` | `index.html` |
| Landing pages | `projects/<game>/index.html` | Served from game repo, linked from `cards.json` |
