#!/usr/bin/env python3
"""Push IF Hub registry changes (games.json + cards.json) to GitHub.

Usage:
    python tools/push_hub.py <game-name>

Stages games.json and cards.json, commits with a message referencing the
game name, and pushes. Skips commit if there are no staged changes.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import git, paths


def main():
    parser = argparse.ArgumentParser(description="Push IF Hub registry changes.")
    parser.add_argument("game", help="Game name (for commit message)")
    args = parser.parse_args()

    cwd = paths.I7_ROOT
    git.add([paths.IFHUB_DIR / "games.json", paths.IFHUB_DIR / "cards.json",
             paths.IFHUB_DIR / "hubs.json"], cwd=cwd)

    if not git.diff_cached_quiet(cwd=cwd):
        print("No hub registry changes to push.")
        return

    git.commit(f"Register {args.game} in IF Hub", cwd=cwd)
    git.push(cwd=cwd)


if __name__ == "__main__":
    main()
