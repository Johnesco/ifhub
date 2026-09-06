# IF Hub — Functional Specification

> What the hub site does today. How games get here is in `docs/publishing.md`; how work happens is in `docs/sdlc.md`.

## 1. What IF Hub is

IF Hub is a static site at https://johnesco.github.io/ifhub/ that shows interactive fiction games next to their source code and walkthroughs. It is receive-only: games are built and tested in their engine workspaces and published to their own GitHub Pages repos (`johnesco.github.io/<game>/`); the hub lists and displays them.

- Pure static site: no server, accounts or tracking. Deployed by GitHub Actions from `site/` on every push to `master` that touches it.
- Nothing from a game is copied into the hub. Every game asset loads from the game's own URL. All repos live under `johnesco.github.io`, so iframes, `fetch()` and `postMessage` are same-origin.
- The data files (`games.json`, `cards.json`) are generated from each game's `ifhub.conf`; nothing in them is edited by hand.

## 2. Pages

| Page | File | Purpose |
|---|---|---|
| Landing page | `index.html` | catalog of game cards, collection picker, theme picker |
| Player | `app.html` | game, source, walkthrough and tests in a resizable split view |
| Walkthrough viewer | `walkthrough.html?game=<id>` | renders a game's walkthrough files; used by the player pane and standalone |

Shared scripts: `themes.js` (themes, §5) and `hub.js` (loading `games.json`/`cards.json` plus `hubs.json`, resolving `?hub=`, filtering; a failed load shows a message instead of an empty page). The player's code is in `app.js` and `app.css`.

### 2.1 Landing page

- Fetches `cards.json` and `hubs.json` and renders one card per entry, in file order. A card shows the title, the subtitle (the game's author line), the description, and a version picker for versioned groups.
- Card actions: Play (the game's own `playUrl`), Source and Walkthrough (hub views in the player). The fullscreen checkbox applies to Play only: it opens the game's own page instead of the player.
- Collections: a dropdown built from `hubs.json` filters the cards by engine or tag. The active collection is in the URL as `?hub=<id>` (bare path for "all"). Switching uses `history.pushState` and re-renders in place; back and forward restore it; a collection other than "all" replaces the page title and subtitle with its own.
- Theme picker (§5.1), persisted in `localStorage` under `ifhub-theme`.
- Static sections: "How It Works" and "Thank You" credits.

### 2.2 Player (`app.html`)

URL parameters: `?game=<id>` (default: first game), `?hub=<id>` (restrict the game selector to a collection), `?view=<panes>` (for example `game+source`, `walkthrough`), `?theme=<id>`.

Toolbar: Library link (keeps the collection filter), Collection selector (re-filters the game selector in place with `history.replaceState`), Game selector, Style dropdown (§5.2), sound controls (§6, shown only when the game reports sound), and the view toggles Game, Source, Walk, Tests.

View switching: Game toggles independently. Source, Walk and Tests are mutually exclusive, and clicking the active one collapses the side pane. The combination is written to `?view=`. Tests appears only for games with `testsUrl`.

Layout: CSS grid with the game pane, a 5px resize handle (mouse and touch) and the side pane; each pane at least 200px. Below 1024px the source sidebar is hidden; below 800px the layout is a single column.

Panes:

- Game: iframe of `playUrl`.
- Source: §4.
- Walkthrough: iframe of `walkthrough.html?game=<id>` when the game has `walkthroughUrl`, otherwise "Not available".
- Tests: iframe of `testsUrl`, whatever report page the workspace produced (Inform 7 games ship an ifPlayer report).

Ctrl+F or Cmd+F focuses the source search while the source pane is visible.

### 2.3 Walkthrough viewer (`walkthrough.html`)

Looks `?game=<id>` up in `games.json`, takes the game folder from `walkthroughUrl`, and fetches `walkthrough.txt`, `walkthrough_output.txt` and `walkthrough-guide.txt` from it. Three views: Commands (with guide sections and a navigation sidebar when a guide exists), Game Text (the transcript), and Replay (typed playback at 0.5x to 4x; Space, arrow keys and 1 to 4 control it). Game Text and Replay are disabled without a transcript; a game that ships only the guide still gets Commands. Download links for the commands and the guide. Replay speed is stored per game under `ifhub-wt-<id>-replay-speed`.

### 2.4 Per-game pages (served in place)

A game repo publishes `play.html` (its own player), `index.html` (a landing page the hub writes once, linking Play plus the hub's Source and Walkthrough views), its raw source file, and its walkthrough text files. Player pages include `theme-listener.js` so hub themes apply (§5.3). The full contract is in `docs/publishing.md`.

## 3. Data

### 3.1 `games.json`

One entry per game, generated from its `ifhub.conf`. URL fields are emitted only when the file exists at build time.

| Field | Meaning |
|---|---|
| `id` | the game folder name, e.g. `zork1-v3` |
| `title`, `author`, `description` | from the conf; `author` is the card subtitle |
| `engine`, `tags` | used by collections and by the source highlighter |
| `playUrl` | `/<game>/play.html`, always present |
| `sourceUrl`, `sourceLabel`, `sourceBrowser` | the raw source file, or the game's own `source.html` when `sourceBrowser` is true (only when the conf says `sourceBrowser = yes`); the label shows in the pane toolbar |
| `walkthroughUrl` | `/<game>/walkthrough.txt`, or `walkthrough-guide.txt` when only the guide exists; its folder is where the viewer reads from |
| `testsUrl` | `/<game>/tests.html` when the file exists |
| `landingUrl` | `/<game>/` when the game has an `index.html` |
| `sound` | `blorb` for games with embedded audio |
| `overlayLabel` | the name of the game's own CSS overlay (§5.2) |
| `versionOf`, `versionLabel`, `versionOrder`, `versionPrimary`, `versionPrimaryLabel` | version-group data (§3.2) |

### 3.2 `cards.json`

Generated from `games.json`: one card per game or version group. Fields: `id`, `base`, `title`, `meta` (the author), `description`, `playUrl`, `landingUrl`, `engine`, `tags`, and when present `sound`, `sourceUrl`, `walkthroughUrl`, `testsUrl`. A group card adds `primaryLabel` and a `versions` list (`id`, `label`, `playUrl`, `landingUrl`, plus the optional URL fields). Membership comes from `versionOf` and `versionPrimary`, or from an id of the form `<base>-vN` when the base has a primary.

### 3.3 `hubs.json`

The list of collections: `id`, `title`, `description`, and `filter`, which is `{ "engine": ... }`, `{ "tag": ... }`, both (AND), or `null` for everything.

## 4. Source viewer

- Fetches `sourceUrl` (cached per game), normalises line endings, and renders a numbered table with syntax highlighting.
- Highlighters by engine: Inform 7 (the default: headings, strings, text substitutions, comments, keywords, tables), Rez (`@element` blocks, comments, strings), Ink (knots and stitches, choices, diverts, tags, logic lines), BASIC for wwwbasic, applesoft, bwbasic and qbjc (line numbers, keywords, strings, REM comments).
- Navigation sidebar (220px, hidden below 1024px): Inform 7 Volume/Book/Part/Chapter/Section headings, Rez elements, Ink knots and stitches, BASIC REM lines. Clicking scrolls to the line and marks it active.
- Search: Ctrl+F, at least two characters, 200ms debounce, highlighted hits with a current-hit marker; Enter and Shift+Enter step through, Escape clears. It walks text nodes, so highlighting is preserved.
- Browser mode: when `sourceBrowser` is true the pane iframes the game's own `source.html` instead. Used by zork1-v0 (multi-file ZIL browser) and dracula-v0 (annotated BASIC).

## 5. Themes

### 5.1 Platform themes

Fifteen themes live in `themes.js`: classic (default), dos, apple2, c64, amiga, mac, atarist, cpm, atari8, trs80, sepia, midnight, forest, lavender, solarized. Each defines `chrome` (hub UI colours and font), `game` (colours, fonts and sizes pushed into game pages) and `scrollbar`. The choice persists in `localStorage` under `ifhub-theme`; pages apply the chrome by setting CSS custom properties on the root element. Retro fonts load from Google Fonts on demand.

### 5.2 Style dropdown and overlays

In the player the Style dropdown lists the platform themes. For a game with `overlayLabel` its own overlay is the first and default option, then a separator, then the themes; the per-game choice is stored under `ifhub-style-<id>`. Choosing a platform theme injects a style block into the same-origin game, source-browser, walkthrough and tests iframes, using engine-specific CSS builders (Parchment, Ink, BASIC, Rez, test report), and posts `ifhub:applyTheme` to the game. Choosing the overlay posts `ifhub:restoreOverlay`.

### 5.3 Message protocol

| Message | Direction | Fields | Purpose |
|---|---|---|---|
| `ifhub:applyTheme` | hub → game | `game`, `scrollbar` | apply the theme colours; the game adds `body.platform-theme-active` and hides its own effects |
| `ifhub:restoreOverlay` | hub → game | | remove the theme and restore the game's own overlay |
| `ifhub:soundReady` | game → hub | | the game has audio; show the sound controls |
| `ifhub:setMute` | hub → game | `muted` | |
| `ifhub:setVolume` | hub → game | `volume` (0 to 1) | |

## 6. Sound controls

Games with embedded blorb audio play it through their own Parchment copy. Once a game posts `ifhub:soundReady`, the player shows a mute button and a 0 to 100 volume slider, pushes the stored state to the game, and persists it under `ifhub-audio-muted` and `ifhub-audio-volume`.

## 7. Hosting and local development

- The hub deploys to GitHub Pages from `site/` through the Actions workflow on every push to `master` that touches `site/**`. Games deploy from their own repos.
- Locally, `python tools/serve.py` serves `site/` at `/ifhub/` and every game folder at `/<game>/` on port 8892; the `hub-site` launch config runs it. Opening the files over `file://` does not work.

## 8. Building and publishing

The hub does not build or test games. Each engine workspace has a `tools/build.py`; the hub's `tools/ship.py` verifies the folder, writes the landing page, sets `hub = yes`, regenerates the data files, publishes the game repo and pushes the hub. See `docs/publishing.md`.
