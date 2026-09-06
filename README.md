# IF Hub

A small static site that shows interactive fiction games online, each with its source code and walkthrough side by side. It exists so finished games can be put in front of people quickly.

**Live site:** [johnesco.github.io/ifhub](https://johnesco.github.io/ifhub/) · **Player:** [app.html](https://johnesco.github.io/ifhub/app.html)

## How a game gets here

IF Hub is receive-only. Games are written, built, and tested in their own engine workspaces; the hub only publishes and displays the result.

1. **Build in the workspace** — `python C:/code/text-games/<engine>/tools/build.py <game>` compiles the game, runs its tests, and lays out a folder with `ifhub.conf`, `play.html`, and (optionally) source, walkthrough, and a `tests.html` report.
2. **Ship to the hub** — `python tools/ship.py <game>` checks that folder, adds the hub's wrapper pages, registers the game in `site/games.json`, publishes the folder to its own GitHub Pages repo (`johnesco.github.io/<game>/`), and pushes the hub.
3. **Play** — the hub iframes the game from its own URL. Nothing is copied into the hub.

The folder contract and the per-engine commands are in [docs/publishing.md](docs/publishing.md).

## Engines

Inform 7 and Z-machine (Parchment), Ink (ink.js), Rez, wwwBASIC and Applesoft BASIC. Each has a workspace under `C:/code/text-games/` with its own tooling and `CLAUDE.md`.

## Layout

```
site/        the hub: index.html (cards), app.html (split-pane player), themes.js, games.json, cards.json, hubs.json
tools/       ship.py (intake), build_games.py (registry), publish.py, push_hub.py, check_links.py, build_landing.py
docs/        publishing.md (the contract), functional-spec.md, sdlc/
reference/   css-overlay.md (theming), multi-version-guide.md (versioned games such as Zork I v0..v3)
```

## Built with

[Parchment](https://github.com/curiousdannii/parchment), [Inform 7](http://inform7.com/), [Ink](https://www.inklestudios.com/ink/), [Rez](https://rez-lang.com/), [ZILF](https://foss.heptapod.net/zilf/zilf), and [Claude](https://claude.ai/).
