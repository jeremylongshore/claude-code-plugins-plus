---
name: klingai-debug-bundle
description: |
  Set up logging and debugging for Kling AI API integrations. Use when troubleshooting video
  generation or building observability. Trigger with phrases like 'klingai debug', 'kling ai logging',
  'klingai troubleshoot', 'debug kling video generation'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, debugging, observability]

---
# Kling AI Debug Bundle

## Overview

Structured logging, request tracing, and diagnostic tools for Kling AI API integrations. Captures request/response pairs, task lifecycle events, and timing metrics for every call to `https://api.klingai.com/v1`.

## Debug-Enabled Client

```python
import jwt, time, os, requests, logging, json
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("kling.debug")

class KlingDebugClient:
    """Kling AI client with full request/response logging."""

    BASE = "https://api.klingai.com/v1"

    def __init__(self):
        self.ak = os.environ["KLING_ACCESS_KEY"]
        self.sk = os.environ["KLING_SECRET_KEY"]
        self._request_log = []

    def _get_headers(self):
        token = jwt.encode(
            {"iss": self.ak, "exp": int(time.time()) + 1800, "nbf": int(time.time()) - 5},
            self.sk, algorithm="HS256", headers={"alg": "HS256", "typ": "JWT"}
        )
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _traced_request(self, method, path, body=None):
        """Execute request with full tracing."""
        url = f"{self.BASE}{path}"
        start = time.monotonic()
        trace = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": method,
            "path": path,
            "request_body": body,
        }

        try:
            if method == "POST":
                r = requests.post(url, headers=self._get_headers(), json=body, timeout=30)
            else:
                r = requests.get(url, headers=self._get_headers(), timeout=30)

            trace["status_code"] = r.status_code
            trace["response_body"] = r.json() if r.content else None
            trace["duration_ms"] = round((time.monotonic() - start) * 1000)

            logger.debug(f"{method} {path} -> {r.status_code} ({trace['duration_ms']}ms)")

            if r.status_code >= 400:
                logger.error(f"API error: {r.status_code} -- {r.text[:300]}")

            r.raise_for_status()
            return r.json()

        except Exception as e:
            trace["error"] = str(e)
            trace["duration_ms"] = round((time.monotonic() - start) * 1000)
            logger.exception(f"Request failed: {path}")
            raise
        finally:
            self._request_log.append(trace)

    def text_to_video(self, prompt, **kwargs):
        body = {
            "model_name": kwargs.get("model", "kling-v2-master"),
            "prompt": prompt,
            "duration": str(kwargs.get("duration", 5)),
            "mode": kwargs.get("mode", "standard"),
        }
        result = self._traced_request("POST", "/videos/text2video", body)
        task_id = result["data"]["task_id"]
        logger.info(f"Task created: {task_id}")
        return self._poll_with_logging("/videos/text2video", task_id)

    def _poll_with_logging(self, endpoint, task_id, max_attempts=120):
        start = time.monotonic()
        for attempt in range(max_attempts):
            time.sleep(10)
            result = self._traced_request("GET", f"{endpoint}/{task_id}")
            status = result["data"]["task_status"]
            elapsed = round(time.monotonic() - start)
            logger.info(f"Poll #{attempt + 1}: status={status}, elapsed={elapsed}s")

            if status == "succeed":
                logger.info(f"Task {task_id} completed in {elapsed}s")
                return result["data"]["task_result"]
            elif status == "failed":
                msg = result["data"].get("task_status_msg", "Unknown")
                logger.error(f"Task {task_id} failed after {elapsed}s: {msg}")
                raise RuntimeError(msg)

        raise TimeoutError(f"Task {task_id} timed out after {max_attempts * 10}s")

    def dump_log(self, filepath="kling_debug.json"):
        with open(filepath, "w") as f:
            json.dump(self._request_log, f, indent=2, default=str)
        logger.info(f"Debug log written to {filepath} ({len(self._request_log)} entries)")
```

## Usage

```python
client = KlingDebugClient()
try:
    result = client.text_to_video("A cat surfing ocean waves at sunset")
    print(f"Video: {result['videos'][0]['url']}")
except Exception:
    pass
finally:
    client.dump_log()  # always save debug log
```

## Structured Log Entry Format

```json
{
  "timestamp": "2026-03-22T10:30:00.000Z",
  "method": "POST",
  "path": "/videos/text2video",
  "request_body": {"model_name": "kling-v2-master", "prompt": "..."},
  "status_code": 200,
  "response_body": {"code": 0, "data": {"task_id": "abc123"}},
  "duration_ms": 342
}
```

## Quick Diagnostic Script

```bash
#!/bin/bash
# kling-diag.sh
echo "=== Kling AI Diagnostics ==="
echo "KLING_ACCESS_KEY: ${KLING_ACCESS_KEY:+set (${#KLING_ACCESS_KEY} chars)}"
echo "KLING_SECRET_KEY: ${KLING_SECRET_KEY:+set (${#KLING_SECRET_KEY} chars)}"

python3 -c "
import jwt, time, os, requests
ak = os.environ.get('KLING_ACCESS_KEY', '')
sk = os.environ.get('KLING_SECRET_KEY', '')
if not ak or not sk: print('ERROR: Missing credentials'); exit(1)
token = jwt.encode({'iss': ak, 'exp': int(time.time())+1800, 'nbf': int(time.time())-5},
                   sk, algorithm='HS256', headers={'alg':'HS256','typ':'JWT'})
r = requests.get('https://api.klingai.com/v1/videos/text2video',
                  headers={'Authorization': f'Bearer {token}'}, timeout=10)
print(f'Auth test: HTTP {r.status_code}')
if r.status_code == 401: print('Fix: Check AK/SK values')
elif r.status_code in (200, 400): print('Auth OK')
"
```

## Task Inspector

```python
def inspect_task(client, endpoint, task_id):
    """Print detailed task information."""
    result = client._traced_request("GET", f"{endpoint}/{task_id}")
    data = result["data"]
    print(f"Task ID:     {data['task_id']}")
    print(f"Status:      {data['task_status']}")
    print(f"Created:     {data.get('created_at', 'N/A')}")
    if data["task_status"] == "succeed":
        for i, video in enumerate(data["task_result"]["videos"]):
            print(f"Video [{i}]:   {video['url']}")
    elif data["task_status"] == "failed":
        print(f"Error:       {data.get('task_status_msg', 'No message')}")
```

## Resources

- [API Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [Developer Console](https://app.klingai.com/global/dev)
