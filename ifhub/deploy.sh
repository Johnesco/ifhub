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
  "feverdream  projects/feverdream/story.ni                       projects/feverdream/web/lib/parchment/feverdream.ulx.js"
  "zork1-v0    none                                               projects/zork1/versions/v0/zork1.z3.js"
  "zork1-v1    projects/zork1/versions/v1/story.ni                projects/zork1/versions/v1/lib/parchment/zork1.ulx.js"
  "zork1-v2    projects/zork1/versions/v2/story.ni                projects/zork1/versions/v2/lib/parchment/zork1.ulx.js"
  "zork1-v3    projects/zork1/versions/v3/story.ni                projects/zork1/versions/v3/lib/parchment/zork1.ulx.js"
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
  [feverdream]="projects/feverdream/tests"
)

WALKTHROUGH_FILES=(walkthrough.html walkthrough.txt walkthrough-guide.txt walkthrough_output.txt)

# Sound asset definitions: local-id  sound-dir (relative to $I7_ROOT)
#   Copies lib/ambient-audio.js, lib/sound-engine.js, lib/sound-config.js, and audio/ directory
declare -A SOUND_DIRS
SOUND_DIRS=(
  [zork1-v3]="projects/zork1/web"
  [feverdream]="projects/feverdream/web"
)

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

  # Copy sound assets if defined for this game
  if [[ -n "${SOUND_DIRS[$id]+x}" ]]; then
    snddir="$I7_ROOT/${SOUND_DIRS[$id]}"
    mkdir -p "$dest/lib"
    for sf in ambient-audio.js sound-engine.js sound-config.js; do
      if [[ -f "$snddir/lib/$sf" ]]; then
        cp "$snddir/lib/$sf" "$dest/lib/$sf"
        echo "  $id: lib/$sf copied"
      else
        echo "  $id: WARNING — lib/$sf not found in ${SOUND_DIRS[$id]}"
      fi
    done
    if [[ -d "$snddir/audio" ]]; then
      cp -r "$snddir/audio" "$dest/audio"
      echo "  $id: audio/ copied"
    else
      echo "  $id: WARNING — audio/ not found in ${SOUND_DIRS[$id]}"
    fi
  fi
done

# Copy v0 ZIL source browser (standalone HTML that fetches from GitHub)
v0_browser="$I7_ROOT/projects/zork1/versions/v0/index.html"
if [[ -f "$v0_browser" ]]; then
  cp "$v0_browser" "games/zork1-v0/source-browser.html"
  echo "  zork1-v0: source-browser.html copied"
fi

# --- Generate standalone play pages ---
echo ""
echo "Generating standalone play pages..."

python3 -c "
import json

with open('games.json') as f:
    games = json.load(f)

with open('play-template.html') as f:
    template = f.read()

with open('sound-standalone.html') as f:
    sound_block = f.read()

for g in games:
    gid = g['id']
    dest = 'games/' + gid
    import os
    if not os.path.isdir(dest):
        continue

    title = g['title']
    binary = g['binary'].split('/')[-1]
    sound = sound_block if g.get('sound') else ''

    page = template.replace('__TITLE__', title)
    page = page.replace('__BINARY__', binary)
    page = page.replace('__SOUND_SCRIPTS__', sound)

    with open(dest + '/index.html', 'w') as f:
        f.write(page)
    print('  ' + gid + ': index.html generated')
"

echo ""
echo "Done. Serve with:  python -m http.server 8000 --directory $(pwd)"
echo "Open:              http://localhost:8000/"
