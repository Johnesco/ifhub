#!/usr/bin/env python3
"""Ship a game folder to IF Hub.

IF Hub is receive-only: it does not build or test games. A game is built in its
engine workspace (text-games/<engine>/tools/build.py) and then shipped here.

Usage:
    python tools/ship.py <game> [--local] [--refresh-pages] [--message "commit message"]
    python tools/ship.py <game> --unlist [--local]
    python tools/ship.py <game> --clean-wrappers [--local]

<game> is the folder name of a game under one of the workspaces.json roots, or a path.

The contract (what the folder must contain):
    ifhub.conf      engine, title (plus description, tags, source, walkthrough, sound...)
    play.html       a self-contained web player, with any libs it needs (lib/parchment/, ...)
Optional, picked up when present (the hub renders these itself):
    <source>        the raw file named by `source =` in ifhub.conf (highlighted in the source pane;
                    or set sourceBrowser = yes and ship your own source.html)
    walkthrough.txt, walkthrough_output.txt, walkthrough-guide.txt   at the game root
    tests.html      a test report page; the hub shows a Tests tab when it exists

Steps:
    1. verify the contract
    2. write the game's landing page (index.html) when missing
       (--refresh-pages rewrites it from the current template)
    3. register: set `hub = yes` in ifhub.conf, rebuild site/games.json + site/cards.json
    4. publish the folder to https://johnesco.github.io/<game>/       (skipped with --local)
    5. commit and push the hub registry so the live hub lists it       (skipped with --local)

--unlist sets `hub = no` instead, rebuilds the registry, and pushes the hub (unless --local).
The game's own repo and Pages site are left alone; it just disappears from the hub.
--clean-wrappers deletes source.html / walkthrough.html that an older hub generated into the
folder (source.html is kept when the conf says sourceBrowser = yes), then continues shipping.
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import output, paths
import build_games


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


def run(cmd: list) -> int:
    return subprocess.run([str(c) for c in cmd]).returncode


def generate_landing(game_dir: Path, conf: dict, refresh: bool) -> None:
    """index.html is the only file the hub writes into a game folder."""
    if not refresh and (game_dir / "index.html").exists():
        print("  index.html: present")
        return
    cmd = [sys.executable, paths.WEB_DIR / "generate_pages.py",
           "--title", conf["title"],
           "--meta", conf.get("author", "An Interactive Fiction"),
           "--description", conf.get("description", "An interactive fiction game."),
           "--id", game_dir.name, "--out", game_dir]
    if refresh:
        cmd.append("--force")
    if run(cmd):
        raise RuntimeError("generate_pages.py failed")


def stale_wrappers(game_dir: Path, conf: dict) -> list[Path]:
    """Pages an older hub generated into the folder; the hub renders these views itself now."""
    stale = []
    if (game_dir / "walkthrough.html").exists():
        stale.append(game_dir / "walkthrough.html")
    if (game_dir / "source.html").exists() and not build_games.as_bool(conf.get("sourceBrowser")):
        stale.append(game_dir / "source.html")
    return stale


def upsert_conf_field(lines: list[str], key: str, value: str) -> list[str]:
    """Set `key = value` in ifhub.conf lines (before any [section]); append if absent."""
    out: list[str] = []
    found = False
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_section = True
        if not in_section and not found and "=" in line and line.split("=", 1)[0].strip() == key:
            out.append(f"{key} = {value}")
            found = True
            continue
        out.append(line)
    if not found:
        insert_at = next((i for i, l in enumerate(out) if l.strip().startswith("[")), len(out))
        out.insert(insert_at, f"{key} = {value}")
    return out


def set_hub_flag(game_dir: Path, value: str) -> None:
    """Write `hub = yes|no` into the game's ifhub.conf, preserving everything else."""
    conf_path = game_dir / "ifhub.conf"
    text = conf_path.read_text(encoding="utf-8")
    lines = upsert_conf_field(text.splitlines(), "hub", value)
    new_text = "\n".join(lines)
    if text.endswith("\n") or not new_text.endswith("\n"):
        new_text += "\n" if not new_text.endswith("\n") else ""
    if new_text != text:
        conf_path.write_text(new_text, encoding="utf-8")
        print(f"  ifhub.conf: set hub = {value}")


def register(game_dir: Path) -> None:
    set_hub_flag(game_dir, "yes")
    build_games.main()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ship a built game folder to IF Hub.")
    parser.add_argument("game", help="Game folder name (under a workspaces.json root) or a path")
    parser.add_argument("--local", action="store_true", help="Register only; do not publish or push")
    parser.add_argument("--refresh-pages", action="store_true",
                        help="Regenerate index.html, source.html, walkthrough.html from the current templates")
    parser.add_argument("--message", default="", help="Commit message for the game repo")
    parser.add_argument("--unlist", action="store_true",
                        help="Set hub = no so the game disappears from the hub (repo and Pages untouched)")
    parser.add_argument("--clean-wrappers", action="store_true",
                        help="Delete source.html / walkthrough.html left behind by the old hub-generated pages")
    args = parser.parse_args()

    game_dir = resolve_game(args.game)
    name = game_dir.name

    if args.unlist:
        print(output.bold(f"=== unlist {name} ==="))
        set_hub_flag(game_dir, "no")
        build_games.main()
        if args.local:
            output.skip("--local: hub registry rebuilt on disk only")
            return
        if run([sys.executable, paths.TOOLS_DIR / "push_hub.py", name]):
            print(output.red("=== unlist failed at push hub ==="))
            sys.exit(1)
        print(output.green(f"=== {name} is no longer listed on the hub ==="))
        return
    print(output.bold(f"=== ship {name} ==="))

    print(output.bold("1. contract"))
    conf, problems = verify_contract(game_dir)
    if problems:
        for p in problems:
            output.fail(p)
        print("\nSee the docstring of this script (or docs/publishing.md) for what a game folder needs.")
        sys.exit(1)
    output.ok(f"{conf['engine']} game '{conf['title']}' at {game_dir}")
    if not (game_dir / "walkthrough.txt").exists() and list(game_dir.glob("tests/*/walkthrough.txt")):
        output.warn("walkthrough.txt exists under tests/ but not at the game root; the hub only reads the root")
    stale = stale_wrappers(game_dir, conf)
    if stale and args.clean_wrappers:
        for f in stale:
            f.unlink()
            print(f"  removed stale {f.name}")
    elif stale:
        output.warn("old generated " + ", ".join(f.name for f in stale) + " present; the hub renders these now. Remove with --clean-wrappers")

    try:
        print(output.bold("2. landing page"))
        generate_landing(game_dir, conf, args.refresh_pages)
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
