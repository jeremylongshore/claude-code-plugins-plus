---
name: replit-known-pitfalls
description: |
  Identify and avoid Replit anti-patterns and common integration mistakes.
  Use when reviewing Replit code for issues, onboarding new developers,
  or auditing existing Replit integrations for best practices violations.
  Trigger with phrases like "replit mistakes", "replit anti-patterns",
  "replit pitfalls", "replit what not to do", "replit code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Replit Known Pitfalls

## Overview
Real gotchas when building on Replit's cloud development platform. Replit's ephemeral container model, Nix-based environment, and always-on hosting create specific failure patterns that differ from traditional deployment.

## Prerequisites
- Active Replit account with deployment access
- Understanding of Replit's container lifecycle
- Familiarity with `.replit` and `replit.nix` configuration

## Instructions

### Step 1: Understand Ephemeral Filesystem

Replit containers reset on sleep. Files written outside persistent storage are lost.

```python
# BAD: writing to local filesystem for persistence
with open("user_data.json", "w") as f:
    json.dump(data, f)  # GONE when container sleeps

# GOOD: use Replit's key-value database or external storage
from replit import db
db["user_data"] = json.dumps(data)

# Or use Replit Object Storage for files
from replit.object_storage import Client
client = Client()
client.upload_from_text("user_data.json", json.dumps(data))
```

### Step 2: Handle Container Sleep/Wake Cycles

Free and Hacker plans sleep after inactivity. Cold starts take 10-30 seconds.

```python
# BAD: assuming server is always running
# Cron jobs and webhooks fail when container is asleep

# GOOD: use Replit Deployments for always-on, or handle cold starts
import time

startup_time = time.time()

@app.route('/health')
def health():
    uptime = time.time() - startup_time
    return {"status": "ok", "uptime_seconds": uptime}

# Use external cron (e.g., cron-job.org) to ping /health every 5 min
# Or upgrade to Always On / Deployments
```

### Step 3: Don't Hardcode Port Numbers

Replit assigns ports dynamically. Hardcoding causes binding failures.

```python
# BAD: hardcoded port
app.run(host='0.0.0.0', port=3000)  # may conflict

# GOOD: use environment variable
import os
port = int(os.environ.get('PORT', 3000))
app.run(host='0.0.0.0', port=port)
```

### Step 4: Manage Nix Dependencies Correctly

Missing system packages in `replit.nix` cause cryptic build failures.

```nix
# replit.nix - BAD: missing system deps for Python packages
{ pkgs }: {
  deps = [ pkgs.python311 ];  # PIL/Pillow will fail to build
}

# GOOD: include system libraries
{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.zlib
    pkgs.libjpeg
    pkgs.libffi
    pkgs.openssl
  ];
}
```

### Step 5: Replit DB Size Limits

Replit's built-in database has a 50MB limit. Large datasets need external storage.

```python
from replit import db

# BAD: storing large blobs in Replit DB
db["images"] = base64_encoded_images  # hits 50MB fast

# GOOD: use Replit DB for metadata, external storage for blobs
db["image_refs"] = json.dumps({"count": 100, "bucket": "s3://my-bucket"})
# Store actual files in Replit Object Storage or external S3
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Data lost on restart | Writing to ephemeral filesystem | Use Replit DB or Object Storage |
| Webhooks timing out | Container sleeping | Use Deployments for always-on |
| Port binding error | Hardcoded port number | Read from `PORT` env var |
| Build failures | Missing Nix system packages | Add to `replit.nix` deps |
| DB write failures | Exceeded 50MB limit | Migrate large data to external storage |

## Examples

### Proper .replit Configuration
```toml
# .replit
run = "python main.py"
entrypoint = "main.py"

[env]
PYTHONPATH = "${REPL_HOME}"

[deployment]
run = "python main.py"
deploymentTarget = "cloudrun"
```

## Resources
- [Replit Docs](https://docs.replit.com)
- [Replit DB Guide](https://docs.replit.com/hosting/databases/replit-database)
- [Nix on Replit](https://docs.replit.com/programming-ide/nix-on-replit)
