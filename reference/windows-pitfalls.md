# Windows / Git Bash Pitfalls

## grep -oP (PCRE) Does Not Work

Git Bash's `grep` does not support `-P` (Perl-compatible regex). Attempting `grep -oP` produces: `grep: -P supports only unibyte and UTF-8 locales`.

**For test framework scripts**: Use `tools/testing/pcre_grep.py` — a portable Python replacement that handles `\K` lookbehinds and `(?=...)` lookaheads. For patterns using only basic alternation (`a|b|c`), use `grep -E` instead.

```bash
# BROKEN on Git Bash:
grep -oP 'score is \K[0-9]+' output.txt

# WORKS — pcre_grep.py (for \K and lookahead patterns):
python3 tools/testing/pcre_grep.py -o -l 'score is \K[0-9]+' output.txt

# WORKS — grep -E (for basic alternation, no PCRE features):
grep -ciE 'you have died|eaten by a grue' output.txt

# WORKS — grep -o + sed (for general use outside test framework):
grep -o 'is the file "[^"]*"' story.ni | sed 's/.*is the file "\([^"]*\)"/\1/'
```

## Pipe to `while read` Creates Subshell

Variables set inside a `while read` loop fed by a pipe are lost when the loop ends (subshell). Use `mapfile` or process substitution instead:

```bash
# BROKEN — RESOURCE_ID resets after loop:
grep ... | while read -r line; do RESOURCE_ID=$((RESOURCE_ID + 1)); done

# WORKS — collect into array first:
mapfile -t ITEMS < <(grep ...)
for item in "${ITEMS[@]}"; do RESOURCE_ID=$((RESOURCE_ID + 1)); done
```

## Native Interpreters (Preferred)

Native Windows CLI interpreters (`glulxe.exe`, `dfrotz.exe`) are built from source via MSYS2 and live at `tools/interpreters/`. They support piped I/O and `--rngseed` for deterministic testing — no WSL required.

**First-time setup**:
1. Install MSYS2: `winget install MSYS2.MSYS2`
2. Open MSYS2 UCRT64 terminal
3. Install tools: `pacman -S --needed mingw-w64-ucrt-x86_64-gcc make git`
4. Build: `cd /c/code/ifhub/tools/interpreters && bash build.sh`

The build script handles three MSYS2/UCRT compatibility patches automatically:
- CheapGlk `bzero` → `memset` (UCRT has no `bzero`)
- Frotz `strndup` → `strdup` (UCRT has no `strndup`)
- Frotz `-fcommon` (GCC 10+ defaults to `-fno-common`)

The Windows GUI `glulxe.exe` at `C:\Program Files\Inform7IDE\Interpreters\` does **not** support piped I/O and cannot be used for automated testing.

## WSL Fallback

If native interpreters are not built, the test framework and pipeline fall back to WSL with Linux-native interpreters. `wsl-check.sh` provides health checks and auto-recovery.

If WSL is unresponsive (`wsl -e echo` hangs), common fixes: `wsl --shutdown` from PowerShell, then retry. WSL2 is known to hang after sleep/hibernate due to Hyper-V architectural issues.
