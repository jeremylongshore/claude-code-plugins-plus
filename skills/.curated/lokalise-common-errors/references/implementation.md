# Lokalise Common Errors -- Implementation Reference

## Overview

Diagnose and fix common Lokalise API errors including authentication failures,
rate limiting, missing keys, and file format issues.

## Prerequisites

- Lokalise API token
- Project ID
- curl or Python for testing

## Error Reference

| Code | Meaning | Fix |
|------|---------|-----|
| 401 | Invalid API token | Regenerate token in Lokalise settings |
| 403 | Insufficient permissions | Check token scope (read vs read+write) |
| 404 | Project or resource not found | Verify project ID |
| 422 | Validation error | Check request body schema |
| 429 | Rate limit exceeded | Add exponential backoff |

## Authentication Diagnostics

```bash
# Test API token
curl -s \
  -H "X-Api-Token: $LOKALISE_API_TOKEN" \
  "https://api.lokalise.com/api2/projects" \
  | python3 -m json.tool | head -20

# Expected: { "projects": [...] }
# If 401: token is invalid or expired
# If 403: token lacks read permission
```

## Python Error Handler with Retry

```python
import os
import json
import time
import urllib.request
import urllib.error

LOKALISE_API_TOKEN = os.environ["LOKALISE_API_TOKEN"]
PROJECT_ID = os.environ["LOKALISE_PROJECT_ID"]
BASE_URL = "https://api.lokalise.com/api2"


class LokalisError(Exception):
    def __init__(self, status: int, message: str, detail: dict = None):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.detail = detail or {}


def lokalise_request(method: str, path: str, payload: dict = None, retries: int = 3) -> dict:
    headers = {
        "X-Api-Token": LOKALISE_API_TOKEN,
        "Content-Type": "application/json",
    }
    body = json.dumps(payload).encode() if payload else None
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())

        except urllib.error.HTTPError as e:
            try:
                detail = json.loads(e.read())
            except Exception:
                detail = {}

            if e.code == 401:
                raise LokalisError(401, "Invalid API token -- check LOKALISE_API_TOKEN", detail)

            if e.code == 403:
                raise LokalisError(403, "Token lacks required permission", detail)

            if e.code == 404:
                raise LokalisError(404, f"Not found: {path}", detail)

            if e.code == 422:
                errors = detail.get("errors", [])
                msg = "; ".join(str(e) for e in errors) if errors else str(detail)
                raise LokalisError(422, f"Validation failed: {msg}", detail)

            if e.code == 429:
                wait = 2 ** attempt
                print(f"Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue

            if e.code >= 500 and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue

            raise LokalisError(e.code, str(e), detail)

        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(1)
                continue
            raise

    raise LokalisError(429, "Max retries exceeded")


def diagnose_project() -> dict:
    """Run Lokalise project diagnostics."""
    results = {}

    # Check token
    key = LOKALISE_API_TOKEN
    results["token_present"] = bool(key)
    results["token_length"] = len(key)

    # Check project access
    try:
        project = lokalise_request("GET", f"/projects/{PROJECT_ID}")
        results["project_accessible"] = True
        results["project_name"] = project.get("project", {}).get("name", "?")
        results["project_keys_count"] = project.get("project", {}).get("statistics", {}).get("keys_total", "?")
    except LokalisError as e:
        results["project_accessible"] = False
        results["error"] = str(e)

    return results


def verify_key_exists(key_name: str) -> bool:
    """Check whether a translation key exists in the project."""
    try:
        result = lokalise_request(
            "GET",
            f"/projects/{PROJECT_ID}/keys",
            payload={"filter_key_name": key_name}
        )
        return len(result.get("keys", [])) > 0
    except Exception:
        return False
```

## Common Issues

### Missing translation key

```python
def ensure_key_exists(key_name: str, default_value: str = "") -> str:
    """Return translation value or fallback if key is missing."""
    try:
        result = lokalise_request(
            "GET",
            f"/projects/{PROJECT_ID}/keys",
            payload={"filter_key_name": key_name, "include_translations": 1}
        )
        keys = result.get("keys", [])
        if keys:
            translations = keys[0].get("translations", [])
            for t in translations:
                if t.get("language_iso") == "en":
                    return t.get("translation", default_value)
        return default_value
    except Exception:
        return default_value
```

### File format validation

```python
import json

def validate_translation_file(filepath: str) -> list:
    """Check JSON translation file for common format issues."""
    errors = []
    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]

    def check_values(obj, path=""):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, dict):
                check_values(value, current_path)
            elif not isinstance(value, str):
                errors.append(f"Non-string value at {current_path}: {type(value).__name__}")
            elif value.strip() == "":
                errors.append(f"Empty value at {current_path}")

    check_values(data)
    return errors
```

## Resources

- [Lokalise API Reference](https://developers.lokalise.com/reference)
- [Lokalise Status](https://status.lokalise.com)
- [Lokalise Error Codes](https://developers.lokalise.com/reference/api-error-codes)

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
