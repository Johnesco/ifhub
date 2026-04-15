#!/usr/bin/env python3
"""One-shot: extract prose from a hand-written landing index.html into landing.json.

For each base group named on the command line, locates the primary's index.html
(the existing hand-written landing page), parses out the prose blocks, and
writes a landing.json into the primary's own repo. That landing.json is then
consumed by build_landing.py to regenerate a standardized index.html.

Usage:
    python tools/migrate_landing.py zork1 familyzoo

The tool is intentionally forgiving: it extracts what it can and leaves the
resulting JSON for the author to polish. It does not overwrite an existing
landing.json unless --force is passed.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import IFHUB_DIR, GAMES_REGISTRY, I7_ROOT
import build_cards


def resolve_path(raw: str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = (I7_ROOT / p).resolve()
    return p


def read_meta(html: str, name: str) -> str:
    m = re.search(
        rf'<meta\s+name="ifhub:{re.escape(name)}"\s+content="([^"]*)"',
        html, re.I)
    return m.group(1) if m else ""


def extract_subtitle(html: str) -> str:
    m = re.search(r'<p\s+class="subtitle"[^>]*>(.*?)</p>', html, re.DOTALL | re.I)
    return m.group(1).strip() if m else ""


def extract_intro(html: str) -> str:
    """Paragraphs between the subtitle block and the first <h2>."""
    after_subtitle = re.split(r'</p>', html, maxsplit=1)
    # Find region starting after subtitle ending and before first h2
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.I)
    if not body_match:
        return ""
    body = body_match.group(1)
    # Drop everything up to and including the subtitle <p>
    m = re.search(r'<p\s+class="subtitle"[^>]*>.*?</p>\s*', body, re.DOTALL | re.I)
    if m:
        body = body[m.end():]
    # Stop at first <h2>
    m = re.search(r'<h2\b', body, re.I)
    if m:
        body = body[:m.start()]
    # Collect <p>...</p> blocks
    paragraphs = re.findall(r'<p\b[^>]*>.*?</p>', body, re.DOTALL | re.I)
    return "\n".join(p.strip() for p in paragraphs).strip()


VERSION_ENTRY_RE = re.compile(
    r'<div\s+class="version-entry"[^>]*>\s*'
    r'<h3\b[^>]*>(?P<heading>.*?)</h3>'
    r'(?P<inner>.*?)</div>\s*(?=<div\s+class="version-entry"|<footer|<h2|</body)',
    re.DOTALL | re.I)


def extract_version_blurbs(html: str, member_ids: list[str],
                           member_labels: dict[str, str]) -> dict:
    """Parse <div class="version-entry"> blocks. Match to registry ids.

    Match strategy: heading text contains the trailing vNN of the id
    (e.g., heading "v3 — Multimedia" → id ending in "-v3" or "-3").
    """
    result: dict[str, dict] = {}
    id_by_vnum: dict[int, str] = {}
    for mid in member_ids:
        inferred = build_cards.infer_base(mid)
        if inferred:
            id_by_vnum[inferred[1]] = mid

    for m in VERSION_ENTRY_RE.finditer(html):
        heading = re.sub(r'<[^>]+>', '', m.group("heading")).strip()
        inner = m.group("inner")
        # Find vNN in the heading (accept "v0", "v03", "v3", "v17" etc.)
        vnum_match = re.search(r'v(\d+)', heading, re.I)
        if not vnum_match:
            continue
        vnum = int(vnum_match.group(1))
        if vnum not in id_by_vnum:
            continue
        mid = id_by_vnum[vnum]

        # summary = first <p> inside the entry (not in <ul>)
        summary_match = re.search(r'<p\b[^>]*>(.*?)</p>', inner, re.DOTALL | re.I)
        summary = summary_match.group(1).strip() if summary_match else ""

        # features = <li>...</li> inside the entry
        features = []
        ul_match = re.search(r'<ul\b[^>]*>(.*?)</ul>', inner, re.DOTALL | re.I)
        if ul_match:
            for li in re.finditer(r'<li\b[^>]*>(.*?)</li>', ul_match.group(1),
                                  re.DOTALL | re.I):
                features.append(li.group(1).strip())

        entry_data = {}
        if summary:
            entry_data["summary"] = summary
        if features:
            entry_data["features"] = features
        if entry_data:
            result[mid] = entry_data

    return result


def extract_primary_cta(html: str) -> str:
    m = re.search(r'<a\s+class="play-latest"[^>]*>(.*?)</a>', html,
                  re.DOTALL | re.I)
    if not m:
        return ""
    return re.sub(r'<[^>]+>', '', m.group(1)).strip()


def find_primary(registry: dict, base: str) -> tuple[str, dict] | None:
    for gid, entry in registry.items():
        if entry.get("versionPrimary"):
            if (entry.get("versionOf") or gid) == base:
                return gid, entry
    return None


def find_source_html(primary_path: Path, primary_entry: dict) -> Path | None:
    """Locate the existing hand-written landing to migrate from."""
    candidates = []
    if primary_entry.get("subpath"):
        candidates.append(primary_path / "browser" / "index.html")
    candidates.append(primary_path / "index.html")
    for c in candidates:
        if c.exists():
            return c
    return None


def migrate_base(base: str, registry: dict, games_by_id: dict,
                 force: bool) -> None:
    primary = find_primary(registry, base)
    if primary is None:
        print(f"[{base}] no versionPrimary found in registry — skipping")
        return
    primary_id, primary_entry = primary
    primary_path = resolve_path(primary_entry.get("path", ""))
    if not primary_path.exists():
        print(f"[{base}] primary path {primary_path} missing — skipping")
        return

    source = find_source_html(primary_path, primary_entry)
    if source is None:
        print(f"[{base}] no existing index.html found to migrate — skipping")
        return

    html = source.read_text(encoding="utf-8")

    member_to_base, _ = build_cards.build_groups(registry)
    member_ids = [gid for gid, b in member_to_base.items() if b == base]
    member_labels = {gid: games_by_id.get(gid, {}).get("title", gid)
                     for gid in member_ids}

    landing = {}
    title = read_meta(html, "title")
    meta_field = read_meta(html, "meta")
    desc = read_meta(html, "description")

    if title:
        landing["title"] = title
    if meta_field:
        landing["meta"] = meta_field
        landing.setdefault("subtitle", meta_field)
    else:
        sub = extract_subtitle(html)
        if sub:
            landing["subtitle"] = sub
    if desc:
        landing["description"] = desc

    cta = extract_primary_cta(html)
    if cta:
        landing["primaryCtaLabel"] = cta

    intro = extract_intro(html)
    if intro:
        landing["introHtml"] = intro

    versions = extract_version_blurbs(html, member_ids, member_labels)
    if versions:
        landing["versions"] = versions

    target = primary_path / "landing.json"
    if target.exists() and not force:
        print(f"[{base}] {target} already exists — use --force to overwrite. Skipping.")
        return

    target.write_text(json.dumps(landing, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print(f"[{base}] wrote {target} "
          f"({len(versions)} version blurbs, {len(landing.get('introHtml',''))} bytes intro)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate hand-written landings into landing.json.")
    parser.add_argument("bases", nargs="+", help="Base ids (e.g., zork1 familyzoo)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing landing.json files")
    args = parser.parse_args()

    registry = json.loads(GAMES_REGISTRY.read_text(encoding="utf-8"))
    games = json.loads((IFHUB_DIR / "games.json").read_text(encoding="utf-8"))
    games_by_id = {g["id"]: g for g in games}

    for base in args.bases:
        migrate_base(base, registry, games_by_id, args.force)


if __name__ == "__main__":
    main()
