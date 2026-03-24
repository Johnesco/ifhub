# CSS Overlay System — Authoring Guide

How to add themed color palettes, atmospheric effects, and visual events to a Parchment game's `play.html`.

## Quick Start

Minimal example — two zones, palette transitions on room change:

1. Copy `tools/web/templates/play-mood.html` to `projects/<game>/play-template.html`
2. Add a `<script>` block before `</body>`:

```html
<script>
MoodEngine.init({
  palettes: {
    indoor: { bufferBg:'#1a1008', bufferFg:'#e8c090', gridBg:'#2a1a08', gridFg:'#c09040', accent:'#f0a030', uiBg:'#1a1008', border:'#3a2810' },
    outdoor: { bufferBg:'#0a1a0e', bufferFg:'#b0d8a0', gridBg:'#0c2010', gridFg:'#70b060', accent:'#60d040', uiBg:'#0a1a0e', border:'#1a3a18' }
  },
  roomZones: {
    'Kitchen': 'indoor',
    'Living Room': 'indoor',
    'Garden': 'outdoor',
    'Forest': 'outdoor'
  },
  fallbackZone: 'indoor'
});
</script>
```

3. Build: `python tools/compile.py <game> --force`

The engine detects `mood-engine.js` in the template and copies it automatically.

## Architecture

### Three-Tier Model

| Tier | What | Where |
|------|------|-------|
| **1. Parchment base** | Default GlkOte classes, `--glkote-*` / `--asyncglk-*` API | `lib/parchment/parchment.css` + `main.css` |
| **2. Static overlay** | Dark theme, colors, fonts, layout | Inline `<style>` in `play.html` |
| **3. Dynamic mood** | Zone palettes, room detection, effects | `mood-engine.js` + game-specific CSS/JS |

Simple projects (sample, dracula) use Tiers 1–2 only. Mood projects (zork1 v3, feverdream, seasons) add Tier 3.

### Platform Theme Override

When a user selects a platform theme in the hub's style dropdown (`app.html`), game `play.html` files receive an `ifhub:applyTheme` postMessage containing the theme's game colors and scrollbar properties. The game injects a `<style id="platform-theme-override">` element with `!important` rules that override all three tiers.

Games with CSS overlays (mood palettes, atmospheric effects) additionally add `body.platform-theme-active` to the body element, which triggers suppression CSS rules:

```css
body.platform-theme-active .crt-scanbar,
body.platform-theme-active .season-vignette,
body.platform-theme-active #gameport::before,
body.platform-theme-active #gameport::after { display: none !important; }

body.platform-theme-active .BufferLine { animation: none !important; }
```

Each game only includes rules for its own overlay elements. The suppression CSS is added to the game's existing `<style>` block.

**Key design decisions:**
- The mood engine (`MoodEngine.init()`) keeps running — it still observes room changes and updates `--mood-*` variables. These just have no visual effect while the platform override style is in place.
- When the overlay is restored via `ifhub:restoreOverlay`, the override style is removed and `body.platform-theme-active` is removed. The mood state instantly reflects the current room.
- The `overlayLabel` field in `games.json` controls which games show an overlay option in the hub's style dropdown.

**postMessage protocol:**

| Message | Direction | Fields |
|---------|-----------|--------|
| `ifhub:applyTheme` | hub → game | `type`, `game` (colors/fonts object), `scrollbar` (thumb/track/hover object) |
| `ifhub:restoreOverlay` | hub → game | `type` |

### How It Works

1. **Houdini `@property`** registers 7 `--mood-*` CSS variables as `<color>` type — enables smooth interpolation
2. `:root` wires `transition` on all 7 variables (default 1.2s)
3. GlkOte variables (`--glkote-buffer-bg`, etc.) are synced by JS, so the entire UI transitions
4. `MoodEngine` attaches a `MutationObserver` on `.GridWindow` to detect room changes from the status bar
5. Room → zone lookup triggers `applyPalette()` which sets all CSS variables
6. Optional hooks fire for game-specific effects (particles, body class toggles, etc.)

### File Layout

```
tools/web/
├── parchment/
│   ├── mood-engine.js           ← Shared mood engine library
│   └── (12 Parchment files)     ← jQuery, parchment.js, quixe.js, etc.
└── templates/
    ├── play-mood.html           ← Mood-enabled base template
    ├── play-parchment.html      ← Standard (non-mood) Parchment template
    └── ...
```

## API Reference

### `MoodEngine.init(config)`

Initialize the mood engine. Call once after DOM is ready (or in a DOMContentLoaded handler).

**Config properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `palettes` | `Object` | Yes | Zone → palette map. Each palette: `{ bufferBg, bufferFg, gridBg, gridFg, accent, uiBg, border }` |
| `roomZones` | `Object` | Yes | Room name → zone key map |
| `fallbackZone` | `string` | No | Zone for unmapped rooms. If omitted, unmapped rooms are ignored |
| `onRoomChange` | `function(roomName, zone)` | No | Called on every room change (even within same zone) |
| `onBufferText` | `function(text, prevText)` | No | Called when new text appears in the buffer window |
| `resolvePalette` | `function(zone, palettes) → palette` | No | Override palette selection (for state-dependent themes) |
| `intro` | `Object` | No | Intro mode config: `{ bodyClass, fadeClass, fadeDuration }` |

### `MoodEngine.refresh()`

Re-apply the current zone's palette. Call after state changes that affect palette selection (e.g., post-fungus override in Fever Dream).

### `MoodEngine.currentRoom` / `MoodEngine.currentZone`

Read-only. Current room name and zone key.

## Palette Design

Each palette defines 7 color properties:

| Property | Controls | Tips |
|----------|----------|------|
| `bufferBg` | Main text area background | Keep dark (#0a–#1a range) |
| `bufferFg` | Main text color | Ensure 4.5:1+ contrast with bufferBg |
| `gridBg` | Status bar background | Slightly lighter/different than bufferBg |
| `gridFg` | Status bar text | Readable against gridBg |
| `accent` | Input text, headers, highlights | Most visually distinct color |
| `uiBg` | Gameport, dialogs, frame | Match or near-match bufferBg |
| `border` | Window borders, separators | Subtle, darker than uiBg |

**Status bar note**: The mood template uses a reversed status bar — `bufferFg` as background, dark text on top. This makes the status bar pop as a bright banner. Adjust `bufferFg` knowing it also serves as the status bar background.

### Example palettes

```javascript
// Warm underground
cave: { bufferBg:'#101114', bufferFg:'#c0c4c0', gridBg:'#14161a', gridFg:'#8090a0', accent:'#7090b0', uiBg:'#101114', border:'#1e2028' }

// Cool water
water: { bufferBg:'#0c1018', bufferFg:'#b8c8d4', gridBg:'#101420', gridFg:'#6688aa', accent:'#60a0c0', uiBg:'#0c1018', border:'#162030' }

// Warm interior
house: { bufferBg:'#1a1008', bufferFg:'#e8c090', gridBg:'#2a1a08', gridFg:'#c09040', accent:'#f0a030', uiBg:'#1a1008', border:'#3a2810' }
```

## Adding Effects

### Room change hook — body class toggles

Toggle CSS effects when entering/leaving specific rooms:

```javascript
MoodEngine.init({
  palettes: { /* ... */ },
  roomZones: { /* ... */ },
  onRoomChange: function(roomName, zone) {
    document.body.classList.toggle('mood-forest', roomName === 'Forest Path');
    particleSystem.switchTo(zone);
  }
});
```

```css
body.mood-forest #gameport::before {
  background: radial-gradient(/* dappled light */);
  opacity: 1;
}
```

### Buffer text hook — event triggers

Match game output text to trigger one-shot visual effects:

```javascript
MoodEngine.init({
  palettes: { /* ... */ },
  roomZones: { /* ... */ },
  onBufferText: function(text, prevText) {
    if (/glass shatters/i.test(text)) triggerGlassBreak();
    if (/faint blue glow/i.test(text)) setSwordGlow('faint');
    // prevText is the lowercase text of the previous buffer node
    if (/^taken\.?$/i.test(text) && /\begg\b/.test(prevText)) triggerTreeSway();
  }
});
```

### Palette overrides — state-dependent themes

Change palettes based on game state (e.g., after consuming an item):

```javascript
var fungusConsumed = false;
var PALETTES_FUNGUS = { ward: { /* warmer colors */ }, /* ... */ };

MoodEngine.init({
  palettes: PALETTES,
  roomZones: ROOM_ZONES,
  resolvePalette: function(zone, palettes) {
    if (fungusConsumed && PALETTES_FUNGUS[zone]) return PALETTES_FUNGUS[zone];
    return null;  // null = use default palette
  },
  onBufferText: function(text) {
    if (/It tastes of nothing/i.test(text)) {
      fungusConsumed = true;
      // Re-apply palette with new override
      setTimeout(function() { MoodEngine.refresh(); }, 2500);
    }
  }
});
```

### Intro mode — startup effect until first input

Add a body class on startup (CRT terminal, medical monitor, etc.) that fades out after the player's first command:

```javascript
MoodEngine.init({
  palettes: { /* ... */ },
  roomZones: { /* ... */ },
  intro: {
    bodyClass: 'crt-intro',     // added on init
    fadeClass: 'crt-fade',      // replaces bodyClass on first input
    fadeDuration: 2500          // ms before fadeClass is removed
  }
});
```

```css
body.crt-intro .BufferWindow {
  color: #33ff33 !important;
  font-family: monospace;
  text-shadow: 0 0 5px rgba(51,255,51,0.5);
}
body.crt-fade .BufferWindow {
  transition: color 2s ease, text-shadow 2s ease;
}
```

The engine uses a settle-then-mutate strategy: after the initial output burst quiets (1s), the next DOM mutation is treated as user input. This works with both WASM (Emglken) and non-WASM (Quixe) engines.

### Pseudo-element overlays

`#gameport::before` and `::after` are scaffolded in the mood template with `opacity: 0`. Activate them via body class:

```css
body.mood-forest #gameport::before {
  background: /* effect */;
  opacity: 1;
}
```

### Particle injection

Create DOM elements for particles (snow, leaves, sparks) with per-element CSS variables for randomized animation:

```javascript
var flake = document.createElement('div');
flake.style.cssText =
  'position:absolute;border-radius:50%;' +
  'width:3px;height:3px;background:rgba(200,215,235,0.3);' +
  '--sf-o:0.3;animation:snowfall 12s linear infinite;';
container.appendChild(flake);
```

## Template Setup

### Creating a mood project from scratch

1. Copy `tools/web/templates/play-mood.html` → `projects/<game>/play-template.html`
2. Adjust initial colors in `@property` declarations and `:root` to match your first zone
3. Add game-specific CSS (particle `@keyframes`, body class toggles, etc.)
4. Add a `<script>` block before `</body>` that calls `MoodEngine.init({...})`
5. Build: `python tools/compile.py <game> --force`

### How templates survive rebuilds

The overlay lives in `play-template.html` (input). `compile.py` detects it and passes `--template` to `setup_web.py`, which generates `play.html` (output) with placeholders substituted. The template is never overwritten by builds.

If the template references `mood-engine.js`, `compile.py` auto-detects it and passes `--mood` to copy the library alongside the Parchment files.

### Manual setup with `setup_web.py`

```bash
python tools/web/setup_web.py \
    --title "My Game" --ulx path/to/game.ulx --out path/to/project \
    --template path/to/play-template.html --mood --force
```

The `--mood` flag:
- Copies `mood-engine.js` to `lib/parchment/`
- Uses `templates/play-mood.html` as default template (if no `--template` given)

## Project Reference

| Project | Tiers | Mood zones | Effects | Template |
|---------|-------|------------|---------|----------|
| sample | 1–2 | None | Static dark theme | Standard |
| dracula | 1–2 | None | Static dark theme | Standard |
| seasons | 1–3 | 4 (winter, spring, summer, fall) | Particle systems, vignette, text glow | `play-template.html` + `mood-engine.js` |
| zork1 v3 | 1–3 | 10 (forest, house, cave, water, ...) | CRT intro, tree canopy, egg flash, sword glow | `play-template.html` (inline engine) |
| feverdream | 1–3 | 7 (ward, treatment, basement, ...) | Monitor intro, glass break, fungus, spray | `play-template.html` (inline engine) |

Seasons uses the shared `mood-engine.js`. Zork1 and feverdream still use inline mood engines (future migration).

## Platform Theme Override

When a platform theme is selected in the hub's style dropdown, `app.html` directly injects `<style id="ifhub-theme-override">` into all same-origin iframes (game, source, walkthrough) via `contentDocument`. Engine-specific CSS builders (`buildParchmentCSS`, `buildInkCSS`, `buildBasicCSS`, `buildChromeCSS`) target the correct selectors for each page type.

Games with `overlayLabel` in `games.json` are exempt from direct injection — they receive `ifhub:applyTheme` / `ifhub:restoreOverlay` via postMessage so their own listener can coordinate `body.platform-theme-active` to suppress visual effects while the mood engine continues running. Non-overlay game `play.html` files do not need a theme listener script.

## Troubleshooting

### GlkOte timing

The engine polls for `.GridWindow` every 500ms because GlkOte creates it dynamically after the game starts. If you see no palette changes, check that the game actually creates a status bar (grid window).

### WASM input detection

Parchment's WASM engine (Emglken/Glulxe) does NOT wrap user input in `.Input` spans. The intro mode uses a settle-then-mutate strategy: after initial output quiets for 1s, the next buffer mutation is treated as user input. If the intro doesn't end, increase the settle timeout.

### `!important` overrides

GlkOte sets inline `background-color` and `color` styles directly on window elements. The mood template uses `!important` on `.GridWindow`, `.BufferWindow`, and `.WindowFrame` to override these. If your palette colors aren't showing, check that `!important` is present.

### Transition duration

The mood template defaults to 1.2s transitions. Seasons uses 2s for a slower, more ambient feel. Adjust in both `:root` `transition` and structural CSS (`.GridWindow`, `.BufferWindow`, `div#gameport`).

### Cache-busting

`setup_web.py` appends `?v=<timestamp>` to `.js` and `.css` references in `play.html`. This includes `mood-engine.js`. If you update the engine and don't see changes, rebuild with `--force`.
