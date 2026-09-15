#!/usr/bin/env python3
"""Publish a game folder to its own GitHub Pages repo.

First publish: creates the GitHub repo, pushes everything, enables Pages. A folder
    that already has local history but no remote is adopted — the remote is created
    and the existing history pushed — rather than treated as already published.
Later runs:    commits changes and pushes to trigger redeployment.

Every git and gh step is checked. If any of them fails the script exits non-zero and
says the game was not published, so ship.py stops before writing the hub registry:
a failed publish must never leave the hub advertising a URL that 404s (#101).

Usage:
    python tools/publish.py <game-name>
    python tools/publish.py <game-name> "commit message"

Publishes to: <org>.github.io/<game-name>/ — the org is IFHUB_GH_ORG, default Johnesco.
Commits it makes carry `Co-Authored-By: $IFHUB_COAUTHOR` when that is set, and no trailer
when it is not — a person running ship.py by hand is not co-authored by anyone.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import git, paths
import build_games

# Commit trailer for the commits this script makes in a game repo. Set IFHUB_COAUTHOR to
# "Name <email>" when Claude is driving; leave it unset when a person runs ship.py, and
# no trailer is added. A model name hardcoded here goes stale at every switch.
_coauthor = os.environ.get("IFHUB_COAUTHOR", "").strip()
COAUTHOR = f"\n\nCo-Authored-By: {_coauthor}" if _coauthor else ""

WORKFLOW_CONTENT = """\
name: Deploy to GitHub Pages

on:
  push:
    branches: [main, master]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - name: Assemble site
        run: |
          mkdir -p _site
          [ -d web ] && cp -r web/* _site/ || true
          [ -d lib ] && cp -r lib _site/ || true
          [ -d assets ] && cp -r assets _site/ || true
          [ -d audio ] && cp -r audio _site/ || true
          [ -d sfx ] && cp -r sfx _site/ || true
          [ -d src ] && cp -r src _site/ || true
          cp *.html _site/ 2>/dev/null || true
          cp *.txt _site/ 2>/dev/null || true
          cp *.ni _site/ 2>/dev/null || true
          cp *.ink _site/ 2>/dev/null || true
          cp *.json _site/ 2>/dev/null || true
          cp *.bas _site/ 2>/dev/null || true
          cp *.js _site/ 2>/dev/null || true
          cp *.css _site/ 2>/dev/null || true
          cp *.rez _site/ 2>/dev/null || true
          cp *.story _site/ 2>/dev/null || true
      - uses: actions/upload-pages-artifact@v3
        with:
          path: _site
      - id: deployment
        uses: actions/deploy-pages@v4
"""


def ensure_workflow(project_dir: Path):
    """Add or update deploy-pages.yml. Returns True if a file was created/changed."""
    workflow_dir = project_dir / ".github" / "workflows"
    workflow_file = workflow_dir / "deploy-pages.yml"
    if workflow_file.exists():
        if workflow_file.read_text(encoding="utf-8") == WORKFLOW_CONTENT:
            return False
        print("  Updating deploy-pages.yml workflow...")
    else:
        print("  Adding deploy-pages.yml workflow...")
    workflow_dir.mkdir(parents=True, exist_ok=True)
    workflow_file.write_text(WORKFLOW_CONTENT, encoding="utf-8")
    git.add([str(workflow_file)], cwd=project_dir)
    return True


def fail(message: str) -> None:
    """Abort the publish.

    ship.py keys the rest of its run off this exit code, so a failure here must never
    be silent: a publish that did not happen has to stop the hub registry being written.
    """
    print(f"ERROR: {message}", file=sys.stderr)
    print("  The game was NOT published; the hub registry has not been touched.", file=sys.stderr)
    sys.exit(1)


def check(rc: int, what: str) -> None:
    """Abort unless a git/gh step succeeded."""
    if rc != 0:
        fail(f"{what} failed (exit {rc}).")


def require_deploying_branch(name: str, project_dir: Path) -> None:
    """Refuse to publish from anything but the branch Pages deploys from.

    A checkout left on a feature branch has a clean tree and a working remote, so
    nothing else notices: the commit lands on that branch, the push succeeds, the
    deploy workflow never fires, and the game is reported as published (#108).
    """
    default = git.gh_default_branch(name)
    current = git.current_branch(cwd=project_dir)
    if default and current != default:
        fail(f"the checkout is on '{current}', but {paths.GH_ORG}/{name} deploys from "
             f"'{default}'. Switch to '{default}' (merging your branch into it if that is "
             "where the work is) and publish again.")


def main():
    parser = argparse.ArgumentParser(description="Publish project to GitHub Pages.")
    parser.add_argument("game", help="Game name (project directory)")
    parser.add_argument("message", nargs="?", default="", help="Commit message")
    args = parser.parse_args()

    project_dir = paths.project_dir(args.game)
    if project_dir is None:
        print(f"ERROR: '{args.game}' is not under any workspace root (see workspaces.json).", file=sys.stderr)
        sys.exit(1)
    msg = args.message or f"Update {args.game}"

    if not (project_dir / "play.html").exists():
        print("ERROR: play.html not found. Run the build first.", file=sys.stderr)
        sys.exit(1)

    # Whether a folder has ever been published is a question about the remote, not about
    # the .git directory: `git init` to keep local history while building a game is
    # ordinary, and used to send this straight into the update branch, pushing to an
    # origin that had never existed (#101).
    has_git = (project_dir / ".git").is_dir()
    published_before = has_git and git.has_remote(cwd=project_dir)

    if not published_before:
        # --- First publish: a fresh folder, or one that already has local history ---
        if has_git:
            print("=== First publish (adopting existing local history) ===")
        else:
            print("=== First-time setup ===")
            print("  Initializing git repo...")
            git.init(cwd=project_dir)

        if git.gh_repo_exists(args.game):
            print(f"  {paths.GH_ORG}/{args.game} already exists on GitHub; wiring up origin...")
            check(git.remote_add(args.game, cwd=project_dir), "git remote add origin")
            require_deploying_branch(args.game, project_dir)
        else:
            print("  Creating GitHub repo...")
            conf_path = project_dir / "ifhub.conf"
            conf = build_games.parse_conf(conf_path) if conf_path.exists() else {}
            repo_desc = f"{conf.get('title', args.game)} -- {conf.get('engine', 'interactive fiction')} game"
            check(git.gh_repo_create(args.game, repo_desc, cwd=project_dir), "gh repo create")

        ensure_workflow(project_dir)

        print("  Adding all files...")
        git.add_all(cwd=project_dir)
        if git.diff_cached_quiet(cwd=project_dir):
            check(git.commit(f"Initial commit: {args.game}{COAUTHOR}", cwd=project_dir), "git commit")

        print("  Pushing to GitHub...")
        check(git.push(cwd=project_dir), "git push")

        print("  Enabling GitHub Pages (workflow deployment)...")
        if git.gh_ensure_pages(args.game):
            # The push above fired the deploy workflow before build_type: workflow was
            # set, so that first run failed. Ask for a fresh one now that it is set.
            print("  Pages newly enabled; requesting a fresh deploy...")
            git.gh_workflow_dispatch(args.game)

        print()
        print("=== Published ===")
        print(f"  Repo:  https://github.com/{paths.GH_ORG}/{args.game}")
        print(f"  Site:  https://{paths.GH_ORG.lower()}.github.io/{args.game}/play.html")
        print("  (Pages may take a minute to deploy)")
    else:
        # --- Subsequent publishes ---
        print(f"=== Publishing {args.game} ===")
        require_deploying_branch(args.game, project_dir)
        ensure_workflow(project_dir)
        git.add_all(cwd=project_dir)

        if git.diff_cached_quiet(cwd=project_dir):
            check(git.commit(f"{msg}{COAUTHOR}", cwd=project_dir), "git commit")
        else:
            ahead = git.ahead_count(cwd=project_dir)
            if not ahead:
                print("  No changes to publish.")
                return
            # An earlier publish committed but its push failed (#101): nothing is staged,
            # yet the game is not online. Finish the job rather than call it done.
            print(f"  Nothing new to commit; {ahead} local commit(s) still unpushed.")
        check(git.push(cwd=project_dir), "git push")

        # Ensure Pages is enabled (catches repos created outside first-time flow)
        if git.gh_ensure_pages(args.game):
            print("  Enabled GitHub Pages (was not configured)")
            git.gh_workflow_dispatch(args.game)

        print()
        print("=== Pushed ===")
        print(f"  Site:  https://{paths.GH_ORG.lower()}.github.io/{args.game}/play.html")
        print("  (Pages will redeploy automatically)")


if __name__ == "__main__":
    main()
