"""Template substitution for the wrapper pages the hub generates (index, source, walkthrough)."""

import re
import time
from pathlib import Path


def render_template(template_path: Path, replacements: dict[str, str]) -> str:
    """Apply __PLACEHOLDER__ -> value substitutions to a template and return the text.

    Kept separate from writing so a caller can ask what the template *would* produce
    and compare it with what a game folder has (check_drift.py).
    """
    text = template_path.read_text(encoding="utf-8")
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
    return text


def substitute_template(
    template_path: Path,
    output_path: Path,
    replacements: dict[str, str],
    cache_bust: bool = False,
):
    """Render a template to a file.

    cache_bust appends ?v=<timestamp> to .js and .css references.
    """
    text = render_template(template_path, replacements)
    if cache_bust:
        bust = f"v={int(time.time())}"
        text = re.sub(r'\.js"', f'.js?{bust}"', text)
        text = re.sub(r'\.css"', f'.css?{bust}"', text)
    output_path.write_text(text, encoding="utf-8")
