#!/usr/bin/env python3
"""Set up a web player for a Sharpee interactive fiction game.

Takes a pre-built Sharpee browser dist (index.html + styles.css + game.js)
and prepares it for IF Hub: renames to play.html and adds the hub theme
listener so platform themes can override Sharpee's default styling.

Sharpee's own template, CSS, and menus are used as-is. The hub's "Classic"
theme simply lets Sharpee's default appearance show through.

Usage:
    # From a Sharpee dist/web/ build output:
    python tools/web/setup_sharpee.py \
        --title "My Game" --dist path/to/dist/web/ --out path/to/project

    # Or from individual files:
    python tools/web/setup_sharpee.py \
        --title "My Game" --html path/to/index.html --out path/to/project
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

THEME_LISTENER = """\

<script>
/* -- IF Hub theme listener (Sharpee) -- */
(function() {
  function applyPlatformTheme(g, sb) {
    var el = document.getElementById('platform-theme-override');
    if (el) el.remove();
    var style = document.createElement('style');
    style.id = 'platform-theme-override';
    style.textContent =
      ':root {' +
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
    document.head.appendChild(style);
  }

  function removePlatformTheme() {
    var el = document.getElementById('platform-theme-override');
    if (el) el.remove();
  }

  window.addEventListener('message', function(e) {
    if (!e.data) return;
    if (e.data.type === 'ifhub:applyTheme') {
      applyPlatformTheme(e.data.game, e.data.scrollbar);
    }
    if (e.data.type === 'ifhub:restoreOverlay') {
      removePlatformTheme();
    }
  });

  // Auto-apply theme from URL param (full-page mode from hub)
  var urlTheme = new URLSearchParams(window.location.search).get('theme');
  if (urlTheme && urlTheme !== 'classic') {
    var s = document.createElement('script');
    s.src = '/ifhub/themes.js';
    s.onload = function() {
      var t = getTheme(urlTheme);
      if (t) applyPlatformTheme(t.game, t.scrollbar);
    };
    document.head.appendChild(s);
  }
})();
</script>
"""


def main():
    parser = argparse.ArgumentParser(description="Set up Sharpee web player")
    parser.add_argument("--title", required=True, help="Game title")
    parser.add_argument("--dist", help="Path to Sharpee dist/web/ directory")
    parser.add_argument("--html", help="Path to a single index.html (alternative to --dist)")
    parser.add_argument("--out", required=True, help="Output project directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing play.html")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    play_html = out_dir / "play.html"

    if play_html.exists() and not args.force:
        print("  play.html already exists (use --force to overwrite)")
        return

    if args.dist:
        dist_dir = Path(args.dist)
        if not dist_dir.is_dir():
            print(f"Error: dist directory not found: {dist_dir}", file=sys.stderr)
            sys.exit(1)

        # Copy all dist files except index.html (becomes play.html)
        for f in dist_dir.iterdir():
            dest = out_dir / f.name
            if f.name == "index.html":
                continue
            if f.is_file():
                shutil.copy2(f, dest)
                print(f"  Copied {f.name}")
            elif f.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(f, dest)
                print(f"  Copied {f.name}/")

        source_html = dist_dir / "index.html"
        if not source_html.exists():
            print(f"Error: index.html not found in {dist_dir}", file=sys.stderr)
            sys.exit(1)

    elif args.html:
        source_html = Path(args.html)
        if not source_html.exists():
            print(f"Error: HTML file not found: {source_html}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: provide either --dist or --html", file=sys.stderr)
        sys.exit(1)

    # Read and transform the source HTML
    html = source_html.read_text(encoding="utf-8")

    # Replace <title> with the provided title
    html = re.sub(r'<title>[^<]*</title>', f'<title>{args.title}</title>', html)

    # Inject hub theme listener before </body>
    if "</body>" in html:
        html = html.replace("</body>", THEME_LISTENER + "</body>")
    else:
        html += THEME_LISTENER

    play_html.write_text(html, encoding="utf-8")
    print(f"  Generated play.html ({len(html)} bytes)")
    print(f"  Output: {out_dir}")


if __name__ == "__main__":
    main()
