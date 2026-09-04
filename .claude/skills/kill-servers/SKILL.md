---
name: kill-servers
description: Stop Portman and clean up any zombie python processes.
disable-model-invocation: true
---

# Stop Servers

Stop Portman and clean up any stale python processes.

## Steps

1. **Check Portman status**:
   ```bash
   python /c/code/portman/portman.py status
   ```

2. **Kill Portman** (if running — find its PID on the configured port):
   ```bash
   netstat -ano 2>/dev/null | grep -E "LISTENING.*:9000"
   # Kill the PID:
   taskkill //F //PID <pid>
   ```

3. **Check for zombie python processes**:
   ```bash
   tasklist 2>/dev/null | grep -c -i python
   ```
   If count > 2 (some may be legitimate), kill all:
   ```bash
   taskkill //F //IM python3.13.exe
   ```

4. **Verify cleanup**:
   ```bash
   tasklist 2>/dev/null | grep -i python || echo "All python processes cleared"
   netstat -ano 2>/dev/null | grep -E "LISTENING.*:(9000|8000|8001|5000)" || echo "All ports free"
   ```

5. **Report** what was killed and confirm ports are free.

## Note

Portman itself doesn't create zombies (single process, no children). But stray `python -m http.server` processes from old sessions may still be lurking. This skill cleans up everything.
