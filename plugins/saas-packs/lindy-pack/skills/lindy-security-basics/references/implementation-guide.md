# Lindy Security Basics - Implementation Guide

# Lindy Security Basics

## Overview
Security practices for Lindy AI agent integrations. Lindy creates autonomous AI agents that can access external services, execute actions, and handle data -- making security boundaries and permission controls essential.

## Prerequisites
- Lindy account with API access
- Understanding of Lindy's agent execution model
- Awareness of connected service permissions

## Instructions

### Step 1: API Key Protection

```python
import os

# Store Lindy API key securely
LINDY_API_KEY = os.environ.get("LINDY_API_KEY")
if not LINDY_API_KEY:
    raise RuntimeError("LINDY_API_KEY not set")

# For production: use secret manager
# NEVER commit keys or pass them as CLI arguments
```

### Step 2: Agent Permission Boundaries

Lindy agents can connect to external services. Limit what each agent can access.

```python
# Define explicit permission boundaries per agent
AGENT_PERMISSIONS = {
    "email-assistant": {
        "allowed_services": ["gmail"],
        "can_send": True,
        "can_delete": False,
        "max_emails_per_hour": 20
    },
    "data-analyst": {
        "allowed_services": ["google_sheets"],
        "can_write": False,  # read-only
        "can_delete": False
    }
}

def validate_agent_action(agent_id: str, action: str, service: str) -> bool:
    perms = AGENT_PERMISSIONS.get(agent_id, {})
    if service not in perms.get("allowed_services", []):
        raise PermissionError(f"Agent {agent_id} not authorized for {service}")
    if action == "delete" and not perms.get("can_delete", False):
        raise PermissionError(f"Agent {agent_id} cannot delete")
    return True
```

### Step 3: Webhook Signature Verification

```python
import hmac, hashlib

def verify_lindy_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.route('/lindy-webhook', methods=['POST'])
def handle_webhook():
    signature = request.headers.get('X-Lindy-Signature', '')
    if not verify_lindy_webhook(request.data, signature, WEBHOOK_SECRET):
        return {"error": "Invalid signature"}, 401
    return process_webhook(request.json)
```

### Step 4: Audit Agent Actions

Log all agent actions for security review and debugging.

```python
def audit_agent_action(agent_id: str, action: str, target: str, result: str):
    logger.info("Agent action", extra={
        "agent_id": agent_id,
        "action": action,
        "target": target,
        "result": result,
        "timestamp": datetime.utcnow().isoformat()
    })
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Agent accesses wrong service | No permission boundaries | Define explicit agent permissions |
| Fake webhook processed | No signature verification | Verify HMAC signatures |
| Key exposure | Hardcoded in source | Use environment variables |
| Runaway agent | No action limits | Set per-hour action quotas |

## Examples

### Permission Check Middleware
```python
@app.before_request
def check_agent_permissions():
    agent_id = request.json.get("agent_id")
    action = request.json.get("action")
    service = request.json.get("service")
    validate_agent_action(agent_id, action, service)
```

## Resources
- [Lindy API Docs](https://docs.lindy.ai)
- [Lindy Security](https://www.lindy.ai/security)
