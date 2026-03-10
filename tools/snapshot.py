#!/usr/bin/env python3
"""Freeze current working source into a version snapshot.

Usage:
    python tools/snapshot.py <game-name> <version>
    python tools/snapshot.py <game-name> <version> --update

New version (no --update):
  Creates <version>/ directory, copies story.ni, encodes binary, copies template.

Update existing version (--update):
  Recompiles from the version's own frozen story.ni, re-encodes binary.
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import paths, process, web


def main():
    parser = argparse.ArgumentParser(description="Freeze/update version snapshots.")
    parser.add_argument("game", help="Game name")
    parser.add_argument("version", help="Version (e.g., v3)")
    parser.add_argument("--update", action="store_true", help="Update existing version")
    args = parser.parse_args()

    project_dir = paths.project_dir(args.game)
    version_dir = project_dir / args.version

    if not project_dir.is_dir():
        print(f"ERROR: Project not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    if args.update:
        # --- Update existing version ---
        if not version_dir.is_dir():
            print(f"ERROR: Version {args.version} does not exist. Run without --update.", file=sys.stderr)
            sys.exit(1)
        if not (version_dir / "story.ni").exists():
            print(f"ERROR: No frozen story.ni in {version_dir}", file=sys.stderr)
            sys.exit(1)

        print(f"Updating {args.version}...")

        # Auto-detect binary type
        parchment_dir = version_dir / "lib" / "parchment"
        binary_type = "gblorb" if (parchment_dir / f"{args.game}.gblorb.js").exists() else "ulx"
        print(f"  Binary type: {binary_type}")

        # Recompile from frozen source
        compile_cmd = [
            sys.executable, str(paths.TOOLS_DIR / "compile.py"),
            args.game, "--source", str(version_dir / "story.ni"), "--compile-only",
        ]
        if binary_type == "gblorb":
            compile_cmd.append("--sound")
        r = process.run(compile_cmd)
        if r.returncode != 0:
            sys.exit(r.returncode)

        # Encode binary
        parchment_dir.mkdir(parents=True, exist_ok=True)
        if binary_type == "gblorb":
            web.write_story_js(
                project_dir / f"{args.game}.gblorb",
                parchment_dir / f"{args.game}.gblorb.js",
            )
            print(f"  {args.game}.gblorb.js updated")
            # Update .ulx.js companion if it exists
            ulx_js = parchment_dir / f"{args.game}.ulx.js"
            if ulx_js.exists() and (project_dir / f"{args.game}.ulx").exists():
                web.write_story_js(
                    project_dir / f"{args.game}.ulx",
                    ulx_js,
                )
                print(f"  {args.game}.ulx.js updated (companion)")
        else:
            web.write_story_js(
                project_dir / f"{args.game}.ulx",
                parchment_dir / f"{args.game}.ulx.js",
            )
            print(f"  {args.game}.ulx.js updated")

        # Copy walkthrough files
        walk_dir = project_dir / "tests" / "inform7"
        if walk_dir.is_dir():
            for wf in ("walkthrough.txt", "walkthrough-guide.txt"):
                src = walk_dir / wf
                if src.exists():
                    shutil.copy2(str(src), str(version_dir / wf))
                    print(f"  {wf} updated")

    else:
        # --- Create new version ---
        if version_dir.is_dir():
            print(f"ERROR: Version {args.version} already exists. Use --update.", file=sys.stderr)
            sys.exit(1)

        if not (project_dir / "story.ni").exists():
            print(f"ERROR: No story.ni in {project_dir}", file=sys.stderr)
            sys.exit(1)

        # Find previous version
        prev_versions = sorted(
            [d for d in project_dir.iterdir() if d.is_dir() and re.match(r"^v\d+$", d.name)],
            key=lambda d: int(re.search(r"\d+", d.name).group()),
        )
        prev_version = prev_versions[-1] if prev_versions else None

        print(f"Creating {args.version}...")
        version_dir.mkdir(parents=True)

        # Copy source
        shutil.copy2(str(project_dir / "story.ni"), str(version_dir / "story.ni"))
        print("  story.ni copied")

        # Encode binary
        parchment_dir = version_dir / "lib" / "parchment"
        parchment_dir.mkdir(parents=True, exist_ok=True)

        gblorb = project_dir / f"{args.game}.gblorb"
        ulx = project_dir / f"{args.game}.ulx"

        if gblorb.exists():
            web.write_story_js(gblorb, parchment_dir / f"{args.game}.gblorb.js")
            print(f"  {args.game}.gblorb.js created")
            if ulx.exists():
                web.write_story_js(ulx, parchment_dir / f"{args.game}.ulx.js")
                print(f"  {args.game}.ulx.js created (companion)")
        elif ulx.exists():
            web.write_story_js(ulx, parchment_dir / f"{args.game}.ulx.js")
            print(f"  {args.game}.ulx.js created")
        else:
            print(f"ERROR: No {args.game}.gblorb or {args.game}.ulx -- compile first", file=sys.stderr)
            sys.exit(1)

        # Copy template from previous version
        if prev_version:
            prev_name = prev_version.name
            print(f"  Copying template from {prev_name}...")

            for page in ("index.html", "parchment.html", "glulxe.html", "source.html"):
                src = prev_version / page
                if src.exists():
                    shutil.copy2(str(src), str(version_dir / page))
                    print(f"    {page}")

            # Generate walkthrough.html from template
            walk_template = paths.WEB_DIR / "walkthrough-template.html"
            if walk_template.exists():
                walk_title = f"Walkthrough -- {project_dir.name} ({args.version})"
                web.substitute_template(
                    walk_template, version_dir / "walkthrough.html",
                    {
                        "__TITLE__": walk_title,
                        "__HEADER__": f"Walkthrough ({args.version})",
                        "__BACK_HREF__": "../",
                        "__STORAGE_KEY__": args.game,
                    },
                )
                print("    walkthrough.html (generated from template)")
            elif (prev_version / "walkthrough.html").exists():
                shutil.copy2(str(prev_version / "walkthrough.html"), str(version_dir / "walkthrough.html"))
                print(f"    walkthrough.html (copied from {prev_name})")

            # Copy lib/ (except binaries)
            prev_lib = prev_version / "lib"
            if prev_lib.is_dir():
                for item in prev_lib.iterdir():
                    if item.name != "parchment":
                        dest = version_dir / "lib" / item.name
                        if item.is_dir():
                            shutil.copytree(str(item), str(dest))
                        else:
                            shutil.copy2(str(item), str(dest))
                        print(f"    lib/{item.name}")
                # Copy parchment engine files (not binaries)
                prev_parchment = prev_lib / "parchment"
                if prev_parchment.is_dir():
                    for f in prev_parchment.iterdir():
                        if not any(f.name.endswith(ext) for ext in (".ulx.js", ".gblorb.js", ".z3.js")):
                            shutil.copy2(str(f), str(parchment_dir / f.name))
                            print(f"    lib/parchment/{f.name}")

            # Copy media/ and audio/
            for extra_dir in ("media", "audio"):
                src = prev_version / extra_dir
                if src.is_dir():
                    shutil.copytree(str(src), str(version_dir / extra_dir))
                    print(f"    {extra_dir}/")
        else:
            print("  No previous version found -- created minimal snapshot")
            print("  You will need to add player pages manually")

        # Copy walkthrough data
        walk_dir = project_dir / "tests" / "inform7"
        if walk_dir.is_dir():
            for wf in ("walkthrough.txt", "walkthrough-guide.txt"):
                src = walk_dir / wf
                if src.exists():
                    shutil.copy2(str(src), str(version_dir / wf))
                    print(f"  {wf} copied")

    print()
    print(f"Done. Version at: {version_dir}")


if __name__ == "__main__":
    main()
