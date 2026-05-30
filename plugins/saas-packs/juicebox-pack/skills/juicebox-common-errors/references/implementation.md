# Juicebox Common Errors -- Implementation Reference

## Overview

Diagnose and resolve common Juicebox API errors including authentication failures,
rate limiting, invalid requests, and integration connection issues.

## Prerequisites

- Juicebox API key and workspace ID
- curl or Python 3.9+ for testing
- Network access to Juicebox API endpoints

## Error Reference

| Code | Meaning | Fix |
|------|---------|-----|
| 401 | Invalid or missing API key | Check key format, regenerate if needed |
| 403 | Insufficient permissions | Verify workspace access level |
| 404 | Resource not found | Confirm project/report ID exists |
| 429 | Rate limit exceeded | Add exponential backoff |
| 500 | Server error | Retry with backoff; check status page |

## Authentication Diagnostics

```bash
# Test API key validity
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $JUICEBOX_API_KEY" \
  "https://api.juicebox.com/v1/projects"
# Expected: 200

# Check workspace access
curl -s \
  -H "Authorization: Bearer $JUICEBOX_API_KEY" \
  "https://api.juicebox.com/v1/workspaces" \
  | python3 -m json.tool
```

## Python Error Handler

```python
import os
import json
import time
import urllib.request
import urllib.error
from typing import Any

JUICEBOX_API_KEY = os.environ["JUICEBOX_API_KEY"]
BASE_URL = "https://api.juicebox.com/v1"

class JuiceboxAPIError(Exception):
    def __init__(self, status_code: int, message: str, detail: dict = None):
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.detail = detail or {}

def juicebox_request(
    method: str,
    path: str,
    payload: dict = None,
    retries: int = 3,
) -> Any:
    url = f"{BASE_URL}{path}"
    headers = {
        "Authorization": f"Bearer {JUICEBOX_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())

        except urllib.error.HTTPError as e:
            body_bytes = e.read()
            try:
                detail = json.loads(body_bytes)
            except Exception:
                detail = {"raw": body_bytes.decode(errors="replace")}

            if e.code == 429:
                wait = 2 ** attempt
                print(f"Rate limited. Waiting {wait}s (attempt {attempt + 1}/{retries})")
                time.sleep(wait)
                continue

            if e.code == 401:
                raise JuiceboxAPIError(401, "Authentication failed -- check JUICEBOX_API_KEY", detail)

            if e.code == 403:
                raise JuiceboxAPIError(403, "Forbidden -- insufficient permissions", detail)

            if e.code == 404:
                raise JuiceboxAPIError(404, f"Not found: {path}", detail)

            if e.code >= 500 and attempt < retries - 1:
                wait = 2 ** attempt
                print(f"Server error {e.code}. Retrying in {wait}s...")
                time.sleep(wait)
                continue

            raise JuiceboxAPIError(e.code, str(e), detail)

        except urllib.error.URLError as e:
            if attempt < retries - 1:
                print(f"Network error: {e}. Retrying...")
                time.sleep(1)
                continue
            raise

    raise JuiceboxAPIError(429, "Max retries exceeded after rate limiting")

def diagnose_connection() -> dict:
    """Run Juicebox connectivity diagnostics."""
    results = {}

    # Check API key presence
    key = os.environ.get("JUICEBOX_API_KEY", "")
    results["api_key_present"] = bool(key)
    results["api_key_length"] = len(key)

    # Check API reachability
    try:
        data = juicebox_request("GET", "/projects")
        results["api_reachable"] = True
        results["project_count"] = len(data.get("projects", []))
    except JuiceboxAPIError as e:
        results["api_reachable"] = False
        results["error"] = str(e)

    return results

if __name__ == "__main__":
    print(json.dumps(diagnose_connection(), indent=2))
```

## Common Integration Issues

### Missing workspace ID

```python
# Always include workspace_id in requests that require it
def get_project(project_id: str, workspace_id: str) -> dict:
    return juicebox_request("GET", f"/workspaces/{workspace_id}/projects/{project_id}")
```

### Invalid date range

```python
from datetime import datetime, timedelta

def valid_date_range(start: datetime, end: datetime) -> bool:
    """Juicebox requires: start < end, range <= 365 days."""
    if start >= end:
        return False
    if (end - start).days > 365:
        return False
    return True
```

## Resources

- Juicebox API Docs
- Juicebox Status

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
