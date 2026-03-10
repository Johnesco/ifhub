"""Path resolution and conversion utilities for IF Hub tools.

Consolidates duplicated path logic from run.py, dashboard.py, and explore.py
into a single source of truth.
"""

import os
import re
import sys
from pathlib import Path

# Resolved once at import time, relative to this file:
#   tools/lib/paths.py -> tools/ -> ifhub/
TOOLS_DIR = Path(__file__).resolve().parent.parent
I7_ROOT = TOOLS_DIR.parent
PROJECTS_DIR = I7_ROOT / "projects"
IFHUB_DIR = I7_ROOT / "ifhub"
TESTING_DIR = TOOLS_DIR / "testing"
WEB_DIR = TOOLS_DIR / "web"

# Compiler paths (Windows system install)
I7_COMPILER = Path(r"C:\Program Files\Inform7IDE\Compilers\inform7.exe")
I6_COMPILER = Path(r"C:\Program Files\Inform7IDE\Compilers\inform6.exe")
INBLORB = Path(r"C:\Program Files\Inform7IDE\Compilers\inblorb.exe")
I7_INTERNAL = Path(r"C:\Program Files\Inform7IDE\Internal")

# Native interpreters
NATIVE_GLULXE = TOOLS_DIR / "interpreters" / "glulxe.exe"
NATIVE_DFROTZ = TOOLS_DIR / "interpreters" / "dfrotz.exe"


def project_dir(name: str) -> Path:
    """Return absolute path to projects/<name>/."""
    return PROJECTS_DIR / name


def to_posix(path: str | Path) -> str:
    """Convert a Windows path to MSYS2/Git Bash posix form.

    C:\\code\\ifhub -> /c/code/ifhub
    """
    s = str(path).replace("\\", "/")
    m = re.match(r"^([A-Za-z]):/", s)
    if m:
        s = "/" + m.group(1).lower() + "/" + s[3:]
    return s


def to_windows(path: str) -> str:
    """Convert a MSYS2/Git Bash path to Windows form.

    /c/code/ifhub -> C:\\code\\ifhub
    """
    m = re.match(r"^/([a-zA-Z])/(.*)", path)
    if m:
        drive = m.group(1).upper()
        rest = m.group(2).replace("/", "\\")
        return f"{drive}:\\{rest}"
    return path.replace("/", "\\")
