#!/usr/bin/env python3
"""Unified build pipeline for IF Hub game projects.

A thin orchestrator that calls existing scripts in order with error handling.
Supports all engines registered in lib/config.ENGINE_REGISTRY.

Usage:
    python tools/pipeline.py <game-name> [stages...] [flags]

Stages (in pipeline order):
    compile   — Build game (engine-specific: I7, Ink, BASIC, etc.)
    test      — Walkthrough + regtest (Inform 7 / Z-machine only)
    push      — Stage changes, show summary, prompt before commit/push

Flags:
    --all             Run: compile test push
    --force           Skip staleness checks
    --dry-run         Show what would happen
    --continue        Resume from last failed stage
    --message "msg"   Commit message for push stage
"""

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import config, git, output, paths, process


# --- Staleness state file (JSON instead of bash key=value) ---

def load_state(state_file: Path) -> dict:
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(state_file: Path, key: str, value: str):
    state = load_state(state_file)
    state[key] = value
    state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def compute_hash(path: Path) -> str:
    if path.exists():
        return hashlib.md5(path.read_bytes()).hexdigest()
    return "none"


def resolve_bin_name(project_dir: Path, name: str) -> str:
    """Resolve binary name: project.conf BINARY_NAME > game dir name."""
    conf_file = project_dir / "tests" / "project.conf"
    if conf_file.exists():
        kv = config._parse_kv(conf_file, project_dir)
        bn = kv.get("BINARY_NAME", "")
        if bn:
            return bn
    return name


def find_binary(project_dir: Path, bin_name: str,
                engine_spec: config.EngineSpec | None = None) -> Path | None:
    # Check engine-specific binary extensions first
    if engine_spec and engine_spec.binary_extensions:
        for ext in engine_spec.binary_extensions:
            p = project_dir / f"{bin_name}{ext}"
            if p.exists():
                return p
    else:
        # Default I7 extensions (backward compat)
        for ext in (".gblorb", ".ulx"):
            p = project_dir / f"{bin_name}{ext}"
            if p.exists():
                return p
    # For web-only engines, play.html is the build artifact
    if engine_spec and not engine_spec.binary_extensions:
        p = project_dir / "play.html"
        if p.exists():
            return p
    return None


# --- Stage implementations ---

def stage_compile(name: str, project_dir: Path, pipeline_sound: bool,
                  engine: str = "inform7", engine_spec: config.EngineSpec | None = None,
                  source_file: str = "story.ni"):
    if engine == "inform7" or not engine_spec:
        # Original Inform 7 path
        cmd = [sys.executable, str(paths.TOOLS_DIR / "compile.py"), name]
        if pipeline_sound:
            cmd.append("--sound")
    elif engine_spec.build_tool == "setup_ink.py":
        source_path = project_dir / source_file
        title = name.replace("-", " ").replace("_", " ").title()
        cmd = [
            sys.executable, str(paths.WEB_DIR / "setup_ink.py"),
            "--title", title,
            "--ink", str(source_path),
            "--out", str(project_dir),
            "--force",
        ]
    elif engine_spec.build_tool == "setup_basic.py":
        source_path = project_dir / source_file
        title = name.replace("-", " ").replace("_", " ").title()
        cmd = [
            sys.executable, str(paths.WEB_DIR / "setup_basic.py"),
            *engine_spec.build_tool_args,
            "--title", title,
            "--source", str(source_path),
            "--out", str(project_dir),
        ]
    elif engine_spec.build_tool == "setup_web.py":
        # Z-machine: find the binary and set up web player
        title = name.replace("-", " ").replace("_", " ").title()
        source_path = project_dir / source_file
        cmd = [
            sys.executable, str(paths.WEB_DIR / "setup_web.py"),
            "--title", title,
            "--ulx", str(source_path),
            "--out", str(project_dir),
        ]
    elif not engine_spec.build_tool:
        output.skip(f"No build tool for {engine_spec.label} — skipping compile")
        return
    else:
        output.skip(f"Unknown build tool {engine_spec.build_tool!r} — skipping compile")
        return

    r = process.run(cmd)
    if r.returncode != 0:
        raise RuntimeError(f"compile failed (exit {r.returncode})")


def stage_test(name: str, project_dir: Path, cfg_pipeline,
               engine_spec: config.EngineSpec | None = None):
    if engine_spec and not engine_spec.has_cli_tests:
        output.skip(f"No CLI tests for {engine_spec.label}")
        return

    has_tests = False

    # Walkthrough
    conf_file = project_dir / "tests" / "project.conf"

    if conf_file.exists():
        cfg = config.load_config(conf_file)

        # Determine seed
        seed = config.get_golden_seed(project_dir, "glulxe")

        # Determine output copy dir
        wt_output_dir = cfg_pipeline.walkthrough_output_dir
        if not wt_output_dir:
            wt_output_dir = str(project_dir)

        # Run walkthrough via Python
        if cfg.primary.walkthrough and Path(cfg.primary.walkthrough).exists():
            print("  Running walkthrough...")
            has_tests = True
            wt_cmd = [
                sys.executable, str(paths.TESTING_DIR / "run_walkthrough.py"),
                "--config", str(conf_file),
            ]
            if seed:
                wt_cmd.extend(["--seed", seed])
            if wt_output_dir and Path(wt_output_dir).is_dir():
                wt_cmd.extend(["--copy-output", wt_output_dir])

            r = process.run(wt_cmd)
            if r.returncode != 0:
                raise RuntimeError(f"walkthrough failed (exit {r.returncode})")

            # Post-test: regenerate guide and sync
            wt_src_dir = project_dir / "tests" / "inform7"
            wt_output = wt_src_dir / "walkthrough_output.txt"
            wt_commands = wt_src_dir / "walkthrough.txt"

            if wt_output.exists() and wt_commands.exists():
                print("  Regenerating walkthrough guide...")
                guide_out = wt_src_dir / "walkthrough-guide.txt"
                process.run([
                    sys.executable, str(paths.TESTING_DIR / "generate-guide.py"),
                    "--walkthrough", str(wt_commands),
                    "--transcript", str(wt_output),
                    "-o", str(guide_out),
                ])
                # Sync guide to web dir
                if wt_output_dir and Path(wt_output_dir).is_dir():
                    dest = Path(wt_output_dir)
                    if dest.resolve() != wt_src_dir.resolve():
                        if guide_out.exists():
                            shutil.copy2(str(guide_out), str(dest / "walkthrough-guide.txt"))
                        print(f"  Walkthrough files synced to: {dest.relative_to(project_dir)}")

        # RegTest
        if cfg.regtest_file and Path(cfg.regtest_file).exists():
            print("  Running regtests...")
            has_tests = True
            r = process.run([
                sys.executable, str(paths.TESTING_DIR / "run_tests.py"),
                "--config", str(conf_file),
            ])
            if r.returncode != 0:
                raise RuntimeError(f"regtests failed (exit {r.returncode})")

    if not has_tests:
        output.skip("No tests configured")


def stage_push(name: str, commit_msg: str):
    print("  Staging changes...")
    cwd = paths.I7_ROOT

    status_text = git.status(cwd=cwd)
    print()
    print(output.bold("Changed files:"))
    if status_text:
        print(status_text)
    else:
        output.skip("No changes to commit.")
        return

    file_count = len(status_text.strip().split("\n"))
    print()
    print(output.bold(f"{file_count} file(s) changed."))

    msg = commit_msg or f"Pipeline build for {name}"
    print()
    print(f"  Commit message: {output.blue(msg)}")
    print()

    try:
        confirm = input("  Commit and push? [y/N] ").strip()
    except (EOFError, KeyboardInterrupt):
        confirm = "n"

    if confirm.lower() != "y":
        output.skip("Push cancelled. Changes remain staged.")
        return

    git.add_all(cwd=cwd)
    git.commit(msg, cwd=cwd)
    git.push(cwd=cwd)
    print(output.green("  Pushed successfully."))


# --- Main ---

PIPELINE_ORDER = ["compile", "test", "push"]
VALID_STAGES = set(PIPELINE_ORDER)


def main():
    parser = argparse.ArgumentParser(description="Unified build pipeline.")
    parser.add_argument("game", help="Game name")
    parser.add_argument("stages", nargs="*", help="Stages to run")
    parser.add_argument("--all", action="store_true", help="compile test push")
    parser.add_argument("--force", action="store_true", help="Skip staleness checks")
    parser.add_argument("--dry-run", action="store_true", help="Show plan only")
    parser.add_argument("--continue", dest="resume", action="store_true", help="Resume from failure")
    parser.add_argument("--message", help="Commit message for push")
    args = parser.parse_args()

    name = args.game
    project_dir = paths.project_dir(name)
    state_file = project_dir / ".pipeline-state"

    if not project_dir.is_dir():
        print(f"ERROR: Project not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    # Determine stages
    stages = list(args.stages)
    for s in stages:
        if s not in VALID_STAGES:
            print(f"Unknown stage: {s}", file=sys.stderr)
            sys.exit(1)

    if args.all:
        stages = ["compile", "test", "push"]

    if not stages:
        stages = ["compile"]

    # Reorder to pipeline order
    stages = [s for s in PIPELINE_ORDER if s in stages]

    # Detect engine early
    conf_fields = config.parse_conf_fields(project_dir)
    engine = config.detect_engine(project_dir, conf_fields)
    engine_spec = config.get_engine_spec(engine)
    source_file_name = config.detect_source_file(project_dir, engine, conf_fields)

    # Pipeline config from project.conf
    conf_file = project_dir / "tests" / "project.conf"
    pipeline_cfg = config.PipelineConfig()
    if conf_file.exists():
        full_cfg = config.load_config(conf_file)
        pipeline_cfg = full_cfg.pipeline
    # Fallback: infer sound from Sounds/ directory
    if not pipeline_cfg.sound and (project_dir / "Sounds").is_dir():
        pipeline_cfg.sound = True

    # Resume support
    if args.resume:
        state = load_state(state_file)
        failed = state.get("STAGE_FAILED", "")
        if not failed:
            print("No failed stage recorded. Nothing to resume.")
            sys.exit(0)
        print(output.yellow(f"Resuming from failed stage: {failed}"))
        original = state.get("STAGE_ORIGINAL_STAGES", "compile").split()
        found = False
        resume_stages = []
        for s in PIPELINE_ORDER:
            if s == failed:
                found = True
            if found and s in original:
                resume_stages.append(s)
        stages = resume_stages
        save_state(state_file, "STAGE_FAILED", "")

    save_state(state_file, "STAGE_ORIGINAL_STAGES", " ".join(stages))

    # Resolve binary name for staleness checks
    bin_name = resolve_bin_name(project_dir, name)
    if pipeline_cfg.binary_name:
        bin_name = pipeline_cfg.binary_name

    # Execution
    engine_label = engine_spec.label if engine_spec else engine
    print(output.bold(f"=== PIPELINE: {name} ({engine_label}) ==="))
    print(f"  Stages: {' '.join(stages)}")
    if args.dry_run:
        print(output.yellow("  Mode: DRY RUN"))
    if args.force:
        print(output.yellow("  Mode: FORCE (skip staleness checks)"))

    results: list[tuple[str, str, int]] = []  # (stage, status, seconds)
    pipeline_start = time.time()

    for stage in stages:
        print()
        print(output.bold(f"=== Stage: {stage} ==="))

        if args.dry_run:
            print(output.yellow(f"  [DRY RUN] Would execute: {stage}"))
            results.append((stage, "DRY_RUN", 0))
            continue

        # Staleness check
        if not args.force:
            state = load_state(state_file)
            skip = False
            if stage == "compile":
                source_path = project_dir / source_file_name if source_file_name else project_dir / "story.ni"
                current = compute_hash(source_path)
                if state.get("STAGE_COMPILE_SOURCE_HASH") == current:
                    skip = True
            elif stage == "test":
                binary = find_binary(project_dir, bin_name, engine_spec)
                if binary:
                    current = compute_hash(binary)
                    if state.get("STAGE_TEST_BINARY_HASH") == current:
                        skip = True
            if skip:
                output.skip(f"No changes since last successful {stage}")
                results.append((stage, "SKIP", 0))
                continue

        start = time.time()
        try:
            if stage == "compile":
                stage_compile(name, project_dir, pipeline_cfg.sound,
                              engine=engine, engine_spec=engine_spec,
                              source_file=source_file_name)
            elif stage == "test":
                stage_test(name, project_dir, pipeline_cfg,
                           engine_spec=engine_spec)
            elif stage == "push":
                stage_push(name, args.message or "")

            elapsed = int(time.time() - start)
            results.append((stage, "OK", elapsed))

            # Update staleness
            if stage == "compile":
                source_path = project_dir / source_file_name if source_file_name else project_dir / "story.ni"
                save_state(state_file, "STAGE_COMPILE_SOURCE_HASH",
                           compute_hash(source_path))
                binary = find_binary(project_dir, bin_name, engine_spec)
                if binary:
                    save_state(state_file, "STAGE_COMPILE_BINARY_HASH", compute_hash(binary))
            elif stage == "test":
                binary = find_binary(project_dir, bin_name, engine_spec)
                if binary:
                    save_state(state_file, "STAGE_TEST_BINARY_HASH", compute_hash(binary))

        except (RuntimeError, Exception) as e:
            save_state(state_file, "STAGE_FAILED", stage)
            print()
            print(output.red(output.bold(f"=== PIPELINE FAILED at stage: {stage} ===")))
            print(f"  {e}")
            print()
            print("Options:")
            print(f"  Fix and resume:  python tools/pipeline.py {name} --continue")
            print(f"  Force retry:     python tools/pipeline.py {name} {stage} --force")
            sys.exit(1)

    # Summary
    total_time = int(time.time() - pipeline_start)
    print()
    print(output.bold(f"=== PIPELINE SUMMARY ({name}) ==="))
    for stage, status, secs in results:
        time_str = f" ({secs}s)" if secs > 0 else ""
        pad = " " * max(0, 12 - len(stage))
        if status == "OK":
            print(f"  {stage}:{pad}{output.green('OK')}{time_str}")
        elif status == "SKIP":
            print(f"  {stage}:{pad}{output.yellow('SKIP')} (unchanged)")
        elif status == "DRY_RUN":
            print(f"  {stage}:{pad}{output.blue('DRY RUN')}")
    print(f"  Total: {total_time}s")

    save_state(state_file, "STAGE_FAILED", "")


if __name__ == "__main__":
    main()
