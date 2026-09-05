# Hub tools

These scripts run on the receive side only. They never compile, run, or test a game; that happens in the engine workspaces (`C:/code/text-games/<engine>/tools/build.py`). The folder contract and the whole workflow are in `docs/publishing.md`.

| Script | Purpose |
|---|---|
| `ship.py <game> [--local] [--refresh-pages] [--message "msg"]` | The intake. Verifies the folder contract, writes the landing page when missing, sets `hub = yes`, rebuilds the registry, publishes the game, pushes the hub. `--local` stops after registering; `--unlist` sets `hub = no` and pushes the registry; `--clean-wrappers` deletes old generated source.html / walkthrough.html |
| `build_games.py` | Regenerates `site/games.json` and `site/cards.json` from every `ifhub.conf` under the `workspaces.json` roots. Title, author, description, tags, and version fields all come from the conf. Idempotent; run by ship and push_hub |
| `publish.py <game> ["message"]` | Commits and pushes a game folder to `Johnesco/<game>`. First run creates the repo, adds the Pages workflow, enables Pages |
| `push_hub.py <game>` | Rebuilds the registry, commits and pushes `site/games.json`, `cards.json`, `hubs.json` |
| `check_links.py [--fix]` | Verifies every URL in the registry resolves to a file on disk; `--fix` drops broken optional URLs |
| `build_landing.py --all` or `<base>` | Regenerates the landing page of a versioned group (zork1, dracula) from the group data in `games.json` and the primary folder's `landing.json` |
| `web/generate_pages.py` | Writes a game's landing page (index.html) from `web/landing-template.html`; used by ship. The only file the hub writes into a game folder |

`lib/`: `paths` (hub root, site dir, workspace discovery), `git` (git and gh helpers), `output`, `process`, `web` (template substitution).
