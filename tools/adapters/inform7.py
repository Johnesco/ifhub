"""Inform 7 adapter — wraps compiled .ulx/.gblorb in a Parchment web player."""

from pathlib import Path


def setup(game_dir: Path, deploy_dir: Path, conf: dict):
    """Import a built Inform 7 game into the deploy directory.

    Expects game_dir to contain a compiled .ulx or .gblorb binary
    (specified by conf['binary']).

    Produces in deploy_dir:
        play.html           — Parchment web player
        lib/parchment/*.js  — Shared Parchment libraries
        lib/parchment/<game>.js — Base64-encoded game binary
        story.ni            — Source copy (if conf['source'] provided)
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from lib import web, output

    binary_name = conf["binary"]
    binary_path = game_dir / binary_name
    if not binary_path.exists():
        raise FileNotFoundError(f"Binary not found: {binary_path}")

    title = conf["title"]
    is_blorb = binary_path.suffix == ".gblorb"
    has_sound = conf.get("sound", "").lower() in ("yes", "true", "blorb")
    has_mood = conf.get("mood", "").lower() in ("yes", "true")

    # Create lib/parchment/
    parchment_dir = deploy_dir / "lib" / "parchment"
    parchment_dir.mkdir(parents=True, exist_ok=True)

    # Copy Parchment libraries
    print("  Copying Parchment libraries...")
    web.copy_parchment_libs(parchment_dir)

    # Copy mood engine if needed
    if has_mood:
        print("  Copying mood-engine.js...")
        web.copy_mood_engine(parchment_dir)

    # Base64-encode game binary
    story_js = f"{binary_name}.js"
    print(f"  Encoding {binary_name} -> {story_js}...")
    web.write_story_js(binary_path, parchment_dir / story_js)

    # Select template
    templates_dir = Path(__file__).resolve().parent.parent / "web" / "templates"
    play_template = conf.get("play_template")
    if play_template:
        template_path = game_dir / play_template
    elif has_mood:
        template_path = templates_dir / "play-mood.html"
    else:
        template_path = Path(__file__).resolve().parent.parent / "web" / "play-template.html"

    # Generate play.html (skip if exists and has custom overlay, unless forced)
    play_html = deploy_dir / "play.html"
    force = conf.get("_force", False)
    if not play_html.exists() or force:
        print("  Generating play.html...")
        web.substitute_template(
            template_path, play_html,
            {
                "__TITLE__": title,
                "__STORY_FILE__": story_js,
                "__STORY_PATH__": f"lib/parchment/{story_js}",
                "__LIB_PATH__": "lib/parchment/",
            },
            cache_bust=True,
        )
    else:
        print("  play.html exists, skipping (use --force to overwrite)")

    # Copy source file
    source_name = conf.get("source")
    if source_name:
        src = game_dir / source_name
        if src.exists():
            import shutil
            dest = deploy_dir / src.name
            shutil.copy2(str(src), str(dest))
            print(f"  Copied {source_name}")

    print(f"  Inform 7 adapter done: {deploy_dir}")
