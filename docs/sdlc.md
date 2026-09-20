# How work happens here

One person plus Claude, one static site, one rule that matters: **Claude cannot verify its own work.** Everything else below exists to make that rule cheap to follow.

## Who decides what

The loop below is for hub work. Before using it, check that the change is hub work at all — the line between the hub and a game is not where it first looks.

A game **runs** on its own. `play.html` is self-contained, its engine workspace builds and tests it, and nothing about playing it involves the hub. But a game does not **publish** itself. The hub does that, and it reaches into the game's folder to do it:

| What the hub writes into a game repo | Where |
|---|---|
| `index.html`, the landing page | `ship.py` `generate_landing()` |
| the `hub = yes\|no` line in the game's own `ifhub.conf` | `ship.py` `set_hub_flag()` |
| `.github/workflows/deploy-pages.yml`, overwritten wholesale | `publish.py` `ensure_workflow()` |
| deletion of a `source.html` / `walkthrough.html` an older hub generated | `ship.py` `stale_wrappers()` |

Then it commits and pushes that repo. So:

> **A game owns how it plays. The hub owns how it ships.**

That is deliberate, not an accident to be tidied away. One owner of the deploy mechanics is why every game deploys the same way instead of each drifting into its own; the cost is that anything about shipping is never about one game.

### Which side is this change on?

**If it forces more than one game repo to move, it is a hub decision.** Ticket it here and use the loop below.

| That game's business | A hub decision — ticket it here |
|---|---|
| the story, its tests, its walkthrough | a new `ifhub.conf` key, or a new meaning for an existing one |
| the engine version it pins, its own build | a new engine, or a source extension the hub highlights |
| its own `CLAUDE.md`, `README.md`, design notes | what the hub renders in any pane |
| bugs in the game | what `ship.py` or `publish.py` write into a game folder |

The awkward cases are the ones that look like one game and are not. Adding Chord source highlighting (#92) read as "a Sharpee thing" and took coordinated commits in six repos. A one-line change to the Pages workflow meant re-publishing five games by hand. Both were hub decisions wearing a game's clothes; the test above catches them.

### Working model

Each game gets its own chat, working in its own folder. **IF Hub is always edited in the hub chat.** A game chat does not change the contract — if it needs the contract changed, that is a ticket here, and it waits. Otherwise two chats edit the same seam from opposite sides and neither knows what the other decided.

The contract itself — what a game folder must contain for the hub to receive it — is `docs/publishing.md`. That file is the interface; this section is who may change it.

## The loop

1. **Ticket first.** Every change starts as a GitHub issue, before any code.
   ```bash
   gh issue create --title "..." --label "task,area:hub" --body "..."
   gh project item-add 3 --owner Johnesco --url <issue-url>      # the board does not pick issues up on its own
   ```
2. **Branch** as `type/short-description` (`feature/`, `fix/`, `docs/`, `task/`, `spike/`). Lowercase, hyphens.
3. **Work**, reading files before editing them and following the patterns already in the code.
4. **Docs in the same change.** A change without its documentation is not done:
   - `docs/functional-spec.md` for anything the site does or any data-file field
   - `docs/publishing.md` when the game-folder contract or a build/ship command changes
   - `CLAUDE.md` when structure or conventions change; `README.md` when the public description changes
5. **Commit** as `#XX: imperative summary` (under 72 characters, body optional). Add `Co-Authored-By: Claude ... <noreply@anthropic.com>` when Claude wrote it.
6. **Pull request** titled like the commit, with `Fixes #XX` in the body; move the card to **Verify**.
7. **John verifies and merges.** Merging closes the issue and moves the card to Done. Small self-contained fixes may go straight to `master`; a push that touches `site/**` deploys the live hub.

If the docs and the code disagree, say so in the issue and let John decide which is right. Do not silently fix either.

## The board

https://github.com/users/Johnesco/projects/3 (project 3, owner Johnesco). Columns: Backlog → Ready → In Progress → Verify → Done.
Automatic: added → Backlog, closed → Done, reopened → In Progress, PR merged → Done. Manual: Backlog → Ready (acceptance criteria clear), Ready → In Progress (work starts), In Progress → Verify (PR open).

## Labels

- **Type**: `feature`, `bug`, `task` (refactor, tooling, cleanup), `docs`, `spike` (research; the deliverable is a recommendation and follow-up tickets)
- **Area**: `area:hub`, `area:tools`, `area:docs`, `area:web-player`, `area:inform7`, `area:sound`, `area:testing`
- **Priority** (optional): `priority:high`, `priority:low`
- **Resolution**, when closing without shipping, with a one-line reason: `resolution:superseded`, `resolution:wontfix`, `resolution:by-design`, `resolution:stale`, `resolution:duplicate`, `resolution:cannot-reproduce`

Bugs: something that crashes, loses data or blocks play is high priority; wrong but usable is normal; cosmetic is low.

## Definition of done

- Works as the acceptance criteria say, without breaking what already worked
- Matches existing patterns; no behavior change unless the ticket asked for one
- Documentation updated as in step 4; links and file references still resolve
- Commits reference the ticket; the PR says `Fixes #XX`
- Card in Verify, waiting for a human

Issue and PR templates live in `.github/`; they carry these checklists.
