#!/usr/bin/env python3
"""Scan every link in site/games.json and site/cards.json; report 404s.

For each URL, resolves to a local file in the game's own repo via
the workspaces.json scan and checks whether the file exists on disk.

By default only reports. With --fix, removes broken URLs from games.json
and cards.json (only sourceUrl/walkthroughUrl/landingUrl — playUrl is never
removed, since a missing play.html is always a build problem, not a data
problem).

Usage:
    python tools/check_links.py
    python tools/check_links.py --fix
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import SITE_DIR, HUB_ROOT
import build_games


FIELDS = ("playUrl", "landingUrl", "sourceUrl", "walkthroughUrl")


def resolve_path(raw: str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = (HUB_ROOT / p).resolve()
    return p


def build_segment_index() -> dict[str, list[Path]]:
    """Map URL first-segment (e.g., 'zork1') to candidate deploy-dir paths.

    Uses the same workspace scanner build_games.py uses, so the resolver
    always matches what the build pipeline actually publishes.
    """
    idx: dict[str, list[Path]] = {}
    for name, path in build_games.discover_game_dirs().items():
        if not path.exists():
            continue
        idx.setdefault(name, [])
        if path not in idx[name]:
            idx[name].append(path)
    return idx


def resolve_local(url: str, seg_idx: dict[str, list[Path]]) -> tuple[Path | None, list[Path]]:
    """Return (existing_local_file, tried_paths). None if nothing exists."""
    if not url or not url.startswith("/"):
        return None, []
    parts = url.strip("/").split("/")
    if not parts:
        return None, []
    segment = parts[0]
    rest = "/".join(parts[1:]) if len(parts) > 1 else ""
    repo_paths = seg_idx.get(segment, [])
    tried: list[Path] = []

    for repo_path in repo_paths:
        # Directory URL (trailing /) -> index.html
        target_rest = rest if rest else "index.html"
        if target_rest.endswith("/"):
            target_rest += "index.html"

        candidate = repo_path / target_rest
        tried.append(candidate)
        if candidate.exists():
            return candidate, tried
    return None, tried


def scan(data: list[dict], seg_idx: dict[str, list[Path]],
         label: str) -> list[tuple[str, str, str]]:
    """Return list of (game_id, field, url) for each broken link."""
    broken: list[tuple[str, str, str]] = []
    for entry in data:
        gid = entry.get("id", "?")
        for field in FIELDS:
            url = entry.get(field)
            if not url:
                continue
            found, _ = resolve_local(url, seg_idx)
            if found is None:
                broken.append((gid, field, url))
        for v in entry.get("versions", []) or []:
            vid = v.get("id", "?")
            url = v.get("playUrl")
            if not url:
                continue
            found, _ = resolve_local(url, seg_idx)
            if found is None:
                broken.append((f"{gid}/versions/{vid}", "playUrl", url))
    return broken


def fix(data: list[dict], seg_idx: dict[str, list[Path]]) -> int:
    """Remove broken sourceUrl/walkthroughUrl/landingUrl entries. Return count removed."""
    removed = 0
    removable_fields = ("sourceUrl", "walkthroughUrl", "landingUrl")
    for entry in data:
        for field in removable_fields:
            url = entry.get(field)
            if not url:
                continue
            found, _ = resolve_local(url, seg_idx)
            if found is None:
                del entry[field]
                removed += 1
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan IF Hub URLs for broken links.")
    parser.add_argument("--fix", action="store_true",
                        help="Remove broken sourceUrl/walkthroughUrl/landingUrl entries")
    args = parser.parse_args()

    games_path = SITE_DIR / "games.json"
    cards_path = SITE_DIR / "cards.json"
    games = json.loads(games_path.read_text(encoding="utf-8"))
    cards = json.loads(cards_path.read_text(encoding="utf-8"))

    seg_idx = build_segment_index()

    broken_games = scan(games, seg_idx, "games.json")
    broken_cards = scan(cards, seg_idx, "cards.json")

    print(f"games.json: {len(broken_games)} broken link(s)")
    for gid, field, url in broken_games:
        print(f"  {gid}: {field} -> {url}")

    print(f"cards.json: {len(broken_cards)} broken link(s)")
    for gid, field, url in broken_cards:
        print(f"  {gid}: {field} -> {url}")

    if args.fix:
        rg = fix(games, seg_idx)
        rc = fix(cards, seg_idx)
        if rg:
            games_path.write_text(json.dumps(games, indent=2, ensure_ascii=False) + "\n",
                                  encoding="utf-8")
        if rc:
            cards_path.write_text(json.dumps(cards, indent=2, ensure_ascii=False) + "\n",
                                  encoding="utf-8")
        print(f"\n--fix: removed {rg} URL(s) from games.json, {rc} from cards.json")
        print("Note: broken playUrl entries are never auto-fixed — they indicate missing builds.")
        if rg:
            print("Re-run 'python tools/build_games.py' to re-sync cards.json.")


if __name__ == "__main__":
    main()
