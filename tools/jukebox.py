#!/usr/bin/env python3
"""IF Hub Jukebox — import, publish, and manage games.

Usage:
    python tools/jukebox.py import /path/to/game/     Import a built game
    python tools/jukebox.py import /path/ --ship       Import + publish
    python tools/jukebox.py publish <game-name>        Publish to GitHub Pages
    python tools/jukebox.py list                       List registered games

The game directory must contain an ifhub.conf manifest:

    engine = inform7
    title = My Game
    binary = my-game.ulx
    source = story.ni
    walkthrough = walkthrough.txt
"""

import argparse
import configparser
import json
import shutil
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
IFHUB_DIR = TOOLS_DIR.parent
SITE_DIR = IFHUB_DIR / "site"
REGISTRY_PATH = IFHUB_DIR / "games-registry.json"

sys.path.insert(0, str(TOOLS_DIR))


# ── Config parsing ──────────────────────────────────────────────────────────

def parse_conf(game_dir: Path) -> dict:
    """Parse ifhub.conf from a game directory into a flat dict."""
    conf_path = game_dir / "ifhub.conf"
    if not conf_path.exists():
        print(f"Error: ifhub.conf not found in {game_dir}", file=sys.stderr)
        sys.exit(1)

    # configparser needs a section header; wrap in [game]
    text = "[game]\n" + conf_path.read_text(encoding="utf-8")
    cp = configparser.ConfigParser()
    cp.read_string(text)

    conf = dict(cp["game"])
    # Validate required fields
    if "engine" not in conf:
        print("Error: ifhub.conf missing 'engine' field", file=sys.stderr)
        sys.exit(1)
    if "title" not in conf:
        print("Error: ifhub.conf missing 'title' field", file=sys.stderr)
        sys.exit(1)

    return conf


def game_name_from_conf(conf: dict, game_dir: Path) -> str:
    """Derive the game name (used as deploy dir name and registry key)."""
    return conf.get("name", game_dir.name)


# ── Registry ────────────────────────────────────────────────────────────────

def load_registry() -> dict:
    """Load games-registry.json."""
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {}


def save_registry(registry: dict):
    """Save games-registry.json."""
    REGISTRY_PATH.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ── Source/walkthrough generators ───────────────────────────────────────────

def generate_source_html(source_path: Path, deploy_dir: Path, conf: dict):
    """Generate source.html with syntax highlighting for the source file."""
    # Check if a generator exists for this engine
    gen_dir = TOOLS_DIR / "web" / "generators"
    gen_script = gen_dir / "source_html.py"
    if gen_script.exists():
        subprocess.run(
            [sys.executable, str(gen_script),
             "--source", str(source_path),
             "--engine", conf["engine"],
             "--title", conf["title"],
             "--out", str(deploy_dir / "source.html")],
            check=False,
        )
    else:
        # Fallback: use generate_pages.py if available
        pages_script = TOOLS_DIR / "web" / "generate_pages.py"
        if pages_script.exists():
            source_filename = Path(conf.get("source", "story.ni")).name
            cmd = [sys.executable, str(pages_script),
                   "--title", conf["title"],
                   "--meta", conf.get("author", ""),
                   "--description", conf.get("description", ""),
                   "--source-file", source_filename,
                   "--out", str(deploy_dir),
                   "--force"]
            # Multi-file source projects
            source_files = conf.get("_source_files")
            if source_files and len(source_files) > 1:
                cmd.extend(["--source-files", ",".join(source_files)])
            subprocess.run(cmd, check=False)


def generate_walkthrough_html(walkthrough_path: Path, deploy_dir: Path, conf: dict):
    """Generate walkthrough.html from a walkthrough text file."""
    walk_template = TOOLS_DIR / "web" / "walkthrough-template.html"
    if not walk_template.exists():
        print("  Warning: walkthrough template not found, skipping")
        return

    from lib import web
    storage_key = game_name_from_conf(conf, walkthrough_path.parent)
    walk_html = deploy_dir / "walkthrough.html"
    force = conf.get("_force", False)
    if not walk_html.exists() or force:
        print("  Generating walkthrough.html...")
        web.substitute_template(
            walk_template, walk_html,
            {
                "__TITLE__": f"Walkthrough -- {conf['title']}",
                "__HEADER__": "Walkthrough",
                "__BACK_HREF__": "play.html",
                "__STORAGE_KEY__": storage_key,
            },
        )


def generate_index_html(deploy_dir: Path, conf: dict, name: str):
    """Generate index.html landing page if it doesn't exist."""
    index_html = deploy_dir / "index.html"
    if index_html.exists():
        return

    pages_script = TOOLS_DIR / "web" / "generate_pages.py"
    if pages_script.exists():
        print("  Generating index.html...")
        source_filename = Path(conf.get("source", "story.ni")).name
        subprocess.run(
            [sys.executable, str(pages_script),
             "--title", conf["title"],
             "--meta", conf.get("author", "An Interactive Fiction"),
             "--description", conf.get("description", "An interactive fiction game."),
             "--source-file", source_filename,
             "--out", str(deploy_dir)],
            check=False,
        )


# ── Registration ────────────────────────────────────────────────────────────

def register_game(name: str, conf: dict, deploy_dir: Path):
    """Add or update the game in games.json and cards.json."""
    games_path = SITE_DIR / "games.json"
    cards_path = SITE_DIR / "cards.json"

    engine = conf["engine"]
    title = conf["title"]
    tags = [t.strip() for t in conf.get("tags", "").split(",") if t.strip()]
    sound = conf.get("sound", "")
    has_sound = sound.lower() in ("yes", "true", "blorb")

    # Build games.json entry
    entry = {
        "id": name,
        "title": title,
        "playUrl": f"/{name}/play.html",
        "landingUrl": f"/{name}/",
        "sourceBrowser": True,
        "sourceUrl": f"/{name}/source.html",
        "engine": engine,
        "tags": tags,
    }
    if has_sound:
        entry["sound"] = "blorb"
    if conf.get("walkthrough"):
        entry["walkthroughUrl"] = f"/{name}/walkthrough.html"
    if conf.get("author"):
        entry["sourceLabel"] = conf.get("source", f"{name}.ni")

    # Update games.json
    games = json.loads(games_path.read_text(encoding="utf-8")) if games_path.exists() else []
    existing = next((i for i, g in enumerate(games) if g["id"] == name), None)
    if existing is not None:
        games[existing] = entry
        print(f"  games.json: updated '{name}'")
    else:
        games.append(entry)
        print(f"  games.json: added '{name}'")
    games_path.write_text(json.dumps(games, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Build cards.json entry
    card = {
        "id": name,
        "base": name,
        "title": title,
        "meta": conf.get("author", "An Interactive Fiction"),
        "description": conf.get("description", "An interactive fiction game."),
        "playUrl": f"/{name}/play.html",
        "landingUrl": f"/{name}/",
        "engine": engine,
        "tags": tags,
    }
    if has_sound:
        card["sound"] = "blorb"

    # Update cards.json
    cards = json.loads(cards_path.read_text(encoding="utf-8")) if cards_path.exists() else []
    existing = next((i for i, c in enumerate(cards) if c["id"] == name), None)
    if existing is not None:
        cards[existing] = card
        print(f"  cards.json: updated '{name}'")
    else:
        cards.append(card)
        print(f"  cards.json: added '{name}'")
    cards_path.write_text(json.dumps(cards, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ── Commands ────────────────────────────────────────────────────────────────

def cmd_import(args):
    """Import a built game into the jukebox."""
    from adapters import get_adapter

    game_dir = Path(args.path).resolve()
    conf = parse_conf(game_dir)
    conf["_force"] = args.force
    name = game_name_from_conf(conf, game_dir)
    engine = conf["engine"]

    print(f"Importing '{name}' (engine: {engine})")
    print(f"  Source: {game_dir}")

    # Resolve deploy directory (paths are relative to IFHUB_DIR)
    registry = load_registry()
    if name in registry and "deploy" in registry[name]:
        deploy_path = registry[name]["deploy"]
        if Path(deploy_path).is_absolute():
            deploy_dir = Path(deploy_path)
        else:
            deploy_dir = (IFHUB_DIR / deploy_path).resolve()
    else:
        # Default: ../text-games/<name>/
        deploy_dir = (IFHUB_DIR.parent / "text-games" / name).resolve()

    deploy_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Deploy: {deploy_dir}")

    # Run engine adapter
    adapter = get_adapter(engine)
    adapter.setup(game_dir, deploy_dir, conf)

    # Generate source.html
    source_name = conf.get("source")
    force = conf.get("_force", False)
    if source_name:
        source_path = deploy_dir / Path(source_name).name
        if not source_path.exists():
            source_path = game_dir / source_name
        if source_path.exists() and (force or not (deploy_dir / "source.html").exists()):
            generate_source_html(source_path, deploy_dir, conf)

    # Generate walkthrough.html
    walkthrough_name = conf.get("walkthrough")
    if walkthrough_name:
        # Check deploy dir first (adapter may have written walkthrough.txt there)
        walk_src = deploy_dir / "walkthrough.txt"
        if not walk_src.exists():
            walk_src = game_dir / walkthrough_name
        if walk_src.exists():
            # Copy to deploy dir if not already there
            walk_dest = deploy_dir / "walkthrough.txt"
            if walk_src != walk_dest:
                shutil.copy2(str(walk_src), str(walk_dest))
            generate_walkthrough_html(walk_dest, deploy_dir, conf)

    # Generate index.html
    generate_index_html(deploy_dir, conf, name)

    # Register in hub
    register_game(name, conf, deploy_dir)

    # Update registry (paths use forward slashes, relative to IFHUB_DIR)
    import os
    rel_deploy = Path(os.path.relpath(deploy_dir, IFHUB_DIR))
    registry[name] = {
        "deploy": str(rel_deploy).replace("\\", "/"),
        "source": str(game_dir).replace("\\", "/"),
        "repo": registry.get(name, {}).get("repo", ""),
    }
    save_registry(registry)

    print(f"\nImport complete: {name}")
    print(f"  Play: {deploy_dir / 'play.html'}")

    if args.ship:
        args.game = name
        cmd_publish(args)


def cmd_publish(args):
    """Publish a game to GitHub Pages."""
    name = args.game
    registry = load_registry()

    if name not in registry:
        print(f"Error: '{name}' not in registry", file=sys.stderr)
        sys.exit(1)

    deploy_path = registry[name].get("deploy", registry[name].get("path", ""))
    deploy_dir = Path(deploy_path) if Path(deploy_path).is_absolute() \
        else (IFHUB_DIR / deploy_path).resolve()

    if not deploy_dir.exists():
        print(f"Error: deploy directory not found: {deploy_dir}", file=sys.stderr)
        sys.exit(1)

    publish_script = TOOLS_DIR / "publish.py"
    if publish_script.exists():
        subprocess.run(
            [sys.executable, str(publish_script), name],
            check=True,
        )
    else:
        print(f"Error: publish.py not found at {publish_script}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args):
    """List all registered games."""
    registry = load_registry()
    if not registry:
        print("No games registered.")
        return

    print(f"{'Name':<30} {'Deploy':<40} {'Repo'}")
    print("-" * 100)
    for name, info in sorted(registry.items()):
        deploy = info.get("deploy", "?")
        repo = info.get("repo", "")
        print(f"{name:<30} {deploy:<40} {repo}")
    print(f"\n{len(registry)} games registered.")


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="IF Hub Jukebox — import, publish, and manage games.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # import
    p_import = sub.add_parser("import", help="Import a built game into the jukebox")
    p_import.add_argument("path", help="Path to game directory (must contain ifhub.conf)")
    p_import.add_argument("--force", action="store_true", help="Overwrite existing play.html")
    p_import.add_argument("--ship", action="store_true", help="Also publish after import")

    # publish
    p_publish = sub.add_parser("publish", help="Publish a game to GitHub Pages")
    p_publish.add_argument("game", help="Game name (as registered)")

    # list
    sub.add_parser("list", help="List all registered games")

    args = parser.parse_args()
    if args.command == "import":
        cmd_import(args)
    elif args.command == "publish":
        cmd_publish(args)
    elif args.command == "list":
        cmd_list(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
