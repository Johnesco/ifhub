#!/usr/bin/env python3
"""Rebuild site/games.json and site/cards.json from ifhub.conf files.

`ifhub.conf` is the single source of truth for every game's metadata. This
script walks every game folder under the workspaces.json roots, parses each
`ifhub.conf`, and emits one games.json entry per game (title, author,
description, tags, URLs). It then collapses versioned groups into cards.json
for the landing page. Nothing in either file is hand-maintained.

URLs (playUrl, landingUrl, sourceUrl, walkthroughUrl, testsUrl) are computed
from the deploy directory name. Each URL is probed on
disk and only emitted if the target file exists — same logic check_links.py
uses in reverse. `playUrl` is always emitted (a missing play.html is a build
bug, not a data bug).

Usage:
    python tools/build_games.py

Idempotent: running twice produces no diff.
"""

from __future__ import annotations

import configparser
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import paths
from lib.paths import SITE_DIR


TRUE_VALUES = {"yes", "true", "1", "on"}


def as_bool(val: str | None) -> bool:
    return (val or "").strip().lower() in TRUE_VALUES


# ── Config parsing ──────────────────────────────────────────────────────────

def parse_conf(path: Path) -> dict:
    """Parse ifhub.conf (flat `key = value` lines) into a dict.

    Section headers are not supported. Anything after the first `[section]`
    line is ignored with a warning.
    """
    text = path.read_text(encoding="utf-8")
    body_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            print(f"  warn: {path} has a [section] header; sections are not "
                  f"supported and everything after it is ignored")
            break
        body_lines.append(line)

    cp = configparser.ConfigParser()
    cp.optionxform = str
    cp.read_string("[DEFAULT]\n" + "\n".join(body_lines))
    return dict(cp.defaults())


# ── Game discovery ──────────────────────────────────────────────────────────

def discover_game_dirs() -> dict[str, Path]:
    """folder name -> game folder for every ifhub.conf under the workspaces.json roots."""
    return paths.discover_games()


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

    `url_prefix` is the path fragment prepended to per-file URLs, e.g. '/zork1'.
    """
    entry: dict = {
        "id": game_id,
        "title": conf.get("title", game_id),
    }
    if conf.get("author"):
        entry["author"] = conf["author"]
    if conf.get("description"):
        entry["description"] = conf["description"]

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

    probe_root = deploy_dir

    # The hub renders walkthroughs itself (site/walkthrough.html) from the raw
    # files at the game root; walkthroughUrl names the commands file (or the guide
    # when a game only ships the annotated guide).
    for wt_name in ("walkthrough.txt", "walkthrough-guide.txt"):
        if (probe_root / wt_name).exists():
            entry["walkthroughUrl"] = f"{url_prefix}/{wt_name}"
            break

    tests_html = probe_root / "tests.html"
    if tests_html.exists():
        entry["testsUrl"] = f"{url_prefix}/tests.html"

    landing_html = probe_root / "index.html"
    if landing_html.exists():
        entry["landingUrl"] = f"{url_prefix}/"

    # The hub renders source itself from the raw file named by `source =`.
    # `sourceBrowser = yes` is an explicit opt-in for games that ship their own
    # source.html (e.g. a multi-file ZIL browser); it is never inferred.
    source_html = probe_root / "source.html"
    if as_bool(conf.get("sourceBrowser")) and source_html.exists():
        entry["sourceBrowser"] = True
        entry["sourceUrl"] = f"{url_prefix}/source.html"
    elif conf.get("source"):
        src_rel = conf["source"].replace("\\", "/").strip("/")
        if (probe_root / src_rel).is_file():
            entry["sourceUrl"] = f"{url_prefix}/{src_rel}"

    engine = conf.get("engine", "")
    if engine:
        entry["engine"] = engine
    entry["tags"] = parse_tags(conf.get("tags", ""))

    # Version flags (for cards.json grouping)
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
    """Return the games.json entry contributed by one deploy dir (0 or 1).

    A game must set `hub = yes` in its ifhub.conf to be listed; that flag is
    the only 'which games appear in the hub' signal.
    """
    conf = parse_conf(deploy_dir / "ifhub.conf")
    if not as_bool(conf.get("hub")):
        return []
    # The id comes from the deploy dir name. (The conf's optional `name`
    # field is cosmetic, left for human reference.)
    deploy_name = deploy_dir.name
    return [build_entry(deploy_name, conf, deploy_dir, f"/{deploy_name}")]


# ── Cards (version-group collapsing) ───────────────────────────────────────

VERSION_SUFFIX_RE = re.compile(r"^(?P<base>.+?)-v?(?P<num>\d+)$")


def infer_base(game_id: str) -> tuple[str, int] | None:
    """If id looks like '<base>-v?NN', return (base, NN). Else None."""
    m = VERSION_SUFFIX_RE.match(game_id)
    if not m:
        return None
    return m.group("base"), int(m.group("num"))


def build_groups(games_by_id: dict) -> tuple[dict[str, str], dict[str, dict]]:
    """Compute version-group membership from games.json entries.

    Returns:
        member_to_base: dict mapping every group-member id -> base id
        base_meta:      dict mapping base id -> {"primary_id": str,
                                                 "primary_label": str}
    """
    primaries: dict[str, dict] = {}
    explicit_members: list[tuple[str, str]] = []

    for gid, entry in games_by_id.items():
        if entry.get("versionPrimary"):
            base = entry.get("versionOf") or gid
            primaries[base] = {
                "primary_id": gid,
                "primary_label": entry.get("versionPrimaryLabel", "Current"),
            }
        if "versionOf" in entry:
            explicit_members.append((gid, entry["versionOf"]))

    member_to_base: dict[str, str] = {}
    for gid, base in explicit_members:
        member_to_base[gid] = base
    for base, meta in primaries.items():
        member_to_base[meta["primary_id"]] = base

    for gid in games_by_id:
        if gid in member_to_base:
            continue
        inferred = infer_base(gid)
        if inferred is None:
            continue
        base, _ = inferred
        if base in primaries:
            member_to_base[gid] = base

    return member_to_base, primaries


def version_order(gid: str, entry: dict) -> int:
    if "versionOrder" in entry:
        return int(entry["versionOrder"])
    inferred = infer_base(gid)
    if inferred:
        return inferred[1]
    return 0


def version_label(gid: str, entry: dict, game_meta: dict) -> str:
    if entry.get("versionLabel"):
        return entry["versionLabel"]
    title = game_meta.get("title") or gid
    inferred = infer_base(gid)
    if inferred:
        _, num = inferred
        suffix = f"v{num:02d}" if num < 100 else f"v{num}"
        if suffix.lower() in title.lower():
            return title
        return f"{suffix} — {title}"
    return title


def _build_cards(games: list[dict]) -> list[dict]:
    """Collapse versioned game groups into landing-page cards (fully derived from games)."""
    games_by_id = {g["id"]: g for g in games}

    member_to_base, primaries = build_groups(games_by_id)

    out_cards: list[dict] = []
    handled_ids: set[str] = set()

    for base, meta in primaries.items():
        primary_id = meta["primary_id"]
        if primary_id not in games_by_id:
            print(f"  warn: primary '{primary_id}' not in games.json, skipping group")
            continue

        primary_game = games_by_id[primary_id]
        members = [gid for gid, b in member_to_base.items()
                   if b == base and gid != primary_id]
        members_sorted = sorted(
            members,
            key=lambda g: version_order(g, games_by_id.get(g, {})),
            reverse=True,
        )

        card: dict = {
            "id": primary_id,
            "base": primary_id,
            "title": primary_game.get("title", primary_id),
            "meta": primary_game.get("author") or "An Interactive Fiction",
            "description": primary_game.get("description", ""),
            "primaryLabel": meta["primary_label"],
        }
        if primary_game.get("sound"):
            card["sound"] = primary_game["sound"]
        card["playUrl"] = primary_game["playUrl"]
        play_segments = primary_game["playUrl"].strip("/").split("/")
        deploy_name = play_segments[0] if play_segments else primary_id
        group_landing = f"/{deploy_name}/"
        card["landingUrl"] = group_landing
        card["engine"] = primary_game.get("engine", "inform7")
        card["tags"] = primary_game.get("tags", [])
        if primary_game.get("sourceUrl"):
            card["sourceUrl"] = primary_game["sourceUrl"]
        if primary_game.get("walkthroughUrl"):
            card["walkthroughUrl"] = primary_game["walkthroughUrl"]
        if primary_game.get("testsUrl"):
            card["testsUrl"] = primary_game["testsUrl"]

        versions_list = []
        for mid in members_sorted:
            mgame = games_by_id.get(mid, {})
            v = {
                "id": mid,
                "label": version_label(mid, mgame, mgame),
                "playUrl": mgame.get("playUrl", f"/{mid}/play.html"),
                "landingUrl": f"{group_landing}#{mid}",
            }
            if mgame.get("sound"):
                v["sound"] = mgame["sound"]
            if mgame.get("sourceUrl"):
                v["sourceUrl"] = mgame["sourceUrl"]
            if mgame.get("walkthroughUrl"):
                v["walkthroughUrl"] = mgame["walkthroughUrl"]
            if mgame.get("testsUrl"):
                v["testsUrl"] = mgame["testsUrl"]
            versions_list.append(v)
        if versions_list:
            card["versions"] = versions_list

        out_cards.append(card)
        handled_ids.add(primary_id)
        handled_ids.update(members)

    for game in games:
        gid = game["id"]
        if gid in handled_ids or gid in member_to_base:
            continue

        card = {
            "id": gid,
            "base": gid,
            "title": game.get("title", gid),
            "meta": game.get("author") or "An Interactive Fiction",
            "description": game.get("description", ""),
        }
        if game.get("sound"):
            card["sound"] = game["sound"]
        card["playUrl"] = game["playUrl"]
        if game.get("landingUrl"):
            card["landingUrl"] = game["landingUrl"]
        card["engine"] = game.get("engine", "inform7")
        card["tags"] = game.get("tags", [])
        if game.get("sourceUrl"):
            card["sourceUrl"] = game["sourceUrl"]
        if game.get("walkthroughUrl"):
            card["walkthroughUrl"] = game["walkthroughUrl"]
        if game.get("testsUrl"):
            card["testsUrl"] = game["testsUrl"]

        out_cards.append(card)
        handled_ids.add(gid)

    out_cards.sort(key=lambda c: c["id"])
    return out_cards


# ── Main ────────────────────────────────────────────────────────────────────

def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def main() -> None:
    games_path = SITE_DIR / "games.json"
    cards_path = SITE_DIR / "cards.json"

    dirs = discover_game_dirs()
    all_entries: list[dict] = []
    for deploy_dir in dirs.values():
        try:
            all_entries.extend(build_entries_for_dir(deploy_dir))
        except (OSError, configparser.Error) as e:
            print(f"  warn: could not parse {deploy_dir}/ifhub.conf: {e}")

    all_entries.sort(key=lambda e: e["id"])

    _write_json(games_path, all_entries)
    print(f"  games.json: wrote {len(all_entries)} entries "
          f"from {len(dirs)} deploy dir(s)")

    cards = _build_cards(all_entries)
    _write_json(cards_path, cards)
    print(f"  cards.json: wrote {len(cards)} cards")


if __name__ == "__main__":
    main()
