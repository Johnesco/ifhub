#!/usr/bin/env bash
# deploy.sh — Gather game assets from projects/ into games/ for hub publishing.
#
# Run from the ifhub directory:
#   bash deploy.sh
#
# Copies from each project: source (.ni), base64 binary (.ulx.js/.gblorb.js),
# walkthrough files, and landing pages. Then generates standalone play.html pages,
# walkthrough pages, and extracts card metadata from landing pages into cards.json.

set -euo pipefail
cd "$(dirname "$0")"

I7_ROOT="$(cd .. && pwd)"

# --- Copy game assets (source, binary, walkthrough) from projects ---
# Asset paths are defined in games.json deploy fields (single source of truth).
python3 "$I7_ROOT/tools/deploy/copy-assets.py" \
    --games-json games.json \
    --i7-root "$I7_ROOT"

# Copy v0 ZIL source browser (standalone HTML that fetches from GitHub)
v0_browser="$I7_ROOT/projects/zork1/versions/v0/index.html"
if [[ -f "$v0_browser" ]]; then
  cp "$v0_browser" "games/zork1-v0/source-browser.html"
  echo "  zork1-v0: source-browser.html copied"
fi

# --- Copy landing pages from projects ---
echo ""
echo "Copying landing pages..."

# Read landing fields from games.json and copy each to games/<base>/index.html
# Use mapfile to avoid pipe-to-while subshell issue on Git Bash
mapfile -t landing_entries < <(python3 -c "
import json, sys
with open('games.json') as f:
    games = json.load(f)
for g in games:
    landing = g.get('landing')
    if landing:
        print(g['id'] + '|' + landing)
")

for entry in "${landing_entries[@]}"; do
    entry="${entry%$'\r'}"  # strip Windows CR
    gid="${entry%%|*}"
    landing_rel="${entry#*|}"
    # Compute base directory (strip -v\d+ suffix)
    base=$(echo "$gid" | sed 's/-v[0-9]*$//')
    landing_src="$I7_ROOT/$landing_rel"
    dest_dir="games/$base"
    mkdir -p "$dest_dir"

    if [[ -f "$landing_src" ]]; then
        cp "$landing_src" "$dest_dir/index.html"
        echo "  $base: landing page copied from $landing_rel"

        # Apply path fixups for Dracula (fetch paths differ between project and hub context)
        if [[ "$base" == "dracula" ]]; then
            sed -i "s|fetch('../src/basic/|fetch('src/basic/|g" "$dest_dir/index.html"
            sed -i "s|fetch('../src/inform/story.ni')|fetch('story.ni')|g" "$dest_dir/index.html"
            echo "  dracula: fetch paths fixed"
        fi
    else
        echo "  WARNING: landing page not found: $landing_src"
    fi
done

# --- Copy Dracula BASIC source files ---
echo ""
echo "Copying Dracula BASIC source..."

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

python3 "$I7_ROOT/tools/deploy/generate-play-pages.py" \
    --games-json games.json \
    --template "$I7_ROOT/tools/web/play-template.html" \
    --i7-root "$I7_ROOT"

# --- Generate walkthrough pages ---
echo ""
echo "Generating walkthrough pages..."

python3 "$I7_ROOT/tools/deploy/generate-walkthrough-pages.py" \
    --games-json games.json \
    --template "$I7_ROOT/tools/web/walkthrough-template.html"

# --- Validate generated play pages ---
echo ""
echo "Validating play pages..."

validation_errors=0
for play_page in games/*/play.html; do
    game_dir=$(dirname "$play_page")
    if ! bash "$I7_ROOT/tools/validate-web.sh" "$game_dir"; then
        validation_errors=$((validation_errors + 1))
    fi
done

if [[ $validation_errors -gt 0 ]]; then
    echo ""
    echo "WARNING: $validation_errors game(s) failed validation"
fi

# --- Extract card metadata from landing pages ---
echo ""
echo "Extracting card metadata..."

python3 "$I7_ROOT/tools/deploy/extract-cards.py" \
    --games-json games.json \
    --i7-root "$I7_ROOT"

echo ""
echo "Done. Serve with:  python -m http.server 8000 --directory $(pwd)"
echo "Open:              http://localhost:8000/"
