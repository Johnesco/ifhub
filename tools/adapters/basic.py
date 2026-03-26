"""BASIC adapter — embeds .bas source in engine-specific web player templates.

Supports: wwwbasic, bwbasic, applesoft, qbjc, jsdos.
"""

import shutil
from pathlib import Path

ENGINE_TEMPLATES = {
    "wwwbasic": "play-wwwbasic.html",
    "bwbasic": "play-bwbasic.html",
    "qbjc": "play-qbjc.html",
    "applesoft": "play-applesoft.html",
    "jsdos": "play-jsdos.html",
}

INLINE_SOURCE_ENGINES = {"wwwbasic", "bwbasic", "applesoft"}


def setup(game_dir: Path, deploy_dir: Path, conf: dict):
    """Import a BASIC game into the deploy directory."""
    engine = conf["engine"]
    title = conf["title"]
    force = conf.get("_force", False)
    script_dir = Path(__file__).resolve().parent.parent / "web"

    deploy_dir.mkdir(parents=True, exist_ok=True)

    # Resolve source/binary
    binary_name = conf.get("binary", "")
    source_name = conf.get("source", "")

    if engine in INLINE_SOURCE_ENGINES:
        # Source is inlined into play.html
        src_path = game_dir / (source_name or binary_name)
        if not src_path.exists():
            # Auto-detect .bas files
            bas_files = list(game_dir.glob("*.bas")) + list(game_dir.glob("*.BAS"))
            if not bas_files:
                src_dir = game_dir / "src" / "basic"
                bas_files = list(src_dir.glob("*.bas")) + list(src_dir.glob("*.BAS"))
            if bas_files:
                src_path = bas_files[0]
            else:
                raise FileNotFoundError(f"No .bas file found in {game_dir}")

        basic_source = src_path.read_text(encoding="utf-8", errors="replace")
        basic_source = basic_source.split("\x1a")[0]  # strip DOS EOF

        # Copy source to deploy dir
        shutil.copy2(str(src_path), str(deploy_dir / src_path.name))
        print(f"  Copied {src_path.name}")

    # Load template
    template_name = ENGINE_TEMPLATES.get(engine, ENGINE_TEMPLATES.get("wwwbasic"))
    local_template = game_dir / "play-template.html"
    if local_template.exists():
        template_path = local_template
        print(f"  Using project template: {local_template.name}")
    else:
        template_path = script_dir / "templates" / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    template = template_path.read_text(encoding="utf-8")
    html = template.replace("__TITLE__", title)
    html = html.replace("__VERSION_LABEL__", conf.get("version_label", ""))
    html = html.replace("__BACK_HREF__", "./")

    if engine in INLINE_SOURCE_ENGINES:
        html = html.replace("__BASIC_SOURCE__", basic_source)
    elif engine == "qbjc":
        compiled = game_dir / binary_name
        if compiled.exists():
            shutil.copy2(str(compiled), str(deploy_dir / compiled.name))
            print(f"  Copied {compiled.name}")
        html = html.replace("__COMPILED_JS__", Path(binary_name).name)
    elif engine == "jsdos":
        bundle = game_dir / binary_name
        if bundle.exists():
            shutil.copy2(str(bundle), str(deploy_dir / bundle.name))
            print(f"  Copied {bundle.name}")
        html = html.replace("__BUNDLE__", Path(binary_name).name)

    # Copy bwBASIC WASM runtime if needed
    if engine == "bwbasic":
        bw_src = script_dir.parent / "engines" / "bwbasic" / "wasm"
        bw_dest = deploy_dir / "lib" / "bwbasic"
        bw_dest.mkdir(parents=True, exist_ok=True)
        for fname in ("bwbasic.js", "bwbasic.wasm"):
            src = bw_src / fname
            if src.exists():
                shutil.copy2(str(src), str(bw_dest / fname))
                print(f"  Copied {fname}")

    # Write play.html
    play_html = deploy_dir / "play.html"
    if not play_html.exists() or force:
        play_html.write_text(html, encoding="utf-8")
        print(f"  Generated play.html ({engine})")
    else:
        print("  play.html exists, skipping")

    print(f"  BASIC adapter done: {deploy_dir}")
