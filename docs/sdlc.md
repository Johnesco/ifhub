# How work happens here

One person plus Claude, one static site, one rule that matters: **Claude cannot verify its own work.** Everything else below exists to make that rule cheap to follow.

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
- Matches existing patterns; no behaviour change unless the ticket asked for one
- Documentation updated as in step 4; links and file references still resolve
- Commits reference the ticket; the PR says `Fixes #XX`
- Card in Verify, waiting for a human

Issue and PR templates live in `.github/`; they carry these checklists.
