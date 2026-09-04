# IF Hub — Functional Specification

> **Status:** Living document. This is the authoritative specification for IF Hub application behavior. It supersedes CLAUDE.md for all feature and behavior descriptions.

---

## 1. Overview

IF Hub is a development hub and web player for Inform 7 interactive fiction. It provides:

- **A shared toolchain** — compilation, testing, web player setup, and project scaffolding
- **A multi-game web player** — the `site/` static site where users play games, read source code, and follow walkthroughs (serves games in-place from their own repos)
- **Inform 7 reference documentation** — syntax guides, formatting, world model, and more

Games run in-browser via [Parchment](https://github.com/curiousdannii/parchment), a JavaScript interpreter for the Glulx and Z-machine virtual machines. Sound-enabled games embed audio in native blorb format.

**Key constraints:**
- Pure static site — no server, no accounts, no tracking
- All game binaries and assets are committed to the repo
- Deployed to GitHub Pages from the repo directly
- Games are separate repositories at `C:/code/text-games/<engine>/<game>/`, built and tested by their engine workspace; the hub discovers them through `workspaces.json` and each game's `ifhub.conf`

**Section map:**
- Sections 2–9: The web player application (pages, registry, source viewer, sound, binary format, visual design, hosting)
- Section 10: Building and publishing (the engine workspaces build; the hub ships)

---

## 2. Pages

IF Hub consists of four page types:

| Page | File | Purpose |
|------|------|---------|
| Landing page | `index.html` | Game catalog with cards, descriptions, and links |
| Split-pane player | `app.html` | Game + source viewer + walkthrough in a resizable layout |
| Shared play page | `play.html` | Parchment game player (loaded in iframes or standalone) |
| Per-game pages | `/<game>/play.html` | Served in-place from game repos via GitHub Pages |

### 2.1 Landing Page (`index.html`)

The hub entry point. Fetches `cards.json` and renders a card for each game.

**Behavior:**
- Renders game cards in document order (same order as `cards.json`)
- Each card shows: title, meta text, description, and links
- Links per card: "Play fullscreen" (game's own `playUrl`), "Play in IF Hub" (`app.html?game=<id>`), "Source" (`/<base>/source.html`), "Walkthrough" (`/<base>/walkthrough.html`)
- Sound-enabled games show "(with sound)" after the play label
- Versioned games show additional version links below the main card links
- Card metadata is maintained in `cards.json`

**Theme picker:**
- A `.title-row` flex container next to the h1 title holds a theme dropdown
- Dropdown populated from `themes.js` with 10 platform themes
- Theme selection persisted in `localStorage` key `ifhub-theme`

**Collections:**
- A Collection dropdown (populated from `hubs.json`) filters the catalog to a curated subset (by engine or tag)
- The active collection is encoded in the URL query string as `?hub=<id>` (the "all" collection uses the bare path), so a filtered view is shareable and bookmarkable
- Changing the collection updates the URL via `history.pushState` and re-renders the cards **in place** — no full page reload, since `cards.json`/`hubs.json` are already in memory
- Browser back/forward (`popstate`) restores the collection encoded in the URL
- When a non-"all" collection is active, the page title and subtitle are replaced with the collection's `title`/`description`
- Deep links (`index.html?hub=<id>`) load the filtered view directly

**Static content sections:**
- "What's Inside" — feature list (play, source, walkthroughs, audio, resizable layout)
- "About" — project description and philosophy
- Footer with Inform 7 and Parchment attribution

### 2.2 Split-Pane Player (`app.html`)

The primary play interface. A two-pane layout with the game on the left and source/walkthrough on the right.

**URL parameters:**
- `?game=<id>` — loads the specified game on startup (defaults to first game in registry)
- `?hub=<id>` — restricts the game selector to a collection from `hubs.json` (defaults to all games)

**Layout:**
- CSS Grid with three columns: game pane, resize handle (5px), source pane
- Game pane width stored in `--game-width` CSS variable, initialized from computed width
- Resize handle supports mouse and touch drag to rebalance panes
- Minimum pane width: 200px on each side

**Toolbar (top, spans full width):**
- Library link (always visible, returns to `index.html`; uses hub-filtered URL when `hub` param is active)
- Collection selector dropdown (populated from `hubs.json`): re-filters the game selector **in place** — no page reload. Uses `history.replaceState` to keep the `?hub=` URL shareable without competing with the player iframe's session history. The currently-loaded game stays loaded if it belongs to the new collection; otherwise the first game in the collection loads
- Game selector dropdown (populated from `games.json`)
- Style dropdown (overlay-aware theme selector): for games with `overlayLabel`, shows the game's native overlay as the default first option, then a separator, then all platform themes; for games without overlays, shows only platform themes. Per-game style preference stored in `localStorage` key `ifhub-style-<gameId>`
- Sound controls (mute button + volume slider) — hidden by default, shown when game iframe reports `ifhub:soundReady`
- View toggle buttons: Game, Source, Walk, Tests (see **View switching** below)

**View switching:**

The toolbar displays four toggle buttons — Game, Source, Walk, and Tests — that control which panes are visible. The buttons follow two rules:

- **Game** is independent: clicking it toggles the game pane on or off regardless of the other buttons.
- **Source, Walk, and Tests** are mutually exclusive (radio behavior): clicking one activates it and deactivates the other two. Clicking the already-active button deactivates it (collapses the right pane).

The active view combination is reflected in the URL query string as `?view=<panes>`, where panes are joined with `+`. Examples: `?view=game+tests`, `?view=game+source`, `?view=tests`. This allows bookmarkable links to specific view states.

The Tests button is only visible for games that have `testsUrl` in `games.json`.

**Pane visibility states:**
- Default: both panes visible (game + source)
- Source/right pane collapsed: `body.source-collapsed` — game fills full width
- Game collapsed: `body.game-collapsed` — right pane fills full width
- Toggle buttons: "Hide Game" / "Show Game" and dismiss (x) button
- Clicking an active right-pane tab collapses the right pane; clicking an inactive tab expands and switches

**Game pane:**
- Iframe loading the game's own play page via `playUrl` from `games.json`
- Updates when game selector changes

**Source pane (source view):**
- Toolbar: file path label, search box, line count, toggle/dismiss buttons
- Navigation sidebar (220px, left): hierarchical outline from Part/Chapter/Section headings
- Code area: syntax-highlighted Inform 7 source rendered as an HTML table
- Source fetched from `sourceUrl` in `games.json`, cached per game ID
- For ZIL source (`sourceBrowser: true`), loads an iframe instead of the code viewer

**Source pane (walkthrough view):**
- Loads walkthrough HTML in an iframe from `walkthroughUrl` in `games.json`
- Shows "Not yet available" message if no walkthrough defined for the game

**Source pane (tests view):**

A fourth view alongside Game, Source, and Walkthrough. Loads the game's `testsUrl` in an iframe, following the same pattern as the walkthrough frame.

- **Viewer page (`tests.html`):** A self-contained HTML page that reads `test-results.json` from its own directory. Each game version that has test results gets its own `tests.html` and `test-results.json` pair.
- **Data format (`test-results.json`):** A compact JSON format produced by `slim-test-results.js` from full `transcript-test` output. Contains only the fields needed for display (pass/fail status, assertion details, command sequences).
- **Summary view:** Shows pass/fail cards for each transcript — a quick overview of test health across the game's transcripts.
- **Detail view:** Collapsible per-command sections showing individual assertions and their results.
- **Visibility:** The Tests toggle button in the toolbar only appears for games that have `testsUrl` in `games.json`. `build_games.py` auto-detects `tests.html` on disk and sets `testsUrl` automatically when building the registry.

**Keyboard shortcuts:**
- Ctrl+F / Cmd+F: focus search box (when source pane is visible)

**Responsive breakpoints:**
- Below 1024px: sidebar hidden
- Below 800px: single-column layout, resize handle hidden

### 2.3 Shared Play Page (`play.html`)

A Parchment player page for standalone use. In the serve-in-place architecture, `app.html` iframes each game's own play page directly — this shared page is a fallback for direct access.

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

**Version-gated CSS effects (Zork I v3+):**

When the binary path matches `zork1-v(\d+)` with version >= 3 (or unversioned current), the page activates `body.zork1-enhanced` with:
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

**Platform theme support:**
- Loads `themes.js` and calls `initTheme('game')` to apply the current theme
- Theme listener responds to `ifhub:applyTheme` and `ifhub:restoreOverlay` postMessage events
- On `ifhub:applyTheme`: injects a `<style id="platform-theme-override">` element with `!important` rules for game colors
- On `ifhub:restoreOverlay`: removes the `<style id="platform-theme-override">` element to restore the native appearance

### 2.4 Per-Game Pages (served in-place)

Each game project owns its own pages (`play.html`, `source.html`, `walkthrough.html`, `index.html`) and deploys them via GitHub Pages. The hub references these pages by URL — no copying or generation needed.

**Game page locations (served from game repos):**
- Zork I: `johnesco.github.io/zork1/` — v0–v3 versioned pages, landing page
- Dracula: `johnesco.github.io/dracula/` — current + v0 BASIC, landing page
- Fever Dream: `johnesco.github.io/feverdream/` — play, source, walkthrough
- Sample: `johnesco.github.io/sample/` — play, source, walkthrough

Each game has 4 standard pages at its root (or version directory):
- `play.html` — Parchment game player
- `source.html` — source browser with syntax highlighting (all games now have this)
- `walkthrough.html` — walkthrough viewer
- `index.html` — landing page with Play, Source, and Walkthrough links

**Landing page link pattern:** Each game's `index.html` provides direct links to Play, Source, and Walkthrough. The hub's landing page (`cards.json`) also links to `/<base>/source.html` and `/<base>/walkthrough.html` on each card.

**Theme listener:**
- All Parchment-based game `play.html` files include a theme listener script that handles `ifhub:applyTheme` and `ifhub:restoreOverlay` postMessage events
- Games with CSS overlays additionally include suppression CSS for `body.platform-theme-active` — the body class hides game-specific visual effects (particles, scanlines, vignettes, pseudo-elements, animations) while the mood engine continues running in the background so that restoring the overlay gives correct room-state colors immediately

---

## 3. Game Registry (`games.json`)

The central data file that drives the landing page, game selector, source viewer, and player.

### 3.1 Schema

Each entry is an object with these fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (e.g., `"zork1-v3"`, `"sample"`) |
| `title` | string | Yes | Display title shown in dropdown and page titles |
| `sourceLabel` | string | No | Label shown in source pane toolbar (e.g., `"zork1-v3.ni"`) |
| `sourceBrowser` | boolean | No | If true, source is loaded in an iframe instead of the code viewer |
| `playUrl` | string | Yes | Absolute URL path to game's play page (e.g., `"/zork1-v3/play.html"`) |
| `sourceUrl` | string | Yes | Absolute URL path to source file or source browser (e.g., `"/zork1-v3/source.html"`) |
| `walkthroughUrl` | string | No | Absolute URL path to walkthrough HTML page |
| `testsUrl` | string | No | Absolute URL path to the tests.html viewer page (e.g., `"/zork1/tests.html"`). When present, the Tests toggle button appears in the toolbar. `build_games.py` auto-detects `tests.html` on disk and sets this field automatically. |
| `landingUrl` | string | No | Absolute URL path to game's landing page (e.g., `"/zork1/"`) |
| `sound` | string | No | Sound mode: `"blorb"` for native Glk sound, absent for no sound |
| `versionLabel` | string | No | Label shown in version lists (e.g., `"v2 — Bug Fixes"`) |
| `overlayLabel` | string | No | Display label for the game's native CSS overlay (e.g., `"Fever Dream Overlay"`). When present, the style dropdown shows this as the default option. |

### 3.2 Card Metadata (`cards.json`)

Card metadata for the hub homepage is maintained in `cards.json`. Each card represents a game (grouping versions) with:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Game ID (primary entry, e.g., `"zork1-v3"`) |
| `base` | string | Base ID (e.g., `"zork1"`) |
| `title` | string | Display title for the card |
| `meta` | string | Subtitle or author info |
| `description` | string | Card description text |
| `sound` | string | Sound mode (if present) |
| `playUrl` | string | Absolute URL to play page |
| `landingUrl` | string | Absolute URL to landing page |
| `versions` | array | Version entries with `id`, `label`, optional `sound`, and `playUrl` |

### 3.3 Current Games

The live list is `site/games.json`, regenerated by `tools/build_games.py` from every `ifhub.conf` found under the `workspaces.json` roots. Landing-page cards are collapsed into `site/cards.json` (versioned groups become one card).

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

### 4.4 Source Browser Mode

For games with `sourceBrowser: true`, the source pane loads a standalone HTML page in an iframe instead of the built-in Inform 7 code viewer. Currently used by:
- `zork1-v0` — ZIL source browser with custom syntax highlighting and annotation features
- `dracula-v0` — BASIC source browser with annotation toggle
- `sample` — Inform 7 source browser (standalone `source.html` page)

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

| `ifhub:applyTheme` | parent → iframe | `type`, `game` (object with colors/fonts), `scrollbar` (object) | Apply platform theme colors, suppress overlay |
| `ifhub:restoreOverlay` | parent → iframe | `type` | Remove platform theme, restore native overlay |
| `ifhub:themeChange` | parent → iframe | `type`, `themeId` (string) | Live theme switch (hub's play.html only) |

Controls are hidden until `ifhub:soundReady` is received. On receipt, the parent pushes the current mute/volume state to the iframe.

---

## 6. Serve-in-Place Architecture

The hub serves games **in-place** from their own GitHub Pages deployments. There is no deploy pipeline that copies files into the hub — each game project is the single source of truth for its own assets.

### 6.1 How It Works

- Each game repo deploys to `johnesco.github.io/<game>/` via GitHub Pages
- `games.json` contains absolute URL paths (`playUrl`, `sourceUrl`, `walkthroughUrl`, `landingUrl`)
- `app.html` loads `iframe.src = game.playUrl` — one line, no construction
- Source viewer fetches `game.sourceUrl` directly (same origin = works)
- Walkthrough viewer iframes `game.walkthroughUrl`

All repos deploy under `johnesco.github.io/*`, making everything same-origin. This means iframes, `fetch()`, and `postMessage` all work freely between the hub and game pages.

### 6.2 Adding a Game

Build the game in its engine workspace (`C:/code/text-games/<engine>/tools/build.py <game>`), then run `python tools/ship.py <game>` from the hub. Ship verifies the folder (`ifhub.conf` + `play.html`), writes the wrapper pages, sets `hub = yes`, regenerates `games.json` and `cards.json`, publishes the game repo (creating it and enabling Pages on first use), and pushes the hub. `games.json` and `cards.json` are never edited by hand.

### 6.3 Serve-in-Place History

Before March 2026 a deploy step copied binaries and generated pages into the hub (`site/games/`, a `deploy` object per entry). All of that is gone: the hub holds URLs only.

### 6.4 Local Development

Use the `/serve` skill: it starts Portman on port 9000 and registers `site/` plus every game folder so the hub and the games load at production-equivalent URLs (`/ifhub/app.html`, `/<game>/play.html`). `/kill-servers` stops it. For the hub pages alone, `.claude/launch.json` defines `hub-site`, a plain `http.server` on port 8892 serving `site/`.

### 6.5 Publishing a Game

Games are built and tested in their engine workspace, then shipped with `python tools/ship.py <game>`. The contract and the per-engine build commands are in `docs/publishing.md`.

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

IF Hub keeps its own copy at `site/lib/parchment/` for `site/play.html`. The copy that gets installed into Inform 7 and Z-machine games lives in the Inform 7 workspace (`C:/code/text-games/i7/tools/web/parchment/`).

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
- **Buffer text:** 16px with 1.6 line-height (19px in Zork I v3+ enhanced mode)

### 8.3 Platform Themes

The hub supports 10 retro platform themes modeled after systems Infocom shipped Z-machine games on. Themes are defined in `themes.js` and each contains three property groups:

- **`chrome`** — Hub UI colors (page background, text, cards, toolbar, borders, buttons, input fields, font family)
- **`game`** — Game iframe colors (buffer/grid backgrounds, text colors, input, font sizes, font families)
- **`scrollbar`** — Scrollbar thumb, track, and hover colors

Theme selection persists in `localStorage` key `ifhub-theme`. The landing page and app page both apply themes by setting CSS custom properties on `document.documentElement`.

**Available themes:** Classic (default), MS-DOS, Apple II, Commodore 64, Amiga, Macintosh, Atari ST, CP/M (Kaypro), Atari 800, TRS-80

### 8.4 Overlay Selector

Games with CSS overlays (mood palettes, atmospheric effects) have their overlay listed as a selectable style option alongside platform themes. The style dropdown in `app.html` shows:

- For games WITH `overlayLabel`: the overlay as the default first option, then a separator, then all platform themes
- For games WITHOUT `overlayLabel`: only platform themes (default from localStorage)

When a platform theme is selected, the hub sends `ifhub:applyTheme` to the game iframe with the theme's game colors. The game's play.html adds `body.platform-theme-active` which suppresses overlay visual effects via CSS rules. The mood engine keeps running in the background so that restoring the overlay gives correct room-state colors immediately.

Style preferences are stored per-game in `localStorage` key `ifhub-style-<gameId>`.

---

## 9. Hosting and Serving

- Hub deployed to **GitHub Pages** from the ifhub repo
- Games deployed to GitHub Pages from their own repos (e.g., `johnesco.github.io/zork1/`)
- Local development: `/serve` (Portman, hub + all games) or the `hub-site` launch config (see 6.4)
- No build or deploy step — the hub is always up to date (games serve from their own repos)
- `file://` protocol does not work (CORS restrictions on JSONP script loading)

---

## 10. Building and Publishing

IF Hub does not build or test games. Each engine workspace under `C:/code/text-games/<engine>/` has a `tools/build.py` that compiles, tests, and lays out the game folder. The hub's `tools/ship.py` verifies the folder contract (`ifhub.conf` + `play.html`), generates the wrapper pages (`index.html`, `source.html`, `walkthrough.html`) when missing, sets `hub = yes`, rebuilds `games.json` + `cards.json`, publishes the folder to its GitHub Pages repo, and pushes the hub registry. See `docs/publishing.md`.
