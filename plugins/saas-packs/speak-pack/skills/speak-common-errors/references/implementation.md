# Speak Common Errors -- Implementation Reference

## Overview

Diagnose and fix common Speak API errors including authentication failures,
session management issues, content delivery problems, and integration errors.

## Prerequisites

- Speak API key and tenant credentials
- curl or Python for diagnostic testing
- Network access to Speak API endpoints

## Error Reference

| Code | Meaning | Fix |
|------|---------|-----|
| 401 | Invalid API key | Regenerate key in Speak dashboard |
| 403 | Access denied | Check tenant permissions |
| 404 | Lesson/resource not found | Verify content IDs |
| 429 | Rate limit exceeded | Implement backoff |
| 500 | Server error | Retry with exponential backoff |

## Authentication Diagnostics

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $SPEAK_API_KEY" \
  "https://api.speak.com/v1/health"
# Expected: 200
```

## Python Error Handler

```python
import os, json, time, urllib.request, urllib.error

SPEAK_API_KEY = os.environ["SPEAK_API_KEY"]
BASE_URL = os.environ.get("SPEAK_BASE_URL", "https://api.speak.com")


class SpeakError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status


def speak_request(method: str, path: str, payload: dict = None, retries: int = 3) -> dict:
    headers = {"Authorization": f"Bearer {SPEAK_API_KEY}", "Content-Type": "application/json"}
    body = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise SpeakError(401, "Invalid API key -- check SPEAK_API_KEY")
            if e.code == 403:
                raise SpeakError(403, "Access denied -- check tenant permissions")
            if e.code == 404:
                raise SpeakError(404, f"Not found: {path}")
            if e.code == 429:
                wait = 2 ** attempt
                print(f"Rate limited. Waiting {wait}s")
                time.sleep(wait)
                continue
            if e.code >= 500 and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise SpeakError(e.code, str(e))
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(1)
                continue
            raise
    raise SpeakError(429, "Max retries exceeded")


def diagnose_speak() -> dict:
    results = {}
    results["api_key_present"] = bool(SPEAK_API_KEY)
    results["api_key_length"] = len(SPEAK_API_KEY)
    try:
        data = speak_request("GET", "/v1/health")
        results["api_reachable"] = True
        results["api_status"] = data.get("status", "unknown")
    except SpeakError as e:
        results["api_reachable"] = False
        results["error"] = str(e)
    try:
        data = speak_request("GET", "/v1/lessons?limit=1")
        results["content_accessible"] = True
    except SpeakError as e:
        results["content_accessible"] = False
        results["content_error"] = str(e)
    return results


if __name__ == "__main__":
    print(json.dumps(diagnose_speak(), indent=2))
```

## Common Issues

### Session timeout

```python
import time

_sessions: dict = {}
SESSION_TTL = 3600


def get_or_create_session(user_id: str, lesson_id: str) -> dict:
    entry = _sessions.get(user_id)
    if entry and time.time() - entry["at"] < SESSION_TTL:
        return entry["session"]
    session = speak_request("POST", "/v1/sessions", {"userId": user_id, "lessonId": lesson_id})
    _sessions[user_id] = {"session": session, "at": time.time()}
    return session
```

### Content not found

```python
def safe_get_lesson(lesson_id: str) -> dict | None:
    try:
        return speak_request("GET", f"/v1/lessons/{lesson_id}")
    except SpeakError as e:
        if e.status == 404:
            print(f"Lesson {lesson_id} not found in this tenant")
            return None
        raise
```

## Resources

- [Speak API Docs](https://developers.speak.com)
- [Speak Status](https://status.speak.com)
