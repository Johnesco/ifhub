---
name: serve
description: Start Portman dev server and register ifhub sites for local testing.
disable-model-invocation: true
argument-hint: "[port]"
---

# Start Local Dev Server (Portman)

Start Portman to serve ifhub and all game projects locally. Default port 9000.

## Steps

1. **Check if Portman is already running**:
   ```bash
   python /c/code/portman/portman.py status
   ```
   If already running, skip to step 4.

2. **Register ifhub sites** (idempotent — safe to re-run):
   ```bash
   python /c/code/portman/portman.py add ifhub "C:\code\ifhub\site"
   ```
   Then register each game project (organized by engine under text-games/):
   ```bash
   for engine_dir in /c/code/text-games/*/; do
       for game_dir in "$engine_dir"*/; do
           [ -f "$game_dir/play.html" ] || continue
           name=$(basename "$game_dir")
           python /c/code/portman/portman.py add "$name" "$game_dir"
       done
   done
   ```

3. **Start Portman** in the background:
   ```bash
   python /c/code/portman/portman.py serve --port <PORT>
   ```
   Use `run_in_background: true` on the Bash tool so it doesn't block the conversation.

4. **Verify it's running** (wait 2 seconds if just started):
   ```bash
   curl -s http://127.0.0.1:<PORT>/api/status
   ```

5. **Report URLs to user**:
   - Dashboard: `http://127.0.0.1:<PORT>/`
   - Hub: `http://127.0.0.1:<PORT>/ifhub/app.html`
   - Games: `http://127.0.0.1:<PORT>/<game>/play.html`

## Important

- Portman is a single process — no zombie risk. Multiple Claude tabs can use it safely.
- Sites are registered in `~/.portman/config.json` and persist across sessions.
- `add` works while the server is running (hot reload via API).
- Uses `Cache-Control: no-cache` — no stale content.
- Default port is 9000. If user specifies a port, use that instead.
- No need to kill zombies first — Portman doesn't create child processes.
