# Sound in Inform 7 Web Games

Research into browser-based sound for Inform 7 games: what exists, what works, and why we use a custom JavaScript overlay.

## Context

Zork1 v3 uses a custom JavaScript overlay for sound — two JS files (`ambient-audio.js`, `sound-effects.js`) that sit outside the interpreter, watch the DOM via MutationObserver, and play HTML5 Audio. This document records the evaluation of existing open-source alternatives.

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

The custom overlay consists of two independent JavaScript modules that observe the DOM and play HTML5 Audio:

### ambient-audio.js — Room-Based Background Music

- **Trigger**: MutationObserver on `.GridWindow` (GlkOte status bar) detects room name changes
- **Behavior**: Maps room names to audio zones, crossfades between zones on room transitions
- **Features**: 1-second fade transitions, autoplay-block recovery, localStorage-persisted mute, ifhub API mode

### sound-effects.js — Text-Triggered One-Shot Sounds

- **Trigger**: MutationObserver on `.BufferWindow` (game text output) matches regex patterns
- **Behavior**: Plays one-shot audio when game text matches configured triggers
- **Features**: Per-trigger cooldown to prevent spam, shares mute state with ambient-audio

### Why MutationObserver?

The overlay approach observes Parchment's DOM output rather than hooking into the interpreter. This gives us:
- **Interpreter independence**: Works with Quixe, Glulxe, or any future Parchment backend
- **No source coupling**: Sound config lives in JavaScript, not `story.ni`
- **Hot-swappable**: Audio zones can change per version without recompiling
- **Graceful degradation**: Missing audio files don't crash the game

### Adding Sound to a New Project

1. Create audio assets in `project/web/audio/` (ambient) and `project/web/audio/sfx/` (effects)
2. Copy `ambient-audio.js` and `sound-effects.js` to `project/web/lib/`
3. Customize the zone map (room-to-audio assignments) and trigger list for the new game
4. Add `<script>` tags after Parchment in `play.html`
5. For ifhub deployment: set `"sound": true` in `games.json` and add the project to `SOUND_DIRS` in `deploy.sh`

### File Locations (Zork1 Reference Implementation)

```
projects/zork1/web/
├── audio/                    ← Background tracks (9 zones, CC0 licensed)
│   └── sfx/                  ← Sound effects (16 triggers)
├── lib/
│   ├── ambient-audio.js      ← Room-based crossfading music
│   └── sound-effects.js      ← Text-triggered one-shot effects
└── play.html                 ← Loads sound scripts after Parchment
```

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
