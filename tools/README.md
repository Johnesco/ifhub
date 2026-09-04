# Hub tools

These scripts run on the receive side only. They never compile, run, or test a game; that happens in the engine workspaces (`C:/code/text-games/<engine>/tools/build.py`). The folder contract and the whole workflow are in `docs/publishing.md`.

| Script | Purpose |
|---|---|
| `ship.py <game> [--local] [--refresh-pages] [--message "msg"]` | The intake. Verifies the folder contract, generates missing wrapper pages, registers the game, publishes it, pushes the hub. `--local` stops after registering |
| `build_games.py` | Regenerates `site/games.json` and `site/cards.json` from every `ifhub.conf` under the `workspaces.json` roots. Idempotent; run by ship and push_hub |
| `register_game.py --name <game> [--title ... --tags ...]` | Sets `hub = yes` (and any fields given) in a game's `ifhub.conf`, then rebuilds the registry |
| `publish.py <game> ["message"]` | Commits and pushes a game folder to `Johnesco/<game>`. First run creates the repo, adds the Pages workflow, enables Pages |
| `push_hub.py <game>` | Rebuilds the registry, repairs mojibake, commits and pushes `site/games.json`, `cards.json`, `hubs.json` |
| `check_links.py [--fix]` | Verifies every URL in the registry resolves to a file on disk; `--fix` drops broken optional URLs |
| `build_landing.py --all` or `<base>` | Regenerates the landing page of a versioned group (zork1) from the primary folder's `landing.json`. Still reads group metadata from `games-registry.json`; needs updating to read `ifhub.conf` |
| `fix_mojibake.py` | Repairs double-encoded UTF-8 in the registry files (called by push_hub) |
| `web/generate_pages.py`, `web/generate_walkthrough.py` | Wrapper-page generators used by ship; their templates are in `web/` |

`lib/`: `paths` (hub root, site dir, workspace discovery), `git` (git and gh helpers), `output`, `process`, `web` (template substitution).
