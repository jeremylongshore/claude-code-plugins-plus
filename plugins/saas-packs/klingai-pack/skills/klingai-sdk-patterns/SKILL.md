---
name: klingai-sdk-patterns
description: |
  Production SDK patterns for Kling AI: client wrapper, retry logic, async polling, and error
  handling. Use when building robust integrations. Trigger with phrases like 'klingai sdk',
  'kling ai client', 'klingai patterns', 'kling ai wrapper'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, sdk, patterns]

---
# Kling AI SDK Patterns

## Overview

Production-ready client patterns for the Kling AI API. Covers auto-refreshing JWT, typed request/response models, exponential backoff polling, async batch submission, and structured error handling.

## Python Client Wrapper

```python
import jwt
import time
import os
import requests
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class KlingConfig:
    access_key: str = field(default_factory=lambda: os.environ["KLING_ACCESS_KEY"])
    secret_key: str = field(default_factory=lambda: os.environ["KLING_SECRET_KEY"])
    base_url: str = "https://api.klingai.com/v1"
    token_buffer_sec: int = 300
    poll_interval_sec: int = 10
    max_poll_attempts: int = 120  # 20 minutes max
    timeout_sec: int = 30

class KlingClient:
    """Production Kling AI client with auto-refreshing JWT."""

    def __init__(self, config: Optional[KlingConfig] = None):
        self.config = config or KlingConfig()
        self._token = None
        self._token_expires = 0

    @property
    def _headers(self) -> dict:
        now = int(time.time())
        if now >= (self._token_expires - self.config.token_buffer_sec):
            payload = {"iss": self.config.access_key, "exp": now + 1800, "nbf": now - 5}
            self._token = jwt.encode(payload, self.config.secret_key,
                                     algorithm="HS256",
                                     headers={"alg": "HS256", "typ": "JWT"})
            self._token_expires = now + 1800
        return {"Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json"}

    def _post(self, path: str, body: dict) -> dict:
        r = requests.post(f"{self.config.base_url}{path}",
                          headers=self._headers, json=body,
                          timeout=self.config.timeout_sec)
        r.raise_for_status()
        return r.json()

    def _get(self, path: str) -> dict:
        r = requests.get(f"{self.config.base_url}{path}",
                         headers=self._headers,
                         timeout=self.config.timeout_sec)
        r.raise_for_status()
        return r.json()

    def _poll_task(self, endpoint: str, task_id: str) -> dict:
        """Poll with exponential backoff until task completes."""
        interval = self.config.poll_interval_sec
        for attempt in range(self.config.max_poll_attempts):
            time.sleep(interval)
            result = self._get(f"{endpoint}/{task_id}")
            status = result["data"]["task_status"]
            if status == "succeed":
                return result["data"]["task_result"]
            elif status == "failed":
                raise KlingGenerationError(result["data"].get("task_status_msg", "Unknown"))
            # Increase interval up to 30s max
            interval = min(interval * 1.2, 30)
        raise KlingTimeoutError(f"Task {task_id} did not complete in time")

    # --- Public API ---

    def text_to_video(self, prompt: str, **kwargs) -> dict:
        body = {"model_name": kwargs.get("model", "kling-v2-master"),
                "prompt": prompt,
                "duration": str(kwargs.get("duration", 5)),
                "aspect_ratio": kwargs.get("aspect_ratio", "16:9"),
                "mode": kwargs.get("mode", "standard")}
        if kwargs.get("negative_prompt"):
            body["negative_prompt"] = kwargs["negative_prompt"]
        if kwargs.get("cfg_scale") is not None:
            body["cfg_scale"] = kwargs["cfg_scale"]
        if kwargs.get("callback_url"):
            body["callback_url"] = kwargs["callback_url"]

        task = self._post("/videos/text2video", body)
        task_id = task["data"]["task_id"]
        if kwargs.get("wait", True):
            return self._poll_task("/videos/text2video", task_id)
        return {"task_id": task_id}

    def image_to_video(self, image_url: str, **kwargs) -> dict:
        body = {"model_name": kwargs.get("model", "kling-v2-1"),
                "image": image_url,
                "duration": str(kwargs.get("duration", 5)),
                "mode": kwargs.get("mode", "standard")}
        if kwargs.get("prompt"):
            body["prompt"] = kwargs["prompt"]

        task = self._post("/videos/image2video", body)
        task_id = task["data"]["task_id"]
        if kwargs.get("wait", True):
            return self._poll_task("/videos/image2video", task_id)
        return {"task_id": task_id}

    def extend_video(self, task_id: str, **kwargs) -> dict:
        body = {"task_id": task_id,
                "prompt": kwargs.get("prompt", ""),
                "duration": str(kwargs.get("duration", 5)),
                "mode": kwargs.get("mode", "standard")}
        result = self._post("/videos/video-extend", body)
        new_task_id = result["data"]["task_id"]
        if kwargs.get("wait", True):
            return self._poll_task("/videos/video-extend", new_task_id)
        return {"task_id": new_task_id}


class KlingError(Exception):
    pass

class KlingGenerationError(KlingError):
    pass

class KlingTimeoutError(KlingError):
    pass
```

## Usage

```python
client = KlingClient()

# Synchronous (waits for result)
result = client.text_to_video(
    "A cat playing piano in a jazz club",
    model="kling-v2-6",
    mode="professional",
    duration=5,
)
print(result["videos"][0]["url"])

# Fire-and-forget (returns task_id)
task = client.text_to_video("Ocean waves at sunset", wait=False)
print(f"Submitted: {task['task_id']}")
```

## Node.js Client

```javascript
import jwt from "jsonwebtoken";

class KlingClient {
  #token = null;
  #tokenExp = 0;

  constructor(ak = process.env.KLING_ACCESS_KEY, sk = process.env.KLING_SECRET_KEY) {
    this.ak = ak;
    this.sk = sk;
    this.base = "https://api.klingai.com/v1";
  }

  #getHeaders() {
    const now = Math.floor(Date.now() / 1000);
    if (now >= this.#tokenExp - 300) {
      this.#token = jwt.sign(
        { iss: this.ak, exp: now + 1800, nbf: now - 5 },
        this.sk, { algorithm: "HS256", header: { typ: "JWT" } }
      );
      this.#tokenExp = now + 1800;
    }
    return { Authorization: `Bearer ${this.#token}`, "Content-Type": "application/json" };
  }

  async textToVideo(prompt, opts = {}) {
    const res = await fetch(`${this.base}/videos/text2video`, {
      method: "POST",
      headers: this.#getHeaders(),
      body: JSON.stringify({
        model_name: opts.model ?? "kling-v2-master",
        prompt,
        duration: String(opts.duration ?? 5),
        aspect_ratio: opts.aspectRatio ?? "16:9",
        mode: opts.mode ?? "standard",
      }),
    });
    const { data } = await res.json();
    return opts.wait === false ? data : this.#poll("/videos/text2video", data.task_id);
  }

  async #poll(endpoint, taskId, interval = 10000) {
    for (let i = 0; i < 120; i++) {
      await new Promise((r) => setTimeout(r, interval));
      const res = await fetch(`${this.base}${endpoint}/${taskId}`, {
        headers: this.#getHeaders(),
      });
      const { data } = await res.json();
      if (data.task_status === "succeed") return data.task_result;
      if (data.task_status === "failed") throw new Error(data.task_status_msg);
      interval = Math.min(interval * 1.2, 30000);
    }
    throw new Error(`Timeout: task ${taskId}`);
  }
}
```

## Retry Decorator

```python
import functools

def retry_on_transient(max_retries=3, backoff_base=2):
    """Retry on 429 (rate limit) and 5xx (server) errors."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except requests.HTTPError as e:
                    if e.response.status_code in (429, 500, 502, 503) and attempt < max_retries:
                        wait = backoff_base ** attempt
                        time.sleep(wait)
                        continue
                    raise
        return wrapper
    return decorator

# Apply to client methods
KlingClient._post = retry_on_transient()(KlingClient._post)
```

## Resources

- [Kling AI Developer Portal](https://app.klingai.com/global/dev)
- [API Overview](https://app.klingai.com/global/dev/document-api/quickStart/productIntroduction/overview)
