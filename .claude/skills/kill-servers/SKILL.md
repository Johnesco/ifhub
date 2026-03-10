---
name: kill-servers
description: Kill all local dev servers and zombie python processes. Use after testing.
disable-model-invocation: true
---

# Kill Local Servers

Stop all dev servers and clean up zombie python processes.

## Steps

1. **Find what's listening** on common dev ports:
   ```bash
   netstat -ano 2>/dev/null | grep -E "LISTENING.*:(8000|8001|8080|3000)" || echo "No servers listening"
   ```

2. **Kill specific port holders** (if found — use PIDs from netstat):
   ```bash
   taskkill //F //PID <pid>
   ```

3. **Kill all zombie python processes** — on Windows, orphaned python processes accumulate and never exit:
   ```bash
   tasklist 2>/dev/null | grep -c -i python
   # If count > 0:
   taskkill //F //IM python3.13.exe
   ```

4. **Verify cleanup**:
   ```bash
   tasklist 2>/dev/null | grep -i python || echo "All python processes cleared"
   netstat -ano 2>/dev/null | grep -E "LISTENING.*:(8000|8001|8080|3000)" || echo "No servers listening"
   ```

5. **Report** the count of processes killed and confirm ports are free.

## Why This Exists

On Windows/Git Bash, `python -m http.server` and `dev-server.py` processes frequently become zombies — they stop serving but never exit. Over multiple sessions this accumulates dozens or hundreds of dead processes. Always run this after testing, or before `/serve` starts a new one.
