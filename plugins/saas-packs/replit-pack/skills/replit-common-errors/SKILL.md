---
name: replit-common-errors
description: |
  Diagnose and fix the top Replit errors: container sleep, port binding, Nix failures, DB limits.
  Use when encountering Replit errors, debugging failed deployments,
  or troubleshooting workspace and hosting issues.
  Trigger with phrases like "replit error", "fix replit", "replit not working",
  "debug replit", "replit broken", "replit deploy failed".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, debugging, errors]

---
# Replit Common Errors

## Overview
Quick reference for the 10 most common Replit errors with real solutions. Covers container lifecycle, Nix configuration, database, deployment, and networking issues.

## Prerequisites
- Replit Workspace access
- Shell tab for diagnostics
- Console tab for error logs

## Error Reference

### 1. Container Sleeping / App Goes Offline
```
Error: Your Repl is sleeping. Run it to wake up.
```
**Cause:** Free/Hacker plan Repls sleep after ~5 minutes of inactivity.
**Solution:**
- Use Replit Deployments (Autoscale or Reserved VM) for always-on
- Or set up external keep-alive pinging (UptimeRobot, cron-job.org)
- Check: Settings > Always On (deprecated in favor of Deployments)

---

### 2. Port Binding / Webview Not Loading
```
Error: EADDRINUSE: address already in use :::3000
```
**Cause:** Previous process still holding the port, or hardcoded port conflicts.
**Solution:**
```bash
# Find and kill the process
lsof -i :3000 | grep LISTEN
kill -9 <PID>

# Or use environment variable for port
```
```typescript
// Always use PORT env var
const port = parseInt(process.env.PORT || '3000');
app.listen(port, '0.0.0.0');  // Must be 0.0.0.0, not localhost
```

---

### 3. Nix Package Build Failure
```
Error: error: Package 'python-xyz' not found in channel 'stable-23_05'
```
**Cause:** Package name wrong, or Nix channel too old.
**Solution:**
```nix
# replit.nix — update channel and fix package names
{ pkgs }: {
  deps = [
    pkgs.nodejs-20_x          # not "nodejs" or "node"
    pkgs.python311             # not "python3" or "python"
    pkgs.python311Packages.pip # not "pip"
    pkgs.zlib                  # for native modules (Pillow, etc.)
    pkgs.openssl               # for crypto dependencies
  ];
}
```
```toml
# .replit — use current stable channel
[nix]
channel = "stable-24_05"
```
After editing `replit.nix`, reload the shell (exit and re-enter Shell tab).

---

### 4. DATABASE_URL Not Set
```
Error: Connection refused / ECONNREFUSED / DATABASE_URL is undefined
```
**Cause:** PostgreSQL not provisioned, or accessing outside Replit.
**Solution:**
1. Open the Database pane in the sidebar
2. Click "Create a database" if none exists
3. `DATABASE_URL` auto-populates in your environment
4. For legacy Replit DB: check `REPLIT_DB_URL` instead

---

### 5. Replit DB Write Failure (50MB Limit)
```
Error: Max storage size exceeded
```
**Cause:** Key-Value Database has a 50 MiB total limit (keys + values).
**Solution:**
```python
# Check current usage
from replit import db
total_keys = len(list(db.keys()))
print(f"Keys: {total_keys} / 5000")

# Migrate large data to Object Storage or PostgreSQL
from replit.object_storage import Client
storage = Client()
storage.upload_from_text('large-data.json', json.dumps(big_data))
del db['large_key']  # Free up KV space
```

---

### 6. Object Storage Bucket Not Found
```
Error: BucketNotFoundError: No bucket found
```
**Cause:** Object Storage bucket not provisioned for this Repl.
**Solution:**
1. Open the Object Storage pane in the sidebar
2. Create a new bucket (auto-names based on Repl)
3. Then use `new Client()` with no arguments — it auto-discovers

---

### 7. Auth Headers Empty
```
req.headers['x-replit-user-id'] === undefined
```
**Cause:** Replit Auth only works on deployed apps (`.replit.app` or custom domain), not in the Workspace Webview during development.
**Solution:**
```typescript
// Mock auth in development
function getUser(req: Request) {
  const userId = req.headers['x-replit-user-id'] as string;
  if (!userId && process.env.NODE_ENV !== 'production') {
    return { id: 'dev-user', name: 'Developer', image: '' };
  }
  if (!userId) return null;
  return {
    id: userId,
    name: req.headers['x-replit-user-name'] as string,
    image: req.headers['x-replit-user-profile-image'] as string,
  };
}
```

---

### 8. Module Not Found After Nix Change
```
Error: Cannot find module '@replit/database'
```
**Cause:** npm packages need separate install from Nix system packages.
**Solution:**
```bash
# Nix = system packages (Python runtime, PostgreSQL, etc.)
# npm/pip = language packages (express, flask, etc.)

# Both are needed:
# In replit.nix: pkgs.nodejs-20_x
# In shell: npm install @replit/database @replit/object-storage

# For Python:
# In replit.nix: pkgs.python311
# In shell: pip install replit flask
```

---

### 9. Deployment Build Timeout
```
Error: Build exceeded time limit
```
**Cause:** Heavy dependencies or slow build step.
**Solution:**
```toml
# .replit — optimize build
[deployment]
build = ["sh", "-c", "npm ci --production && npm run build"]
run = ["sh", "-c", "node dist/index.js"]

# Tips:
# - Use npm ci instead of npm install
# - Use --production to skip devDependencies
# - Use TypeScript incremental builds: tsc --incremental
# - Remove unused packages from package.json
```

---

### 10. Secrets Not Available in Deployment
```
Error: API_KEY is undefined in production
```
**Cause:** Secrets added in Workspace may not have synced (legacy behavior).
**Solution:**
- As of 2025, deployment secrets sync automatically with Workspace secrets
- Verify in Deployments > Settings > Environment Variables
- For Account-level secrets: Settings > Secrets (applies to all Repls)
- Restart the deployment after adding secrets

## Quick Diagnostics
```bash
# Check Replit status
curl -s https://status.replit.com/api/v2/summary.json | jq '.status.description'

# Check built-in env vars
echo "REPL_SLUG=$REPL_SLUG"
echo "REPL_OWNER=$REPL_OWNER"
echo "REPLIT_DB_URL=${REPLIT_DB_URL:+SET}"
echo "DATABASE_URL=${DATABASE_URL:+SET}"

# Check installed packages
npm list --depth=0 2>/dev/null
pip list 2>/dev/null | head -20
```

## Resources
- [Replit Status Page](https://status.replit.com)
- [Replit Docs](https://docs.replit.com)
- [Nix on Replit](https://docs.replit.com/programming-ide/nix-on-replit)
- [Replit Secrets](https://docs.replit.com/replit-workspace/workspace-features/secrets)

## Next Steps
For comprehensive debugging, see `replit-debug-bundle`.
