#!/usr/bin/env python3
"""Rebuild site/cards.json from games.json + games-registry.json.

Collapses versioned-game groups into a single card with `versions:[...]`.
Preserves hand-edited card metadata (meta, description, tags, sound) by
reading the existing cards.json and merging.

A registry entry is part of a version group if any of:
    - versionOf: "<base-id>"          explicit
    - versionPrimary: true            marks the featured version of a group
    - naming-convention match         id matches "<base>-v?\\d+" and <base> is
                                       a primary id (explicit fields always win)

Usage:
    python tools/build_cards.py

Idempotent: running twice produces no diff.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import IFHUB_DIR, GAMES_REGISTRY


VERSION_SUFFIX_RE = re.compile(r"^(?P<base>.+?)-v?(?P<num>\d+)$")


def infer_base(game_id: str) -> tuple[str, int] | None:
    """If id looks like '<base>-v?NN', return (base, NN). Else None."""
    m = VERSION_SUFFIX_RE.match(game_id)
    if not m:
        return None
    return m.group("base"), int(m.group("num"))


def build_groups(registry: dict) -> tuple[dict[str, str], dict[str, dict]]:
    """Compute version-group membership from the registry.

    Returns:
        member_to_base: dict mapping every group-member id -> base id
        base_meta:      dict mapping base id -> {"primary_id": str,
                                                 "primary_label": str}
    """
    primaries: dict[str, dict] = {}
    explicit_members: list[tuple[str, str]] = []

    for gid, entry in registry.items():
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

    for gid in registry:
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


def load_json(path: Path) -> list | dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def main() -> None:
    games_path = IFHUB_DIR / "games.json"
    cards_path = IFHUB_DIR / "cards.json"

    games: list[dict] = load_json(games_path)
    cards_existing: list[dict] = load_json(cards_path) if cards_path.exists() else []
    registry: dict = load_json(GAMES_REGISTRY) if GAMES_REGISTRY.exists() else {}

    games_by_id = {g["id"]: g for g in games}
    cards_by_id = {c["id"]: c for c in cards_existing}
    reg_by_id = registry

    member_to_base, primaries = build_groups(registry)

    out_cards: list[dict] = []
    handled_ids: set[str] = set()

    # Emit one card per version group, using the primary's metadata.
    for base, meta in primaries.items():
        primary_id = meta["primary_id"]
        if primary_id not in games_by_id:
            print(f"  warn: primary '{primary_id}' not in games.json, skipping group")
            continue

        primary_game = games_by_id[primary_id]
        existing = cards_by_id.get(primary_id, {})
        members = [gid for gid, b in member_to_base.items()
                   if b == base and gid != primary_id]
        members_sorted = sorted(
            members,
            key=lambda g: version_order(g, reg_by_id.get(g, {})),
            reverse=True,
        )

        card: dict = {
            "id": primary_id,
            "base": primary_id,
            "title": primary_game.get("title") or existing.get("title", primary_id),
            "meta": existing.get("meta", "An Interactive Fiction"),
            "description": existing.get("description", ""),
            "primaryLabel": meta["primary_label"],
        }
        if primary_game.get("sound") or existing.get("sound"):
            card["sound"] = primary_game.get("sound") or existing.get("sound")
        card["playUrl"] = primary_game["playUrl"]
        # Group landing URL: derived from the deploy-dir name in the registry
        # (handles shared-repo groups whose primary game has no per-version
        # landingUrl in games.json — e.g., familyzoo-17 lives in /familyzoo/).
        primary_entry = reg_by_id.get(primary_id, {})
        primary_path = primary_entry.get("path", "")
        deploy_name = Path(primary_path).name if primary_path else primary_id
        group_landing = primary_game.get("landingUrl") or f"/{deploy_name}/"
        card["landingUrl"] = group_landing
        card["engine"] = primary_game.get("engine", existing.get("engine", "inform7"))
        card["tags"] = primary_game.get("tags", existing.get("tags", []))
        if primary_game.get("sourceUrl"):
            card["sourceUrl"] = primary_game["sourceUrl"]
        if primary_game.get("walkthroughUrl"):
            card["walkthroughUrl"] = primary_game["walkthroughUrl"]

        versions_list = []
        for mid in members_sorted:
            mgame = games_by_id.get(mid, {})
            mentry = reg_by_id.get(mid, {})
            v = {
                "id": mid,
                "label": version_label(mid, mentry, mgame),
                "playUrl": mgame.get("playUrl", f"/{mid}/play.html"),
                "landingUrl": f"{group_landing}#{mid}",
            }
            if mgame.get("sound"):
                v["sound"] = mgame["sound"]
            if mgame.get("sourceUrl"):
                v["sourceUrl"] = mgame["sourceUrl"]
            if mgame.get("walkthroughUrl"):
                v["walkthroughUrl"] = mgame["walkthroughUrl"]
            versions_list.append(v)
        if versions_list:
            card["versions"] = versions_list

        out_cards.append(card)
        handled_ids.add(primary_id)
        handled_ids.update(members)

    # Emit one card per standalone (non-versioned) game.
    for game in games:
        gid = game["id"]
        if gid in handled_ids:
            continue
        if gid in member_to_base:
            # Member of a group whose primary isn't in games.json — skip silently.
            continue

        existing = cards_by_id.get(gid, {})
        card = {
            "id": gid,
            "base": gid,
            "title": game.get("title") or existing.get("title", gid),
            "meta": existing.get("meta", "An Interactive Fiction"),
            "description": existing.get("description", ""),
        }
        if game.get("sound") or existing.get("sound"):
            card["sound"] = game.get("sound") or existing.get("sound")
        card["playUrl"] = game["playUrl"]
        if game.get("landingUrl"):
            card["landingUrl"] = game["landingUrl"]
        card["engine"] = game.get("engine", existing.get("engine", "inform7"))
        card["tags"] = game.get("tags", existing.get("tags", []))
        if game.get("sourceUrl"):
            card["sourceUrl"] = game["sourceUrl"]
        if game.get("walkthroughUrl"):
            card["walkthroughUrl"] = game["walkthroughUrl"]
        if existing.get("sourceBrowser"):
            card["sourceBrowser"] = True

        out_cards.append(card)
        handled_ids.add(gid)

    out_cards.sort(key=lambda c: c["id"])

    write_json(cards_path, out_cards)
    print(f"  cards.json: wrote {len(out_cards)} cards "
          f"({len(primaries)} versioned groups)")


if __name__ == "__main__":
    main()
