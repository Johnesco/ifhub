# Topaz Double (vendored source)

`build_topaz.py` reads the Amiga disk font here and writes
`site/fonts/TopazDoubleSerif.ttf`. Keeping the source in the repo makes that
file reproducible without the network.

| File here | Upstream path |
|---|---|
| `TopazDoubleSerif-16` | `Fonts/Topaz Double Serif/16` |
| `LICENSE` | `LICENSE` |

- Upstream: https://github.com/amigavision/TopazDouble
- Commit: `c7eb6f8fe40b8f0533ee3f5e76b7f28ea43e8ee8` (2026-03-04)
- Blob of `TopazDoubleSerif-16`: `bcb4d0ea6ff7224b12a1a49d1a17e6a3855205ac`, 4152 bytes —
  check with `git hash-object tools/fonts/TopazDouble/TopazDoubleSerif-16`
- License: MIT, © 2024 Alex Limi. The TTF built from this file is a
  derivative, so the same notice ships beside it as
  `site/fonts/TopazDouble-LICENSE.txt`.

**Serif** is the AmigaOS 1.2/1.3 Topaz, designed by Bob Burns; **Sans** is the
2.x/3.x one. The Amiga theme imitates Workbench 1.3, so it takes Serif. Both
are drawn 8x16: the original 8x8 Topaz doubled in height, because the Amiga's
640x200 and 640x256 modes had tall pixels, and a square-pixel screen shows
plain 8x8 Topaz at half the height the Amiga did.

Do not edit `TopazDoubleSerif-16`. Change the conversion in `build_topaz.py`,
or take a new upstream commit and update this file.
