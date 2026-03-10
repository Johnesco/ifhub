"""Git and GitHub CLI operations."""

import subprocess
from pathlib import Path

from . import process


def status(cwd: Path | str | None = None) -> str:
    """Return git status --short output."""
    r = process.run(["git", "status", "--short"], cwd=cwd, capture=True)
    return r.stdout.strip()


def diff_cached_quiet(cwd: Path | str | None = None) -> bool:
    """Return True if there are staged changes."""
    r = process.run(["git", "diff", "--cached", "--quiet"], cwd=cwd, capture=True)
    return r.returncode != 0


def add(files: list[str | Path], cwd: Path | str | None = None):
    """Stage specific files."""
    str_files = [str(f) for f in files]
    process.run(["git", "add"] + str_files, cwd=cwd)


def add_all(cwd: Path | str | None = None):
    """Stage all changes."""
    process.run(["git", "add", "-A"], cwd=cwd)


def commit(message: str, cwd: Path | str | None = None) -> int:
    """Create a commit. Returns exit code."""
    r = process.run(["git", "commit", "-m", message], cwd=cwd)
    return r.returncode


def push(cwd: Path | str | None = None, set_upstream: str = "") -> int:
    """Push to remote. Returns exit code."""
    cmd = ["git", "push"]
    if set_upstream:
        cmd.extend(["-u", "origin", set_upstream])
    r = process.run(cmd, cwd=cwd)
    return r.returncode


def init(cwd: Path | str | None = None):
    """Initialize a git repo."""
    process.run(["git", "init"], cwd=cwd)
    process.run(["git", "branch", "-M", "main"], cwd=cwd)


def gh_repo_create(name: str, description: str, cwd: Path | str | None = None) -> int:
    """Create a GitHub repo via gh CLI."""
    r = process.run(
        ["gh", "repo", "create", f"Johnesco/{name}", "--public",
         "--source=.", "--description", description],
        cwd=cwd,
    )
    return r.returncode


def gh_enable_pages(repo_name: str) -> int:
    """Enable GitHub Pages with workflow deployment."""
    r = process.run(
        ["gh", "api", f"repos/Johnesco/{repo_name}/pages",
         "-X", "POST", "-f", "build_type=workflow"],
        capture=True,
    )
    return r.returncode
