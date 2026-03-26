"""Sharpee adapter — imports dist/web/ output and adds hub theme support."""

import re
import shutil
from pathlib import Path


THEME_INIT = """\

<script src="theme-listener.js"></script>
<script>
ThemeListener.init({
  buildCSS: function(g, sb) {
    return ':root {' +
      '  --dos-blue: ' + g.bodyBg + ';' +
      '  --dos-cyan: ' + g.inputFg + ';' +
      '  --dos-white: ' + g.emphFg + ';' +
      '  --dos-bright-white: ' + g.bufferFg + ';' +
      '  --dos-black: ' + g.bodyBg + ';' +
      '}\\n' +
      'body { background: ' + g.bodyBg + ' !important; color: ' + g.bufferFg + ' !important; ' +
      '  font-family: ' + g.monoFamily + ' !important; ' +
      '  font-size: ' + g.bufferSize + ' !important; ' +
      '  line-height: ' + g.bufferLineHeight + ' !important; }\\n' +
      '#status-line { background: ' + g.gridBg + ' !important; color: ' + g.gridFg + ' !important; }\\n' +
      '#text-content p { color: ' + g.bufferFg + ' !important; }\\n' +
      '.command-echo { color: ' + g.emphFg + ' !important; }\\n' +
      '#command-input { color: ' + g.inputFg + ' !important; caret-color: ' + g.inputFg + '; }\\n' +
      '.prompt { color: ' + g.inputFg + ' !important; }\\n' +
      '* { scrollbar-color: ' + sb.thumb + ' ' + sb.track + '; }\\n' +
      '::-webkit-scrollbar { width: 10px; background: ' + sb.track + '; }\\n' +
      '::-webkit-scrollbar-thumb { background: ' + sb.thumb + '; border-radius: 4px; }\\n' +
      '::-webkit-scrollbar-thumb:hover { background: ' + sb.thumbHover + '; }\\n';
  },
  dispatchResize: false
});
</script>
"""


def setup(game_dir: Path, deploy_dir: Path, conf: dict):
    """Import a built Sharpee game into the deploy directory."""
    title = conf["title"]
    force = conf.get("_force", False)
    script_dir = Path(__file__).resolve().parent.parent / "web"

    # The binary field for Sharpee points to the dist/web directory
    dist_name = conf["binary"]
    dist_dir = game_dir / dist_name
    if not dist_dir.is_dir():
        raise FileNotFoundError(f"Dist directory not found: {dist_dir}")

    deploy_dir.mkdir(parents=True, exist_ok=True)

    # Copy all dist files except index.html (becomes play.html)
    for f in dist_dir.iterdir():
        dest = deploy_dir / f.name
        if f.name == "index.html":
            continue
        if f.is_file():
            shutil.copy2(str(f), str(dest))
            print(f"  Copied {f.name}")
        elif f.is_dir():
            if dest.exists():
                shutil.rmtree(str(dest))
            shutil.copytree(str(f), str(dest))
            print(f"  Copied {f.name}/")

    # Transform index.html → play.html with theme injection
    source_html = dist_dir / "index.html"
    if not source_html.exists():
        raise FileNotFoundError(f"index.html not found in {dist_dir}")

    play_html = deploy_dir / "play.html"
    if not play_html.exists() or force:
        html = source_html.read_text(encoding="utf-8")
        html = re.sub(r'<title>[^<]*</title>', f'<title>{title}</title>', html)

        # Copy theme-listener.js
        tl_src = script_dir / "parchment" / "theme-listener.js"
        tl_dest = deploy_dir / "theme-listener.js"
        if tl_src.exists():
            shutil.copy2(str(tl_src), str(tl_dest))
            print("  Copied theme-listener.js")

        # Inject theme init
        if "</body>" in html:
            html = html.replace("</body>", THEME_INIT + "</body>")
        else:
            html += THEME_INIT

        play_html.write_text(html, encoding="utf-8")
        print(f"  Generated play.html ({len(html)} bytes)")
    else:
        print("  play.html exists, skipping")

    # Copy source files — for multi-file projects, copy entire src/ tree
    source_name = conf.get("source")
    source_files = []
    if source_name:
        src_dir = game_dir / "src"
        if src_dir.is_dir():
            # Copy all .ts files from src/ tree
            for ts_file in sorted(src_dir.rglob("*.ts")):
                rel = ts_file.relative_to(game_dir)
                dest = deploy_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(ts_file), str(dest))
                source_files.append(str(rel).replace("\\", "/"))
            if source_files:
                print(f"  Copied {len(source_files)} source files from src/")
                conf["_source_files"] = source_files
        else:
            # Single file
            src = game_dir / source_name
            if src.exists():
                shutil.copy2(str(src), str(deploy_dir / src.name))
                print(f"  Copied {source_name}")

    # Extract walkthrough from .transcript files
    walkthrough_name = conf.get("walkthrough")
    if not walkthrough_name:
        # Auto-detect: check walkthroughs/ and tests/transcripts/
        for wdir in ("walkthroughs", "tests/transcripts"):
            candidates = sorted((game_dir / wdir).glob("*.transcript")) if (game_dir / wdir).is_dir() else []
            if candidates:
                walkthrough_name = str(candidates[0].relative_to(game_dir))
                break

    if walkthrough_name and (game_dir / walkthrough_name).exists():
        transcript_path = game_dir / walkthrough_name
        commands = extract_commands_from_transcript(transcript_path)
        if commands:
            # Write bare commands
            wt_path = deploy_dir / "walkthrough.txt"
            wt_path.write_text("\n".join(commands) + "\n", encoding="utf-8")
            print(f"  Extracted {len(commands)} commands -> walkthrough.txt")
            # Update conf so jukebox generates walkthrough.html
            conf["walkthrough"] = "walkthrough.txt"

        # Check for test results with full game output
        for results_dir in (game_dir / "dist" / "test-results", game_dir / "test-results"):
            if results_dir.is_dir():
                full_transcript = extract_full_transcript_from_results(results_dir)
                if full_transcript:
                    out_path = deploy_dir / "walkthrough_output.txt"
                    out_path.write_text(full_transcript, encoding="utf-8")
                    print(f"  Extracted full transcript -> walkthrough_output.txt")
                    break

    print(f"  Sharpee adapter done: {deploy_dir}")


def extract_commands_from_transcript(transcript_path: Path) -> list[str]:
    """Extract bare commands from a Sharpee .transcript file.

    Reads lines starting with '> ' and returns the command text.
    Skips assertion lines ([OK:], [FAIL:]) and metadata.
    """
    commands = []
    in_body = False
    for line in transcript_path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "---":
            in_body = True
            continue
        if not in_body:
            continue
        if line.startswith("> "):
            commands.append(line[2:].strip())
    return commands


def extract_full_transcript_from_results(results_dir: Path) -> str | None:
    """Read the most recent JSON test results and extract command+output pairs.

    Returns a formatted transcript string, or None if no results found.
    """
    import json

    json_files = sorted(results_dir.glob("results_*.json"), reverse=True)
    if not json_files:
        return None

    data = json.loads(json_files[0].read_text(encoding="utf-8"))
    lines = []
    for transcript in data.get("transcripts", []):
        for cmd in transcript.get("commands", []):
            inp = cmd["command"]["input"]
            out = cmd.get("actualOutput", "")
            lines.append(f">{inp}")
            if out:
                lines.append(out.rstrip())
            lines.append("")

    return "\n".join(lines) if lines else None
