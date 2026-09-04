"""Template substitution for the wrapper pages the hub generates (index, source, walkthrough)."""

import re
import time
from pathlib import Path


def substitute_template(
    template_path: Path,
    output_path: Path,
    replacements: dict[str, str],
    cache_bust: bool = False,
):
    """Apply __PLACEHOLDER__ -> value substitutions to a template file.

    cache_bust appends ?v=<timestamp> to .js and .css references.
    """
    text = template_path.read_text(encoding="utf-8")
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
    if cache_bust:
        bust = f"v={int(time.time())}"
        text = re.sub(r'\.js"', f'.js?{bust}"', text)
        text = re.sub(r'\.css"', f'.css?{bust}"', text)
    output_path.write_text(text, encoding="utf-8")
