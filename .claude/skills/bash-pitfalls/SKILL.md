# Bash Pitfalls (Windows / Git Bash)

globs: ["**/*.sh", "**/project.conf", "tools/**"]

## Quick Checklist

When writing or editing shell scripts on this project:

1. **No `grep -oP`** — Git Bash lacks PCRE. Use `pcre_grep.py` or `grep -E`
2. **No pipe to `while read`** — Variables set in the loop are lost (subshell). Use `mapfile` + `for`
3. **Native interpreters** — `tools/interpreters/glulxe.exe` and `dfrotz.exe` preferred over WSL
4. **WSL fallback** — If native not built, tests auto-fall back to WSL. `wsl --shutdown` fixes hangs

See `reference/windows-pitfalls.md` for full details, examples, and MSYS2 build instructions.
