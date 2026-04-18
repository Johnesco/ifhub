#!/usr/bin/env python3
"""Rebuild site/games.json from ifhub.conf files + workspace scan + disk probing.

`ifhub.conf` is the single source of truth for every game's metadata. This
script walks all registered deploy directories (discovered via workspaces.json
plus any overrides in games-registry.json), parses each `ifhub.conf`, and
emits one games.json entry per game. A game's conf may declare one or more
`[target.<id>]` sections for multi-target layouts (e.g., Sharpee's familyzoo
ships 17 tutorial versions from one repo at subpaths /v01/.../v17/).

URLs (playUrl, landingUrl, sourceUrl, walkthroughUrl, testsUrl) are computed
from the deploy directory name + optional `subpath`. Each URL is probed on
disk and only emitted if the target file exists — same logic check_links.py
uses in reverse. `playUrl` is always emitted (a missing play.html is a build
bug, not a data bug).

Usage:
    python tools/build_games.py

Idempotent: running twice produces no diff. push_hub.py runs this before
build_cards.py so games.json and cards.json always agree.
"""

from __future__ import annotations

import configparser
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import (
    IFHUB_DIR, GAMES_REGISTRY, WORKSPACES_FILE, I7_ROOT,
)


TRUE_VALUES = {"yes", "true", "1", "on"}


def as_bool(val: str | None) -> bool:
    return (val or "").strip().lower() in TRUE_VALUES


def resolve_path(raw: str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = (I7_ROOT / p).resolve()
    return p


# ── Config parsing ──────────────────────────────────────────────────────────

def parse_conf(path: Path) -> tuple[dict, dict[str, dict]]:
    """Parse ifhub.conf into (parent, targets).

    Top-level KEY=VALUE lines become the parent dict. `[target.<id>]` sections
    become target dicts that inherit parent fields. If there are no target
    sections, targets is empty and the game is single-target.
    """
    text = path.read_text(encoding="utf-8")
    parent_lines: list[str] = []
    section_lines: list[str] = []
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_section = True
            section_lines.append(line)
        elif in_section:
            section_lines.append(line)
        else:
            parent_lines.append(line)

    merged = "[DEFAULT]\n" + "\n".join(parent_lines)
    if section_lines:
        merged += "\n" + "\n".join(section_lines)

    cp = configparser.ConfigParser()
    cp.optionxform = str
    cp.read_string(merged)

    parent = {k: v for k, v in cp.defaults().items()}
    targets: dict[str, dict] = {}
    for section in cp.sections():
        if section.startswith("target."):
            tid = section[len("target."):]
            targets[tid] = {k: v for k, v in cp[section].items()}
    return parent, targets


# ── Game discovery ──────────────────────────────────────────────────────────

def discover_game_dirs() -> dict[str, Path]:
    """Return dict mapping the deploy-dir basename to its absolute path.

    Walks each workspace root from workspaces.json and collects any immediate
    subdirectory containing an ifhub.conf. Registry entries with non-workspace
    paths (e.g., `../npmsharpee/from-fork/*`) are layered on top so games
    outside the declared workspaces still get picked up.
    """
    dirs: dict[str, Path] = {}

    if WORKSPACES_FILE.exists():
        try:
            ws_data = json.loads(WORKSPACES_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            ws_data = {"workspaces": []}
        for ws in ws_data.get("workspaces", []):
            root = resolve_path(ws.get("root", ""))
            if not root.is_dir():
                continue
            for sub in sorted(root.iterdir()):
                if not sub.is_dir():
                    continue
                if (sub / "ifhub.conf").exists():
                    dirs[sub.name] = sub

    if GAMES_REGISTRY.exists():
        try:
            registry = json.loads(GAMES_REGISTRY.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            registry = {}
        # Collect unique deploy paths (the same path may back many entries in
        # the legacy familyzoo layout — de-dupe by resolved path).
        seen: set[Path] = set()
        for entry in registry.values():
            raw = entry.get("path", "")
            if not raw:
                continue
            resolved = resolve_path(raw)
            if resolved in seen or not resolved.is_dir():
                continue
            seen.add(resolved)
            if (resolved / "ifhub.conf").exists():
                dirs.setdefault(resolved.name, resolved)

    return dirs


# ── Entry building ──────────────────────────────────────────────────────────

# Fields passed through unchanged from conf → games.json entry (straight copy).
# Left side is the conf key, right side the games.json key.
PASSTHROUGH_STRING_FIELDS = {
    "sourceLabel": "sourceLabel",
    "overlayLabel": "overlayLabel",
    "versionLabel": "versionLabel",
    "versionPrimaryLabel": "versionPrimaryLabel",
}


def parse_tags(raw: str) -> list[str]:
    return [t.strip() for t in raw.split(",") if t.strip()]


ENGINE_SOURCE_EXT = {
    "inform7": ".ni",
    "sharpee": ".ts",
    "ink": ".ink",
    "rez": ".rez",
    "wwwbasic": ".bas",
    "qbjc": ".bas",
    "applesoft": ".bas",
    "zmachine": ".zil",
}


def derive_source_label(conf: dict, fallback_id: str) -> str:
    """Sensible fallback if ifhub.conf doesn't set sourceLabel explicitly."""
    source = conf.get("source", "")
    if source:
        return Path(source).name
    ext = ENGINE_SOURCE_EXT.get(conf.get("engine", ""), ".ni")
    return f"{fallback_id}{ext}"


def build_entry(game_id: str, conf: dict, deploy_dir: Path,
                url_prefix: str) -> dict:
    """Turn a resolved conf dict into a games.json entry.

    `url_prefix` is the path fragment prepended to per-file URLs — e.g.
    '/familyzoo/v01' for a multi-target game, '/zork1' for a top-level one.
    """
    entry: dict = {
        "id": game_id,
        "title": conf.get("title", game_id),
    }

    # sourceLabel: explicit override > derived from source field
    src_label = conf.get("sourceLabel") or derive_source_label(conf, game_id)
    entry["sourceLabel"] = src_label

    sound = conf.get("sound", "").strip().lower()
    if sound:
        # "yes"/"true" → "blorb" (the legacy value); explicit "blorb" preserved
        entry["sound"] = "blorb" if sound in TRUE_VALUES else sound

    if "overlayLabel" in conf:
        entry["overlayLabel"] = conf["overlayLabel"]

    if "versionLabel" in conf:
        entry["versionLabel"] = conf["versionLabel"]
    if "versionPrimaryLabel" in conf:
        entry["versionPrimaryLabel"] = conf["versionPrimaryLabel"]

    entry["playUrl"] = f"{url_prefix}/play.html"

    # Probe root: some engines (e.g., Sharpee) deploy assets under a
    # `browser/` subdir that GH Pages serves at the repo root, so disk
    # paths don't match URL paths. If browser/play.html exists, probe
    # from there; otherwise probe the deploy dir directly.
    probe_root = deploy_dir / "browser" if (deploy_dir / "browser" / "play.html").exists() else deploy_dir

    walkthrough_html = probe_root / "walkthrough.html"
    if walkthrough_html.exists():
        entry["walkthroughUrl"] = f"{url_prefix}/walkthrough.html"

    tests_html = probe_root / "tests.html"
    if tests_html.exists():
        entry["testsUrl"] = f"{url_prefix}/tests.html"

    landing_html = probe_root / "index.html"
    if landing_html.exists():
        entry["landingUrl"] = f"{url_prefix}/"

    # sourceBrowser defaults ON. Absent ifhub.conf key = default. Explicit
    # `sourceBrowser = no` turns it off (raw-source URL like /zork1/story.ni).
    raw_sb = conf.get("sourceBrowser")
    if raw_sb is None:
        source_browser = True
    else:
        source_browser = as_bool(raw_sb)

    source_html = probe_root / "source.html"
    if source_browser and source_html.exists():
        entry["sourceBrowser"] = True
        entry["sourceUrl"] = f"{url_prefix}/source.html"
    elif conf.get("source"):
        # Keep the full relative path (e.g. src/cloak_of_darkness.rez) — some
        # engines point at a subfolder source; the URL must match.
        src_rel = conf["source"].replace("\\", "/").strip("/")
        src_path = probe_root / src_rel
        if src_path.exists():
            entry["sourceUrl"] = f"{url_prefix}/{src_rel}"
        elif source_html.exists():
            entry["sourceBrowser"] = True
            entry["sourceUrl"] = f"{url_prefix}/source.html"

    engine = conf.get("engine", "")
    if engine:
        entry["engine"] = engine
    entry["tags"] = parse_tags(conf.get("tags", ""))

    # Version flags (for build_cards.py grouping)
    if "versionOf" in conf:
        entry["versionOf"] = conf["versionOf"]
    if as_bool(conf.get("versionPrimary")):
        entry["versionPrimary"] = True
    if "versionOrder" in conf:
        try:
            entry["versionOrder"] = int(conf["versionOrder"])
        except ValueError:
            pass

    return entry


def build_entries_for_dir(deploy_dir: Path) -> list[dict]:
    """Return every games.json entry contributed by one deploy dir.

    A game (or target) must set `hub = yes` in its ifhub.conf to be listed.
    This is the explicit opt-in that replaces games-registry.json as the
    'which games appear in the hub' signal.
    """
    conf_path = deploy_dir / "ifhub.conf"
    parent, targets = parse_conf(conf_path)
    deploy_name = deploy_dir.name

    if not targets:
        if not as_bool(parent.get("hub")):
            return []
        # Single-target: id comes from the deploy dir name. (The conf's
        # optional `name` field is cosmetic, left for human reference.)
        url_prefix = f"/{deploy_name}"
        return [build_entry(deploy_name, parent, deploy_dir, url_prefix)]

    # For multi-target games, assets may live under a `browser/` subdir
    # (e.g., Sharpee). Resolve that once so every target probes correctly.
    asset_root = deploy_dir / "browser" if (deploy_dir / "browser").is_dir() else deploy_dir

    out: list[dict] = []
    for tid, tconf in targets.items():
        if not as_bool(tconf.get("hub")):
            continue
        subpath = tconf.get("subpath", "").strip("/")
        if subpath:
            target_deploy = asset_root / subpath
            url_prefix = f"/{deploy_name}/{subpath}"
        else:
            target_deploy = asset_root
            url_prefix = f"/{deploy_name}"
        out.append(build_entry(tid, tconf, target_deploy, url_prefix))
    return out


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    games_path = IFHUB_DIR / "games.json"

    dirs = discover_game_dirs()
    all_entries: list[dict] = []
    for deploy_dir in dirs.values():
        try:
            all_entries.extend(build_entries_for_dir(deploy_dir))
        except (OSError, configparser.Error) as e:
            print(f"  warn: could not parse {deploy_dir}/ifhub.conf: {e}")

    all_entries.sort(key=lambda e: e["id"])

    games_path.write_text(
        json.dumps(all_entries, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"  games.json: wrote {len(all_entries)} entries "
          f"from {len(dirs)} deploy dir(s)")


if __name__ == "__main__":
    main()
