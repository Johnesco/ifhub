# IF Hub — Functional Specification

> **Status:** Living document. This is the authoritative specification for IF Hub application behavior. It supersedes CLAUDE.md for all feature and behavior descriptions.

---

## 1. Overview

IF Hub is a static website that serves multiple interactive fiction (IF) games through a unified browser-based interface. Users can play games, read syntax-highlighted source code, and follow annotated walkthroughs — all without downloads, plugins, or server-side logic.

Games run in-browser via [Parchment](https://github.com/curiousdannii/parchment), a JavaScript interpreter for the Glulx and Z-machine virtual machines. Sound-enabled games embed audio in native blorb format.

**Key constraints:**
- Pure static site — no server, no accounts, no tracking
- All game binaries and assets are committed to the repo
- Deployed to GitHub Pages from the repo directly

---

## 2. Pages

IF Hub consists of four page types:

| Page | File | Purpose |
|------|------|---------|
| Landing page | `index.html` | Game catalog with cards, descriptions, and links |
| Split-pane player | `app.html` | Game + source viewer + walkthrough in a resizable layout |
| Shared play page | `play.html` | Parchment game player (loaded in iframes or standalone) |
| Standalone play pages | `games/<id>/play.html` | Per-game generated pages from `play-template.html` |

### 2.1 Landing Page (`index.html`)

The hub entry point. Fetches `games.json` at load time and renders a card for each game that has a `card` object defined.

**Behavior:**
- Renders game cards in document order (same order as `games.json`)
- Each card shows: title, meta text, description, and links
- Links per card: "Play fullscreen", "Play in IF Hub" (`app.html?game=<id>`), "About" (landing page)
- Sound-enabled games show "(with sound)" after the play label
- Versioned games show additional version links below the main card links
- Version links are rendered from the card's `versions` array, resolving labels from the game map

**Static content sections:**
- "What's Inside" — feature list (play, source, walkthroughs, audio, resizable layout)
- "About" — project description and philosophy
- Footer with Inform 7 and Parchment attribution

### 2.2 Split-Pane Player (`app.html`)

The primary play interface. A two-pane layout with the game on the left and source/walkthrough on the right.

**URL parameters:**
- `?game=<id>` — loads the specified game on startup (defaults to first game in registry)

**Layout:**
- CSS Grid with three columns: game pane, resize handle (5px), source pane
- Game pane width stored in `--game-width` CSS variable, initialized from computed width
- Resize handle supports mouse and touch drag to rebalance panes
- Minimum pane width: 200px on each side

**Toolbar (top, spans full width):**
- Game selector dropdown (populated from `games.json`)
- Sound controls (mute button + volume slider) — hidden by default, shown when game iframe reports `ifhub:soundReady`
- View tabs: "Source" and "Walkthrough"

**Pane visibility states:**
- Default: both panes visible
- Source collapsed: `body.source-collapsed` — game fills full width
- Game collapsed: `body.game-collapsed` — source fills full width
- Toggle buttons: "Hide Game" / "Show Game" and dismiss (x) button
- Clicking an active tab collapses the source pane; clicking an inactive tab expands and switches

**Game pane:**
- Iframe loading `play.html?binary=<path>&title=<title>`
- Updates when game selector changes

**Source pane (source view):**
- Toolbar: file path label, search box, line count, toggle/dismiss buttons
- Navigation sidebar (220px, left): hierarchical outline from Part/Chapter/Section headings
- Code area: syntax-highlighted Inform 7 source rendered as an HTML table
- Source fetched from path in `games.json` `source` field, cached per game ID
- For ZIL source (`sourceBrowser: true`), loads an iframe instead of the code viewer

**Source pane (walkthrough view):**
- Loads walkthrough HTML in an iframe from the `walkthrough` field in `games.json`
- Shows "Not yet available" message if no walkthrough defined for the game

**Keyboard shortcuts:**
- Ctrl+F / Cmd+F: focus search box (when source pane is visible)

**Responsive breakpoints:**
- Below 1024px: sidebar hidden
- Below 800px: single-column layout, resize handle hidden

### 2.3 Shared Play Page (`play.html`)

A Parchment player page used in two contexts:
1. Loaded in iframes by `app.html`
2. Accessible directly via URL

**URL parameters:**
- `?binary=<path>` — path to the `.ulx.js` or `.gblorb.js` binary
- `?title=<title>` — game title (used for page title and loading display)

**Parchment configuration:**
- `default_story`: binary path from URL parameter
- `lib_path`: `lib/parchment/`
- `story_name`: derived from binary path (filename only) — required for Parchment's file type detection
- `use_proxy`: 0 (disabled)
- `do_vm_autosave`: 1 (enabled)

**CSS theming:**
- Base dark theme with Glk variable overrides (buffer, grid, input colors)
- Serif font stack: Iowan Old Style, Palatino, Georgia, Times New Roman
- Monospace font stack: SF Mono, Fira Code, Cascadia Code, Consolas
- Custom scrollbar styling (dark track, subtle thumb)
- Glk style overrides: `.Input` (bold gold), `.Style_user1` (hidden), `.Style_header`, `.Style_alert`, `.Style_note`

**Version-gated CSS effects (Zork I v4+):**

When the binary path matches `zork1-v(\d+)` with version >= 4 (or unversioned current), the page activates `body.zork1-enhanced` with:
- Mood palette system: CSS custom properties (`--mood-*`) updated dynamically via JS based on the current room's zone
- Smooth 1.2s color transitions between zones using CSS `@property` registered custom properties
- CRT terminal intro effect on first load
- Reversed status bar styling
- "Up a Tree" visual effects (canopy glow, falling leaves)
- Egg taken golden explosion flash
- Larger font sizes (19px buffer, 17px grid)
- Text fade-in on new content
- Sword blue glow vignette effect

**Sound integration:**
- When embedded in `app.html`, responds to `ifhub:setMute` and `ifhub:setVolume` postMessage commands
- Posts `ifhub:soundReady` to parent when sound is available

**Page lifecycle:**
- `pageshow` event handler: reloads on back/forward navigation (`e.persisted`) to prevent stale game state

### 2.4 Standalone Play Pages (`games/<id>/play.html`)

Generated by `deploy.sh` from `play-template.html`. One per game.

**Template placeholders:**
- `__TITLE__` — game title from `games.json`
- `__BINARY__` — binary filename (basename only)

**Differences from shared `play.html`:**
- Binary path is hardcoded (not from URL parameters)
- `lib_path` points to `../../lib/parchment/` (relative to `games/<id>/`)
- No version-gated CSS effects
- Cache-busting `?v=<timestamp>` appended to all `.js` and `.css` references

### 2.5 Per-Game Landing Pages (`games/<base>/index.html`)

Generated by `deploy.sh` from `landing-template.html` for games with a `card` object (unless `customLanding: true`).

**Template placeholders:**
- `__TITLE__` — card title
- `__SUBTITLE_SECTION__` — optional subtitle paragraph
- `__PLAY_URL__` — link to play page (relative)
- `__PLAY_LABEL__` — "Play" or "Play Latest Version", with "(with sound)" if applicable
- `__PROSE_SECTION__` — card prose paragraphs or description
- `__EXTRA_PAGES_SECTION__` — links to extra pages (map, scenarios, etc.)
- `__VERSION_SECTION__` — version history cards with per-version features, links, and play buttons
- `__COMMUNITY_SECTION__` — grouped external links (categorized)
- `__FOOTER__` — custom footer HTML

**Layout:**
- Breadcrumb navigation back to IF Hub
- Max-width 740px centered content
- Version entries as styled cards with feature lists
- Community links in a 2-column grid

---

## 3. Game Registry (`games.json`)

The central data file that drives the landing page, game selector, source viewer, and player.

### 3.1 Schema

Each entry is an object with these fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (e.g., `"zork1-v4"`, `"sample"`) |
| `title` | string | Yes | Display title shown in dropdown and page titles |
| `sourceLabel` | string | No | Label shown in source pane toolbar (e.g., `"zork1-v4.ni"`) |
| `source` | string | No | Path to source file relative to ifhub root (e.g., `"games/sample/story.ni"`) |
| `sourceBrowser` | boolean | No | If true, source is loaded in an iframe instead of the code viewer |
| `binary` | string | Yes | Path to base64-encoded game binary (e.g., `"games/sample/sample.ulx.js"`) |
| `walkthrough` | string | No | Path to walkthrough HTML file |
| `sound` | string | No | Sound mode: `"blorb"` for native Glk sound, absent for no sound |
| `versionLabel` | string | No | Label shown in version lists (e.g., `"v2 — Bug Fixes"`) |
| `card` | object | No | If present, game appears as a card on the landing page |

### 3.2 Card Object

Controls how the game appears on the landing page and its generated landing page.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Card heading |
| `meta` | string | Yes | Italicized subtitle (e.g., `"An Interactive Adventure"`) |
| `description` | string | Yes | Card body text (HTML allowed) |
| `subtitle` | string | No | Additional subtitle for the landing page |
| `prose` | string[] | No | Array of HTML paragraphs for the landing page story section |
| `versions` | string[] | No | Array of game IDs to show as version links (newest first) |
| `versionDetails` | object | No | Map of game ID to version detail object (tagline, features, extraLinks) |
| `customLanding` | boolean | No | If true, `deploy.sh` skips generating a landing page (game provides its own) |
| `extraPages` | object[] | No | Array of `{label, href}` for extra page links |
| `communityLinks` | object[] | No | Array of `{heading, links: [{label, href}]}` for external link sections |
| `footer` | string | No | Custom HTML footer for the landing page |

### 3.3 Current Games

| ID | Title | Binary Format | Sound | Has Card |
|----|-------|--------------|-------|----------|
| `zork1-v0` | Zork I (v0 — Original ZIL) | `.z3.js` | No | No (version of zork1-v4) |
| `zork1-v1` | Zork I (v1) | `.ulx.js` | No | No (version of zork1-v4) |
| `zork1-v2` | Zork I (v2) | `.ulx.js` | No | No (version of zork1-v4) |
| `zork1-v3` | Zork I (v3) | `.ulx.js` | Blorb | No (version of zork1-v4) |
| `zork1-v4` | Zork I (v4 — Current) | `.gblorb.js` | Blorb | Yes (primary card) |
| `dracula` | Dracula's Castle | `.ulx.js` | No | Yes (custom landing) |
| `feverdream` | Fever Dream | `.gblorb.js` | Blorb | Yes |
| `sample` | Sample | `.ulx.js` | No | Yes |

---

## 4. Source Viewer

The source viewer renders Inform 7 source code with syntax highlighting, navigation, and search.

### 4.1 Syntax Highlighting

Line-by-line highlighting with these token classes:

| Class | Color | Matches |
|-------|-------|---------|
| `.syn-head` | `#e0c8a0` bold | Part/Chapter/Section/Volume/Book headings |
| `.syn-tbl` | `#9090b0` | Table declarations |
| `.syn-str` | `#8bab6e` | String literals (`"..."`) |
| `.syn-sub` | `#7ea8b0` | Text substitutions (`[...]` inside strings) |
| `.syn-cmt` | `#605840` italic | Comments (`[...]` outside strings) |
| `.syn-kw` | `#c08050` | Keywords (Understand, Instead, After, Before, etc.) |
| `.syn-num` | `#b08a70` | Numeric literals |
| `.syn-rule` | `#b89860` | Rule names |

**Highlighting precedence:** Headings and table lines are highlighted as a whole line. Otherwise, the highlighter tracks state across the line: normal → string → substitution → comment, with bracket depth counting for nested `[...]`.

### 4.2 Navigation Sidebar

- Parses heading lines matching `^(Volume|Book|Part|Chapter|Section)\s+(.+)`
- Renders as a hierarchical list: Part/Volume/Book at top level, Chapter indented, Section further indented
- Clicking a nav item scrolls the corresponding line into view and marks it as active
- Hidden below 1024px viewport width

### 4.3 Search

- Activated by Ctrl+F or clicking the search box
- Minimum 2 characters to trigger search
- 200ms debounce on input
- Highlights matches with `.search-hit` class (gold background)
- Current match highlighted with `.search-current` (brighter, with outline)
- Enter: next match; Shift+Enter: previous match; Escape: clear and blur
- Uses TreeWalker to find text nodes, preserving existing syntax highlight spans

### 4.4 Source Browser (ZIL)

For games with `sourceBrowser: true` (currently only `zork1-v0`), the source pane loads a standalone HTML page in an iframe instead of the built-in code viewer. This page is a custom ZIL source browser with its own navigation and annotation features.

---

## 5. Sound System

### 5.1 Architecture

Sound-enabled games use **native Glk/blorb sound**. Audio files (`.ogg`) are embedded in the `.gblorb` binary at compile time. Parchment's Emglken WASM engine plays sounds via AudioContext when the game issues Glk sound channel calls.

There is no JavaScript overlay or separate audio file loading. The game binary is self-contained.

### 5.2 Hub Sound Controls (`app.html`)

The split-pane player provides centralized sound controls in the toolbar:

- **Mute button** — SVG speaker icon, toggles between speaker and muted state
- **Volume slider** — range input (0-100), default 70

**Persistence:** Mute state and volume are stored in `localStorage`:
- `ifhub-audio-muted`: `"1"` or `"0"`
- `ifhub-audio-volume`: integer 0-100

**postMessage protocol:**

| Message | Direction | Fields | Purpose |
|---------|-----------|--------|---------|
| `ifhub:soundReady` | iframe → parent | `type` | Game has sound capability; show controls |
| `ifhub:setMute` | parent → iframe | `type`, `muted` (boolean) | Toggle mute |
| `ifhub:setVolume` | parent → iframe | `type`, `volume` (0.0-1.0) | Set volume |

Controls are hidden until `ifhub:soundReady` is received. On receipt, the parent pushes the current mute/volume state to the iframe.

---

## 6. Deploy Pipeline (`deploy.sh`)

Assembles the `games/` directory from project source trees and generates HTML pages.

### 6.1 Asset Copying

For each entry in the `GAMES` array:
1. Copy source `.ni` file to `games/<id>/story.ni` (skip if `"none"`)
2. Copy binary file to `games/<id>/<filename>`
3. Copy walkthrough files from `WALKTHROUGH_DIRS` (if defined): `walkthrough.html`, `walkthrough.txt`, `walkthrough-guide.txt`, `walkthrough_output.txt`

**Special handling:**
- `zork1-v0`: copies `source-browser.html` (standalone ZIL source viewer)
- `dracula`: copies custom landing page and BASIC source files, fixes relative fetch paths
- `zork1`: copies extra pages (map, scenarios, testing, etc.) to `games/zork1/extras/`

### 6.2 Page Generation

**Standalone play pages** (`games/<id>/play.html`):
- Generated from `play-template.html` for every game with a directory
- Cache-busting `?v=<timestamp>` appended to `.js` and `.css` references
- Versioned games (`-v\d+$` suffix) also get an `index.html` redirect to `play.html`

**Landing pages** (`games/<base>/index.html`):
- Generated from `landing-template.html` for games with a `card` (excluding `customLanding: true`)
- Versioned games use the base ID (strip `-v\d+$`) for the landing directory
- Populates version history, community links, prose sections, and extra page links from `games.json`

### 6.3 Configuration

Adding a new game requires updates in three places:

1. **`games.json`** — game entry with id, title, binary, source paths
2. **`deploy.sh` GAMES array** — `"id  source-path  binary-path"` entry
3. **`deploy.sh` WALKTHROUGH_DIRS** — if the game has walkthrough files

Missing any of these causes the game to silently not appear or show warnings during deploy.

---

## 7. Binary Format

### 7.1 `.ulx.js` / `.gblorb.js` Wrapping

Parchment loads game binaries via JSONP-style `<script>` tags. The binary file must be a single-line JavaScript file:

```
processBase64Zcode('BASE64_ENCODED_BINARY')
```

**Requirements:**
- Single quotes around the base64 string
- No `var` declaration, no semicolons
- Entire file must be exactly one line (no interior newlines)
- `processBase64Zcode` is defined by Parchment's `parchment.js`

**Why JSONP?** Avoids CORS restrictions that would block `fetch()` on `file://` URLs.

### 7.2 Parchment Library Files

Each deployment needs 12 files in `lib/parchment/`:

| File | Role |
|------|------|
| `jquery.min.js` | DOM library |
| `main.js` | Game loader |
| `main.css` | Layout styling |
| `parchment.css` | Engine styling |
| `parchment.js` | Engine (with AudioContext sound support) |
| `quixe.js` | JS Glulx interpreter |
| `glulxe.js` | WASM Glulx interpreter |
| `ie.js` | IE compatibility (nomodule) |
| `bocfel.js` | Z-machine interpreter |
| `resourcemap.js` | Resource mapping |
| `zvm.js` | Z-machine VM |
| `waiting.gif` | Loading indicator |

IF Hub maintains its own copy at `ifhub/lib/parchment/` separate from the shared tooling copy at `tools/web/parchment/`.

---

## 8. Visual Design

### 8.1 Color Palette

Dark theme throughout:

| Element | Color | Usage |
|---------|-------|-------|
| Page background | `#0a0a0a` | HTML background |
| Content background | `#111` | Cards, game area, buffer window |
| Primary text | `#d4c5a9` | Body text, buffer text |
| Heading text | `#e8d8b0` / `#c4b48a` | h1 / h2 |
| Accent / links | `#e8d090` | Links, input caret, active nav |
| Muted text | `#aa9966` / `#887755` | Subtitles, meta, footer |
| Borders | `#2a2418` / `#1e1a14` | Cards, grid window, dividers |
| Status bar | `#1c1810` bg, `#aa9966` fg | Grid window (Glk) |

### 8.2 Typography

- **Body:** Georgia, "Times New Roman", serif
- **Code:** SF Mono, Fira Code, Cascadia Code, Consolas, Courier New, monospace
- **Code font size:** 13px with 1.55 line-height
- **Buffer text:** 16px with 1.6 line-height (19px in Zork I v4+ enhanced mode)

---

## 9. Hosting and Serving

- Deployed to **GitHub Pages** from the repo
- Run `deploy.sh` to update `games/`, commit, and push
- Local development: `python -m http.server 8000` from the `ifhub/` directory
- No build step beyond `deploy.sh` — the site is ready to serve as-is
- `file://` protocol does not work (CORS restrictions on JSONP script loading)
