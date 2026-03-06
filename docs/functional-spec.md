# IF Hub — Functional Specification

> **Status:** Living document. This is the authoritative specification for IF Hub application behavior. It supersedes CLAUDE.md for all feature and behavior descriptions.

---

## 1. Overview

IF Hub is a development hub and web player for Inform 7 interactive fiction. It provides:

- **A shared toolchain** — compilation, testing, web player setup, and project scaffolding
- **A multi-game web player** — the `ifhub/` static site where users play games, read source code, and follow walkthroughs (serves games in-place from their own repos)
- **Inform 7 reference documentation** — syntax guides, formatting, world model, and more

Games run in-browser via [Parchment](https://github.com/curiousdannii/parchment), a JavaScript interpreter for the Glulx and Z-machine virtual machines. Sound-enabled games embed audio in native blorb format.

**Key constraints:**
- Pure static site — no server, no accounts, no tracking
- All game binaries and assets are committed to the repo
- Deployed to GitHub Pages from the repo directly
- Projects are separate repositories — IF Hub provides tools, projects consume them. The `projects/` directory is gitignored; each project is checked out locally for development

**Section map:**
- Sections 2–9: The web player application (pages, registry, source viewer, sound, binary format, visual design, hosting)
- Section 10: Compilation pipeline (shared build tools)
- Section 11: Testing framework (shared test infrastructure)

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
- Links per card: "Play fullscreen" (game's own `playUrl`), "Play in IF Hub" (`app.html?game=<id>`), "About" (game's `landingUrl`)
- Sound-enabled games show "(with sound)" after the play label
- Versioned games show additional version links below the main card links
- Card metadata is maintained in `cards.json`

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

### 2.4 Per-Game Pages (served in-place)

Each game project owns its own pages (`play.html`, `source.html`, `walkthrough.html`, `index.html`) and deploys them via GitHub Pages. The hub references these pages by URL — no copying or generation needed.

**Game page locations (served from game repos):**
- Zork I: `johnesco.github.io/zork1/` — v0–v4 versioned pages, landing page
- Dracula: `johnesco.github.io/dracula/` — current + v0 BASIC, landing page
- Fever Dream: `johnesco.github.io/feverdream/` — play, source, walkthrough
- Sample: `johnesco.github.io/sample/` — play, source, walkthrough

Each game has 4 standard pages at its root (or version directory):
- `play.html` — Parchment game player
- `source.html` — source browser (for non-I7 games) or `story.ni` (raw I7 source)
- `walkthrough.html` — walkthrough viewer
- `index.html` — landing page

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
| `sourceBrowser` | boolean | No | If true, source is loaded in an iframe instead of the code viewer |
| `playUrl` | string | Yes | Absolute URL path to game's play page (e.g., `"/zork1/v4/play.html"`) |
| `sourceUrl` | string | Yes | Absolute URL path to source file or source browser (e.g., `"/zork1/v4/story.ni"`) |
| `walkthroughUrl` | string | No | Absolute URL path to walkthrough HTML page |
| `landingUrl` | string | No | Absolute URL path to game's landing page (e.g., `"/zork1/"`) |
| `sound` | string | No | Sound mode: `"blorb"` for native Glk sound, absent for no sound |
| `versionLabel` | string | No | Label shown in version lists (e.g., `"v2 — Bug Fixes"`) |

### 3.2 Card Metadata (`cards.json`)

Card metadata for the hub homepage is maintained in `cards.json`. Each card represents a game (grouping versions) with:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Game ID (primary entry, e.g., `"zork1-v4"`) |
| `base` | string | Base ID (e.g., `"zork1"`) |
| `title` | string | Display title for the card |
| `meta` | string | Subtitle or author info |
| `description` | string | Card description text |
| `sound` | string | Sound mode (if present) |
| `playUrl` | string | Absolute URL to play page |
| `landingUrl` | string | Absolute URL to landing page |
| `versions` | array | Version entries with `id`, `label`, optional `sound`, and `playUrl` |

### 3.3 Current Games

| ID | Title | Sound | Play URL |
|----|-------|-------|----------|
| `zork1-v0` | Zork I (v0 — Original ZIL) | No | `/zork1/v0/play.html` |
| `zork1-v1` | Zork I (v1) | No | `/zork1/v1/play.html` |
| `zork1-v2` | Zork I (v2) | No | `/zork1/v2/play.html` |
| `zork1-v3` | Zork I (v3) | Blorb | `/zork1/v3/play.html` |
| `zork1-v4` | Zork I (v4 — Current) | Blorb | `/zork1/v4/play.html` |
| `dracula` | Dracula's Castle | No | `/dracula/play.html` |
| `feverdream` | Fever Dream | Blorb | `/feverdream/play.html` |
| `sample` | Sample | No | `/sample/play.html` |

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

## 6. Serve-in-Place Architecture

The hub serves games **in-place** from their own GitHub Pages deployments. There is no deploy pipeline that copies files into the hub — each game project is the single source of truth for its own assets.

### 6.1 How It Works

- Each game repo deploys to `johnesco.github.io/<game>/` via GitHub Pages
- `games.json` contains absolute URL paths (`playUrl`, `sourceUrl`, `walkthroughUrl`, `landingUrl`)
- `app.html` loads `iframe.src = game.playUrl` — one line, no construction
- Source viewer fetches `game.sourceUrl` directly (same origin = works)
- Walkthrough viewer iframes `game.walkthroughUrl`

All repos deploy under `johnesco.github.io/*`, making everything same-origin. This means iframes, `fetch()`, and `postMessage` all work freely between the hub and game pages.

### 6.2 What Was Eliminated

| Before | After |
|--------|-------|
| `deploy.sh` (copies binaries, walkthroughs, generates pages) | Gone |
| `tools/deploy/generate-play-pages.py` | Gone |
| `tools/deploy/copy-assets.py` | Gone |
| `tools/deploy/extract-cards.py` + card extraction | Gone (cards.json maintained manually) |
| `ifhub/games/` directory (15+ files per game) | Gone |
| Pipeline `deploy` stage | Gone |
| `deploy` object in games.json entries | Replaced by URL fields |

### 6.3 Adding a New Game

1. Ensure the game project has the 4 standard pages (`play.html`, `source.html`, `walkthrough.html`, `index.html`)
2. Deploy the game repo to GitHub Pages
3. Add an entry to `games.json` with URL fields
4. Add card metadata to `cards.json`

### 6.4 Local Development (`tools/dev-server.py`)

A multi-root Python HTTP server that maps URL prefixes to local directories, providing production-equivalent URLs for development:

```
/ifhub/*      → ifhub/
/zork1/*      → projects/zork1/
/dracula/*    → projects/dracula/
/feverdream/* → projects/feverdream/
/sample/*     → projects/sample/
```

```bash
python tools/dev-server.py [--port 8000]
# Open http://127.0.0.1:8000/ifhub/app.html
```

The server auto-discovers games from the `projects/` directory. It binds to `127.0.0.1` (not `""`) to avoid IPv6 issues on Windows.

### 6.5 Post-Build Validation (`tools/validate-web.sh`)

After compiling a game, `compile.sh` runs `validate-web.sh` on the project's web player directory. The validator checks:

1. `play.html` exists
2. No unsubstituted template tokens remain
3. All `src="..."` and `href="..."` references point to files that exist on disk
4. Binary `.js` file is exactly 1 line
5. Binary `.js` file starts with `processBase64Zcode('`
6. `parchment_options` contains `story_name`
7. `parchment.js` is loaded

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

- Hub deployed to **GitHub Pages** from the ifhub repo
- Games deployed to GitHub Pages from their own repos (e.g., `johnesco.github.io/zork1/`)
- Local development: `python tools/dev-server.py` (multi-root server for hub + all games)
- No build or deploy step — the hub is always up to date (games serve from their own repos)
- `file://` protocol does not work (CORS restrictions on JSONP script loading)

---

## 10. Compilation Pipeline

IF Hub provides shared tools for compiling, packaging, and publishing Inform 7 projects. All tools live in `tools/` and operate on projects under `projects/<name>/`.

### 10.1 Compilation (`compile.sh`)

```
bash /c/code/ifhub/tools/compile.sh <game-name> [--sound] [--source PATH] [--compile-only]
```

Compiles a project's `story.ni` (or an alternate source via `--source`) to a playable web game in a single command.

**Options:**
| Flag | Purpose |
|------|---------|
| `--sound` | Embed `.ogg` audio in a `.gblorb` binary |
| `--source PATH` | Use this `story.ni` instead of the project's own (e.g., a frozen version snapshot) |
| `--compile-only` | Skip the web player update step (`setup-web.sh` + `validate-web.sh`) |

**Standard pipeline** (4 steps):
1. Inform 7 → Inform 6 (`inform7.exe -source story.ni -o story.i6`)
2. Inform 6 → Glulx (`inform6.exe -w -G story.i6 <name>.ulx`)
3. Clean intermediates (`story.i6`)
4. Update web player (`setup-web.sh` → base64-encode `.ulx` into `.ulx.js`) — skipped with `--compile-only`

**Sound pipeline** (`--sound`, 6 steps):
1. Inform 7 → Inform 6
2. Inform 6 → Glulx
3. Generate blurb manifest (`generate-blurb.sh`)
4. Package blorb (`inblorb <name>.blurb <name>.gblorb`)
5. Clean intermediates (`story.i6`, `.blurb`)
6. Update web player (`setup-web.sh` → base64-encode `.gblorb` into `.gblorb.js`) — skipped with `--compile-only`

**Pre-flight checks** (run before expensive compilation):
- Colon in story title — Windows cannot have colons in filenames; `inblorb` fails. Exits with guidance to use a dash instead.
- Missing `Sounds/` directory — when `--sound` is passed, verifies `.ogg` files exist at `project/Sounds/` before starting.

**Custom template support:** If `play-template.html` exists in the project root, it is passed to `setup-web.sh` via `--template`.

**Post-build validation:** After `setup-web.sh` completes, `compile.sh` runs `validate-web.sh` on the generated `web/` directory to catch common deployment issues (missing files, broken template tokens, malformed binaries). See section 6.5 for the full list of checks. Skipped when `--compile-only` is used.

**Output:**
- `<name>.ulx` — Glulx binary (always produced)
- `<name>.gblorb` — Blorb package (only with `--sound`)
- `web/play.html` — Ready-to-serve Parchment player page (unless `--compile-only`)
- `web/lib/parchment/` — Parchment library + base64-encoded game binary (unless `--compile-only`)

**Note on `--source`:** When using `--source`, the compiled output (`.ulx`, `.gblorb`) is still written to the project root (`projects/<name>/`), not alongside the source file. The `Sounds/` directory is also resolved relative to the project root, so sound assets are shared across all versions.

### 10.2 Sound Manifest (`generate-blurb.sh`)

```
bash /c/code/ifhub/tools/generate-blurb.sh \
    --ulx <path> --source <path> --sounds <path> --out <path>
```

Parses `story.ni` for `Sound of ... is the file "..."` declarations and generates a `.blurb` file for `inblorb`. Resource IDs start at 3 (1 and 2 are reserved for cover images by convention). Converts Git Bash paths to Windows paths for `inblorb.exe` compatibility.

### 10.3 Web Player Setup (`setup-web.sh`)

```
bash /c/code/ifhub/tools/web/setup-web.sh \
    --title <title> --ulx <path> --out <path>
    # or --blorb <path> instead of --ulx
```

Bootstraps a Parchment web player for any project:
1. Creates `<out>/lib/parchment/` with all 12 Parchment library files
2. Base64-encodes the game binary into a `.ulx.js` or `.gblorb.js` wrapper
3. Generates `play.html` from the template with cache-busting `?v=<timestamp>` params

Accepts `--template` for project-specific HTML templates (overrides the default `tools/web/play-template.html`).

### 10.4 Project Scaffolding (`new-project.sh`)

```
bash /c/code/ifhub/tools/new-project.sh "Game Title" game-name
```

Creates a complete project skeleton at `projects/<game-name>/`:

| File | Purpose |
|------|---------|
| `story.ni` | Starter Inform 7 source with title, scoring, and one room |
| `CLAUDE.md` | Project guide with build/test/play instructions |
| `.gitignore` | Ignores build output, IDE files, `_site/` |
| `.github/workflows/deploy-pages.yml` | GitHub Pages deployment workflow |
| `tests/project.conf` | Test configuration (pre-populated for glulxe) |
| `tests/run-tests.sh` | Thin wrapper → `tools/testing/run-tests.sh` |
| `tests/run-walkthrough.sh` | Thin wrapper → `tools/testing/run-walkthrough.sh` |
| `tests/find-seeds.sh` | Thin wrapper → `tools/testing/find-seeds.sh` |
| `tests/seeds.conf` | Golden seeds placeholder |
| `tests/<name>.regtest` | Starter RegTest with a smoke test |
| `tests/inform7/walkthrough.txt` | Starter walkthrough (single `look` command) |

The `web/` directory is created later by `compile.sh`.

### 10.5 Version Snapshots (`snapshot.sh`)

```
bash /c/code/ifhub/tools/snapshot.sh <game-name> <version>
bash /c/code/ifhub/tools/snapshot.sh <game-name> <version> --update
```

Manages frozen version snapshots in `projects/<name>/<version>/`.

**New version** (no `--update`):
- Creates the version directory
- Copies `story.ni` from project root
- Base64-encodes binary into `lib/parchment/`: prefers `.gblorb` → `.gblorb.js` (with `.ulx.js` companion), falls back to `.ulx` → `.ulx.js`
- Copies template files (player pages, `lib/`, `media/`) from the previous version, excluding binary `.js` files (`*.ulx.js`, `*.gblorb.js`, `*.z3.js`)
- Copies walkthrough data from `tests/inform7/` if present

**Update existing** (`--update`):
- **Never overwrites frozen source** — recompiles from the version's own `story.ni` via `compile.sh --source <version>/story.ni --compile-only`
- Auto-detects binary type from existing web files: if `<name>.gblorb.js` exists → compiles with `--sound`, otherwise plain `.ulx`
- Re-encodes the compiled binary into `lib/parchment/` (updates `.ulx.js` companion if present for gblorb versions)
- Copies walkthrough command files (`walkthrough.txt`, `walkthrough-guide.txt`) from `tests/inform7/` — but **not** `walkthrough_output.txt` (version-specific game transcript)
- Errors if the version has no `story.ni` (e.g., ZIL-only v0)

### 10.6 Site Assembly (`build-site.sh`)

```
bash /c/code/ifhub/tools/build-site.sh <game-name>
```

Assembles a deployable `_site/` directory by copying `web/*` then overlaying each `versions/vN/`. The assembled output matches what GitHub Actions produces for deployment. If no version snapshots exist, `_site/` is just a copy of `web/`.

### 10.7 Publishing (`publish.sh`)

```
bash /c/code/ifhub/tools/publish.sh <game-name> ["commit message"]
```

Publishes a project to GitHub Pages at `johnesco.github.io/<game-name>/`.

**First run:** Initializes a git repo, creates a GitHub repo via `gh`, pushes, and enables GitHub Pages with workflow-based deployment.

**Subsequent runs:** Stages all changes, commits, and pushes to trigger redeployment.

---

## 11. Testing Framework

IF Hub provides a shared, engine-agnostic testing framework. The framework scripts live in `tools/testing/` and `tools/regtest.py`. Projects supply configuration and test data; the framework handles execution and diagnostics.

### 11.1 Architecture

```
tools/
├── regtest.py                  ← RegTest runner (Python, used by all projects)
└── testing/
    ├── run-walkthrough.sh      ← Walkthrough runner (config-driven)
    ├── find-seeds.sh           ← RNG seed sweeper (config-driven)
    └── run-tests.sh            ← RegTest wrapper (config-driven)
```

All three scripts in `tools/testing/` require `--config PATH` pointing to a project's `tests/project.conf`. The config file is a bash-sourceable script that defines engine paths, game paths, score patterns, and diagnostic settings.

Projects provide thin wrapper scripts that pre-configure `--config` and delegate to the framework:

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
I7_HUB="/mnt/c/code/ifhub"
CONFIG="$SCRIPT_DIR/project.conf"
exec bash "$I7_HUB/tools/testing/run-walkthrough.sh" --config "$CONFIG" "$@"
```

Both invocation styles work:
```bash
# Via project wrapper
wsl -e bash tests/run-walkthrough.sh --seed 3

# Via framework directly
wsl -e bash tools/testing/run-walkthrough.sh --config projects/zork1/tests/project.conf --seed 3
```

### 11.2 Test Types

#### 11.2.1 Walkthroughs (`run-walkthrough.sh`)

Deterministic end-to-end playthroughs that pipe a command file through an interpreter and evaluate the result.

```
bash run-walkthrough.sh --config PATH [--alt] [--seed N] [--no-seed] [--diff] [--quiet] [--no-save]
```

| Flag | Purpose |
|------|---------|
| `--alt` | Use the alternate engine (e.g., dfrotz for Z-machine) |
| `--seed N` | Override the RNG seed |
| `--no-seed` | Run with true randomness (no seed) |
| `--diff` | Show unified diff against saved baseline output |
| `--quiet` | Suppress diagnostics, return only the exit code |
| `--no-save` | Don't overwrite the saved output file |

**Execution flow:**
1. Sources `project.conf` for engine/game/walkthrough paths
2. Loads golden seed from `seeds.conf` (if no `--seed` or `--no-seed`)
3. Checks binary hash against stored hash for staleness warning
4. Appends `score` command to walkthrough input (ensures final score is captured)
5. Pipes input through interpreter, captures transcript
6. Extracts score using regex patterns from config
7. Counts deaths, errors ("can't see", "can't go"), score changes
8. Checks for endgame/won patterns
9. Runs `diagnostics_extra()` hook if defined in config
10. Reports pass/fail based on `PASS_THRESHOLD`
11. Saves transcript to output file (unless `--no-save`)

**Exit codes:** 0 = pass, 1 = fail, 2 = configuration error.

#### 11.2.2 RegTest (`run-tests.sh`)

Targeted scenario testing using `regtest.py`. Each test sends a sequence of commands and asserts expected text appears in the response.

```
bash run-tests.sh --config PATH [regtest-options...] [test-pattern]
```

All arguments after `--config` are passed through to `regtest.py`:
- `-v` — verbose (show transcripts)
- `-l` — list available tests
- `--vital` — stop on first error
- `<pattern>` — run only tests matching the pattern

RegTest files (`.regtest`) define tests as `* test-name` blocks with `> command` / `expected output` pairs.

#### 11.2.3 Seed Sweeps (`find-seeds.sh`)

Brute-force search for RNG seeds where the walkthrough achieves a passing score. Used after code changes invalidate the current golden seed.

```
bash find-seeds.sh --config PATH [--alt] [--max N] [--stop|--no-stop]
```

| Flag | Purpose |
|------|---------|
| `--alt` | Sweep for the alternate engine |
| `--max N` | Search range (default: 200) |
| `--stop` | Stop on first passing seed (default) |
| `--no-stop` | Continue sweep to find all passing seeds |

**Output:** Reports best/worst/median/average scores, pass rate, and recommends a golden seed with a `seeds.conf`-formatted line including the binary hash and date.

### 11.3 Configuration Contract (`project.conf`)

Each project provides a `tests/project.conf` that is sourced by the framework. The framework sets `PROJECT_DIR` before sourcing.

#### Required Variables

| Variable | Type | Description |
|----------|------|-------------|
| `PROJECT_NAME` | string | Display name for diagnostics output |
| `PRIMARY_ENGINE_NAME` | string | Engine identifier (e.g., `"glulxe"`) |
| `PRIMARY_ENGINE_PATH` | path | Absolute path to interpreter binary |
| `PRIMARY_ENGINE_SEED_FLAG` | string | CLI flag for RNG seeding (e.g., `"--rngseed"`) |
| `PRIMARY_GAME_PATH` | path | Path to compiled game binary |
| `PRIMARY_WALKTHROUGH` | path | Path to walkthrough command file |
| `PRIMARY_OUTPUT_FILE` | path | Path to save transcript output |
| `PRIMARY_SEEDS_KEY` | string | Key for `seeds.conf` lookup (e.g., `"glulxe"`) |
| `SCORE_REGEX` | PCRE | Regex to extract final score from transcript |
| `SCORE_FALLBACK_REGEX` | PCRE | Fallback score regex (different output format) |
| `MAX_SCORE_REGEX` | PCRE | Regex to extract maximum possible score |
| `PASS_THRESHOLD` | integer | Minimum score for a passing walkthrough |
| `DEFAULT_MAX_SCORE` | integer | Displayed max when regex doesn't match |
| `DEATH_PATTERNS` | PCRE | Pipe-delimited patterns matching death messages |
| `WON_PATTERNS` | PCRE | Pipe-delimited patterns matching endgame/victory |

#### Optional Variables

| Variable | Type | Description |
|----------|------|-------------|
| `ALT_ENGINE_NAME` | string | Alternate engine identifier (e.g., `"dfrotz"`) |
| `ALT_ENGINE_PATH` | path | Path to alternate interpreter |
| `ALT_ENGINE_SEED_FLAG` | string | Alternate engine's seed flag |
| `ALT_GAME_PATH` | path | Path to alternate game binary |
| `ALT_WALKTHROUGH` | path | Path to alternate walkthrough |
| `ALT_OUTPUT_FILE` | path | Path to alternate output file |
| `ALT_SEEDS_KEY` | string | Key for alternate engine in `seeds.conf` |
| `REGTEST_FILE` | path | Path to `.regtest` file |
| `REGTEST_ENGINE` | path | Path to interpreter for RegTest |
| `REGTEST_GAME` | path | Path to game binary for RegTest |
| `SCORELESS_GAME` | boolean | Set to `true` for games without scoring; pass/fail uses `WON_PATTERNS` instead |

#### `diagnostics_extra()` Hook

Projects can define a `diagnostics_extra()` function in `project.conf` that receives the transcript file path as `$1`. The framework calls it during the diagnostics phase of `run-walkthrough.sh`. Used for project-specific analysis (e.g., Zork I tracks troll and thief encounters).

### 11.4 Golden Seed Methodology

Interactive fiction interpreters use random number generators for combat outcomes, NPC behavior, and other non-deterministic events. A **golden seed** is an RNG seed value that produces a deterministic walkthrough achieving a passing score.

#### `seeds.conf` Format

```
engine:seed:hash_prefix:date
```

| Field | Description |
|-------|-------------|
| `engine` | Matches `PRIMARY_SEEDS_KEY` or `ALT_SEEDS_KEY` in `project.conf` |
| `seed` | Integer RNG seed value |
| `hash_prefix` | First 8 characters of the game binary's SHA-256 hash |
| `date` | ISO date when the seed was discovered (`YYYY-MM-DD`) |

Example:
```
glulxe:3:a1b2c3d4:2026-02-15
dfrotz:7:e5f6a7b8:2026-02-15
```

#### Binary Hash Verification

When `run-walkthrough.sh` loads a golden seed, it computes the current binary's SHA-256 hash and compares the first 8 characters against the stored hash. A mismatch produces a warning — the game binary has changed since the seed was discovered, and the seed may no longer produce a passing walkthrough.

#### Seed Discovery Workflow

1. Code change invalidates the current golden seed (walkthrough fails)
2. Run `find-seeds.sh` to sweep seeds 1–200 (or higher with `--max`)
3. Script reports the first passing seed with a ready-to-paste `seeds.conf` line
4. Update `tests/seeds.conf` with the new seed

### 11.5 Interpreter Requirements

Tests require CLI interpreters that support piped I/O and RNG seeding. The Windows GUI interpreters (`C:\Program Files\Inform7IDE\Interpreters\`) do not support piped I/O and cannot be used for automated testing.

**Native Windows** (preferred — no WSL needed):

| Interpreter | VM | Path | Seed Flag |
|-------------|-----|------|-----------|
| `glulxe.exe` | Glulx | `tools/interpreters/glulxe.exe` | `--rngseed N` |
| `dfrotz.exe` | Z-machine | `tools/interpreters/dfrotz.exe` | `-s N` |

Built from source via MSYS2 UCRT64 (`bash tools/interpreters/build.sh`). Gitignored — each developer builds locally. The test framework auto-detects native interpreters via `project.conf` platform detection: if `$OSTYPE == "msys"` and the `.exe` exists, it is used directly.

**WSL fallback** (used when native interpreters are not available):

| Interpreter | VM | Path | Seed Flag |
|-------------|-----|------|-----------|
| `glulxe` | Glulx | `~/glulxe/glulxe` | `--rngseed N` |
| `dfrotz` | Z-machine | `~/frotz-install/usr/games/dfrotz` | `-s N` |

Both interpreters use `-q` (quiet mode) to suppress interpreter chrome and produce clean transcript output.

**WSL dependency:** If WSL is unresponsive (`wsl -e echo` hangs) and native interpreters are not built, all tests are blocked. Common fix: `wsl --shutdown` from PowerShell, then retry.

### 11.6 Per-Project Test Structure

Each project maintains a `tests/` directory with configuration, wrapper scripts, and test data. The `new-project.sh` scaffolding tool creates this structure automatically.

```
tests/
├── project.conf           ← Configuration (sourced by framework)
├── run-tests.sh           ← Wrapper → tools/testing/run-tests.sh
├── run-walkthrough.sh     ← Wrapper → tools/testing/run-walkthrough.sh
├── find-seeds.sh          ← Wrapper → tools/testing/find-seeds.sh
├── seeds.conf             ← Golden seeds (engine:seed:hash:date)
├── <name>.regtest         ← RegTest scenario files
└── inform7/               ← Test data for primary engine
    ├── walkthrough.txt            ← Walkthrough commands
    └── walkthrough_output.txt     ← Generated transcript (gitignored)
```

Projects with an alternate engine (e.g., Zork I with both Glulx and Z-machine) add a parallel data directory:

```
tests/
├── inform7/               ← Primary engine (glulxe) test data
│   ├── walkthrough.txt
│   └── walkthrough_output.txt
└── zil/                   ← Alternate engine (dfrotz) test data
    ├── walkthrough.txt
    └── walkthrough_output.txt
```

### 11.7 Adding Tests to a New Project

For projects created with `new-project.sh`, the test infrastructure is ready immediately. For manual setup:

1. **Create `tests/project.conf`** — Define all required variables (see 11.3). Use an existing config as a template.
2. **Create wrapper scripts** — Three thin scripts (`run-tests.sh`, `run-walkthrough.sh`, `find-seeds.sh`) that delegate to `tools/testing/` with `--config`.
3. **Write a walkthrough** — A plain text file with one command per line. Append `score` at the end to capture the final score.
4. **Write RegTest scenarios** — A `.regtest` file with `* test-name` blocks testing specific mechanics.
5. **Discover a golden seed** — Run `find-seeds.sh` and update `seeds.conf`.
6. **Verify** — Run all three test types and confirm pass results.
