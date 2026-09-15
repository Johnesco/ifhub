"""Git and GitHub CLI operations."""

import base64
import subprocess
from pathlib import Path

from . import process
from .paths import GH_ORG


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


def current_branch(cwd: Path | str | None = None) -> str:
    """Return the current branch name."""
    r = process.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd, capture=True)
    return r.stdout.strip()


def has_upstream(cwd: Path | str | None = None) -> bool:
    """Return True if the current branch has an upstream tracking branch."""
    r = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "@{u}"],
        cwd=cwd, capture_output=True, text=True,
    )
    return r.returncode == 0


def is_repo_root(cwd: Path | str | None = None) -> bool:
    """True if cwd itself is a git repo (a .git directory or worktree file lives there)."""
    return (Path(cwd or ".") / ".git").exists()


def remote_url(cwd: Path | str | None = None, name: str = "origin") -> str | None:
    """The URL a remote points at, or None if cwd is not a repo or has no such remote.

    Confined to a repo rooted at cwd on purpose. Git otherwise walks up the tree to find
    one, so a plain game folder inside a workspace repo reports the *workspace's* origin —
    which is how sharpee-sound-test came to look like a game pointed at the wrong repo
    when it is simply not a repo at all (#109).
    """
    if not is_repo_root(cwd):
        return None
    r = subprocess.run(
        ["git", "remote", "get-url", name],
        cwd=cwd, capture_output=True, text=True,
    )
    return r.stdout.strip() if r.returncode == 0 else None


def has_remote(cwd: Path | str | None = None, name: str = "origin") -> bool:
    """Return True if the repo rooted at cwd has a remote of this name.

    Together with the remote's URL naming this game (remote_names_repo), this is what
    says whether a folder has been published. A .git directory alone does not: `git init`
    to keep local history while building a game is ordinary and says nothing about
    whether GitHub has it.
    """
    return remote_url(cwd, name) is not None


def remote_names_repo(url: str, repo_name: str) -> bool:
    """True if a remote URL points at GH_ORG/repo_name.

    Accepts https and ssh forms, with or without .git. has_remote() only says that a
    remote called origin exists; this says whether it is the right one (#109).
    """
    tail = url.strip().rstrip("/")
    if tail.endswith(".git"):
        tail = tail[:-4]
    tail = tail.replace(":", "/")  # git@github.com:Org/name -> git@github.com/Org/name
    return tail.lower().endswith(f"/{GH_ORG}/{repo_name}".lower())


def push(cwd: Path | str | None = None, set_upstream: str = "") -> int:
    """Push to remote. Auto-sets upstream if not configured."""
    if not set_upstream and not has_upstream(cwd):
        set_upstream = current_branch(cwd)
    cmd = ["git", "push"]
    if set_upstream:
        cmd.extend(["-u", "origin", set_upstream])
    r = process.run(cmd, cwd=cwd)
    return r.returncode


def init(cwd: Path | str | None = None):
    """Initialize a git repo."""
    process.run(["git", "init"], cwd=cwd)
    process.run(["git", "branch", "-M", "main"], cwd=cwd)


def remote_add(repo_name: str, cwd: Path | str | None = None, name: str = "origin") -> int:
    """Point a local repo at an existing GitHub repo."""
    r = process.run(
        ["git", "remote", "add", name, f"https://github.com/{GH_ORG}/{repo_name}.git"],
        cwd=cwd,
    )
    return r.returncode


def gh_repo_create(name: str, description: str, cwd: Path | str | None = None) -> int:
    """Create a GitHub repo via gh CLI."""
    r = process.run(
        ["gh", "repo", "create", f"{GH_ORG}/{name}", "--public",
         "--source=.", "--description", description],
        cwd=cwd,
    )
    return r.returncode


def gh_enable_pages(repo_name: str) -> int:
    """Enable GitHub Pages with workflow deployment."""
    r = process.run(
        ["gh", "api", f"repos/{GH_ORG}/{repo_name}/pages",
         "-X", "POST", "-f", "build_type=workflow"],
        capture=True,
    )
    return r.returncode


def gh_ensure_pages(repo_name: str) -> bool:
    """Ensure GitHub Pages is enabled (idempotent). Returns True if it was newly enabled."""
    check = process.run(
        ["gh", "api", f"repos/{GH_ORG}/{repo_name}/pages"],
        capture=True,
    )
    if check.returncode == 0:
        return False  # already enabled
    # Not enabled yet — enable it
    gh_enable_pages(repo_name)
    return True


def gh_repo_exists(repo_name: str) -> bool:
    """Return True if the GitHub repo exists."""
    r = process.run(
        ["gh", "repo", "view", f"{GH_ORG}/{repo_name}", "--json", "name"],
        capture=True,
    )
    return r.returncode == 0


def gh_workflow_dispatch(repo_name: str, workflow: str = "deploy-pages.yml") -> int:
    """Trigger a workflow run by hand.

    Needed the first time Pages is enabled: the push that creates the repo fires the
    deploy workflow before `build_type: workflow` is set, so that first run fails.
    The workflow declares `workflow_dispatch:`, so a fresh run can just be asked for.
    """
    r = process.run(
        ["gh", "workflow", "run", workflow, "--repo", f"{GH_ORG}/{repo_name}"],
        capture=True,
    )
    return r.returncode


def ahead_count(cwd: Path | str | None = None) -> int:
    """Commits on the current branch that its upstream does not have. 0 when no upstream."""
    r = subprocess.run(
        ["git", "rev-list", "--count", "@{u}..HEAD"],
        cwd=cwd, capture_output=True, text=True,
    )
    out = r.stdout.strip()
    return int(out) if r.returncode == 0 and out.isdigit() else 0


def gh_default_branch(repo_name: str) -> str | None:
    """The branch GitHub treats as the repo's default — the one Pages deploys from.

    None when the repo does not exist. A checkout on any other branch can commit and
    push cleanly and still deploy nothing (#108).
    """
    r = process.run(
        ["gh", "api", f"repos/{GH_ORG}/{repo_name}", "--jq", ".default_branch"],
        capture=True,
    )
    return (r.stdout.strip() or None) if r.returncode == 0 else None


def gh_file_on_branch(repo_name: str, path: str, ref: str) -> str | None:
    """A file's contents as committed on a branch of the GitHub repo. None if absent."""
    r = process.run(
        ["gh", "api", f"repos/{GH_ORG}/{repo_name}/contents/{path}?ref={ref}", "--jq", ".content"],
        capture=True,
    )
    if r.returncode != 0 or not r.stdout.strip():
        return None
    return base64.b64decode(r.stdout.strip()).decode("utf-8")
