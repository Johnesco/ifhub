# Dog Star Adventure

**Engine:** js-dos (DOSBox in browser)
**Author:** Lance Micklus (SoftSide Magazine, May 1979)
**Dialect:** GW-BASIC (line-numbered, uses INKEY$, FILE I/O)

## Why js-dos?

Dog Star uses `INKEY$` for "press any key" prompts and `OPEN/CLOSE` for save/load,
which won't work in wwwBASIC (synchronous) or qbjc (can't parse GW-BASIC line numbers
with GOTO targets). The only option is running it in a real BASIC interpreter via DOSBox.

## Setup Steps

1. **Get GW-BASIC or QBASIC:** You need `GWBASIC.EXE` or `QBASIC.EXE` (not redistributable)
2. **Create .jsdos bundle:**
   ```
   mkdir dogstar-bundle
   cp GWBASIC.EXE dogstar-bundle/
   cp src/basic/DOGSTAR.BAS dogstar-bundle/
   ```
3. **Create dosbox.conf:**
   ```ini
   [autoexec]
   mount c .
   c:
   gwbasic dogstar.bas
   ```
4. **ZIP as .jsdos:** `zip dogstar.jsdos -j dogstar-bundle/*`
5. **Generate play.html:**
   ```bash
   python tools/web/setup_basic.py \
       --engine jsdos --title "Dog Star Adventure" \
       --bundle dogstar.jsdos --out projects/dogstar
   ```

## Source

- Original: SoftSide Magazine, May 1979
- IF Archive: https://www.ifarchive.org/if-archive/games/source/basic/dogstar.bas
- Modified by Gern for Zenith Z-100 (1983/1984)
