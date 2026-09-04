#!/usr/bin/env python3
"""Ship a game folder to IF Hub.

IF Hub is receive-only: it does not build or test games. A game is built in its
engine workspace (text-games/<engine>/tools/build.py) and then shipped here.

Usage:
    python tools/ship.py <game> [--local] [--refresh-pages] [--message "commit message"]

<game> is the folder name of a game under one of the workspaces.json roots, or a path.

The contract (what the folder must contain):
    ifhub.conf      engine, title (plus description, tags, source, walkthrough, sound...)
    play.html       a self-contained web player, with any libs it needs (lib/parchment/, ...)
Optional, picked up when present:
    <source>        the file named by `source =` in ifhub.conf (shown in the hub's source pane)
    walkthrough.txt, walkthrough_output.txt, walkthrough-guide.txt   (root or tests/*/)
    tests.html      a test report page; the hub shows a Tests tab when it exists

Steps:
    1. verify the contract
    2. generate the hub's wrapper pages when missing: index.html, source.html, walkthrough.html
       (--refresh-pages regenerates them from the current templates)
    3. register: set `hub = yes` in ifhub.conf, rebuild site/games.json + site/cards.json
    4. publish the folder to https://johnesco.github.io/<game>/       (skipped with --local)
    5. commit and push the hub registry so the live hub lists it       (skipped with --local)
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import output, paths
import build_games
import register_game


def resolve_game(arg: str) -> Path:
    p = Path(arg)
    if (p / "ifhub.conf").exists():
        return p.resolve()
    dirs = build_games.discover_game_dirs()
    if arg in dirs:
        return dirs[arg]
    print(f"ERROR: '{arg}' is not a game folder and is not under any workspace root.", file=sys.stderr)
    print("  Roots come from workspaces.json; a game folder needs an ifhub.conf.", file=sys.stderr)
    sys.exit(1)


def verify_contract(game_dir: Path) -> tuple[dict, list[str]]:
    problems: list[str] = []
    conf_path = game_dir / "ifhub.conf"
    conf = build_games.parse_conf(conf_path) if conf_path.exists() else {}
    if not conf_path.exists():
        problems.append("ifhub.conf is missing")
    else:
        for key in ("engine", "title"):
            if not conf.get(key):
                problems.append(f"ifhub.conf has no `{key} =` line")
    if not (game_dir / "play.html").exists():
        problems.append("play.html is missing: build the game in its workspace first")
    src = conf.get("source")
    if src and not (game_dir / src).exists():
        problems.append(f"ifhub.conf names `source = {src}` but that file does not exist")
    return conf, problems


def has_walkthrough(game_dir: Path) -> bool:
    if (game_dir / "walkthrough.txt").exists():
        return True
    tests = game_dir / "tests"
    if tests.is_dir():
        if (tests / "walkthrough.txt").exists():
            return True
        return any((sub / "walkthrough.txt").exists() for sub in tests.iterdir() if sub.is_dir())
    return False


def run(cmd: list) -> int:
    return subprocess.run([str(c) for c in cmd]).returncode


def generate_pages(game_dir: Path, conf: dict, refresh: bool) -> None:
    py = sys.executable
    if refresh or not (game_dir / "index.html").exists() or not (game_dir / "source.html").exists():
        cmd = [py, paths.WEB_DIR / "generate_pages.py",
               "--title", conf["title"],
               "--meta", conf.get("meta", "An Interactive Fiction"),
               "--description", conf.get("description", "An interactive fiction game."),
               "--id", game_dir.name, "--out", game_dir]
        if conf.get("source"):
            cmd += ["--source-file", conf["source"]]
        if refresh:
            cmd.append("--force")
        if run(cmd):
            raise RuntimeError("generate_pages.py failed")
    else:
        print("  index.html, source.html: present")

    if has_walkthrough(game_dir):
        if refresh or not (game_dir / "walkthrough.html").exists():
            cmd = [py, paths.WEB_DIR / "generate_walkthrough.py", "--title", conf["title"], "--out", game_dir]
            if refresh:
                cmd.append("--force")
            if run(cmd):
                raise RuntimeError("generate_walkthrough.py failed")
        else:
            print("  walkthrough.html: present")
    else:
        print("  no walkthrough.txt: skipping walkthrough.html")


def register(game_dir: Path) -> None:
    conf_path = game_dir / "ifhub.conf"
    lines = register_game.upsert_conf_field(register_game.read_conf_lines(conf_path), "hub", "yes")
    new_text = "\n".join(lines)
    if not new_text.endswith("\n"):
        new_text += "\n"
    if new_text != conf_path.read_text(encoding="utf-8"):
        conf_path.write_text(new_text, encoding="utf-8")
        print("  ifhub.conf: set hub = yes")
    build_games.main()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ship a built game folder to IF Hub.")
    parser.add_argument("game", help="Game folder name (under a workspaces.json root) or a path")
    parser.add_argument("--local", action="store_true", help="Register only; do not publish or push")
    parser.add_argument("--refresh-pages", action="store_true",
                        help="Regenerate index.html, source.html, walkthrough.html from the current templates")
    parser.add_argument("--message", default="", help="Commit message for the game repo")
    args = parser.parse_args()

    game_dir = resolve_game(args.game)
    name = game_dir.name
    print(output.bold(f"=== ship {name} ==="))

    print(output.bold("1. contract"))
    conf, problems = verify_contract(game_dir)
    if problems:
        for p in problems:
            output.fail(p)
        print("\nSee the docstring of this script (or docs/publishing.md) for what a game folder needs.")
        sys.exit(1)
    output.ok(f"{conf['engine']} game '{conf['title']}' at {game_dir}")

    try:
        print(output.bold("2. wrapper pages"))
        generate_pages(game_dir, conf, args.refresh_pages)
        print(output.bold("3. register"))
        register(game_dir)
    except RuntimeError as e:
        print(output.red(f"=== ship failed: {e} ==="))
        sys.exit(1)

    if args.local:
        print()
        output.skip("--local: not publishing. The game is registered in the on-disk hub.")
        print(f"  Preview:  /serve (Portman), then http://127.0.0.1:9000/ifhub/app.html?game={name}")
        return

    print(output.bold("4. publish"))
    cmd = [sys.executable, paths.TOOLS_DIR / "publish.py", name]
    if args.message:
        cmd.append(args.message)
    if run(cmd):
        print(output.red("=== ship failed at publish ==="))
        sys.exit(1)

    print(output.bold("5. push hub"))
    if run([sys.executable, paths.TOOLS_DIR / "push_hub.py", name]):
        print(output.red("=== ship failed at push hub ==="))
        sys.exit(1)

    print()
    print(output.green(output.bold("=== shipped ===")))
    print(f"  Game:  https://{paths.GH_ORG.lower()}.github.io/{name}/play.html")
    print(f"  Hub:   https://{paths.GH_ORG.lower()}.github.io/ifhub/app.html?game={name}")
    print("  (Pages redeploys take a minute or two)")


if __name__ == "__main__":
    main()
