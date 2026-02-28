# Inform 7 Central Hub

This folder is the single home for all Inform 7 authoring, compilation, and testing.
Any project under `C:\code\` that needs to generate, edit, or build Inform 7 source references this location.

## Directory Structure

```
C:\code\ifhub\
├── CLAUDE.md              ← You are here
├── reference/
│   ├── syntax-guide.md    ← Core Inform 7 syntax and structure
│   ├── text-formatting.md ← Text substitutions and output formatting
│   ├── world-model.md     ← Advanced kinds, properties, rooms/regions/backdrops, relations
│   ├── understanding.md   ← Understand command, parser tokens, and grammar
│   ├── lists.md           ← List operations, sorting, and iteration
│   ├── extensions.md      ← Extension system: including, authoring, versioning
│   ├── descriptions-adaptive-text.md ← Descriptions, quantifiers, adaptive text, dynamic change
│   ├── rulebooks.md       ← Action processing order, rules, going, persuasion, senses
│   └── activities-phrases.md ← Activities, phrase definitions, control flow, decisions
├── tools/
│   ├── build-site.sh      ← Assemble _site/ from web/ + versions/ for deployment
│   ├── snapshot.sh        ← Freeze current source into a version snapshot
│   ├── regtest.py         ← Shared RegTest runner (used by all project test suites)
│   ├── testing/           ← Generic testing framework
│   │   ├── run-walkthrough.sh  ← Walkthrough runner (config-driven)
│   │   ├── find-seeds.sh       ← RNG seed sweeper (config-driven)
│   │   └── run-tests.sh        ← RegTest wrapper (config-driven)
│   └── web/               ← Web player setup
│       ├── setup-web.sh        ← Bootstrap a Parchment web player for any project
│       ├── play-template.html  ← HTML template (__TITLE__, __STORY_FILE__ placeholders)
│       └── parchment/          ← Shared Parchment library (copy, don't symlink)
│           ├── jquery.min.js
│           ├── main.js         ← Parchment game loader
│           ├── main.css
│           ├── parchment.js    ← Parchment engine (Glulxe variant)
│           ├── parchment.css
│           ├── quixe.js        ← Quixe interpreter (JS Glulx)
│           └── glulxe.js       ← Glulxe interpreter (WASM)
├── projects/              ← Game projects
│   ├── dracula/           ← Dracula: Inform 7 Edition
│   ├── feverdream/        ← Fever Dream
│   ├── sample/            ← Sample practice game
│   └── zork1/             ← Zork I: Inform 7 Edition
│       ├── web/           ← Site-level pages (landing, map, scenarios)
│       ├── versions/      ← Frozen version snapshots (v0, v1, v2, v3)
│       └── _site/         ← Assembled deploy directory (gitignored)
└── ifhub/                 ← IF Hub web player
```

## Compiler

Inform 7 is installed system-wide via the GUI installer:

- **IDE**: `C:\Program Files\Inform7IDE\Inform.exe`
- **I7 compiler**: `C:\Program Files\Inform7IDE\Compilers\inform7.exe`
- **I6 compiler**: `C:\Program Files\Inform7IDE\Compilers\inform6.exe`
- **Internal**: `C:\Program Files\Inform7IDE\Internal`

CLI compilation — compile directly from `story.ni`, no `.inform` bundle needed:
```bash
# Step 1: Compile I7 → I6 (directly from story.ni)
"/c/Program Files/Inform7IDE/Compilers/inform7.exe" \
    -internal "/c/Program Files/Inform7IDE/Internal" \
    -source /path/to/story.ni \
    -o /path/to/story.i6 \
    -silence

# Step 2: Compile I6 → Glulx
"/c/Program Files/Inform7IDE/Compilers/inform6.exe" -w -G \
    /path/to/story.i6 \
    /path/to/output.ulx

# Step 3: Clean up intermediate file
rm /path/to/story.i6
```

Do NOT create `.inform/` IDE project bundles. The `-source` and `-o` flags let us compile without them.

## Testing

### Shared Tools
- `tools/regtest.py` — RegTest runner, used by all projects
- `tools/testing/` — Generic testing framework (walkthrough runner, seed sweeper, RegTest wrapper)

### Interpreters (WSL)
- **glulxe** (Glulx): `~/glulxe/glulxe` — for Inform 7 compiled games
- **dfrotz** (Z-machine): `~/frotz-install/usr/games/dfrotz` — for ZIL compiled games

### Testing Framework (`tools/testing/`)

The testing framework provides three reusable scripts driven by a per-project `project.conf`:

| Script | Purpose |
|---|---|
| `run-walkthrough.sh` | Runs a walkthrough through an interpreter with RNG seeding and diagnostics |
| `find-seeds.sh` | Sweeps RNG seeds to find ones where the walkthrough achieves a passing score |
| `run-tests.sh` | Wraps `regtest.py` with project-specific engine/game/test file |

All three require `--config PATH` pointing to a project's `tests/project.conf`. The config file is a bash-sourceable file that defines:

- Engine paths, seed flags, and game file paths (primary + optional alternate)
- Score extraction regex patterns and pass threshold
- Diagnostic grep patterns (deaths, won-flag)
- RegTest file, engine, and game paths
- Optional `diagnostics_extra()` function for project-specific output

#### Adding Testing to a New Project

1. Create `<name>/tests/project.conf` (see `projects/zork1/tests/project.conf` as a template)
2. Create thin wrapper scripts in `<name>/tests/` that delegate to `tools/testing/`:
   ```bash
   #!/bin/bash
   SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
   PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
   I7_ROOT="$(dirname "$PROJECT_DIR")"
   exec bash "$I7_ROOT/tools/testing/run-walkthrough.sh" --config "$SCRIPT_DIR/project.conf" "$@"
   ```
3. Add walkthrough data files, seeds.conf, and regtest files as needed

#### Generic vs Project Scripts

- **Generic** (`tools/testing/*.sh`): Use `--config` + `--alt` flags. Engine-agnostic.
- **Project wrappers** (`<name>/tests/*.sh`): Pre-configure `--config`, translate legacy flags (e.g., `--zil` → `--alt`).

Both invocation styles work:
```bash
# Via project wrapper (backward compatible)
wsl -e bash tests/run-walkthrough.sh --zil --seed 3

# Via generic framework directly
wsl -e bash tools/testing/run-walkthrough.sh --config projects/zork1/tests/project.conf --alt --seed 3
```

### Per-Project Tests
Each project has a `tests/` subfolder with project-specific config, data, and wrapper scripts.
The `project.conf` file centralizes all project-specific paths and patterns.

## Web Player (`tools/web/`)

Parchment is a browser-based Glulx interpreter that plays `.ulx` games in any modern browser. The shared library files live in `tools/web/parchment/` — each project gets its own copy.

### Adding a Web Player to a New Project

Use the setup script:
```bash
bash /c/code/ifhub/tools/web/setup-web.sh \
    --title "My Game" \
    --ulx /path/to/game.ulx \
    --out /path/to/project/web
```

This creates:
```
project/web/
├── play.html                  ← Ready-to-serve player page
└── lib/parchment/
    ├── jquery.min.js          ← jQuery
    ├── main.js                ← Parchment loader
    ├── main.css               ← Styling
    ├── parchment.js           ← Engine variant
    ├── parchment.css          ← Engine styling
    ├── quixe.js               ← Quixe interpreter  ← REQUIRED (engine)
    ├── glulxe.js              ← Glulxe interpreter  ← REQUIRED (engine)
    └── game.ulx.js            ← Base64-encoded game binary
```

To serve locally:
```bash
python -m http.server 8000 --directory project/web
# then open http://localhost:8000/play.html
```

After recompiling the game, update the web binary:
```bash
B64=$(base64 -w 0 game.ulx) && echo "processBase64Zcode('${B64}')" > web/lib/parchment/game.ulx.js
```

### `.ulx.js` Binary Wrapping Format

Parchment loads game binaries as `.ulx.js` files — JavaScript files that deliver the base64-encoded `.ulx` binary via a JSONP-style callback. The **required format** is:

```
processBase64Zcode('BASE64_ENCODED_BINARY')
```

- Single quotes around the base64 string (not double quotes)
- No `var` declaration, no semicolons — just the bare function call
- The base64 string is the raw `.ulx` file encoded with `base64 -w 0` (no line wrapping)
- The `processBase64Zcode` function is defined by Parchment's `main.js`; it decodes the base64 and boots the interpreter
- **Why not raw binary?** Parchment loads the game via a `<script src="...">` tag (JSONP pattern). This avoids CORS restrictions that would block `fetch()` on `file://` URLs. The Inform compilers output raw `.ulx` binaries and have no concept of Parchment — the wrapping step is a deployment concern, not skippable

**Converting from other formats:** Some older setups wrap the binary as `var defined_game_b64 = "...";` — this does NOT work with the standard Parchment loader used in our projects. To convert:

```bash
sed 's/^var defined_game_b64 = "/processBase64Zcode('"'"'/; s/";$/'"'"')/' old.ulx.js > new.ulx.js
```

### Troubleshooting: "Error loading engine: 404"

**Cause:** Parchment's `main.js` dynamically loads the interpreter engine (`quixe.js` or `glulxe.js`) at runtime via the `lib_path` option. If these engine files are missing from `lib/parchment/`, the load fails with a 404.

**The required 7 files** in `lib/parchment/` are:

| File | Role | What happens if missing |
|------|------|------------------------|
| `jquery.min.js` | DOM library | Page fails to initialize |
| `main.js` | Game loader | No game loads at all |
| `main.css` | Layout styling | Game works but looks broken |
| `parchment.css` | Engine styling | Game works but looks broken |
| `parchment.js` | Engine variant | Fallback to quixe, may still work |
| **`quixe.js`** | **JS Glulx interpreter** | **"Error loading engine: 404"** |
| **`glulxe.js`** | **WASM Glulx interpreter** | **"Error loading engine: 404"** |

The CSS and jQuery files produce visible errors if missing. The **engine files** (`quixe.js`, `glulxe.js`) are the sneaky ones — they're loaded asynchronously by `main.js`, so the page appears to load fine until the engine request returns 404.

**Fix:** Always copy all 7 library files. Use `setup-web.sh` which handles this automatically.

### Note on file:// Protocol

Opening `play.html` directly as a `file://` URL may also fail due to browser CORS restrictions on local JSONP requests. Always use a local HTTP server (`python -m http.server`).

## Projects

Each Inform 7 project lives under `C:\code\ifhub\projects\`.

- Each project gets its own subfolder (e.g., `projects/zork1/`, `projects/sample/`)
- Do NOT create `.inform` bundles — compile directly using `-source` and `-o` flags
- The `story.ni` in each project subfolder is the **single source of truth** for that project
- Other repos (like `C:\code\resume\writing\`) may contain **read-only snapshots** of source for display — those are NOT for compilation or editing
- When a project compiles, the output (.ulx, .ulx.js) gets deployed to the consuming repo

### Version Snapshots (opt-in)

Projects with multiple playable milestones can use a `versions/` directory to store frozen snapshots separate from the live `web/` site pages. This is opt-in — projects without `versions/` work exactly as before.

```
project/
├── web/            ← Site-level pages (landing, map, etc.)
├── versions/       ← Frozen version snapshots (opt-in)
│   ├── v0/
│   ├── v1/
│   └── ...
└── _site/          ← Assembled deploy directory (gitignored)
```

**Tools**:
- `tools/build-site.sh <game-name>` — Assembles `_site/` from `web/` + `versions/` for deployment
- `tools/snapshot.sh <game-name> <version>` — Freezes current `story.ni` + `.ulx` into a new version
- `tools/snapshot.sh <game-name> <version> --update` — Updates an existing version's source, binary, and walkthrough data

**Deployment**: GitHub Actions assembles `_site/` inline (copies `web/*` then overlays `versions/vN/`). The assembly is inlined in the workflow since game repos don't have access to `tools/build-site.sh`. The `_site/` directory is gitignored.

### Known Projects

| Project | Source | What the repo holds |
|---|---|---|
| zork1 | `projects/zork1/story.ni` | Source, tests, web site, GitHub Pages |
| dracula | `projects/dracula/story.ni` | Source, BASIC reference, web site, GitHub Pages |
| sample | `projects/sample/story.ni` | Source, tests, web player (local-only, no git) |

## Key Rules for Generating story.ni Files

### File Format
- Inform 7 source files are plain text with a `.ni` extension
- The file is traditionally named `story.ni`
- First line must be the title and author: `"Title" by "Author Name"`
- Use natural English syntax — Inform 7 reads like prose, not code

### Organization
- Use `Part`, `Chapter`, `Section` headings to organize (in that hierarchy order)
- Parts are top-level, Chapters nest inside Parts, Sections inside Chapters

### Special Characters in Text
Inform 7 does NOT allow literal special characters in `say` strings. Use substitutions:
- `[apostrophe]` for `'` inside strings
- `[quotation mark]` for `"` inside strings
- `[bracket]` and `[close bracket]` for `[` and `]`
- Never use curly quotes or smart quotes

### Text Output Formatting
See `reference/text-formatting.md` for complete list. Key ones:
- `[paragraph break]` — blank line between paragraphs
- `[line break]` — newline without blank line
- `[bold type]` / `[roman type]` — toggle bold on/off
- `[italic type]` / `[roman type]` — toggle italic on/off
- `[fixed letter spacing]` / `[variable letter spacing]` — monospace on/off

### Long Text Pattern
For long passages, break `say` statements into multiple sequential `say` calls within a `To say` phrase:
```inform7
To say my-long-text:
    say "First paragraph.[paragraph break]";
    say "Second paragraph.[paragraph break]";
    say "Third paragraph."
```
Then invoke with `say "[my-long-text]"` — note the name is hyphenated, not spaced.

### Common Patterns
See `reference/syntax-guide.md` for full reference. Quick hits:
- Kinds: `A widget is a kind of thing.`
- Properties: `A widget has text called the label.`
- Rooms: `The Kitchen is a room. "Description here."`
- Actions: `Instead of pushing the button: say "Click."`
- Custom actions: `Requesting help is an action out of world applying to nothing.`
- Understand: `Understand "help" as requesting help.`

### Testing
- Inform 7 compiles to Glulx (.ulx) or Z-machine (.z8)
- Web playable via Quixe (Glulx interpreter in JS)
- Always test: rooms are reachable, actions respond, text renders properly

## Reference from Other Projects

Other project CLAUDE.md files can reference this hub:
```markdown
For Inform 7 syntax and conventions, see C:\code\ifhub\CLAUDE.md
```
