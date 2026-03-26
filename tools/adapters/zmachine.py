"""Z-machine adapter — wraps .z3/.z5 binaries in a Parchment web player."""

from pathlib import Path


def setup(game_dir: Path, deploy_dir: Path, conf: dict):
    """Import a Z-machine game into the deploy directory."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from lib import web

    binary_name = conf["binary"]
    binary_path = game_dir / binary_name

    # Z-machine binaries may already be .js wrapped
    if not binary_path.exists():
        raise FileNotFoundError(f"Binary not found: {binary_path}")

    title = conf["title"]

    parchment_dir = deploy_dir / "lib" / "parchment"
    parchment_dir.mkdir(parents=True, exist_ok=True)

    print("  Copying Parchment libraries...")
    web.copy_parchment_libs(parchment_dir)

    # If binary is already a .js file (pre-wrapped), just copy it
    if binary_path.suffix == ".js":
        import shutil
        dest = deploy_dir / binary_name
        shutil.copy2(str(binary_path), str(dest))
        story_js = binary_name
        print(f"  Copied {binary_name}")
    else:
        story_js = f"{binary_name}.js"
        print(f"  Encoding {binary_name} -> {story_js}...")
        web.write_story_js(binary_path, parchment_dir / story_js)

    # Generate play.html
    template_path = Path(__file__).resolve().parent.parent / "web" / "play-template.html"
    play_html = deploy_dir / "play.html"
    force = conf.get("_force", False)

    if not play_html.exists() or force:
        print("  Generating play.html...")
        web.substitute_template(
            template_path, play_html,
            {
                "__TITLE__": title,
                "__STORY_FILE__": story_js,
                "__STORY_PATH__": story_js if "/" in story_js else f"lib/parchment/{story_js}",
                "__LIB_PATH__": "lib/parchment/",
            },
            cache_bust=True,
        )
    else:
        print("  play.html exists, skipping")

    # Copy source files (ZIL)
    source_name = conf.get("source")
    if source_name:
        import shutil
        src = game_dir / source_name
        if src.is_dir():
            dest = deploy_dir / src.name
            if dest.exists():
                shutil.rmtree(str(dest))
            shutil.copytree(str(src), str(dest))
            print(f"  Copied {source_name}/")
        elif src.exists():
            shutil.copy2(str(src), str(deploy_dir / src.name))
            print(f"  Copied {source_name}")

    print(f"  Z-machine adapter done: {deploy_dir}")
