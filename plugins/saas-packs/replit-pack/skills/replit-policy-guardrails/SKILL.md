---
name: replit-policy-guardrails
description: |
  Implement Replit lint rules, policy enforcement, and automated guardrails.
  Use when setting up code quality rules for Replit integrations, implementing
  pre-commit hooks, or configuring CI policy checks for Replit best practices.
  Trigger with phrases like "replit policy", "replit lint",
  "replit guardrails", "replit best practices check", "replit eslint".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Replit Policy Guardrails

## Overview
Policy enforcement for Replit-hosted applications. Replit's shared hosting model, public-by-default Repls, and resource limits require guardrails around secrets exposure, resource consumption, and deployment security.

## Prerequisites
- Replit account with Deployments access
- Understanding of Replit's security model
- Awareness of Replit's Terms of Service

## Instructions

### Step 1: Prevent Secrets Exposure

Replit Repls are public by default. Secrets in code are visible to anyone.

```python
# BAD: secrets in source code (visible in public Repl)
API_KEY = "sk-live-abc123"  # anyone can see this

# GOOD: use Replit Secrets (Environment Variables)
import os
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY not set in Replit Secrets")

# Validate secrets are properly configured on startup
REQUIRED_SECRETS = ["API_KEY", "DATABASE_URL", "JWT_SECRET"]
missing = [s for s in REQUIRED_SECRETS if not os.environ.get(s)]
if missing:
    raise RuntimeError(f"Missing required secrets: {missing}")
```

### Step 2: Resource Usage Limits

Replit enforces CPU and memory limits. Guard against runaway processes.

```python
import resource, signal

# Set memory limit (512MB)
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))  # 1024: 1 KB

# Set CPU time limit
def timeout_handler(signum, frame):
    raise TimeoutError("Request exceeded CPU time limit")

signal.signal(signal.SIGALRM, timeout_handler)

@app.route('/process')
def process_request():
    signal.alarm(30)  # 30 second max per request
    try:
        result = heavy_computation()
        return jsonify(result)
    except TimeoutError:
        return jsonify({"error": "Request timed out"}), 504  # HTTP 504 Gateway Timeout
    finally:
        signal.alarm(0)  # cancel alarm
```

### Step 3: Deployment Visibility Controls

Ensure production Repls are not accidentally made public.

```python
# Validate deployment configuration before deploy
def validate_deployment_config():
    checks = []
    # Check visibility
    if os.environ.get("REPL_SLUG"):
        # Running on Replit
        if not os.environ.get("REPL_DEPLOYMENT"):
            checks.append("WARNING: Running as Repl, not Deployment (may sleep)")
    # Check required env vars
    if os.environ.get("NODE_ENV") != "production":
        checks.append("WARNING: NODE_ENV not set to production")
    # Check HTTPS
    if not os.environ.get("REPL_DEPLOYMENT"):
        checks.append("INFO: Custom domain HTTPS managed by Replit Deployments")
    return checks
```

### Step 4: Database Access Controls

Replit DB is accessible to anyone with the Repl URL if not properly secured.

```python
from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth or not verify_token(auth):
            return jsonify({"error": "Unauthorized"}), 401  # HTTP 401 Unauthorized
        return f(*args, **kwargs)
    return decorated

# Protect all database-accessing endpoints
@app.route('/api/data')
@require_auth
def get_data():
    return jsonify(db.get("data"))
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secrets leaked | Code is public by default | Use Replit Secrets, never hardcode |
| OOM kills | No memory limits | Set resource limits, monitor usage |
| Unauthorized DB access | No auth on endpoints | Add authentication middleware |
| Repl sleeping in prod | Using Repl instead of Deployment | Use Replit Deployments for production |

## Examples

### Startup Security Check
```python
def security_check():
    issues = []
    if not os.environ.get("JWT_SECRET"):
        issues.append("CRITICAL: JWT_SECRET not configured")
    if os.environ.get("DEBUG") == "true":
        issues.append("WARNING: Debug mode enabled in production")
    return {"secure": len(issues) == 0, "issues": issues}
```

## Resources
- [Replit Security](https://docs.replit.com/programming-ide/workspace-features/secrets)
- [Replit Deployments](https://docs.replit.com/hosting/deployments)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale