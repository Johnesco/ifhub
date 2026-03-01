# Build Pipeline Guide

End-to-end walkthrough: from writing Inform 7 source to playing in a browser with sound.

## Overview

```
story.ni ──► inform7.exe ──► story.i6 ──► inform6.exe ──► game.ulx
                                                              │
                                                      base64 -w 0
                                                              │
                                                        game.ulx.js
                                                              │
                                              ┌───────────────┤
                                              ▼               ▼
                                     Project web/       ifhub deploy
                                     (local play)       (GitHub Pages)
```

## Step 1: Write the Source

Create `story.ni` in your project directory:

```
projects/<game>/story.ni
```

First line must be the title and author:

```inform7
"My Game" by "Author Name"
```

See `reference/syntax-guide.md` for Inform 7 syntax. Key rules:

- Use `[apostrophe]`, `[quotation mark]`, `[bracket]` instead of literal special characters in text
- Organize with `Part`, `Chapter`, `Section` headings
- Do NOT create `.inform` bundles — we compile directly from `.ni` files

## Step 2: Compile

Two-step CLI compilation. No IDE needed.

### Step 2a: Inform 7 → Inform 6

```bash
"/c/Program Files/Inform7IDE/Compilers/inform7.exe" \
    -internal "/c/Program Files/Inform7IDE/Internal" \
    -source projects/<game>/story.ni \
    -o projects/<game>/story.i6 \
    -silence
```

Exit code 0 = success. Any errors print to stderr with line numbers.

### Step 2b: Inform 6 → Glulx

```bash
"/c/Program Files/Inform7IDE/Compilers/inform6.exe" -w -G \
    projects/<game>/story.i6 \
    projects/<game>/<game>.ulx
```

Flags: `-w` suppresses warnings, `-G` targets Glulx format (.ulx).

### Step 2c: Clean Up

```bash
rm projects/<game>/story.i6
```

The `.i6` file is an intermediate artifact. Only `story.ni` (source) and `<game>.ulx` (binary) matter.

### One-Liner

```bash
cd projects/<game> && \
"/c/Program Files/Inform7IDE/Compilers/inform7.exe" \
    -internal "/c/Program Files/Inform7IDE/Internal" \
    -source story.ni -o story.i6 -silence && \
"/c/Program Files/Inform7IDE/Compilers/inform6.exe" -w -G story.i6 <game>.ulx && \
rm story.i6
```

## Step 3: Set Up the Web Player

Parchment is a browser-based Glulx interpreter. Each project gets a `web/` directory with Parchment libraries and the encoded game binary.

### Option A: Use the Setup Script

```bash
bash tools/web/setup-web.sh \
    --title "My Game" \
    --ulx projects/<game>/<game>.ulx \
    --out projects/<game>/web
```

This creates:

```
projects/<game>/web/
├── play.html                  ← Ready-to-serve player page
└── lib/parchment/
    ├── jquery.min.js
    ├── main.js
    ├── main.css
    ├── parchment.js
    ├── parchment.css
    ├── quixe.js               ← JS Glulx interpreter
    ├── glulxe.js              ← WASM Glulx interpreter
    └── <game>.ulx.js          ← Base64-encoded game binary
```

All 7 Parchment library files are required. Missing `quixe.js` or `glulxe.js` causes "Error loading engine: 404".

### Option B: Manual Setup

If the web directory already exists, just update the binary:

```bash
B64=$(base64 -w 0 projects/<game>/<game>.ulx) && \
echo "processBase64Zcode('${B64}')" > projects/<game>/web/lib/parchment/<game>.ulx.js
```

The `.ulx.js` format is a JSONP callback — single quotes, no semicolons:

```
processBase64Zcode('BASE64_ENCODED_BINARY')
```

## Step 4: Test Locally

```bash
python -m http.server 8000 --directory projects/<game>/web
# Open http://localhost:8000/play.html
```

Do NOT open `play.html` as a `file://` URL — browsers block the JSONP script loading due to CORS.

## Step 5: Add Sound (Optional)

Sound uses a JavaScript overlay that watches the game's DOM output. Two trigger modes:

| Mode | How It Works | Recompile Needed? |
|------|-------------|-------------------|
| **Text matching** | Regex patterns matched against game output | No |
| **Style_user1** | Hidden commands emitted from `story.ni` | Yes |

### 5a: Copy the Sound Engine

```bash
bash tools/web/setup-web.sh --sound ...
# Or manually:
cp tools/web/sound-engine.js projects/<game>/web/lib/
```

### 5b: Create Sound Config

Create `projects/<game>/web/lib/sound-config.js`:

```javascript
SoundEngine.init({
  storageKey: '<game>-audio-muted',

  // Style_user1 triggers (precise, from story.ni)
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

### 5c: Add Audio Files

```
projects/<game>/web/audio/
└── sfx/
    ├── glass.mp3
    └── bird.mp3
```

Format: MP3. Keep effects short (1-5 seconds). CC0 sources: [BigSoundBank](https://bigsoundbank.com), [Freesound](https://freesound.org).

### 5d: Update play.html

Add to the `<style>` block:

```css
.Style_user1 { display: none; }
```

Add before `</body>`:

```html
<script src="lib/sound-engine.js"></script>
<script src="lib/sound-config.js"></script>
```

### 5e: Add Style_user1 Triggers to story.ni (If Using)

```inform7
Include Glulx Text Effects by Emily Short.

To issue sound command (T - text):
	say "[first custom style][T][roman type]".
```

Then emit commands at the desired moments:

```inform7
Instead of opening the coffin:
	issue sound command "SFX:creak";
	say "The lid groans open."
```

The `SFX:` prefix is required. The id after it must match a key in the `sfx` object in `sound-config.js`. After adding Style_user1 triggers, recompile (Step 2) and update the web binary (Step 3b).

Text-matching triggers require no source changes and no recompilation.

### 5f: Test Sound Locally

```bash
python -m http.server 8000 --directory projects/<game>/web
```

Play through to the trigger point. Verify:
- Sound plays at the right moment
- Style_user1 text is invisible (no "SFX:..." visible in game output)
- Mute button appears and persists state

## Step 6: Deploy to IF Hub

IF Hub serves all games through a unified browser interface at GitHub Pages.

### 6a: Register the Game

Add an entry to `ifhub/games.json`:

```json
{
  "id": "<game>",
  "title": "My Game",
  "sourceLabel": "<game>.ni",
  "source": "games/<game>/story.ni",
  "binary": "games/<game>/<game>.ulx.js",
  "sound": true,
  "card": {
    "title": "My Game",
    "meta": "A Subtitle",
    "description": "Landing page description."
  }
}
```

Set `"sound": true` to enable sound controls in the hub UI. Omit the field or set `false` for games without sound.

### 6b: Add to deploy.sh

Add the game to the `GAMES` array:

```bash
"<game>  projects/<game>/story.ni  projects/<game>/web/lib/parchment/<game>.ulx.js"
```

If the game has walkthroughs, add to `WALKTHROUGH_DIRS`:

```bash
[<game>]="projects/<game>/web"
```

If the game has sound, add to `SOUND_DIRS`:

```bash
[<game>]="projects/<game>/web"
```

### 6c: Run the Deploy

```bash
cd ifhub
bash deploy.sh
```

This copies source, binary, walkthroughs, and sound assets from the project into `ifhub/games/<game>/`, then generates standalone `index.html` play pages.

### 6d: Test the Hub Locally

```bash
python -m http.server 8000 --directory ifhub
# Open http://localhost:8000/
```

Verify:
- Game appears in the dropdown on `app.html`
- Game loads and plays correctly
- Sound controls appear (if sound-enabled)
- Standalone page works at `games/<game>/index.html`

### 6e: Push to Deploy

```bash
cd ifhub
git add games/<game>/ games.json deploy.sh
git commit -m "Add <game> to IF Hub"
git push
```

GitHub Pages deploys automatically from the push.

## Quick Reference: Common Operations

### Recompile and Update Web After Editing story.ni

```bash
cd projects/<game>

# Compile
"/c/Program Files/Inform7IDE/Compilers/inform7.exe" \
    -internal "/c/Program Files/Inform7IDE/Internal" \
    -source story.ni -o story.i6 -silence && \
"/c/Program Files/Inform7IDE/Compilers/inform6.exe" -w -G story.i6 <game>.ulx && \
rm story.i6

# Update web binary
B64=$(base64 -w 0 <game>.ulx) && \
echo "processBase64Zcode('${B64}')" > web/lib/parchment/<game>.ulx.js
```

### Update ifhub After Recompiling

```bash
cd ifhub && bash deploy.sh
```

### Add a Text-Matching Sound Trigger (No Recompile)

Edit `projects/<game>/web/lib/sound-config.js` — add to `textTriggers`:

```javascript
{ id: 'door', pattern: /door creaks/i,
  src: 'audio/sfx/door.mp3', volume: 0.3, cooldownMs: 5000 }
```

Drop the audio file in `web/audio/sfx/`. Refresh the browser.

### Add a Style_user1 Sound Trigger (Requires Recompile)

1. Add to `sfx` in `sound-config.js`:
   ```javascript
   creak: { src: 'audio/sfx/creak.mp3', volume: 0.3 }
   ```

2. Add to `story.ni`:
   ```inform7
   issue sound command "SFX:creak";
   ```

3. Drop the audio file in `web/audio/sfx/`
4. Recompile and update web binary (see above)

### Change Volume or Cooldown (No Recompile)

Edit values directly in `sound-config.js`. Volume is 0.0-1.0, multiplied by master volume.

## File Locations

| File | Location | Purpose |
|------|----------|---------|
| I7 compiler | `/c/Program Files/Inform7IDE/Compilers/inform7.exe` | Compiles .ni → .i6 |
| I6 compiler | `/c/Program Files/Inform7IDE/Compilers/inform6.exe` | Compiles .i6 → .ulx |
| Internal | `/c/Program Files/Inform7IDE/Internal` | Extensions, templates |
| Setup script | `tools/web/setup-web.sh` | Bootstrap web player |
| Sound engine (source of truth) | `tools/web/sound-engine.js` | Shared, copied to projects |
| Play template (projects) | `tools/web/play-template.html` | Template for project play pages |
| Play template (ifhub) | `ifhub/play-template.html` | Template for ifhub standalone pages |
| Deploy script | `ifhub/deploy.sh` | Copies assets into ifhub/games/ |
| Game registry | `ifhub/games.json` | Game metadata for hub UI |
| Sound editing guide | `reference/sound.md` | Trigger modes, architecture, editing |

## Related Documentation

- `CLAUDE.md` — Project conventions, compiler details, Parchment troubleshooting
- `reference/sound.md` — Sound architecture, trigger editing guide, decision record
- `ifhub/README.md` — IF Hub deployment details, games.json schema, sound wiring
