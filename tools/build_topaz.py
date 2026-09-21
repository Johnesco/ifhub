#!/usr/bin/env python3
"""Build site/fonts/TopazDoubleSerif.ttf from the Amiga disk font it traces.

The Amiga theme's game pane uses Topaz, the Workbench 1.2/1.3 system font. The
one cleanly licensed, pixel-exact Topaz is amigavision/TopazDouble (MIT), and it
ships as an AmigaOS disk font -- a loadable hunk file holding a struct
TextFont -- which no browser can read. This script reads that file and writes a
TrueType font whose outlines trace every lit pixel exactly.

Nothing is drawn by hand. Every contour comes from the bitmap, so the TTF can be
rebuilt at any time from the vendored source in tools/fonts/TopazDouble/
(provenance in SOURCE.md there).

The result has no CRT effect in it: plain square pixels, 8x16, native at 16px
the way IBM VGA 8x16 is. Any scanline look belongs on the screen, not in the
typeface (#135).

Usage:
    python tools/build_topaz.py             # write site/fonts/TopazDoubleSerif.ttf
    python tools/build_topaz.py --preview   # also print sample glyphs as text

Requires fontTools (pip install fonttools). The site itself needs nothing.
"""

import argparse
import calendar
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.output import ok, fail
from lib.paths import SITE_DIR, TOOLS_DIR

try:
    from fontTools.fontBuilder import FontBuilder
    from fontTools.misc.timeTools import timestampSinceEpoch
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTFont
except ImportError:
    fail("fontTools is required: pip install fonttools")
    sys.exit(1)

SOURCE = TOOLS_DIR / "fonts" / "TopazDouble" / "TopazDoubleSerif-16"
OUTPUT = SITE_DIR / "fonts" / "TopazDoubleSerif.ttf"

FAMILY = "Topaz Double Serif"
COPYRIGHT = "Copyright (c) 2024 Alex Limi. Original Topaz 1.x design by Bob Burns."
LICENSE_NAME = "MIT License"
LICENSE_URL = "https://github.com/amigavision/TopazDouble/blob/main/LICENSE"

# Stamped into the head table instead of the time of the build, so rebuilding
# gives the same bytes and git sees no change. It is the date of the upstream
# commit the vendored source came from (tools/fonts/TopazDouble/SOURCE.md).
SOURCE_DATE = (2026, 3, 4, 19, 26, 32)

# One Amiga pixel is 100 font units, so a 16-pixel-tall cell is a 1600-unit em
# and the face is native at 16px -- the same grid as the other bitmap faces.
UNITS_PER_PIXEL = 100

# Typographic characters IF prose uses that Latin-1, and so the Amiga, never had.
# Drawing them with the nearest Topaz glyph keeps a word in one face instead of
# dropping a Courier New quote into the middle of it.
SUBSTITUTES = {
    0x2018: 0x27, 0x2019: 0x27,   # single curly quotes -> '
    0x201C: 0x22, 0x201D: 0x22,   # double curly quotes -> "
    0x2013: 0x2D, 0x2014: 0x2D,   # en and em dash      -> -
}

# --- AmigaOS load file and disk font structures -----------------------------

HUNK_HEADER = 0x3F3
HUNK_CODE = 0x3E9
HUNK_DATA = 0x3EA
DFH_ID = 0x0F80  # dfh_FileID of a disk font

# struct DiskFontHeader, after the 4-byte "moveq #-1,d0; rts" that stops a font
# file doing anything if someone runs it. The leading Node is 14 bytes.
DFH_OFFSET = 4
DFH_FORMAT = ">IIBBI HHI 32s"

# struct TextFont, which follows the header directly. Pointers are offsets from
# the start of the hunk; the loader would relocate them, and we do not load.
TF_FORMAT = ">IIBBI I H" "H B B H H H H B B I H I I I"
TF_FIELDS = (
    "ln_succ", "ln_pred", "ln_type", "ln_pri", "ln_name", "reply_port", "length",
    "ysize", "style", "flags", "xsize", "baseline", "bold_smear", "accessors",
    "lo_char", "hi_char", "char_data", "modulo", "char_loc", "char_space", "char_kern",
)


def read_hunk(data: bytes) -> bytes:
    """Return the body of the single code or data hunk in an Amiga load file."""
    def u32(pos):
        return struct.unpack_from(">I", data, pos)[0]

    if u32(0) != HUNK_HEADER:
        raise ValueError("not an Amiga load file (no HUNK_HEADER)")
    pos = 4
    while True:  # resident library names, terminated by a zero length
        n = u32(pos)
        pos += 4
        if n == 0:
            break
        pos += n * 4
    first, last = u32(pos + 4), u32(pos + 8)
    pos += 12 + (last - first + 1) * 4  # skip the table of hunk sizes
    if (u32(pos) & 0x3FFFFFFF) not in (HUNK_CODE, HUNK_DATA):
        raise ValueError("first hunk is neither code nor data")
    size = (u32(pos + 4) & 0x3FFFFFFF) * 4
    return data[pos + 8:pos + 8 + size]


def read_font(path: Path) -> dict:
    """Parse a disk font into its metrics and one bitmap per character."""
    hunk = read_hunk(path.read_bytes())

    dfh = struct.unpack_from(DFH_FORMAT, hunk, DFH_OFFSET)
    if dfh[5] != DFH_ID:
        raise ValueError(f"bad dfh_FileID {dfh[5]:#06x}, expected {DFH_ID:#06x}")
    tf = dict(zip(TF_FIELDS, struct.unpack_from(
        TF_FORMAT, hunk, DFH_OFFSET + struct.calcsize(DFH_FORMAT))))

    height, modulo = tf["ysize"], tf["modulo"]
    rows = [hunk[tf["char_data"] + r * modulo:tf["char_data"] + (r + 1) * modulo]
            for r in range(height)]

    def lit(row, bit):
        return (rows[row][bit >> 3] >> (7 - (bit & 7))) & 1

    # One CharLoc entry per character from lo to hi, plus the font's default
    # glyph, which the Amiga drew for anything it had no image for.
    count = tf["hi_char"] - tf["lo_char"] + 2
    glyphs = []
    for i in range(count):
        offset, width = struct.unpack_from(">HH", hunk, tf["char_loc"] + 4 * i)
        advance = tf["xsize"]
        if tf["char_space"]:
            advance = struct.unpack_from(">h", hunk, tf["char_space"] + 2 * i)[0]
        kern = struct.unpack_from(">h", hunk, tf["char_kern"] + 2 * i)[0] if tf["char_kern"] else 0
        pixels = {(kern + x, r) for r in range(height) for x in range(width)
                  if lit(r, offset + x)}
        glyphs.append({"pixels": pixels, "advance": advance, "width": width})

    return {
        "height": height,
        "xsize": tf["xsize"],
        "baseline": tf["baseline"],
        "lo_char": tf["lo_char"],
        "hi_char": tf["hi_char"],
        "proportional": bool(tf["char_space"]),
        "glyphs": glyphs,
    }


# --- Tracing ---------------------------------------------------------------

# Direction after each kind of turn, walking clockwise with y up.
RIGHT_TURN = {(1, 0): (0, -1), (0, -1): (-1, 0), (-1, 0): (0, 1), (0, 1): (1, 0)}
LEFT_TURN = {v: k for k, v in RIGHT_TURN.items()}


def trace(pixels: set, ascent: int) -> list:
    """Outline a glyph's lit pixels as closed contours, in pixel units, y up.

    Every lit pixel contributes its four edges walked clockwise; an edge shared
    by two lit pixels appears once in each direction and cancels. What survives
    is exactly the boundary -- outer edges clockwise, a hole's edges counter-
    clockwise -- which is TrueType's own convention, so the shapes need no union
    and no orientation pass, and adjacent pixels leave no seam between them.

    Where two pixels meet only at a corner the walk always takes the sharpest
    right turn, so diagonal neighbours stay separate shapes rather than joining
    into a figure eight.
    """
    edges = set()
    for x, r in pixels:
        top, bottom = ascent - r, ascent - r - 1
        corners = [(x, top), (x + 1, top), (x + 1, bottom), (x, bottom)]
        for i in range(4):
            edge = (corners[i], corners[(i + 1) % 4])
            reverse = (edge[1], edge[0])
            if reverse in edges:
                edges.remove(reverse)
            else:
                edges.add(edge)

    leaving = {}
    for start, end in edges:
        leaving.setdefault(start, []).append(end)

    contours = []
    while leaving:
        start = next(iter(leaving))
        point, heading, contour = start, None, [start]
        while True:
            exits = leaving[point]
            if heading is None or len(exits) == 1:
                nxt = exits[0]
            else:
                by_heading = {(e[0] - point[0], e[1] - point[1]): e for e in exits}
                for turn in (RIGHT_TURN[heading], heading, LEFT_TURN[heading]):
                    if turn in by_heading:
                        nxt = by_heading[turn]
                        break
            exits.remove(nxt)
            if not exits:
                del leaving[point]
            heading = (nxt[0] - point[0], nxt[1] - point[1])
            point = nxt
            if point == start:
                break
            contour.append(point)
        contours.append(simplify(contour))
    return contours


def simplify(points: list) -> list:
    """Drop the points that lie in the middle of a straight run."""
    kept = []
    n = len(points)
    for i, p in enumerate(points):
        a, b = points[i - 1], points[(i + 1) % n]
        if (p[0] - a[0]) * (b[1] - p[1]) != (p[1] - a[1]) * (b[0] - p[0]):
            kept.append(p)
    return kept


# --- TrueType --------------------------------------------------------------

def glyph_name(code: int) -> str:
    return "space" if code == 0x20 else f"uni{code:04X}"


def build(font: dict):
    upp = UNITS_PER_PIXEL
    ascent_px = font["baseline"] + 1          # rows above the baseline, inclusive
    descent_px = font["height"] - ascent_px
    upm = font["height"] * upp

    order, glyf, metrics, cmap = [".notdef"], {}, {}, {}

    def add(name, glyph):
        pen = TTGlyphPen(None)
        xs = []
        for contour in trace(glyph["pixels"], ascent_px):
            pen.moveTo((contour[0][0] * upp, contour[0][1] * upp))
            for x, y in contour[1:]:
                pen.lineTo((x * upp, y * upp))
            pen.closePath()
            xs.extend(p[0] for p in contour)
        glyf[name] = pen.glyph()
        metrics[name] = (glyph["advance"] * upp, (min(xs) if xs else 0) * upp)

    # The Amiga's default glyph stands in for anything the font lacks.
    add(".notdef", font["glyphs"][-1])

    for code in range(font["lo_char"], font["hi_char"] + 1):
        glyph = font["glyphs"][code - font["lo_char"]]
        # DEL and the C1 controls are control codes, not characters. The Amiga
        # points every one of them at its default block, so mapping them would
        # draw a solid block where the text should draw nothing.
        if code == 0x7F or 0x80 <= code <= 0x9F:
            continue
        name = glyph_name(code)
        add(name, glyph)
        order.append(name)
        cmap[code] = name

    for code, stand_in in SUBSTITUTES.items():
        if stand_in in cmap and code not in cmap:
            cmap[code] = cmap[stand_in]

    fb = FontBuilder(upm, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyf)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ascent_px * upp, descent=-descent_px * upp)
    fb.setupNameTable({
        "familyName": FAMILY,
        "styleName": "Regular",
        "uniqueFontIdentifier": f"{FAMILY} Regular; built by ifhub tools/build_topaz.py",
        "fullName": FAMILY,
        "psName": FAMILY.replace(" ", "") + "-Regular",
        "copyright": COPYRIGHT,
        "licenseDescription": LICENSE_NAME,
        "licenseInfoURL": LICENSE_URL,
        "description": "AmigaOS 1.2/1.3 Topaz at 8x16, traced pixel for pixel "
                       "from amigavision/TopazDouble.",
    })
    fb.setupOS2(
        sTypoAscender=ascent_px * upp, sTypoDescender=-descent_px * upp,
        sTypoLineGap=0, usWinAscent=ascent_px * upp, usWinDescent=descent_px * upp,
        xAvgCharWidth=font["xsize"] * upp, fsType=0, achVendID="NONE",
    )
    fb.setupPost(isFixedPitch=0 if font["proportional"] else 1)

    stamp = timestampSinceEpoch(calendar.timegm(SOURCE_DATE + (0, 0, 0)))
    fb.font["head"].created = fb.font["head"].modified = stamp
    fb.font.recalcTimestamp = False
    return fb


def preview(font: dict, text: str):
    for ch in text:
        glyph = font["glyphs"][ord(ch) - font["lo_char"]]
        print(f"  {ch!r}")
        for r in range(font["height"]):
            line = "".join("#" if (x, r) in glyph["pixels"] else "."
                           for x in range(font["xsize"]))
            marker = "  <- baseline" if r == font["baseline"] else ""
            print(f"    {line}{marker}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--preview", action="store_true",
                        help="print sample glyphs as text before writing")
    args = parser.parse_args()

    font = read_font(SOURCE)
    if args.preview:
        preview(font, "Agy@")

    fb = build(font)
    fb.save(str(OUTPUT))

    check = TTFont(str(OUTPUT))
    mapped = len(check.getBestCmap())
    ok(f"{OUTPUT.relative_to(SITE_DIR.parent)}: {len(check.getGlyphOrder())} glyphs, "
       f"{mapped} characters, {font['xsize']}x{font['height']} cell, "
       f"{check['head'].unitsPerEm} units per em")


if __name__ == "__main__":
    main()
