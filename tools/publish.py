#!/usr/bin/env python3
"""Publish an Inform 7 project to GitHub Pages.

First run:  creates the GitHub repo, enables Pages, pushes everything.
Later runs: commits changes and pushes to trigger redeployment.

Usage:
    python tools/publish.py <game-name>
    python tools/publish.py <game-name> "commit message"

Publishes to: johnesco.github.io/<game-name>/
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import config, git, paths, process

WORKFLOW_CONTENT = """\
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
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
          cp *.html _site/ 2>/dev/null || true
          cp *.txt _site/ 2>/dev/null || true
          cp *.ni _site/ 2>/dev/null || true
          cp *.ink _site/ 2>/dev/null || true
          cp *.json _site/ 2>/dev/null || true
          cp *.bas _site/ 2>/dev/null || true
          cp *.js _site/ 2>/dev/null || true
          cp *.css _site/ 2>/dev/null || true
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


def main():
    parser = argparse.ArgumentParser(description="Publish project to GitHub Pages.")
    parser.add_argument("game", help="Game name (project directory)")
    parser.add_argument("message", nargs="?", default="", help="Commit message")
    args = parser.parse_args()

    project_dir = paths.project_dir(args.game)
    msg = args.message or f"Update {args.game}"

    if not (project_dir / "play.html").exists():
        print("ERROR: play.html not found. Run compile.py first.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"

    if not git_dir.is_dir():
        # --- First-time setup ---
        print("=== First-time setup ===")
        print("  Initializing git repo...")
        git.init(cwd=project_dir)

        print("  Creating GitHub repo...")
        conf_fields = config.parse_conf_fields(project_dir)
        engine = config.detect_engine(project_dir, conf_fields)
        engine_spec = config.get_engine_spec(engine)
        repo_desc = engine_spec.repo_description(args.game) if engine_spec else f"{args.game} -- An Interactive Fiction"
        git.gh_repo_create(args.game, repo_desc, cwd=project_dir)

        ensure_workflow(project_dir)

        print("  Adding all files...")
        git.add_all(cwd=project_dir)
        git.commit(
            f"Initial commit: {args.game}\n\nCo-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>",
            cwd=project_dir,
        )

        print("  Pushing to GitHub...")
        git.push(cwd=project_dir, set_upstream="main")

        print("  Enabling GitHub Pages (workflow deployment)...")
        git.gh_enable_pages(args.game)

        print()
        print("=== Published ===")
        print(f"  Repo:  https://github.com/{paths.GH_ORG}/{args.game}")
        print(f"  Site:  https://{paths.GH_ORG.lower()}.github.io/{args.game}/play.html")
        print("  (Pages may take a minute to deploy)")
    else:
        # --- Subsequent publishes ---
        print(f"=== Publishing {args.game} ===")
        ensure_workflow(project_dir)
        git.add_all(cwd=project_dir)

        if not git.diff_cached_quiet(cwd=project_dir):
            print("  No changes to publish.")
            return

        git.commit(
            f"{msg}\n\nCo-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>",
            cwd=project_dir,
        )
        git.push(cwd=project_dir)

        print()
        print("=== Pushed ===")
        print(f"  Site:  https://johnesco.github.io/{args.game}/play.html")
        print("  (Pages will redeploy automatically)")


if __name__ == "__main__":
    main()
