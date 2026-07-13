# Lindy Security Basics -- Implementation Details

## API Key Security

### Secrets Audit

```python
import os
import re
from pathlib import Path

def audit_api_key_exposure() -> list[str]:
    """Scan common locations for accidentally exposed API keys."""
    issues = []
    SENSITIVE_FILES = [".env", ".env.local", "config.json", "settings.py"]
    KEY_PATTERN = re.compile(r"sk-lindy-[a-zA-Z0-9]{20,}", re.IGNORECASE)

    for filename in SENSITIVE_FILES:
        path = Path(filename)
        if path.exists():
            content = path.read_text()
            if KEY_PATTERN.search(content):
                issues.append(f"Potential Lindy API key found in {filename}")
            if ".env" in filename:
                gitignore = Path(".gitignore")
                if not gitignore.exists() or filename not in gitignore.read_text():
                    issues.append(f"{filename} not in .gitignore")

    if not os.environ.get("LINDY_API_KEY"):
        issues.append("LINDY_API_KEY not set in environment")

    return issues


issues = audit_api_key_exposure()
for issue in issues:
    print(f"[SECURITY WARNING] {issue}")
if not issues:
    print("[OK] No obvious API key exposure issues")
```

## Advanced Patterns

### Webhook Signature Verification

```python
import hmac
import hashlib
import os
import time
from flask import Flask, request, jsonify

app = Flask(__name__)
WEBHOOK_TOLERANCE_SECONDS = 300

def verify_lindy_webhook(payload: bytes, signature: str, secret: str) -> bool:
    if not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), payload, hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


@app.post("/lindy/webhook")
def handle_webhook():
    webhook_secret = os.environ.get("LINDY_WEBHOOK_SECRET", "")
    if not webhook_secret:
        return jsonify({"error": "webhook secret not configured"}), 500

    signature = request.headers.get("X-Lindy-Signature", "")
    if not signature or not verify_lindy_webhook(request.data, signature, webhook_secret):
        return jsonify({"error": "invalid signature"}), 401

    ts_header = request.headers.get("X-Lindy-Timestamp", "")
    if ts_header:
        try:
            age = time.time() - int(ts_header)
            if age > WEBHOOK_TOLERANCE_SECONDS:
                return jsonify({"error": f"webhook too old ({age:.0f}s)"}), 401
        except ValueError:
            pass

    event = request.json
    print(f"[OK] Verified webhook: {event.get('type')}")
    return jsonify({"status": "ok"}), 200
```

### Input Sanitization

```python
import re
from typing import Any

MAX_INPUT_LENGTH = 10_000
DISALLOWED_PATTERNS = [
    re.compile(r"<script[^>]*>", re.IGNORECASE),
    re.compile(r"\{\{.*?\}\}"),
]

def sanitize_agent_input(value: Any, field_name: str = "input") -> str:
    if not isinstance(value, str):
        raise TypeError(f"Expected string for {field_name}")
    if len(value) > MAX_INPUT_LENGTH:
        raise ValueError(f"{field_name} too long ({len(value)} chars, max {MAX_INPUT_LENGTH})")
    for pattern in DISALLOWED_PATTERNS:
        if pattern.search(value):
            raise ValueError(f"Disallowed content in {field_name}")
    # Strip control characters
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value).strip()
```

## Troubleshooting

### API Key Appeared in Git History

1. Immediately revoke the key in Lindy dashboard (Settings > API Keys)
2. Generate a new key and update all deployment environments
3. Use `git filter-repo` to remove the key from history
4. If repo was public, assume the key was scraped

### Webhook Signature Verification Fails

1. Verify you are using raw request bytes, not parsed JSON
2. Confirm the webhook secret matches exactly (no trailing whitespace)
3. Check that your proxy is not modifying the request body

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
