"""Rez adapter — imports Rez dist/ output and adds hub theme support."""

import re
import shutil
from pathlib import Path


THEME_INIT = """\

<script src="theme-listener.js"></script>
<script>
ThemeListener.init({
  buildCSS: function(g, sb) {
    return 'body, html { background: ' + g.bodyBg + ' !important; color: ' + g.bufferFg + ' !important; ' +
      'font-family: ' + g.propFamily + ' !important; }\\n' +
      '#game-container, .box, .card, .content, .section { background: ' + g.bufferBg + ' !important; color: ' + g.bufferFg + ' !important; }\\n' +
      '.title, .subtitle, h1, h2, h3, strong { color: ' + g.headerFg + ' !important; }\\n' +
      'a, a.choice { color: ' + g.inputFg + ' !important; }\\n' +
      'a:hover, a.choice:hover { color: ' + g.headerFg + ' !important; }\\n' +
      '.button, button { background: ' + g.gridBg + ' !important; color: ' + g.gridFg + ' !important; border-color: ' + g.gridBg + ' !important; }\\n' +
      '.button:hover, button:hover { background: ' + g.emphFg + ' !important; }\\n' +
      'blockquote { border-left-color: ' + g.inputFg + ' !important; color: ' + g.emphFg + ' !important; }\\n' +
      '.navbar, .hero { background: ' + g.gridBg + ' !important; }\\n' +
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
    """Import a built Rez game into the deploy directory."""
    title = conf["title"]
    force = conf.get("_force", False)
    script_dir = Path(__file__).resolve().parent.parent / "web"

    # The binary field for Rez points to the dist directory
    dist_name = conf["binary"]
    dist_dir = game_dir / dist_name
    if not dist_dir.is_dir():
        raise FileNotFoundError(f"Dist directory not found: {dist_dir}")

    deploy_dir.mkdir(parents=True, exist_ok=True)

    # Copy all dist files except index.html
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

    # Transform index.html → play.html
    source_html = dist_dir / "index.html"
    if not source_html.exists():
        raise FileNotFoundError(f"index.html not found in {dist_dir}")

    play_html = deploy_dir / "play.html"
    if not play_html.exists() or force:
        html = source_html.read_text(encoding="utf-8")
        html = re.sub(r'<title>[^<]*</title>', f'<title>{title}</title>', html)

        tl_src = script_dir / "parchment" / "theme-listener.js"
        tl_dest = deploy_dir / "theme-listener.js"
        if tl_src.exists():
            shutil.copy2(str(tl_src), str(tl_dest))
            print("  Copied theme-listener.js")

        if "</body>" in html:
            html = html.replace("</body>", THEME_INIT + "</body>")
        else:
            html += THEME_INIT

        play_html.write_text(html, encoding="utf-8")
        print(f"  Generated play.html ({len(html)} bytes)")
    else:
        print("  play.html exists, skipping")

    # Copy source
    source_name = conf.get("source")
    if source_name:
        src = game_dir / source_name
        if src.exists():
            shutil.copy2(str(src), str(deploy_dir / src.name))
            print(f"  Copied {source_name}")

    print(f"  Rez adapter done: {deploy_dir}")
