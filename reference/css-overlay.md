# CSS Overlay System

How game projects customize the Parchment web player's appearance. Each game's `play.html` layers custom CSS on top of Parchment's base styles to create a themed experience.

## Three-Tier Architecture

### Tier 1: Parchment Base (shared library)

**Files**: `lib/parchment/parchment.css` + `lib/parchment/main.css`

Every game loads these via `<link>` tags. They provide:
- Default GlkOte window classes (`.BufferWindow`, `.GridWindow`, `.Input`)
- CSS custom property API (`--glkote-*`, `--asyncglk-*`)
- Light/dark theme toggle via `[data-theme=dark]`
- Scrollbar, reverse text, error pane styling

### Tier 2: Static CSS Overlay (per-project `play.html`)

Each game's `play.html` contains an inline `<style>` block that overrides Parchment defaults. This is the **minimum** every project should have.

**Standard CSS variables** (set in `:root`):

```css
:root {
  /* Buffer window (main game text) */
  --glkote-buffer-bg: #111;
  --glkote-buffer-fg: #d4c5a9;
  --glkote-buffer-reverse-bg: #d4c5a9;
  --glkote-buffer-reverse-fg: #111;
  --glkote-buffer-size: 16px;
  --glkote-buffer-line-height: 1.6;

  /* Grid window (status line) */
  --glkote-grid-bg: #1c1810;
  --glkote-grid-fg: #aa9966;
  --glkote-grid-reverse-bg: #aa9966;
  --glkote-grid-reverse-fg: #1c1810;
  --glkote-grid-size: 14px;

  /* Input and system */
  --glkote-input-fg: #e8d090;
  --glkote-error-border: #882020;
  --glkote-warning-border: #3333aa;

  /* Fonts */
  --glkote-prop-family: "Iowan Old Style", Palatino, Georgia, "Times New Roman", serif;
  --glkote-mono-family: "SF Mono", "Fira Code", "Cascadia Code", Consolas, "Courier New", monospace;
  --glkote-grid-mono-family: var(--glkote-mono-family);

  /* AsyncGlk UI (dialogs, file chooser) */
  --asyncglk-ui-bg: #1a1810;
  --asyncglk-ui-border: #3a2a10;
  --asyncglk-ui-fg: #d4c5a9;
  --asyncglk-ui-selected: #2a2010;
  --asyncglk-ui-textbox: #111;
}
```

**Standard structural CSS** (same across all projects):

```css
html, body { height: 100%; margin: 0; padding: 0; background: #0a0a0a; overflow: hidden; }
div#gameport { position: absolute; inset: 0; background: #111; }
.WindowFrame { background: #111; }
.GridWindow { border-bottom: 1px solid #2a2418; padding: 6px 12px; }
.BufferWindowInner { padding: 20px 40px; }
.Input { font-weight: bold; color: #e8d090; caret-color: #e8d090; }
.Style_user1 { display: none; }
.Style_header { color: #e8d8b0; }
.Style_alert { color: #cc8844; }
.Style_note { color: #aa9966; }
```

**Standard scrollbar and loading pane** (same across all projects):

```css
.BufferWindow::-webkit-scrollbar { width: 8px; }
.BufferWindow::-webkit-scrollbar-track { background: #1a1a1a; }
.BufferWindow::-webkit-scrollbar-thumb { background: #3a3020; border-radius: 4px; }
.BufferWindow::-webkit-scrollbar-thumb:hover { background: #5a4a30; }

#loadingpane {
  position: absolute; width: 100%; text-align: center; top: 35%;
  color: #887755; font-size: 1.2em; font-family: Georgia, "Times New Roman", serif;
}
@keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }
#loadingpane em { animation: pulse 1.5s ease-in-out infinite; }
```

Simple projects (sample, dracula) use only Tier 2. The CSS template comes from `tools/web/play-template.html`.

### Tier 3: Dynamic Mood System (advanced projects)

Projects with atmospheric effects (zork1 v4, feverdream) add two more layers on top of the static overlay:

#### 3a. Houdini `@property` Color Transitions

Registers CSS custom properties as `<color>` type so CSS can smoothly interpolate them:

```css
@property --mood-buffer-bg { syntax: '<color>'; inherits: true; initial-value: #111111; }
@property --mood-buffer-fg { syntax: '<color>'; inherits: true; initial-value: #d4c5a9; }
@property --mood-grid-bg   { syntax: '<color>'; inherits: true; initial-value: #1c1810; }
@property --mood-grid-fg   { syntax: '<color>'; inherits: true; initial-value: #aa9966; }
@property --mood-accent    { syntax: '<color>'; inherits: true; initial-value: #e8d090; }
@property --mood-ui-bg     { syntax: '<color>'; inherits: true; initial-value: #111111; }
@property --mood-border    { syntax: '<color>'; inherits: true; initial-value: #2a2418; }
```

The `--mood-*` variables are set on `:root` with `transition: 1.2s ease-in-out`. GlkOte variables are synced to them by JavaScript, so the entire UI transitions smoothly when the mood changes.

#### 3b. JavaScript MutationObserver Engine

An IIFE in `play.html` that:

1. **Observes room changes** — MutationObserver on `.GridWindow` detects status line updates
2. **Extracts room name** — reads first `.GridLine` text content
3. **Maps room to zone** — lookup in a `ROOM_ZONES` object (e.g., `'Forest Path': 'forest'`)
4. **Applies palette** — sets `--mood-*` and `--glkote-*` CSS variables via `document.documentElement.style.setProperty()`
5. **Watches buffer text** — second MutationObserver on `.BufferWindow` matches text patterns for event triggers
6. **Detects user input** — tracks `lastNodeText` from previous buffer mutation (Parchment WASM mode does NOT wrap input in `.Input` spans)

#### Zone Palettes

Each project defines its own zone palette map:

```javascript
var PALETTES = {
  forest:  { bufferBg:'#0a1a0e', bufferFg:'#b0d8a0', gridBg:'#0c2010', ... },
  cave:    { bufferBg:'#101114', bufferFg:'#c0c4c0', gridBg:'#14161a', ... },
  water:   { bufferBg:'#0c1018', bufferFg:'#b8c8d4', gridBg:'#101420', ... },
  // ...
};

var ROOM_ZONES = {
  'Forest Path': 'forest',
  'Kitchen': 'house',
  'Cellar': 'cave',
  // ...
};
```

#### Effect Triggers

Body class toggles activate CSS animations:

| Effect | Class | Trigger Pattern |
|--------|-------|-----------------|
| CRT terminal intro | `body.crt-intro` | Startup (removed after first input) |
| Medical monitor intro | `body.monitor-intro` | Startup (Fever Dream) |
| Tree canopy + leaves | `body.mood-tree` | Room = "Up a Tree" |
| Egg explosion | `body.egg-shake` | "taken" + "egg" in buffer |
| Sword glow | `body.sword-glow-*` | "faint blue glow" in buffer |
| Glass break | `body.glass-shake` | "glass shatters" in buffer |
| Fungus consumed | `body.fungus-ripple`, `body.state-fungus` | "It tastes of nothing" |
| Spray exposure | `body.spray-glitch`, `body.state-spray` | "Something cold and chemical" |

#### Overlay Layers

Pseudo-elements on `#gameport` provide visual effect layers:

- `#gameport::before` — dappled light, canopy glow, scanline overlays
- `#gameport::after` — vignettes, color washes, breathing effects

Dynamic DOM injection creates particles (`.leaf`, `.egg-spark`, `.glass-shard`) with per-element CSS variable parameters for randomized animation.

## Which Projects Use What

| Project | Tier 1 | Tier 2 (Static) | Tier 3 (Dynamic) |
|---------|--------|-----------------|-------------------|
| sample | Parchment base | Dark theme, standard layout | None |
| dracula | Parchment base | Dark theme, standard layout | None |
| feverdream | Parchment base | Dark theme, custom colors | Mood zones, event effects |
| zork1 v1-v3 | Parchment base | Dark theme, standard layout | None |
| zork1 v4 | Parchment base | Dark theme, larger fonts | Mood zones, CRT, tree, egg, sword |

## IF Hub Shared Player

`ifhub/play.html` version-gates Tier 3 effects. When the binary path matches `zork1-v(\d+)` with version >= 4, it adds `body.zork1-enhanced` and activates the mood system. Other games get Tier 2 static theming only.

## Adding Mood Theming to a New Project

1. Add Houdini `@property` declarations for the 7 mood variables
2. Set `:root` transitions on all `--mood-*` variables
3. Wire GlkOte variables to mood variables: `--glkote-buffer-bg: var(--mood-buffer-bg)` etc.
4. Define `PALETTES` and `ROOM_ZONES` in a `<script>` IIFE
5. Attach MutationObservers for `.GridWindow` (room changes) and `.BufferWindow` (text events)
6. Add CSS for body class toggles and `@keyframes` animations
7. Use `#gameport::before` / `::after` pseudo-elements for overlay effects

See `projects/zork1/play.html` (most complete example) or `projects/feverdream/play.html` for reference implementations.
