#!/usr/bin/env python3
"""Register a game in IF Hub by flipping its ifhub.conf to `hub = yes`.

`ifhub.conf` is the single source of truth for a game's metadata. This
script finds the game's deploy dir, ensures the conf is complete and opted
in (`hub = yes`), then regenerates games.json + cards.json via build_games.py.

Usage:
    python tools/register_game.py --name <game> [--title ...] [--tags ...] ...

Any CLI flag that differs from the conf will be written into ifhub.conf,
so the conf stays authoritative.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import paths
import build_games


CONF_KEY_FROM_ARG = {
    "title": "title",
    "description": "description",
    "engine": "engine",
    "tags": "tags",
    "sound": "sound",
    "version_of": "versionOf",
    "version_label": "versionLabel",
    "version_order": "versionOrder",
    "version_primary": "versionPrimary",
    "version_primary_label": "versionPrimaryLabel",
}


def find_deploy_dir(name: str) -> Path | None:
    """Look up the game's deploy dir via workspaces + registry, same as build_games."""
    dirs = build_games.discover_game_dirs()
    if name in dirs:
        return dirs[name]
    # Fallback: check PROJECTS_DIR
    candidate = paths.PROJECTS_DIR / name
    if (candidate / "ifhub.conf").exists():
        return candidate
    return None


def read_conf_lines(conf_path: Path) -> list[str]:
    return conf_path.read_text(encoding="utf-8").splitlines() if conf_path.exists() else []


def upsert_conf_field(lines: list[str], key: str, value: str) -> list[str]:
    """Set `key = value` in the pre-section part of the conf. Appends if absent."""
    out: list[str] = []
    found = False
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_section = True
        if not in_section and "=" in line and not found:
            k = line.split("=", 1)[0].strip()
            if k == key:
                out.append(f"{key} = {value}")
                found = True
                continue
        out.append(line)
    if not found:
        # Insert before the first section, or at end.
        insert_at = len(out)
        for i, line in enumerate(out):
            s = line.strip()
            if s.startswith("[") and s.endswith("]"):
                insert_at = i
                break
        out.insert(insert_at, f"{key} = {value}")
    return out


def main():
    parser = argparse.ArgumentParser(description="Register a game in IF Hub.")
    parser.add_argument("--name", required=True, help="Project directory name")
    parser.add_argument("--title", default=None, help="Display title")
    parser.add_argument("--meta", default=None, help="Subtitle (cards.json only)")
    parser.add_argument("--description", default=None, help="Description")
    parser.add_argument("--sound", default=None, help="Sound type: 'blorb' or empty")
    parser.add_argument("--engine", default=None, help="Engine type")
    parser.add_argument("--tags", default=None, help="Comma-separated tags")
    parser.add_argument("--version-of", default=None, dest="version_of")
    parser.add_argument("--version-label", default=None, dest="version_label")
    parser.add_argument("--version-order", type=int, default=None, dest="version_order")
    parser.add_argument("--version-primary", action="store_true", dest="version_primary")
    parser.add_argument("--version-primary-label", default=None,
                        dest="version_primary_label")
    args = parser.parse_args()

    name = args.name
    deploy_dir = find_deploy_dir(name)
    if deploy_dir is None:
        print(f"ERROR: no ifhub.conf found for '{name}' in any workspace.", file=sys.stderr)
        print(f"  Create one at <project-dir>/ifhub.conf first.", file=sys.stderr)
        sys.exit(1)

    conf_path = deploy_dir / "ifhub.conf"
    lines = read_conf_lines(conf_path)

    # Apply CLI overrides to the conf.
    for arg_name, conf_key in CONF_KEY_FROM_ARG.items():
        val = getattr(args, arg_name)
        if val is None or val == "":
            continue
        if arg_name == "version_primary":
            if val:
                lines = upsert_conf_field(lines, conf_key, "yes")
            continue
        if arg_name == "version_order":
            lines = upsert_conf_field(lines, conf_key, str(val))
            continue
        lines = upsert_conf_field(lines, conf_key, str(val))

    # Always ensure hub = yes.
    lines = upsert_conf_field(lines, "hub", "yes")

    new_text = "\n".join(lines)
    if not new_text.endswith("\n"):
        new_text += "\n"
    if new_text != conf_path.read_text(encoding="utf-8"):
        conf_path.write_text(new_text, encoding="utf-8")
        print(f"  updated {conf_path.relative_to(paths.I7_ROOT)}")
    else:
        print(f"  no conf changes needed for {name}")

    # Regenerate derived files (games.json + cards.json).
    build_games.main()

    print(f"\nDone. Next: publish to GitHub Pages with:")
    print(f"  python tools/publish.py {name}")


if __name__ == "__main__":
    main()
