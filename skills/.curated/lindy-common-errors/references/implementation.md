# Lindy Common Errors -- Implementation Details

## Error Categories

### Authentication Errors (401)

**Diagnosis checklist:**

1. Verify `LINDY_API_KEY` is set in your environment
2. Check the key hasn't been rotated in Lindy dashboard under Settings > API Keys
3. Confirm the Authorization header format: `Authorization: Bearer <key>`

```python
import os

def validate_lindy_key() -> str:
    key = os.environ.get("LINDY_API_KEY", "")
    if not key:
        raise RuntimeError(
            "LINDY_API_KEY not set. Generate at settings/api"
        )
    if len(key) < 20:
        raise RuntimeError(f"LINDY_API_KEY appears truncated ({len(key)} chars)")
    return key
```

### Webhook Delivery Failures

**Common causes:**

- Endpoint URL unreachable from public internet
- SSL certificate invalid or self-signed
- Endpoint takes longer than 30 seconds to respond

```python
import hmac
import hashlib
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.post("/lindy/webhook")
def handle_lindy_webhook():
    secret = os.environ.get("LINDY_WEBHOOK_SECRET", "")
    if secret:
        sig = request.headers.get("X-Lindy-Signature", "")
        expected = "sha256=" + hmac.new(
            secret.encode(), request.data, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return jsonify({"error": "invalid signature"}), 401

    event = request.json
    print(f"[Lindy] Received: {event.get('type', 'unknown')}")
    return jsonify({"received": True}), 200
```

### Agent Run Failures

**Diagnosis steps:**

1. Retrieve run logs via API or the dashboard Runs tab
2. Check for missing required input fields
3. Verify third-party integrations have valid credentials

```python
import os
import requests

def get_run_status(agent_id: str, run_id: str) -> dict:
    resp = requests.get(
        f"https://api.lindy.ai/v1/agents/{agent_id}/runs/{run_id}",
        headers={"Authorization": f"Bearer {os.environ['LINDY_API_KEY']}"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") == "failed":
        error = data.get("error", {})
        print(f"[FAIL] Step {error.get('step_index')}: {error.get('message')}")
    return data
```

## Advanced Patterns

### Retry Wrapper for Transient Errors

```python
import time
import random
import functools
import requests

def lindy_retry(max_retries: int = 4, backoff_base: float = 1.5):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return fn(*args, **kwargs)
                except requests.HTTPError as e:
                    status = e.response.status_code if e.response else 0
                    if status in (429, 502, 503) and attempt < max_retries - 1:
                        wait = (backoff_base ** attempt) + random.uniform(0, 0.5)
                        print(f"[{status}] Retry {attempt+1}/{max_retries} in {wait:.1f}s")
                        time.sleep(wait)
                    else:
                        raise
        return wrapper
    return decorator

@lindy_retry()
def trigger_agent(agent_id: str, inputs: dict) -> dict:
    resp = requests.post(
        f"https://api.lindy.ai/v1/agents/{agent_id}/runs",
        headers={
            "Authorization": f"Bearer {os.environ['LINDY_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={"inputs": inputs},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
```

## Troubleshooting

### Agent Runs But Produces Wrong Output

1. Check if trigger event data format has changed
2. Verify all required integrations are still connected
3. Review run logs for warnings about missing fields
4. Test with a manual trigger using known-good inputs

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
