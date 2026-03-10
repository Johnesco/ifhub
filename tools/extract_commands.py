#!/usr/bin/env python3
"""Extract walkthrough commands from a game transcript or story.ni.

Usage:
    python tools/extract_commands.py transcript.txt
    python tools/extract_commands.py transcript.txt -o walkthrough.txt
    python tools/extract_commands.py --from-source story.ni -o walkthrough.txt

Modes:
    (default)       Extract commands from a TRANSCRIPT file (lines starting with >)
    --from-source   Extract commands from "Test me with ..." in a story.ni file
"""

import argparse
import re
import sys
from pathlib import Path


def extract_from_transcript(text: str) -> list[str]:
    """Extract player commands from a game transcript."""
    meta_cmds = {"transcript", "script", "quit", "restart", "restore", "save", "undo"}
    commands = []
    for line in text.splitlines():
        if line.startswith(">"):
            cmd = line.lstrip("> ").strip()
            if cmd and cmd.split()[0].lower() not in meta_cmds:
                commands.append(cmd)
    return commands


def extract_from_source(text: str) -> list[str]:
    """Extract commands from Inform 7 'Test ... with ...' definitions."""
    tests: dict[str, list[str]] = {}
    for m in re.finditer(r'Test\s+(\w+)\s+with\s+"([^"]+)"', text, re.IGNORECASE):
        name = m.group(1).lower()
        cmds = [c.strip() for c in m.group(2).split(" / ") if c.strip()]
        tests[name] = cmds

    def expand(cmds: list[str], seen: set[str] | None = None) -> list[str]:
        if seen is None:
            seen = set()
        result = []
        for cmd in cmds:
            ref = re.match(r"^test\s+(\w+)$", cmd, re.IGNORECASE)
            if ref and ref.group(1).lower() in tests and ref.group(1).lower() not in seen:
                seen.add(ref.group(1).lower())
                result.extend(expand(tests[ref.group(1).lower()], seen))
            else:
                result.append(cmd)
        return result

    if "me" in tests:
        return expand(tests["me"])
    # Fall back to all tests in order
    result = []
    for name in tests:
        result.extend(expand(tests[name]))
    return result


def main():
    parser = argparse.ArgumentParser(description="Extract walkthrough commands.")
    parser.add_argument("input", help="Transcript or source file")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument("--from-source", action="store_true",
                        help="Extract from story.ni Test definitions")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    text = input_path.read_text(encoding="utf-8")

    if args.from_source:
        commands = extract_from_source(text)
    else:
        commands = extract_from_transcript(text)

    if not commands:
        print(f"No commands found in {input_path}", file=sys.stderr)
        sys.exit(1)

    result = "\n".join(commands) + "\n"

    if args.output:
        output_path = Path(args.output)
        if output_path.exists():
            print(f"WARNING: {output_path} already exists -- overwriting", file=sys.stderr)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result, encoding="utf-8")
        print(f"Extracted {len(commands)} commands -> {output_path}")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
