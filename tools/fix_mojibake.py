#!/usr/bin/env python3
"""Repair double-encoded UTF-8 (mojibake) in site/games.json and site/cards.json.

Classic symptom: UTF-8 bytes for "—" (0xE2 0x80 0x94) were once decoded as
cp1252 and re-encoded as UTF-8, producing the three visible chars "â€"". This
walks the JSON, spots strings that round-trip cleanly cp1252 → utf-8, and
replaces them with the recovered text.

Root cause seen in this repo: commit 5bcab05 rewrote site/cards.json and
site/games.json through a tool path that double-encoded UTF-8. register_game.py
and ship.py themselves are correct (they use encoding="utf-8" consistently),
so this script exists as a defensive repair + pre-commit guard invoked from
push_hub.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
TARGETS = [SITE / "games.json", SITE / "cards.json"]


def _fix_string(s: str) -> str:
    if not isinstance(s, str):
        return s
    try:
        candidate = s.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s
    # Only accept if a known double-encoded prefix was present — avoids false
    # positives on legitimate characters that happen to round-trip.
    markers = ("\u00e2\u20ac", "\u00c2\u00a0", "\u00e2\u0080")
    if candidate != s and any(m in s for m in markers):
        return candidate
    return s


def _walk(obj):
    if isinstance(obj, dict):
        return {k: _walk(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk(v) for v in obj]
    if isinstance(obj, str):
        return _fix_string(obj)
    return obj


def repair(paths: list[Path] | None = None) -> list[Path]:
    """Repair the given JSON files in place. Returns paths that were changed."""
    targets = paths if paths is not None else TARGETS
    changed: list[Path] = []
    for path in targets:
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8")
        data = json.loads(original)
        fixed = _walk(data)
        new = json.dumps(fixed, indent=2, ensure_ascii=False) + "\n"
        if new != original:
            path.write_text(new, encoding="utf-8")
            changed.append(path)
    return changed


def main() -> int:
    changed = repair()
    for path in TARGETS:
        tag = "repaired" if path in changed else "no change"
        print(f"{tag} {path.relative_to(SITE.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
