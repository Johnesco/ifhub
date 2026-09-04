# Multi-Version Games — Repo Model & Workflow

Canonical reference for projects that ship multiple playable versions (e.g. zork1, dracula). Every multi-version project's CLAUDE.md should link here instead of duplicating these instructions.

## Concept

Some projects keep **multiple playable versions** as a portfolio trail — each version a milestone showing design choices, testing methodology, and the evolution from a faithful port toward something new. Versions appear on the IF Hub landing page newest-first, with the original (v0) at the bottom.

A multi-version project has:
- **Current** — the active working copy. Lives in the main repo (e.g. `Johnesco/zork1`). Always in progress; gets frozen into the next numbered version when ready.
- **v0** — the untouchable original (often a different engine: ZIL, BASIC, etc.). Lives in its own repo (e.g. `Johnesco/zork1-v0`).
- **v1, v2, v3, …** — frozen published snapshots. Each lives in its own repo (e.g. `Johnesco/zork1-v1`).

## Repo Layout (one repo per version)

```
Johnesco/<game>          ← Current (the working copy, no version number)
Johnesco/<game>-v0       ← Original engine (read-only)
Johnesco/<game>-v1       ← Frozen: faithful port
Johnesco/<game>-v2       ← Frozen: bug fixes / enhancements
Johnesco/<game>-v3       ← Frozen: multimedia / further enhancements
```

Each repo deploys independently to its own GitHub Pages site. The IF Hub registry (`site/games.json`, generated from each game's `ifhub.conf`) iframes them all into one browsable hub.

**Local clones** mirror the same naming:
```
/c/code/text-games/<engine>/<game>/        ← Current
/c/code/text-games/<engine>/<game>-v1/     ← Per-version repos
/c/code/text-games/<engine>/<game>-v2/
…
```

(v0 may live in a different engine workspace — e.g. `wwwbasic/dracula-v0/` or `zmachine/zork1-v0/` — depending on the original platform.)

## Version Philosophy

Each project defines its own promotion rules; the common pattern is:

| Version | Editing policy |
|---|---|
| **v0** | **Never touch.** The original, exactly as released. Fixes are only ever applied in v1+. |
| **v1** | **Bugs only.** A faithful 1:1 translation. Original-engine bugs that survive translation may be left alone or fixed depending on the project's stance. No enhancements, no quality-of-life. |
| **v2** | **Any fixes or enhancements** that change text or behavior. First version where game design intentionally diverges from the original. |
| **v3** | **Multimedia + sparse text guidance.** Sound, atmosphere, additional player guidance written to match the original's terse style. |
| **Current** | The default work target. All new development. Will become the next numbered version when frozen. |

Project-specific deviations belong in that project's CLAUDE.md.

## Where to Edit What

**Default work target is Current.** Unless explicitly told to patch a frozen version, all changes go into `<game>/story.ni` (or equivalent) in the main repo.

**Patching a frozen version** (rare — e.g. discovered bug, label fix):
1. Edit `<game>-vN/story.ni` directly in the per-version repo
2. Recompile from that source (each repo is self-contained)
3. Run that version's walkthrough/tests with its golden seed
4. Commit, push — GitHub Pages redeploys
5. **Propagate upward.** If a fix lands in vN, apply the same change to v(N+1), v(N+2), …, and Current. Never propagate downward.

The cascade rule: *each version is a strict superset of the one below it.* v2 contains everything in v1 plus its own changes; v3 contains everything in v2 plus its own; and so on.

## Per-Version Repo Structure

Every version repo is **self-contained** — it can build and deploy on its own:

```
<game>-vN/
├── ifhub.conf            ← Engine, title, binary, tags, version metadata
├── story.ni              ← Frozen source for this version
├── <game>-vN.ulx         ← Compiled binary (or .gblorb for sound versions)
├── play.html             ← Parchment player
├── source.html           ← Source browser
├── walkthrough.html      ← Walkthrough viewer
├── walkthrough.txt       ← Raw commands
├── walkthrough-guide.txt ← Annotated guide
├── walkthrough_output.txt ← Generated transcript
├── lib/parchment/
│   ├── ...engine files
│   └── <game>-vN.ulx.js  ← Base64-encoded binary for the web player
└── tests/
    └── project.conf      ← Test runner config (golden seed lives here)
```

Each version repo has its own **golden seed** in `tests/seeds.conf` — different versions may need different seeds because their RNG paths diverge. Always check that file when running walkthroughs.

## Building and Testing

Build each version in the Inform 7 workspace by folder name:

```bash
# Current
python C:/code/text-games/i7/tools/build.py <game>

# Frozen versions
python C:/code/text-games/i7/tools/build.py <game>-v2
python C:/code/text-games/i7/tools/build.py <game>-v2 --no-test
```

Walkthroughs are deterministic per version; the build picks up each version's golden seed from its own `tests/seeds.conf`, and you can run one by hand:

```bash
cd C:/code/text-games/i7/<game>-v2
python ../tools/run_walkthrough.py --config tests/project.conf --seed <golden-seed>
```

## Hub Registration

Each version is its own game folder with its own `ifhub.conf`. The version fields group them on the hub:

```ini
# <game>/ifhub.conf  (Current)
versionPrimary = yes
versionPrimaryLabel = Current

# <game>-v1/ifhub.conf
versionOf = <game>
versionLabel = v1 — The Port
versionOrder = 1        # optional; defaults to the number in the folder name
```

`versionOf` groups the entries into one card; `versionPrimary = yes` marks the entry shown at the top of the group. Ship each version with `python C:/code/ifhub/tools/ship.py <game>-vN`; `build_games.py` (run by ship) collapses the group into `site/cards.json`. The group's landing page is generated by `python C:/code/ifhub/tools/build_landing.py <game>` from the primary folder's `landing.json`.

## Deploy

Each repo deploys to its own GitHub Pages site on `git push`:

- `johnesco.github.io/<game>/` — Current
- `johnesco.github.io/<game>-vN/` — Frozen version N

The IF Hub iframes those URLs from `site/games.json`. Pushing a version repo automatically updates that version on the hub once GH Pages finishes (≈30s–2min).

## Common Mistakes

- **Editing a frozen version when you meant to edit Current.** Default work goes into the main repo, not `<game>-vN`. Check `pwd` before editing `story.ni`.
- **Forgetting to propagate upward.** A bug fix in v2 must also be applied to v3, v4, …, Current. The cascade isn't automatic.
- **Editing a `.ulx` / `.gblorb` directly.** Always edit `story.ni` and recompile. The base64-encoded `*.ulx.js` / `*.gblorb.js` for the web player is regenerated by the build.
- **Stale binaries.** A version's `story.ni` and its compiled binary must match. If you change source, recompile that repo before committing — otherwise the deployed game won't reflect the source. (`build.py <game>-vN` does this.)
- **Reusing one walkthrough seed.** Different versions need different golden seeds; check each repo's `tests/seeds.conf`.

## See Also

- `C:/code/ifhub/docs/publishing.md` — the game-folder contract and the build/ship workflow
- Project-specific `CLAUDE.md` files for game systems, scoring, etc.
