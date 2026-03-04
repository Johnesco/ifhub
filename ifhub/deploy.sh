#!/usr/bin/env bash
# deploy.sh — Gather game assets from sibling repos into games/ for publishing.
#
# Run from the ifhub directory:
#   bash deploy.sh
#
# Each game keeps its own repo. This script copies just the two files
# needed for the web player: the source (.ni) and the base64 binary (.ulx.js).

set -euo pipefail
cd "$(dirname "$0")"

I7_ROOT="$(cd .. && pwd)"

# Game definitions: local-id  source-ni-path  binary-path
#   Paths are relative to $I7_ROOT.
GAMES=(
  "sample      projects/sample/story.ni                           projects/sample/web/lib/parchment/sample.ulx.js"
  "dracula     projects/dracula/story.ni                          projects/dracula/web/lib/parchment/dracula.ulx.js"
  "feverdream  projects/feverdream/story.ni                       projects/feverdream/web/lib/parchment/feverdream.gblorb.js"
  "zork1-v0    none                                               projects/zork1/versions/v0/zork1.z3.js"
  "zork1-v1    projects/zork1/versions/v1/story.ni                projects/zork1/versions/v1/lib/parchment/zork1.ulx.js"
  "zork1-v2    projects/zork1/versions/v2/story.ni                projects/zork1/versions/v2/lib/parchment/zork1.ulx.js"
  "zork1-v3    projects/zork1/versions/v3/story.ni                projects/zork1/versions/v3/lib/parchment/zork1.gblorb.js"
  "zork1-v4    projects/zork1/versions/v4/story.ni                projects/zork1/versions/v4/lib/parchment/zork1.gblorb.js"
)

# Walkthrough definitions: local-id  walkthrough-dir
#   walkthrough-dir is relative to $I7_ROOT and should contain:
#     walkthrough.html  walkthrough.txt  walkthrough-guide.txt  walkthrough_output.txt
declare -A WALKTHROUGH_DIRS
WALKTHROUGH_DIRS=(
  [sample]="projects/sample/web"
  [zork1-v0]="projects/zork1/versions/v0"
  [zork1-v1]="projects/zork1/versions/v1"
  [zork1-v2]="projects/zork1/versions/v2"
  [zork1-v3]="projects/zork1/versions/v3"
  [zork1-v4]="projects/zork1/versions/v4"
  [feverdream]="projects/feverdream/tests"
)

WALKTHROUGH_FILES=(walkthrough.html walkthrough.txt walkthrough-guide.txt walkthrough_output.txt)

for entry in "${GAMES[@]}"; do
  read -r id src bin <<< "$entry"
  dest="games/$id"
  mkdir -p "$dest"

  if [[ "$src" != "none" ]]; then
    if [[ -f "$I7_ROOT/$src" ]]; then
      cp "$I7_ROOT/$src" "$dest/story.ni"
      echo "  $id: story.ni copied"
    else
      echo "  $id: WARNING — $src not found, skipping source"
    fi
  fi

  if [[ -f "$I7_ROOT/$bin" ]]; then
    cp "$I7_ROOT/$bin" "$dest/$(basename "$bin")"
    echo "  $id: $(basename "$bin") copied"
  else
    echo "  $id: WARNING — $bin not found, skipping binary"
  fi

  # Copy walkthrough files if defined for this game
  if [[ -n "${WALKTHROUGH_DIRS[$id]+x}" ]]; then
    wtdir="$I7_ROOT/${WALKTHROUGH_DIRS[$id]}"
    for wf in "${WALKTHROUGH_FILES[@]}"; do
      if [[ -f "$wtdir/$wf" ]]; then
        cp "$wtdir/$wf" "$dest/$wf"
        echo "  $id: $wf copied"
      else
        echo "  $id: WARNING — $wf not found in ${WALKTHROUGH_DIRS[$id]}"
      fi
    done
  fi

done

# Copy v0 ZIL source browser (standalone HTML that fetches from GitHub)
v0_browser="$I7_ROOT/projects/zork1/versions/v0/index.html"
if [[ -f "$v0_browser" ]]; then
  cp "$v0_browser" "games/zork1-v0/source-browser.html"
  echo "  zork1-v0: source-browser.html copied"
fi

# --- Copy Dracula custom landing page + BASIC source ---
echo ""
echo "Copying Dracula custom landing..."

dracula_landing="$I7_ROOT/projects/dracula/web/index.html"
if [[ -f "$dracula_landing" ]]; then
  cp "$dracula_landing" "games/dracula/index.html"
  echo "  dracula: custom landing page copied"
  # Fix fetch paths: ../src/basic/ → src/basic/, ../src/inform/story.ni → story.ni
  sed -i "s|fetch('../src/basic/|fetch('src/basic/|g" "games/dracula/index.html"
  sed -i "s|fetch('../src/inform/story.ni')|fetch('story.ni')|g" "games/dracula/index.html"
  echo "  dracula: fetch paths fixed"
fi

mkdir -p "games/dracula/src/basic"
for f in "$I7_ROOT/projects/dracula/src/basic/"*.bas; do
  if [[ -f "$f" ]]; then
    cp "$f" "games/dracula/src/basic/"
    echo "  dracula: $(basename "$f") copied"
  fi
done

# --- Copy Zork1 extra pages ---
echo ""
echo "Copying Zork1 extra pages..."

mkdir -p "games/zork1/extras" "games/zork1/extras/scenarios"
for f in map.html mapV0.html scenarios.html testing.html translation-challenges.html fdesc.html; do
  src_file="$I7_ROOT/projects/zork1/web/$f"
  if [[ -f "$src_file" ]]; then
    cp "$src_file" "games/zork1/extras/$f"
    echo "  zork1: extras/$f copied"
  else
    echo "  zork1: WARNING — $f not found, skipping"
  fi
done

# Copy scenarios directory contents
if [[ -d "$I7_ROOT/projects/zork1/web/scenarios" ]]; then
  cp "$I7_ROOT/projects/zork1/web/scenarios/"* "games/zork1/extras/scenarios/"
  echo "  zork1: extras/scenarios/* copied"
fi

# Fix relative links in extra pages: ./ → ../ (landing page is one dir up)
sed -i 's|href="./"|href="../"|g' games/zork1/extras/*.html 2>/dev/null || true

# --- Generate standalone play pages ---
echo ""
echo "Generating standalone play pages..."

python3 -c "
import json, time, re, os, sys

i7_root = sys.argv[1]

with open('games.json', encoding='utf-8') as f:
    games = json.load(f)

with open('play-template.html', encoding='utf-8') as f:
    generic_template = f.read()

# Cache-busting: append ?v=<timestamp> to .js and .css references so browsers
# don't serve stale scripts after a rebuild (e.g. after switching parchment.js).
cache_bust = 'v=' + str(int(time.time()))

for g in games:
    gid = g['id']
    dest = 'games/' + gid
    if not os.path.isdir(dest):
        continue

    title = g['title']
    binary = g['binary'].split('/')[-1]

    # Per-game template support: if playTemplate is set in games.json,
    # use that project-specific template (preserves CSS atmospheric effects).
    # Otherwise fall back to the generic hub template.
    custom_tmpl = g.get('playTemplate')
    if custom_tmpl:
        tmpl_path = os.path.join(i7_root, custom_tmpl)
        if os.path.isfile(tmpl_path):
            with open(tmpl_path, encoding='utf-8') as f:
                tmpl = f.read()
            print('  ' + gid + ': using custom template ' + custom_tmpl)
        else:
            print('  WARNING: ' + tmpl_path + ' not found, using generic template')
            tmpl = generic_template
    else:
        tmpl = generic_template

    page = tmpl.replace('__TITLE__', title)
    page = page.replace('__BINARY__', binary)
    page = page.replace('__STORY_FILE__', binary)
    page = page.replace('__STORY_PATH__', binary)
    page = page.replace('__LIB_PATH__', '../../lib/parchment/')
    page = re.sub(r'\.js\"', '.js?' + cache_bust + '\"', page)
    page = re.sub(r'\.css\"', '.css?' + cache_bust + '\"', page)

    # Write play.html (renamed from index.html)
    with open(dest + '/play.html', 'w', encoding='utf-8') as f:
        f.write(page)
    print('  ' + gid + ': play.html generated')

    # For versioned games, write a backward-compat redirect at index.html
    # (non-versioned games get a landing page at index.html instead)
    if re.search(r'-v\d+$', gid):
        redirect = '''<!DOCTYPE html>
<html><head>
<meta charset=\"utf-8\">
<meta http-equiv=\"refresh\" content=\"0;url=play.html\">
<title>Redirecting...</title>
</head><body>
<p>Redirecting to <a href=\"play.html\">play page</a>...</p>
</body></html>'''
        with open(dest + '/index.html', 'w', encoding='utf-8') as f:
            f.write(redirect)
        print('  ' + gid + ': index.html redirect generated')
" "$I7_ROOT"

# --- Generate landing pages ---
echo ""
echo "Generating landing pages..."

python3 -c "
import json, re, os

with open('games.json', encoding='utf-8') as f:
    games = json.load(f)

with open('landing-template.html', encoding='utf-8') as f:
    landing_tmpl = f.read()

# Build game map for version lookups
game_map = {g['id']: g for g in games}

for g in games:
    c = g.get('card')
    if not c or c.get('customLanding'):
        continue

    gid = g['id']
    base = re.sub(r'-v\d+\$', '', gid)
    is_versioned = base != gid

    # Play URL (from landing page to play page)
    if is_versioned:
        play_url = '../' + gid + '/play.html'
    else:
        play_url = 'play.html'

    # Play label
    if is_versioned:
        play_label = 'Play Latest Version' + (' (with sound)' if g.get('sound') else '')
    else:
        play_label = 'Play' + (' (with sound)' if g.get('sound') else '')

    # Subtitle section
    subtitle = c.get('subtitle', '')
    subtitle_html = '<p class=\"subtitle\">' + subtitle + '</p>' if subtitle else ''

    # Prose section
    prose = c.get('prose', [])
    prose_html = '\n'.join('<p>' + p + '</p>' for p in prose) if prose else '<p>' + c.get('description', '') + '</p>'

    # Extra pages section
    extra_pages = c.get('extraPages', [])
    if extra_pages:
        links = ' '.join('<a href=\"' + ep['href'] + '\">' + ep['label'] + '</a>' for ep in extra_pages)
        extra_pages_html = '<div class=\"extra-pages\">' + links + '</div>'
    else:
        extra_pages_html = ''

    # Version section
    version_ids = [gid] + c.get('versions', [])
    vd = c.get('versionDetails', {})
    if vd:
        version_cards = []
        for vid in version_ids:
            vg = game_map.get(vid)
            if not vg:
                continue
            d = vd.get(vid, {})
            label = vg.get('versionLabel', vid)
            tagline = d.get('tagline', '')
            features = d.get('features', [])
            extra_links = d.get('extraLinks', [])

            # Play link for this version
            if base == vid:
                v_play_url = 'play.html'
            else:
                v_play_url = '../' + vid + '/play.html'
            v_play_label = 'Play' + (' (with sound)' if vg.get('sound') else '')

            links_html = '<a href=\"' + v_play_url + '\">' + v_play_label + '</a>'
            links_html += ' <a href=\"../../app.html?game=' + vid + '\">Source</a>'

            if vg.get('walkthrough'):
                if base == vid:
                    wt_url = 'walkthrough.html'
                else:
                    wt_url = '../' + vid + '/walkthrough.html'
                links_html += ' <a href=\"' + wt_url + '\">Walkthrough</a>'

            for el in extra_links:
                links_html += ' <a href=\"' + el['href'] + '\">' + el['label'] + '</a>'

            features_html = ''
            if features:
                items = '\n'.join('    <li>' + f + '</li>' for f in features)
                features_html = '\n  <ul>\n' + items + '\n  </ul>'

            card_html = '<div class=\"version-entry\">\n'
            card_html += '  <h3>' + label + '</h3>\n'
            card_html += '  <p>' + tagline + '</p>' + features_html + '\n'
            card_html += '  <div class=\"version-links\">\n'
            card_html += '    ' + links_html + '\n'
            card_html += '  </div>\n'
            card_html += '</div>'
            version_cards.append(card_html)

        version_section = '<h2>Version History</h2>\n\n' + '\n\n'.join(version_cards) if version_cards else ''
    else:
        version_section = ''

    # Community section
    community = c.get('communityLinks', [])
    if community:
        sections = []
        for section in community:
            links = '\n    '.join('<a href=\"' + l['href'] + '\">' + l['label'] + '</a>' for l in section['links'])
            sec_html = '<div class=\"links-section\">\n'
            sec_html += '  <h3>' + section['heading'] + '</h3>\n'
            sec_html += '  <div class=\"links-grid\">\n    ' + links + '\n  </div>\n'
            sec_html += '</div>'
            sections.append(sec_html)
        community_html = '<h2>Community &amp; Related Projects</h2>\n\n' + '\n\n'.join(sections)
    else:
        community_html = ''

    # Footer
    footer = c.get('footer', '')

    # Build page from template
    page = landing_tmpl
    page = page.replace('__TITLE__', c['title'])
    page = page.replace('__SUBTITLE_SECTION__', subtitle_html)
    page = page.replace('__PLAY_URL__', play_url)
    page = page.replace('__PLAY_LABEL__', play_label)
    page = page.replace('__PROSE_SECTION__', prose_html)
    page = page.replace('__EXTRA_PAGES_SECTION__', extra_pages_html)
    page = page.replace('__VERSION_SECTION__', version_section)
    page = page.replace('__COMMUNITY_SECTION__', community_html)
    page = page.replace('__FOOTER__', footer)

    # Write landing page
    dest = 'games/' + base
    os.makedirs(dest, exist_ok=True)
    with open(dest + '/index.html', 'w', encoding='utf-8') as f:
        f.write(page)
    print('  ' + base + ': landing page generated')
"

echo ""
echo "Done. Serve with:  python -m http.server 8000 --directory $(pwd)"
echo "Open:              http://localhost:8000/"
