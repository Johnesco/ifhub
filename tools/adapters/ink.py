"""Ink adapter — wraps compiled .json story in an ink.js web player."""

import shutil
from pathlib import Path


def setup(game_dir: Path, deploy_dir: Path, conf: dict):
    """Import a built Ink game into the deploy directory."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from lib import web

    binary_name = conf["binary"]
    binary_path = game_dir / binary_name
    if not binary_path.exists():
        raise FileNotFoundError(f"Binary not found: {binary_path}")

    title = conf["title"]
    force = conf.get("_force", False)
    script_dir = Path(__file__).resolve().parent.parent / "web"

    deploy_dir.mkdir(parents=True, exist_ok=True)

    # Copy story JSON to deploy dir
    dest_json = deploy_dir / binary_path.name
    shutil.copy2(str(binary_path), str(dest_json))
    print(f"  Copied {binary_path.name}")

    # Copy theme-listener.js
    tl_src = script_dir / "parchment" / "theme-listener.js"
    tl_dest = deploy_dir / "theme-listener.js"
    if tl_src.exists():
        shutil.copy2(str(tl_src), str(tl_dest))
        print("  Copied theme-listener.js")

    # Generate play.html from ink template
    template_path = script_dir / "templates" / "play-ink.html"
    play_html = deploy_dir / "play.html"

    if (not play_html.exists() or force) and template_path.exists():
        story_data = binary_path.read_text(encoding="utf-8").strip()
        template = template_path.read_text(encoding="utf-8")
        html = template.replace("__TITLE__", title)
        html = html.replace("__STORY_DATA__", story_data)
        play_html.write_text(html, encoding="utf-8")
        print("  Generated play.html")
    elif play_html.exists():
        print("  play.html exists, skipping")

    # Copy source file
    source_name = conf.get("source")
    if source_name:
        src = game_dir / source_name
        if src.exists():
            shutil.copy2(str(src), str(deploy_dir / src.name))
            print(f"  Copied {source_name}")

    print(f"  Ink adapter done: {deploy_dir}")
