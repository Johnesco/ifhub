#!/usr/bin/env python3
"""Generic RegTest runner for Inform 7 projects.

Requires a project.conf file (--config) with test file, engine, and game paths.

Usage:
    python tools/testing/run_tests.py --config PATH
    python tools/testing/run_tests.py --config PATH -v
    python tools/testing/run_tests.py --config PATH -l
    python tools/testing/run_tests.py --config PATH cellar
    python tools/testing/run_tests.py --config PATH -v --vital cellar
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib import config, paths, process


def main():
    # Separate --config from passthrough args
    parser = argparse.ArgumentParser(
        description="Run regtests via regtest.py.",
        # Don't error on unknown args — they're passed through to regtest.py
    )
    parser.add_argument("--config", required=True, help="Path to project.conf")

    args, passthrough = parser.parse_known_args()

    conf_path = Path(args.config)
    if not conf_path.exists():
        print(f"ERROR: Config file not found: {conf_path}", file=sys.stderr)
        sys.exit(2)

    cfg = config.load_config(conf_path)

    # Build interpreter command with optional seed
    interp_cmd = f"{cfg.regtest_engine}"
    seed = config.get_golden_seed(conf_path.parent.parent, cfg.primary.seeds_key or "glulxe")
    if seed and cfg.primary.seed_flag:
        interp_cmd += f" {cfg.primary.seed_flag} {seed}"
    interp_cmd += " -q"

    regtest_py = paths.TOOLS_DIR / "regtest.py"
    cmd = [
        sys.executable, str(regtest_py),
        "-i", interp_cmd,
        "-g", cfg.regtest_game,
        cfg.regtest_file,
    ] + passthrough

    result = process.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
