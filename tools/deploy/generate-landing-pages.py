#!/usr/bin/env python3
"""Generate landing pages for games that have card metadata in games.json.

Usage:
    python3 generate-landing-pages.py \
        --games-json PATH \
        --template PATH \
        [--output-dir PATH]
"""

import argparse
import json
import os
import re


def main():
    parser = argparse.ArgumentParser(description="Generate landing pages from games.json")
    parser.add_argument("--games-json", required=True, help="Path to games.json")
    parser.add_argument("--template", required=True, help="Path to landing-template.html")
    parser.add_argument("--output-dir", default="games", help="Base output directory")
    args = parser.parse_args()

    with open(args.games_json, encoding="utf-8") as f:
        games = json.load(f)

    with open(args.template, encoding="utf-8") as f:
        landing_tmpl = f.read()

    # Build game map for version lookups
    game_map = {g["id"]: g for g in games}

    for g in games:
        c = g.get("card")
        if not c or c.get("customLanding"):
            continue

        gid = g["id"]
        base = re.sub(r"-v\d+$", "", gid)
        is_versioned = base != gid

        # Play URL (from landing page to play page)
        if is_versioned:
            play_url = "../" + gid + "/play.html"
        else:
            play_url = "play.html"

        # Play label
        if is_versioned:
            play_label = "Play Latest Version" + (" (with sound)" if g.get("sound") else "")
        else:
            play_label = "Play" + (" (with sound)" if g.get("sound") else "")

        # Subtitle section
        subtitle = c.get("subtitle", "")
        subtitle_html = '<p class="subtitle">' + subtitle + "</p>" if subtitle else ""

        # Prose section
        prose = c.get("prose", [])
        prose_html = (
            "\n".join("<p>" + p + "</p>" for p in prose)
            if prose
            else "<p>" + c.get("description", "") + "</p>"
        )

        # Extra pages section
        extra_pages = c.get("extraPages", [])
        if extra_pages:
            links = " ".join(
                '<a href="' + ep["href"] + '">' + ep["label"] + "</a>"
                for ep in extra_pages
            )
            extra_pages_html = '<div class="extra-pages">' + links + "</div>"
        else:
            extra_pages_html = ""

        # Version section
        version_ids = [gid] + c.get("versions", [])
        vd = c.get("versionDetails", {})
        if vd:
            version_cards = []
            for vid in version_ids:
                vg = game_map.get(vid)
                if not vg:
                    continue
                d = vd.get(vid, {})
                label = vg.get("versionLabel", vid)
                tagline = d.get("tagline", "")
                features = d.get("features", [])
                extra_links = d.get("extraLinks", [])

                # Play link for this version
                if base == vid:
                    v_play_url = "play.html"
                else:
                    v_play_url = "../" + vid + "/play.html"
                v_play_label = "Play" + (" (with sound)" if vg.get("sound") else "")

                links_html = '<a href="' + v_play_url + '">' + v_play_label + "</a>"
                links_html += ' <a href="../../app.html?game=' + vid + '">Source</a>'

                if vg.get("walkthrough"):
                    if base == vid:
                        wt_url = "walkthrough.html"
                    else:
                        wt_url = "../" + vid + "/walkthrough.html"
                    links_html += ' <a href="' + wt_url + '">Walkthrough</a>'

                for el in extra_links:
                    links_html += ' <a href="' + el["href"] + '">' + el["label"] + "</a>"

                features_html = ""
                if features:
                    items = "\n".join("    <li>" + feat + "</li>" for feat in features)
                    features_html = "\n  <ul>\n" + items + "\n  </ul>"

                card_html = '<div class="version-entry">\n'
                card_html += "  <h3>" + label + "</h3>\n"
                card_html += "  <p>" + tagline + "</p>" + features_html + "\n"
                card_html += '  <div class="version-links">\n'
                card_html += "    " + links_html + "\n"
                card_html += "  </div>\n"
                card_html += "</div>"
                version_cards.append(card_html)

            version_section = (
                '<h2>Version History</h2>\n\n' + "\n\n".join(version_cards)
                if version_cards
                else ""
            )
        else:
            version_section = ""

        # Community section
        community = c.get("communityLinks", [])
        if community:
            sections = []
            for section in community:
                links = "\n    ".join(
                    '<a href="' + l["href"] + '">' + l["label"] + "</a>"
                    for l in section["links"]
                )
                sec_html = '<div class="links-section">\n'
                sec_html += "  <h3>" + section["heading"] + "</h3>\n"
                sec_html += '  <div class="links-grid">\n    ' + links + "\n  </div>\n"
                sec_html += "</div>"
                sections.append(sec_html)
            community_html = (
                "<h2>Community &amp; Related Projects</h2>\n\n" + "\n\n".join(sections)
            )
        else:
            community_html = ""

        # Footer
        footer = c.get("footer", "")

        # Build page from template
        page = landing_tmpl
        page = page.replace("__TITLE__", c["title"])
        page = page.replace("__SUBTITLE_SECTION__", subtitle_html)
        page = page.replace("__PLAY_URL__", play_url)
        page = page.replace("__PLAY_LABEL__", play_label)
        page = page.replace("__PROSE_SECTION__", prose_html)
        page = page.replace("__EXTRA_PAGES_SECTION__", extra_pages_html)
        page = page.replace("__VERSION_SECTION__", version_section)
        page = page.replace("__COMMUNITY_SECTION__", community_html)
        page = page.replace("__FOOTER__", footer)

        # Write landing page
        dest = os.path.join(args.output_dir, base)
        os.makedirs(dest, exist_ok=True)
        with open(os.path.join(dest, "index.html"), "w", encoding="utf-8") as f:
            f.write(page)
        print("  " + base + ": landing page generated")


if __name__ == "__main__":
    main()
