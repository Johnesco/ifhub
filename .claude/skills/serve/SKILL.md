---
name: serve
description: Start the ifhub dev server for local testing. Kills zombie processes first.
disable-model-invocation: true
argument-hint: "[port]"
---

# Start Local Dev Server

Start `tools/dev-server.py` for local testing. Default port 8000.

## Steps

1. **Kill zombies first** — always check for and kill stale python processes before starting:
   ```bash
   # Check for existing python processes
   tasklist 2>/dev/null | grep -i python
   # If any found, check which are listening on the target port
   netstat -ano 2>/dev/null | grep -E "LISTENING.*:<PORT>"
   # Kill any process holding the port (use the PID from netstat)
   taskkill //F //PID <pid>
   # If there are many zombie python processes (10+), kill them all:
   taskkill //F //IM python3.13.exe
   ```

2. **Start the server** in the background:
   ```bash
   python /c/code/ifhub/tools/dev-server.py --port <PORT> &
   ```
   Use `run_in_background: true` on the Bash tool so it doesn't block the conversation.

3. **Verify it's listening** (wait 2 seconds first):
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:<PORT>/ifhub/
   ```

4. **Report URLs to user**:
   - Hub: `http://127.0.0.1:<PORT>/ifhub/app.html`
   - Zork1 landing: `http://127.0.0.1:<PORT>/zork1/`
   - Zork1 v3: `http://127.0.0.1:<PORT>/zork1/v3/play.html`
   - Zork1 latest: `http://127.0.0.1:<PORT>/zork1/play.html`

## Important

- The dev server uses `Cache-Control: no-cache` — no stale content issues.
- The server maps `/<game>/*` to `projects/<game>/` and `/ifhub/*` to `ifhub/`.
- Always kill before starting. Never leave zombies.
- If port is in use and can't be freed, try port+1.
- Use `/kill-servers` to tear down when done.
