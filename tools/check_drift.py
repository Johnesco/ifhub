#!/usr/bin/env python3
"""Report which games carry a stale copy of something the hub owns; bring them current.

The hub writes two files into every game folder and then owns them: the Pages
workflow (`.github/workflows/deploy-pages.yml`, from WORKFLOW_CONTENT in publish.py)
and the landing page (`index.html`, from tools/web/landing-template.html). A game
picks up the current workflow whenever it is published, and its landing page only
when shipped with --refresh-pages — so after either template changes, every game that
is not re-published keeps the old copy, and nothing says which ones (#99).

    python tools/check_drift.py            report every game: workflow and landing page
    python tools/check_drift.py --fix      rewrite stale workflows and publish those games
    python tools/check_drift.py --fix --force   ... and stale landing pages too

--fix only touches games that are listed (hub = yes), published (have a remote), and
have a clean working tree — publish.py commits everything in the folder, and a drift
commit must not sweep up work in progress. Each game is published through publish.py,
so a failure stops that game and the sweep goes on to the next; the summary says which.

Landing pages need --force because there is no marker in a generated index.html, so a
stale page and a hand-edited one look the same. The workflow has no such ambiguity.
Versioned-group primaries (zork1, dracula, familyzoo) get their landing page from
build_landing.py and are skipped here.

Exit status is 1 when anything is stale, so the check can gate a script.
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import git, output, paths
from lib.web import render_template
import build_games
import build_landing
import publish

LANDING_TEMPLATE = paths.WEB_DIR / "landing-template.html"
WORKFLOW_REL = Path(".github") / "workflows" / "deploy-pages.yml"


def landing_replacements(name: str, conf: dict) -> dict[str, str]:
    """The substitutions a game's landing page is rendered with.

    ship.py builds generate_pages.py's arguments from this too, so "what the template
    would produce" here is exactly what shipping would write.
    """
    return {
        "__TITLE__": conf.get("title", name),
        "__META__": conf.get("author", "An Interactive Fiction"),
        "__DESCRIPTION__": conf.get("description", "An interactive fiction game."),
        "__ID__": name,
    }


def expected_landing(name: str, conf: dict) -> str:
    return render_template(LANDING_TEMPLATE, landing_replacements(name, conf))


def workflow_state(game_dir: Path) -> str:
    """'current', 'stale' or 'missing'."""
    wf = game_dir / WORKFLOW_REL
    if not wf.exists():
        return "missing"
    return "current" if wf.read_text(encoding="utf-8") == publish.WORKFLOW_CONTENT else "stale"


def landing_state(game_dir: Path, conf: dict) -> str:
    """'current', 'stale', 'missing', or 'versioned' (build_landing.py owns it; not checked)."""
    index = game_dir / "index.html"
    if not index.exists():
        return "missing"
    text = index.read_text(encoding="utf-8")
    if text.startswith(build_landing.MARKER):
        return "versioned"
    return "current" if text == expected_landing(game_dir.name, conf) else "stale"


def survey() -> list[tuple[str, Path, dict, str, str]]:
    """(name, dir, conf, workflow_state, landing_state) for every discovered game."""
    rows = []
    for name, game_dir in sorted(build_games.discover_game_dirs().items()):
        conf = build_games.parse_conf(game_dir / "ifhub.conf")
        rows.append((name, game_dir, conf, workflow_state(game_dir), landing_state(game_dir, conf)))
    return rows


def report(rows) -> tuple[list[str], list[str]]:
    """Print the survey; return (names with stale workflow, names with stale landing)."""
    stale_wf = [r[0] for r in rows if r[3] == "stale"]
    stale_lp = [r[0] for r in rows if r[4] == "stale"]
    width = max(len(r[0]) for r in rows) if rows else 10
    print(f"{'game':<{width}}  workflow  landing")
    for name, _, conf, wf, lp in rows:
        listed = "" if build_games.as_bool(conf.get("hub")) else "   (not listed)"
        flag = " <-" if wf == "stale" or lp == "stale" else ""
        print(f"{name:<{width}}  {wf:<8}  {lp:<9}{listed}{flag}")
    print()
    print(f"{len(rows)} game(s): {len(stale_wf)} stale workflow(s), {len(stale_lp)} stale landing page(s)")
    return stale_wf, stale_lp


def fix(rows, stale_wf: list[str], stale_lp: list[str], force: bool) -> int:
    """Bring stale games current and publish them. Returns the number that failed."""
    by_name = {r[0]: r for r in rows}
    targets = sorted(set(stale_wf) | (set(stale_lp) if force else set()))
    if stale_lp and not force:
        output.warn(f"{len(stale_lp)} stale landing page(s) left alone; --force rewrites them "
                    "(there is no marker, so a hand-edited page looks the same as a stale one)")
    if not targets:
        print("Nothing to fix.")
        return 0

    done, skipped, failed = [], [], []
    for name in targets:
        _, game_dir, conf, wf, lp = by_name[name]
        print(output.bold(f"=== {name} ==="))
        if not build_games.as_bool(conf.get("hub")):
            output.skip("not listed (hub = no); the hub does not manage this folder")
            skipped.append(name)
            continue
        if not (game_dir / ".git").is_dir() or not git.has_remote(cwd=game_dir):
            output.skip("not published; ship it first")
            skipped.append(name)
            continue
        dirty = git.status(cwd=game_dir)
        if dirty:
            output.skip(f"working tree has {len(dirty.splitlines())} uncommitted change(s); "
                        "a drift commit must not sweep those up")
            skipped.append(name)
            continue

        changed = []
        if wf == "stale":
            publish.ensure_workflow(game_dir)
            changed.append("deploy-pages.yml")
        if force and lp == "stale":
            (game_dir / "index.html").write_text(expected_landing(name, conf), encoding="utf-8")
            print("  Rewriting index.html from the current template...")
            changed.append("index.html")

        msg = "Bring hub-owned files current: " + ", ".join(changed)
        rc = subprocess.run([sys.executable, str(paths.TOOLS_DIR / "publish.py"), name, msg]).returncode
        if rc:
            output.fail(f"publish failed (exit {rc}); the rewrite is left in the working tree")
            failed.append(name)
        else:
            done.append(name)

    print()
    print(output.bold("=== drift fix ==="))
    print(f"  brought current: {len(done)}" + (f"  ({', '.join(done)})" if done else ""))
    if skipped:
        print(f"  skipped:         {len(skipped)}  ({', '.join(skipped)})")
    if failed:
        print(output.red(f"  failed:          {len(failed)}  ({', '.join(failed)})"))
    return len(failed)


def main() -> None:
    parser = argparse.ArgumentParser(description="Find game folders whose hub-owned files are stale.")
    parser.add_argument("--fix", action="store_true",
                        help="Rewrite stale workflows and publish those games")
    parser.add_argument("--force", action="store_true",
                        help="With --fix: also rewrite stale landing pages (may overwrite hand edits)")
    args = parser.parse_args()

    if args.force and not args.fix:
        print("ERROR: --force only means something with --fix.", file=sys.stderr)
        sys.exit(2)

    rows = survey()
    stale_wf, stale_lp = report(rows)

    if args.fix:
        print()
        sys.exit(1 if fix(rows, stale_wf, stale_lp, args.force) else 0)

    sys.exit(1 if (stale_wf or stale_lp) else 0)


if __name__ == "__main__":
    main()
