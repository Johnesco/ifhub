#!/usr/bin/env python3
"""Unified I7 test suite orchestrator.

All testing is scenario-based. There is no separate "walkthrough" concept —
scenarios that happen to win the game are automatically walkthrough candidates.
The one marked "primary" in the scenario index is the canonical walkthrough.

Layers:
  1. plotex    — PlotEx puzzle model verification (design-time)
  2. regtest   — RegTest assertion checks (pass/fail per assertion)
  3. scenarios — Full scenario runs with diagnostics (transcripts, score, win detection)

Usage:
    python test_suite.py --config tests/project.conf
    python test_suite.py --config tests/project.conf --layer scenarios
    python test_suite.py --config tests/project.conf --layer scenarios --category combat
    python test_suite.py --config tests/project.conf --json
    python test_suite.py --config tests/project.conf --ci
"""

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
_IFHUB_TOOLS = _TOOLS_DIR.parent.parent.parent / "ifhub" / "tools"
if _IFHUB_TOOLS.is_dir():
    sys.path.insert(0, str(_IFHUB_TOOLS))
else:
    sys.path.insert(0, str(_TOOLS_DIR.parent))
from lib import config, process

_report_spec = importlib.util.spec_from_file_location(
    "i7_report", str(_TOOLS_DIR / "report.py"))
_report_mod = importlib.util.module_from_spec(_report_spec)
_report_spec.loader.exec_module(_report_mod)
write_report = _report_mod.write_report
format_report = _report_mod.format_report

# Regtest runner lives in ifhub/tools/testing/ (needs lib/ on sys.path)
IFHUB_TESTING_DIR = _IFHUB_TOOLS / "testing" if _IFHUB_TOOLS.is_dir() else _TOOLS_DIR


def compute_sha256_prefix(path, length=8):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:length]
    except OSError:
        return "unknown"


def load_suite(tests_dir):
    """Load suite.json or return a minimal default."""
    suite_path = tests_dir / "suite.json"
    if suite_path.is_file():
        return json.loads(suite_path.read_text(encoding="utf-8"))
    # Default: enable scenarios if regtest exists
    layers = {}
    for p in tests_dir.glob("*.regtest"):
        layers["scenarios"] = {"enabled": True, "regtest_file": p.name}
        break
    return {"version": 1, "layers": layers}


def run_plotex(cfg, suite, tests_dir, verbose=False):
    """PlotEx puzzle model verification."""
    plotex_conf = suite.get("layers", {}).get("plotex", {})
    if not plotex_conf.get("enabled"):
        return {"status": "skip", "detail": "not configured"}

    plotex_file = tests_dir / plotex_conf.get("file", "")
    if not plotex_file.is_file():
        return {"status": "skip", "detail": f"file not found: {plotex_file.name}"}

    plotex_py = _TOOLS_DIR / "plotex3.py"
    if not plotex_py.is_file():
        return {"status": "skip", "detail": "plotex3.py not installed"}

    result = process.run(
        [sys.executable, str(plotex_py), str(plotex_file), "-T"],
        capture=True,
    )
    if verbose:
        print(result.stdout or "")

    if result.returncode == 0:
        return {"status": "pass", "detail": "all tests passed"}
    return {"status": "fail", "detail": (result.stderr or result.stdout or "").strip()[:200]}


def run_regtest(cfg, suite, tests_dir, verbose=False):
    """RegTest assertion checks."""
    regtest_file = cfg.regtest_file
    if not regtest_file or not Path(regtest_file).is_file():
        for p in tests_dir.glob("*.regtest"):
            regtest_file = str(p)
            break
    if not regtest_file:
        return {"status": "skip", "detail": "no regtest file"}

    # Build interpreter command with golden seed
    seed = config.get_golden_seed(cfg.project_dir, cfg.primary.seeds_key)
    interp_cmd = cfg.primary.path
    if seed:
        interp_cmd += f" {cfg.primary.seed_flag} {seed}"
    interp_cmd += " -q"

    regtest_py = _IFHUB_TOOLS / "regtest.py"

    result = process.run(
        [sys.executable, str(regtest_py),
         "-i", interp_cmd,
         "-g", cfg.primary.game_path,
         regtest_file],
        capture=True,
    )
    output = result.stdout or ""
    if verbose:
        print(output)

    # Save full regtest output for dashboard inspection
    detail_dir = tests_dir / "results"
    detail_dir.mkdir(parents=True, exist_ok=True)
    (detail_dir / "regtest-latest.txt").write_text(output, encoding="utf-8")

    # Parse failures from output
    # regtest.py format: <CheckClass:linenum "pattern">: not found
    failures = [l.strip() for l in output.splitlines()
                if ">:" in l and ("not found" in l or "found" in l)]

    if result.returncode == 0:
        return {"status": "pass", "detail": "all assertions passed",
                "failures": []}
    return {"status": "fail", "detail": f"{len(failures)} assertion(s) failed",
            "failures": failures}


def run_scenarios(cfg, suite, tests_dir, category=None, verbose=False):
    """Full scenario runs with diagnostics and win detection."""
    sc_conf = suite.get("layers", {}).get("scenarios", {})
    if not sc_conf.get("enabled", True):
        return {"status": "skip", "detail": "disabled"}

    # Check if regtest file exists
    has_regtest = False
    if cfg.regtest_file and Path(cfg.regtest_file).is_file():
        has_regtest = True
    else:
        for p in tests_dir.glob("*.regtest"):
            has_regtest = True
            break
    if not has_regtest:
        return {"status": "skip", "detail": "no regtest file"}

    conf_path = tests_dir / "project.conf"
    cmd = [sys.executable, str(_TOOLS_DIR / "run_scenarios.py"),
           "--config", str(conf_path), "--all", "--json"]
    if category:
        cmd.extend(["--category", category])

    result = process.run(cmd, capture=True)

    try:
        data = json.loads(result.stdout)
        # Save detailed scenario results for the dashboard
        detail_path = tests_dir / "results"
        detail_path.mkdir(parents=True, exist_ok=True)
        (detail_path / "scenarios-latest.json").write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8")
        wins = data.get("win_scenarios", [])
        primary = data.get("primary")
        layer_result = {
            "status": "pass" if data.get("failed", 0) == 0 else "fail",
            "total": data.get("total", 0),
            "passed": data.get("passed", 0),
            "failed": data.get("failed", 0),
            "skipped": data.get("skipped", 0),
            "wins": len(wins),
            "win_scenarios": wins,
            "duration": data.get("duration_seconds", 0),
        }
        if primary:
            layer_result["primary_walkthrough"] = primary
        return layer_result
    except (json.JSONDecodeError, TypeError):
        if result.returncode == 0:
            return {"status": "pass", "detail": "completed"}
        return {"status": "fail", "detail": (result.stdout or "").strip()[:200]}


def main():
    parser = argparse.ArgumentParser(description="Unified I7 test suite orchestrator.")
    parser.add_argument("--config", required=True, help="Path to project.conf")
    parser.add_argument("--layer", help="Run only this layer (plotex, regtest, scenarios)")
    parser.add_argument("--category", help="Category filter for scenarios layer")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--ci", action="store_true", help="CI mode: JSON output, exit code")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    cfg = config.load_config(args.config)
    tests_dir = cfg.project_dir / "tests"
    suite = load_suite(tests_dir)

    binary_hash = compute_sha256_prefix(cfg.primary.game_path)
    start_time = time.time()

    layer_results = {}

    layers = [
        ("plotex", lambda: run_plotex(cfg, suite, tests_dir, args.verbose)),
        ("regtest", lambda: run_regtest(cfg, suite, tests_dir, args.verbose)),
        ("scenarios", lambda: run_scenarios(cfg, suite, tests_dir, args.category, args.verbose)),
    ]

    for layer_name, runner in layers:
        if args.layer and args.layer != layer_name:
            continue

        if not args.json and not args.ci:
            print(f"  Running {layer_name}...", end=" ", flush=True)

        result = runner()
        layer_results[layer_name] = result

        if not args.json and not args.ci:
            status = result.get("status", "skip").upper()
            detail = result.get("detail", "")
            if "total" in result:
                detail = f"{result.get('passed', 0)}/{result['total']}"
                wins = result.get("wins", 0)
                if wins:
                    detail += f", {wins} win-paths"
            print(f"{status}  {detail}")

    elapsed = time.time() - start_time

    report = write_report(cfg.project_dir, layer_results, binary_hash, elapsed)

    if args.json or args.ci:
        json.dump(report, sys.stdout, indent=2)
        print()
    else:
        print()
        print(format_report(report))

    sys.exit(1 if report["overall"] == "fail" else 0)


if __name__ == "__main__":
    main()
