#!/usr/bin/env python3
"""One-shot migration: move games-registry.json fields into each game's ifhub.conf.

This is the cut-over for the "games.json becomes a build artifact" refactor.
After this runs, the registry can be emptied; build_games.py reconstructs
games.json from ifhub.conf + workspace scan + disk probing.

What it does:

1. For every entry in site/games.json, locates the source game dir (via the
   legacy games-registry.json path or a workspace scan) and writes any
   fields that ifhub.conf doesn't already imply — title overrides,
   sourceLabel, overlayLabel, sourceBrowser (when false), version flags —
   plus the new `hub = yes` opt-in marker.

2. For Sharpee's familyzoo multi-target layout (17 ids all pointing at the
   same repo with `entry`/`binary`/`subpath`), rewrites
   text-games/sharpee/familyzoo/ifhub.conf with 17 `[target.*]` sections.

3. Adds the `from-fork` workspace to workspaces.json so the 3 sharpee fork
   games (armoured-sharpee, cloak-sharpee, dungeo) stop needing explicit
   registry paths.

4. Empties games-registry.json to `{}`. Callers still read it (paths.py,
   check_links.py) but it no longer carries data.

Idempotent: running twice should produce the same result as running once.

Usage:
    python tools/migrate_registry_to_conf.py --dry-run   # preview
    python tools/migrate_registry_to_conf.py             # apply
"""

from __future__ import annotations

import argparse
import configparser
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import (
    IFHUB_DIR, GAMES_REGISTRY, WORKSPACES_FILE, I7_ROOT,
)
import build_games


FORK_WORKSPACE = {"engine": "sharpee", "root": "../npmsharpee/from-fork", "deploy": "in-place"}


def resolve_path(raw: str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = (I7_ROOT / p).resolve()
    return p


# ── Conf file rewriting ─────────────────────────────────────────────────────

def render_kv_lines(fields: dict, key_order: list[str] | None = None) -> list[str]:
    """Render a dict as 'key = value' lines in the preferred key order."""
    out = []
    seen = set()
    if key_order:
        for k in key_order:
            if k in fields:
                out.append(f"{k} = {fields[k]}")
                seen.add(k)
    for k in fields:
        if k not in seen:
            out.append(f"{k} = {fields[k]}")
    return out


PARENT_KEY_ORDER = [
    "engine", "name", "title", "author", "description",
    "binary", "source", "walkthrough", "tags",
    "sound", "mood", "sourceLabel", "overlayLabel", "sourceBrowser",
    "versionOf", "versionLabel", "versionOrder",
    "versionPrimary", "versionPrimaryLabel",
    "hub",
]

TARGET_KEY_ORDER = [
    "hub", "entry", "binary", "subpath",
    "title", "description", "walkthrough",
    "versionOf", "versionLabel", "versionOrder",
    "versionPrimary", "versionPrimaryLabel",
]


def split_conf_text(text: str) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """Split raw conf text into parent KV lines and (section_name, lines) tuples.

    Preserves comments and blank lines inside each chunk.
    """
    parent_lines: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current: list[str] | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = []
            sections.append((stripped[1:-1], current))
        elif current is not None:
            current.append(line)
        else:
            parent_lines.append(line)
    return parent_lines, sections


def parse_kv_lines(lines: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    cp = configparser.ConfigParser()
    cp.optionxform = str
    cp.read_string("[x]\n" + "\n".join(lines))
    for k, v in cp["x"].items():
        fields[k] = v
    return fields


def apply_overrides_to_conf(conf_path: Path,
                            parent_overrides: dict,
                            target_overrides: dict[str, dict],
                            target_creation_order: list[str] | None = None,
                            dry_run: bool = False) -> bool:
    """Rewrite conf_path, merging in parent_overrides and target_overrides.

    Targets not currently present in the conf get appended in
    `target_creation_order`. Returns True if the file changed.
    """
    if conf_path.exists():
        original_text = conf_path.read_text(encoding="utf-8")
    else:
        original_text = ""

    parent_raw_lines, sections = split_conf_text(original_text)
    parent_fields = parse_kv_lines(parent_raw_lines)
    parent_fields.update(parent_overrides)

    # Merge / add target sections.
    existing_targets: dict[str, dict] = {}
    existing_order: list[str] = []
    for sec_name, sec_lines in sections:
        if sec_name.startswith("target."):
            tid = sec_name[len("target."):]
            existing_targets[tid] = parse_kv_lines(sec_lines)
            existing_order.append(tid)

    final_targets = dict(existing_targets)
    final_order = list(existing_order)
    for tid, overrides in target_overrides.items():
        final_targets.setdefault(tid, {}).update(overrides)
        if tid not in final_order:
            final_order.append(tid)
    if target_creation_order:
        # If a creation order was requested, use that to re-sort targets.
        ordered = [t for t in target_creation_order if t in final_targets]
        for t in final_order:
            if t not in ordered:
                ordered.append(t)
        final_order = ordered

    # Build new text
    out: list[str] = []
    out.extend(render_kv_lines(parent_fields, PARENT_KEY_ORDER))
    for tid in final_order:
        out.append("")
        out.append(f"[target.{tid}]")
        out.extend(render_kv_lines(final_targets[tid], TARGET_KEY_ORDER))
    new_text = "\n".join(out) + "\n"

    if new_text == original_text:
        return False
    if dry_run:
        print(f"  would rewrite {conf_path}")
        return True
    conf_path.write_text(new_text, encoding="utf-8")
    print(f"  rewrote {conf_path}")
    return True


# ── Derivation helpers (mirrors build_games.py logic) ───────────────────────

def derive_entry(deploy_dir: Path, game_id: str, parent: dict,
                 target_override: dict | None = None) -> dict:
    """What build_games.py would produce given the current conf + a pending
    override. Used to compute the delta that still needs to be written."""
    conf = dict(parent)
    if target_override:
        conf.update(target_override)
    url_prefix = f"/{deploy_dir.name}"
    if target_override and target_override.get("subpath"):
        url_prefix = f"/{deploy_dir.name}/{target_override['subpath'].strip('/')}"
        deploy_dir = deploy_dir / target_override["subpath"].strip("/")
    return build_games.build_entry(game_id, conf, deploy_dir, url_prefix)


# ── Planning overrides per game ─────────────────────────────────────────────

# Fields on a games.json entry that map directly to ifhub.conf keys.
GAMES_JSON_TO_CONF_KEY = {
    "title": "title",
    "sourceLabel": "sourceLabel",
    "overlayLabel": "overlayLabel",
    "versionLabel": "versionLabel",
    "versionPrimaryLabel": "versionPrimaryLabel",
}


def compute_single_target_overrides(game_entry: dict, parent: dict,
                                    registry_entry: dict | None = None) -> dict:
    """What extra fields must go into the top-level conf to reproduce game_entry."""
    overrides: dict = {"hub": "yes"}

    # Direct field overrides when the conf value differs.
    for gj_key, conf_key in GAMES_JSON_TO_CONF_KEY.items():
        if gj_key in game_entry and parent.get(conf_key) != game_entry[gj_key]:
            overrides[conf_key] = game_entry[gj_key]

    # sourceBrowser — current games.json: absent => no sourceBrowser flag
    # (URL points at raw source). Conf default is sourceBrowser=true.
    # So if games.json lacks sourceBrowser, we must write `sourceBrowser = no`.
    if not game_entry.get("sourceBrowser"):
        overrides["sourceBrowser"] = "no"

    # Tags — override if they differ from conf's derived list.
    conf_tags = build_games.parse_tags(parent.get("tags", ""))
    entry_tags = list(game_entry.get("tags", []))
    if conf_tags != entry_tags:
        overrides["tags"] = ", ".join(entry_tags)

    # Sound flag
    sound_in_entry = game_entry.get("sound")
    conf_sound = parent.get("sound", "").strip().lower()
    conf_has_sound = conf_sound in {"yes", "true", "1", "blorb"}
    if sound_in_entry and not conf_has_sound:
        overrides["sound"] = "yes"
    elif not sound_in_entry and conf_has_sound:
        overrides["sound"] = "no"

    # Version fields from registry (these only existed in the registry,
    # not in games.json, under the old scheme).
    if registry_entry:
        if registry_entry.get("versionOf"):
            overrides["versionOf"] = registry_entry["versionOf"]
        if registry_entry.get("versionLabel") and "versionLabel" not in overrides:
            overrides["versionLabel"] = registry_entry["versionLabel"]
        if registry_entry.get("versionOrder") is not None:
            overrides["versionOrder"] = str(registry_entry["versionOrder"])
        if registry_entry.get("versionPrimary"):
            overrides["versionPrimary"] = "yes"
        if registry_entry.get("versionPrimaryLabel"):
            overrides["versionPrimaryLabel"] = registry_entry["versionPrimaryLabel"]

    return overrides


def compute_target_overrides(target_entry: dict,
                             registry_entry: dict,
                             parent: dict) -> dict:
    """Override dict for a [target.<id>] section of a multi-target conf."""
    ov: dict = {"hub": "yes"}

    # Copy over structural fields from the registry.
    for k in ("entry", "binary", "subpath", "walkthrough"):
        if registry_entry.get(k):
            ov[k] = registry_entry[k]

    # Copy title/description from the registry (or games.json entry).
    for k in ("title", "description"):
        v = target_entry.get(k) or registry_entry.get(k)
        if v and parent.get(k) != v:
            ov[k] = v

    # Version fields from registry
    for k in ("versionOf", "versionLabel"):
        if registry_entry.get(k):
            ov[k] = registry_entry[k]
    if registry_entry.get("versionOrder") is not None:
        ov["versionOrder"] = str(registry_entry["versionOrder"])
    if registry_entry.get("versionPrimary"):
        ov["versionPrimary"] = "yes"
    if registry_entry.get("versionPrimaryLabel"):
        ov["versionPrimaryLabel"] = registry_entry["versionPrimaryLabel"]

    return ov


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate registry fields into ifhub.conf files")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report changes without writing files")
    args = parser.parse_args()

    registry = json.loads(GAMES_REGISTRY.read_text(encoding="utf-8"))
    games = json.loads((IFHUB_DIR / "games.json").read_text(encoding="utf-8"))
    games_by_id = {g["id"]: g for g in games}

    # Group familyzoo-* entries for multi-target rewrite.
    familyzoo_members: list[str] = [gid for gid, e in registry.items()
                                    if e.get("path") == "../text-games/sharpee/familyzoo"]
    familyzoo_dir = resolve_path("../text-games/sharpee/familyzoo")

    # Per-dir accumulators.
    per_dir_parent: dict[Path, dict] = {}
    per_dir_targets: dict[Path, dict[str, dict]] = {}
    per_dir_target_order: dict[Path, list[str]] = {}

    def note_parent(deploy_dir: Path, overrides: dict) -> None:
        per_dir_parent.setdefault(deploy_dir, {}).update(overrides)

    def note_target(deploy_dir: Path, tid: str, overrides: dict) -> None:
        per_dir_targets.setdefault(deploy_dir, {}).setdefault(tid, {}).update(overrides)
        order = per_dir_target_order.setdefault(deploy_dir, [])
        if tid not in order:
            order.append(tid)

    for gid, entry in registry.items():
        path_raw = entry.get("path", "")
        if not path_raw:
            continue
        deploy_dir = resolve_path(path_raw)
        if not deploy_dir.is_dir():
            print(f"  skip: {gid} has path {path_raw} which doesn't exist")
            continue
        conf_path = deploy_dir / "ifhub.conf"
        if not conf_path.exists():
            print(f"  skip: {gid} has no ifhub.conf at {conf_path}")
            continue

        parent_conf, existing_targets = build_games.parse_conf(conf_path)

        if gid in familyzoo_members:
            # All familyzoo-* go into target sections of the same conf.
            g_entry = games_by_id.get(gid, {})
            ov = compute_target_overrides(g_entry, entry, parent_conf)
            note_target(deploy_dir, gid, ov)
            continue

        # Single-target games.
        g_entry = games_by_id.get(gid)
        if g_entry is None:
            # In registry but not in games.json (unregistered-but-tracked). Skip.
            continue
        ov = compute_single_target_overrides(g_entry, parent_conf, entry)
        note_parent(deploy_dir, ov)

    # Sharpee familyzoo: ensure parent hub=yes is NOT set (only targets are)
    # and also carry over the parent title from games.json if needed.
    if familyzoo_dir in per_dir_targets:
        # Don't set hub=yes on the parent — only on each target.
        per_dir_parent.setdefault(familyzoo_dir, {})

    # Apply overrides.
    changed = 0
    for deploy_dir in sorted(set(list(per_dir_parent) + list(per_dir_targets)), key=lambda p: str(p)):
        conf_path = deploy_dir / "ifhub.conf"
        parent_ov = per_dir_parent.get(deploy_dir, {})
        target_ov = per_dir_targets.get(deploy_dir, {})
        order = per_dir_target_order.get(deploy_dir)
        if apply_overrides_to_conf(conf_path, parent_ov, target_ov,
                                   target_creation_order=order,
                                   dry_run=args.dry_run):
            changed += 1

    # workspaces.json — ensure from-fork workspace is present.
    ws = json.loads(WORKSPACES_FILE.read_text(encoding="utf-8"))
    workspaces = ws.get("workspaces", [])
    if not any(w.get("root") == FORK_WORKSPACE["root"] for w in workspaces):
        if args.dry_run:
            print(f"  would add workspace {FORK_WORKSPACE['root']} to workspaces.json")
        else:
            workspaces.append(FORK_WORKSPACE)
            ws["workspaces"] = workspaces
            WORKSPACES_FILE.write_text(
                json.dumps(ws, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
            )
            print(f"  added workspace {FORK_WORKSPACE['root']} to workspaces.json")
        changed += 1

    # Empty the registry.
    if registry:
        if args.dry_run:
            print(f"  would clear games-registry.json (currently {len(registry)} entries)")
        else:
            GAMES_REGISTRY.write_text("{}\n", encoding="utf-8")
            print(f"  cleared games-registry.json ({len(registry)} entries removed)")
        changed += 1

    print(f"\n{'would change' if args.dry_run else 'changed'} {changed} file(s)")


if __name__ == "__main__":
    main()
