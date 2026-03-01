# Sound in Inform 7 Web Games

Research into browser-based sound for Inform 7 games: what exists, what works, and why we use a custom JavaScript overlay. Includes the full architecture reference and editing guide for the shared sound engine.

## Context

IF Hub games use a custom JavaScript overlay for sound — a shared engine (`sound-engine.js`) plus per-game config (`sound-config.js`) that sit outside the interpreter, watch the DOM via MutationObserver, and play HTML5 Audio. An optional `ambient-audio.js` handles room-based background music. This document records the evaluation of existing open-source alternatives and documents the current architecture.

**Date**: February 2026

## The Landscape: What Exists

### 1. Parchment (curiousdannii) — The Closest Contender

**Repo**: github.com/curiousdannii/parchment (MIT license)

The Jan 2025 release (2025.1.14) was a major architectural overhaul:
- Replaced Quixe/ZVM with **Glulxe** (WASM) + **Bocfel** via Emglken
- Uses **RemGlk-rs** (Rust port of RemGlk) as the Glk layer
- Uses **AsyncGlk** (TypeScript Glk library) for the browser-side UI

**Sound status**: The Emglken 0.7 release notes mention "sound support!" and AsyncGlk has a `glkaudio` Rust module (a Symphonia-based audio decoder compiled to WASM). However:
- The Parchment developer (Dannii) explicitly said on intfiction.org: **"Not yet, RemGlk-rs and GlkOte don't support sound yet. But I am intending to add it soon!"**
- The Inform 7 template for Parchment has **not** been updated with sound support
- The `glkaudio` module is just a **decoder** (compressed audio to WAV), not a complete Glk sound channel implementation
- No one has confirmed sound actually working end-to-end in the browser

**Assessment**: The pieces are being assembled (decoder exists, interpreter supports sound opcodes, architecture is there) but the **browser-side playback plumbing is not connected yet**. Most promising project but not usable today.

### 2. Quixe (erkyrath) — Stalled

**Repo**: github.com/erkyrath/quixe (MIT license)

- PR #3 ("Implement graphics and sound" by eevee) has been **open since 2014**
- Graphics were merged in 2015 (Quixe 2.1.0), but sound was deferred
- The GlkOte companion PR #1 has a partial Web Audio API implementation (AudioChannel, volume control, multi-sound playback) but is also **open since 2014**
- Sound notifications, Vorbis decoding, and MOD format are unimplemented
- Last activity: 2015

**Assessment**: Dead end. The PRs have been open for 10+ years. Quixe is being superseded by the Glulxe-via-WASM approach in new Parchment anyway.

### 3. Bisquixe (mathbrush/Brian Rushton) — Works But IDE-Only

- Enhanced Quixe with full Glk sound functions (channels, volume, notifications)
- Uses "Simple Multimedia Effects" Inform 7 extension
- Implements all standard Glk sound including `sound-notify` and `volume-notify` events
- **Actually works** — the game "Transparent" plays online with sound via Bisquixe

**But**:
- Requires the **Inform IDE** — activated via `Release along with the 'Bisquixe' interpreter`
- Audio files need **dual format** (`.ogg` in materials/Sounds, `.mp3` in release/Sounds)
- No evidence of CLI compilation support — designed around IDE "Release" workflow
- Replaces our entire Parchment-based pipeline
- Not clear where the source code lives (no obvious GitHub repo found)
- Single-developer project, unclear maintenance status

**Assessment**: Proves the concept works, but the IDE dependency and pipeline incompatibility make it impractical for our CLI-based workflow.

### 4. Vorple — Mature But Different Architecture

**Repo**: github.com/vorple/inform7 (MIT license)

- Complete multimedia toolkit with its own custom interpreter
- Rich sound API: `play music file`, `play sound effect`, playlists, looping, volume, status queries
- Compatible with our Inform 7 v10.1.2
- Well documented, actively maintained

**But**:
- Requires **replacing Parchment entirely** with the Vorple interpreter
- Designed around IDE "Release" workflow
- Sound is authored in `story.ni` — couples audio to game source
- Zone-based ambient crossfading still needs custom logic regardless
- Would require reworking the entire web player pipeline

**Assessment**: Best existing solution for sound-in-source, but wrong architecture for our needs. We'd be trading one custom system for a larger dependency.

## Summary Matrix

| System | Sound Works? | Open Source? | CLI Compatible? | Our Pipeline? | Active? |
|--------|-------------|-------------|----------------|--------------|---------|
| **Parchment (new)** | Not yet | MIT | Yes | Yes | Active |
| **Quixe** | No (PRs stalled 10yr) | MIT | Yes | Yes | Stalled |
| **Bisquixe** | Yes | Unknown | No (IDE-only) | No | Unclear |
| **Vorple** | Yes | MIT | No (IDE "Release") | No | Active |
| **Our custom overlay** | Yes | N/A | Yes | Yes | Ours |

## Decision

**No existing open-source project is close enough to adopt.** The closest is Parchment's new architecture, which has the decoder and interpreter pieces but the browser playback layer isn't wired up yet. The developer intends to add it "soon" but there's no timeline.

The projects that actually work today (Bisquixe, Vorple) both require the Inform IDE's "Release" workflow and would mean abandoning our CLI compilation pipeline, Parchment setup, and JSONP binary loading.

**Continue with the custom JavaScript overlay approach.** It's the only solution that:
- Works today
- Is compatible with our CLI pipeline
- Works with any interpreter (Parchment, Quixe, Glulxe)
- Doesn't couple sound to `story.ni`
- Is under our control

When Parchment eventually ships native sound support, we can evaluate migrating — but that's a future opportunity, not a current option.

## Our Sound Architecture

The custom overlay consists of independent JavaScript modules that observe the DOM and play HTML5 Audio. The shared sound engine lives at `tools/web/sound-engine.js` and is copied into each project. Each game provides its own `sound-config.js` with trigger definitions.

### sound-engine.js — Shared Sound Effects Engine

**Source of truth**: `tools/web/sound-engine.js` (copied to each project's `web/lib/`)

Supports two trigger modes:

| Mode | Trigger | Best For |
|------|---------|----------|
| **Style_user1** | `<span class="Style_user1">SFX:id</span>` in DOM | Precise, author-controlled triggers from `story.ni` |
| **Text matching** | Regex patterns against `.BufferWindow` text | Ambient/incidental sounds tied to prose |

Features:
- MutationObserver on `.BufferWindow` (game text output)
- Per-trigger cooldown to prevent spam (text triggers)
- ifhub integration (`window.SOUND_AUDIO_BASE`, `window.ifhubSfx` API)
- Standalone mute button with localStorage persistence (hidden in ifhub mode)

### sound-config.js — Per-Game Trigger Definitions

The only file that differs between games. Calls `SoundEngine.init()` with game-specific triggers:

```javascript
SoundEngine.init({
  storageKey: 'mygame-audio-muted',

  // Style_user1 triggers (precise, from story.ni via Glulx Text Effects)
  sfx: {
    glass: { src: 'audio/sfx/glass.mp3', volume: 0.4 }
  },

  // Text-matching triggers (regex against game output)
  textTriggers: [
    { id: 'bird', pattern: /chirping of a song bird/i,
      src: 'audio/sfx/bird.mp3', volume: 0.25, cooldownMs: 10000 }
  ]
});
```

#### Editing Sound Triggers

**To add a new text-matching trigger**, add an entry to the `textTriggers` array:

```javascript
{ id: 'unique-id',              // Used for cooldown tracking
  pattern: /regex pattern/i,    // Matched against game output text
  src: 'audio/sfx/file.mp3',   // Path to audio file (relative to web/)
  volume: 0.3,                  // 0.0–1.0 (scaled by master volume)
  cooldownMs: 5000 }            // Minimum ms between plays (prevents spam)
```

Tips for text triggers:
- Use case-insensitive patterns (`/i` flag) — game output capitalization varies
- Match the most specific phrase possible to avoid false positives
- Use longer cooldowns (10000–30000ms) for triggers that could fire repeatedly
- One sound plays per DOM node — if multiple patterns match the same text, only the first wins

**To add a new Style_user1 trigger**, add an entry to the `sfx` object and emit the command from `story.ni`:

```javascript
// In sound-config.js:
sfx: {
  glass: { src: 'audio/sfx/glass.mp3', volume: 0.4 },
  creak: { src: 'audio/sfx/creak.mp3', volume: 0.3 }
}
```

```inform7
[In story.ni — requires Glulx Text Effects extension:]
Include Glulx Text Effects by Emily Short.

To issue sound command (T - text):
	say "[first custom style][T][roman type]".

Instead of opening the door:
	issue sound command "SFX:creak";
	say "The door creaks open."
```

The `SFX:` prefix is required. The id after it must match a key in the `sfx` object. The CSS rule `.Style_user1 { display: none; }` must be present in `play.html` to hide the command text.

Style_user1 triggers have no cooldown — they fire every time the game emits the command. This is intentional: since the game author controls when they fire, spam prevention is the author's responsibility.

**To change volume or cooldown**, edit the values directly in `sound-config.js`. No recompilation needed (these are JavaScript-side settings). Volume values are 0.0–1.0 and are multiplied by the master volume (set by ifhub's volume slider or defaulting to 1.0).

**To remove a trigger**, delete its entry from the config. For Style_user1 triggers, also remove the `issue sound command` call from `story.ni` (optional — orphaned commands are silently ignored).

#### Audio File Guidelines

- **Format**: MP3 (universal browser support)
- **License**: CC0 recommended. [BigSoundBank](https://bigsoundbank.com) and [Freesound](https://freesound.org) are good sources
- **Location**: `project/web/audio/sfx/` for sound effects, `project/web/audio/` for ambient loops
- **Size**: Keep effects short (1–5 seconds). Ambient loops can be longer but compress well
- **Naming**: Use descriptive lowercase names matching the trigger id (e.g., `glass.mp3` for trigger id `glass`)

### ambient-audio.js — Room-Based Background Music (Optional)

Per-game module (not shared). Only Zork1 v3 uses this currently.

- **Trigger**: MutationObserver on `.GridWindow` (GlkOte status bar) detects room name changes
- **Behavior**: Maps room names to audio zones, crossfades between zones on room transitions
- **Features**: 1-second fade transitions, autoplay-block recovery, localStorage-persisted mute, ifhub API mode

### Why MutationObserver?

The overlay approach observes Parchment's DOM output rather than hooking into the interpreter. This gives us:
- **Interpreter independence**: Works with Quixe, Glulxe, or any future Parchment backend
- **Flexible coupling**: Text triggers need no source changes; Style_user1 triggers give precise control when needed
- **Hot-swappable**: Audio config can change without recompiling (for text triggers)
- **Graceful degradation**: Missing audio files don't crash the game

### Adding Sound to a New Project

1. Copy the sound engine: `bash tools/web/setup-web.sh --sound ...` (or manually copy `tools/web/sound-engine.js` to `project/web/lib/`)
2. Create `project/web/lib/sound-config.js` with trigger definitions (see template above)
3. Create audio assets in `project/web/audio/sfx/`
4. Add to `play.html`:
   - CSS: `.Style_user1 { display: none; }` (in `<style>` block)
   - Scripts: `<script src="lib/sound-engine.js"></script>` and `<script src="lib/sound-config.js"></script>` before `</body>`
5. If using Style_user1 triggers: add `Include Glulx Text Effects by Emily Short` and the `issue sound command` phrase to `story.ni`
6. For ifhub deployment: set `"sound": true` in `games.json` and add the project to `SOUND_DIRS` in `deploy.sh`

### File Locations

```
tools/web/
└── sound-engine.js              ← Source of truth for the shared engine

projects/<game>/web/
├── audio/                       ← Ambient loops (optional)
│   └── sfx/                     ← Sound effects
├── lib/
│   ├── sound-engine.js          ← Copied from tools/web/
│   ├── sound-config.js          ← Game-specific triggers (EDIT THIS)
│   └── ambient-audio.js         ← Room-based music (optional, per-game)
└── play.html                    ← Loads sound scripts after Parchment
```

## Interpreter Compatibility

Our overlay watches `.GridWindow`, `.BufferWindow`, and `.Style_user1` — CSS classes produced by the GlkOte and AsyncGlk display libraries. Both libraries produce identical class names, confirmed in source:

```javascript
// GlkOte (erkyrath/glkote, glkote.js)
if (win.type == 'grid')    typeclass = 'GridWindow';
if (win.type == 'buffer')  typeclass = 'BufferWindow';
// Style mapping: 'user1' → 'Style_user1', 'user2' → 'Style_user2'

// AsyncGlk (curiousdannii/asyncglk, windows.ts)
const window_types = { buffer: 'BufferWindow', grid: 'GridWindow', graphics: 'GraphicsWindow' }
// Style mapping: identical to GlkOte
```

Any interpreter using either display layer will work with the overlay:

| Engine / Platform | Display Layer | Compatible? | Active? |
|---|---|---|---|
| **Parchment (current)** | AsyncGlk | Yes | Active (Jan 2025 overhaul) |
| **Parchment (older / our local copy)** | GlkOte | Yes | Superseded but still deployed |
| **Quixe (standalone)** | GlkOte (bundled) | Yes | Active (June 2025 update) |
| **Bisquixe** | GlkOte (via Quixe) | Yes | Active |
| **iplayif.com** | AsyncGlk (is Parchment) | Yes | Active |
| **Borogove IDE preview** (non-Vorple) | Parchment | Yes | Active |
| **All Emglken interpreters** (Bocfel, Glulxe, Git, Hugo, Scare, TADS) | AsyncGlk | Yes | Active |
| **Vorple** | Haven (own classes) | No | Active |
| **HugoJS (standalone)** | Haven | No | Maintained |
| **Ink / inkjs** | Own HTML (choice-based) | No | Active |
| **TADS native Web UI** | Own framework | No | Maintained |

The incompatible interpreters all use their own display libraries with different CSS classes. Vorple games already have their own multimedia system, so the gap is not a practical concern.

## Style_user1 Sound Commands

Glk defines two custom text styles (`user1`, `user2`) reserved for application use. Both GlkOte and AsyncGlk render them as `<span class="Style_user1">`. This enables **explicit sound commands from game logic** — invisible to the player, detectable by the overlay.

**Status**: Implemented and deployed. Fever Dream uses Style_user1 for precise triggers. Zork1 v3 uses text-matching only. Both approaches coexist in the shared sound engine.

### How It Works

**In `story.ni`** (using the "Glulx Text Effects" extension by Emily Short):
```inform7
Include Glulx Text Effects by Emily Short.

To issue sound command (T - text):
	say "[first custom style][T][roman type]".

Instead of opening the coffin:
	issue sound command "SFX:coffin-creak";
	say "The lid groans open."
```

**In CSS** (hide from player):
```css
.Style_user1 { display: none; }
```

**In sound-config.js** (map command to audio):
```javascript
sfx: {
  'coffin-creak': { src: 'audio/sfx/coffin.mp3', volume: 0.3 }
}
```

The CSS `display: none` hides the text before it renders — no flash. The MutationObserver catches the DOM node regardless of visibility.

### What This Enables

- **Precise triggers**: Fire sounds at exact narrative moments, not via fragile regex
- **Metadata the status bar can't express**: e.g., "Frigid River but rapids are getting louder" (currently indistinguishable from calm river)
- **Volume/fade instructions**: Could extend the command format (e.g., `AMBIENT:volume:0.5`)
- **Zone overrides**: Signal a zone change without waiting for a room transition

### When to Use Each Mode

| | Text matching | Style_user1 |
|---|---|---|
| Sound logic lives in | JavaScript only | Split: triggers in story.ni, playback in JS |
| Recompile to change triggers? | No | Yes |
| Precision | Pattern-matching (can misfire) | Exact (author-controlled) |
| Volume/cooldown tuning | Edit sound-config.js (no recompile) | Edit sound-config.js (no recompile) |
| Best for | Incidental sounds, ambient triggers | Key narrative moments, unique events |

Use text matching as the default — it's simpler and doesn't require source changes. Use Style_user1 when a trigger needs to be precise (the same text appears in multiple contexts, or the trigger must fire at a specific point in a multi-paragraph response).

### Compatibility

Style_user1 has the **same compatibility as the overlay itself** — it's just another CSS class from the same GlkOte/AsyncGlk code path. Every interpreter in the "Yes" column above will render `.Style_user1`.

In non-browser interpreters (terminal), the player would see the raw command text. Guard with a conditional if needed, or accept it as a browser-only feature.

## Sources

- Parchment releases — github.com/curiousdannii/parchment/releases
- Async Parchment update — intfiction.org/t/async-parchment-update-live-on-iplayif-com-jan-2025/71463
- Parchment template "not updated with sound support yet" — intfiction.org/t/is-the-update-to-informs-parchment-able-to-do-graphics-and-sounds/75268/3
- Quixe PR #3 — github.com/erkyrath/quixe/pull/3
- GlkOte PR #1 — github.com/erkyrath/glkote/pull/1
- AsyncGlk glkaudio decoder — github.com/curiousdannii/asyncglk
- Emglken — github.com/curiousdannii/emglken
- Bisquixe — intfiction.org/t/the-bisquixe-interpreter-for-inform-7-and-inform-10-styling-new-full-sound-internal-links/66166
- Vorple Multimedia — vorple-if.com/docs/extension-multimedia.html
- Glulx interpreters with sound (2024) — intfiction.org/t/glulx-interpreters-that-support-sound-2024-edition/69761
