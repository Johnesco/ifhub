# Platform fonts

The character sets the machines actually shipped, self-hosted because Google
Fonts carries none of them. `site/fonts.css` declares the `@font-face` rules;
`ensureRetroFonts()` in `site/themes.js` injects that stylesheet into the hub
and into every game iframe, so a game shows the same face inside the hub and on
its own `play.html`.

A browser downloads only the face the selected theme names, so picking a theme
costs one font, not seven.

## What is here, and under what terms

| File | Theme | Machine | Cell | Source and license |
|---|---|---|---|---|
| `WebPlus_IBM_VGA_8x16.woff` | MS-DOS | IBM MCGA/VGA (PS/2) video BIOS | 8×16 | [The Ultimate Oldschool PC Font Pack](https://int10h.org/oldschool-pc-fonts/) v2.2, outline version © VileR 2020 — [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/) |
| `PrintChar21.ttf` | Apple II | Apple II character ROM, 40-column | 7×8 | [Kreative Software Apple II Fonts](https://www.kreativekorp.com/software/fonts/apple2/) © Rebecca G. Bettencourt — Free Use License |
| `CandyAntics.ttf` | Atari 800 | ATASCII | 8×8 | [Kreative Software Retro Computing Fonts](https://www.kreativekorp.com/software/fonts/retro/) © Rebecca G. Bettencourt — Free Use License |
| `ProjectJasonTall.ttf` | Atari ST | TOS system font | 8×16 | [Kreative Software Retro Computing Fonts](https://www.kreativekorp.com/software/fonts/retro/) © Rebecca G. Bettencourt — Free Use License |
| `AnotherMansTreasureMIII64C.ttf` | TRS-80 | Model III character ROM, 64-column | 8×24 | [Kreative Software TRS-80 Fonts](https://www.kreativekorp.com/software/fonts/trs80/) © Rebecca G. Bettencourt — Free Use License |
| `PetMe64.ttf` | Commodore 64 | C64 character ROM, 40-column | 8×8 | [Kreative Software Retro Computing Fonts](https://www.kreativekorp.com/software/fonts/retro/) © Rebecca G. Bettencourt — Free Use License |
| `TopazDoubleSerif.ttf` | Amiga | AmigaOS 1.2/1.3 Topaz, doubled in height | 8×16 | Built by `tools/build_topaz.py` from [amigavision/TopazDouble](https://github.com/amigavision/TopazDouble) © 2024 Alex Limi — MIT; Topaz 1.x design by Bob Burns |

License texts, verbatim as distributed: `int10h-LICENSE.txt`,
`KreativeSoftware-FreeLicense.txt` (Free Use License version 1.2f, retrieved
2026-09-20), `TopazDouble-LICENSE.txt` (MIT).

CP/M keeps the Google-hosted VT323 — Kaypro terminals emulated the ADM-3A and
H19, so a DEC-family face is defensible there.

No face here carries a CRT effect. The C64 and Amiga used to use Jens Kutílek's
**Sixtyfour** and **Workbench** — the right machines' faces, under a good
license, but variable fonts whose `SCAN` and `BLED` axes carve scanline gaps
into the glyph outlines. That detail is smaller than a glyph, so it only lands
on whole pixels at multiples of the design grid and goes to fuzz or lumpy edges
everywhere else. An effect that distorts belongs on the screen, where it can be
tuned and switched off, not in a typeface (#135).

## Topaz is built, not downloaded

`TopazDoubleSerif.ttf` is the one file here nobody distributed as a font a
browser can read. Upstream ships an AmigaOS disk font; `tools/build_topaz.py`
parses it and traces each pixel into TrueType outlines. Regenerate it with:

    python tools/build_topaz.py

The source bitmap and its provenance live in `tools/fonts/TopazDouble/`. MIT
permits the conversion; it asks only that the notice travel with the result,
which is what `TopazDouble-LICENSE.txt` is.

## Rules for changing anything in this folder

**Do not modify these files by hand.** The Kreative Software Free Use License forbids
derivative works, which rules out subsetting them or converting them to WOFF —
they ship as the TTFs they were distributed as. Redistribution is permitted on
the conditions that the license travels with them verbatim and that Kreative
Korporation is credited, both of which this file and the license text satisfy.

The int10h font is CC BY-SA 4.0, which does permit adaptation, but requires
credit to **VileR** with a link to <https://int10h.org/oldschool-pc-fonts/> and
puts any modified version under a compatible license. It is shipped unmodified
as the `.woff` from the pack's web-fonts archive.

Neither license reaches the pages that display text in these fonts; both cover
the font files themselves.

## Sizing

Each face is a bitmap traced to outlines, so it is crisp at its native pixel
size and at whole multiples of it, and soft anywhere else. That is why the
themes set `bufferSize` to the sizes they do:

- IBM VGA 8×16 and Project Jason Tall are 16 pixels tall — native at `16px`.
- Print Char 21, Candy Antics and Pet Me 64 are 8 pixels tall — `16px` is 2×.
- Topaz Double Serif is 16 pixels tall — native at `16px`.
- Another Mans Treasure MIII 64C is 24 pixels tall — native at `24px`.

Changing a `bufferSize` off one of those values is what makes a theme look
blurry.
