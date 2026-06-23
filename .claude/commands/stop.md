---
description: Stop the frontend and backend servers
---

Find and stop any processes running on ports 3080 (frontend) and 8001 (backend).

- macOS/Linux: `lsof -ti:3080,8001 | xargs kill 2>/dev/null || true`
- Windows: Use `netstat -aon | findstr :PORT` to find PIDs, then `taskkill /F /PID <pid>`
