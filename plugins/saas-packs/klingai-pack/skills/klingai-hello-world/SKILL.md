---
name: klingai-hello-world
description: |
  Create your first Kling AI video generation with a minimal working example. Use when learning
  Kling AI or testing your setup. Trigger with phrases like 'kling ai hello world', 'first kling video',
  'klingai quickstart', 'test klingai'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, quickstart]

---
# Kling AI Hello World

## Overview

Generate your first AI video in under 20 lines of code. This skill walks through the complete create-poll-download cycle using the Kling AI REST API.

**Base URL:** `https://api.klingai.com/v1`

## Prerequisites

- Completed `klingai-install-auth` setup
- Python 3.8+ with `requests` and `PyJWT`
- At least 10 credits in your Kling AI account

## Minimal Example — Python

```python
import jwt, time, os, requests

# --- Auth ---
def get_token():
    ak = os.environ["KLING_ACCESS_KEY"]
    sk = os.environ["KLING_SECRET_KEY"]
    payload = {"iss": ak, "exp": int(time.time()) + 1800, "nbf": int(time.time()) - 5}
    return jwt.encode(payload, sk, algorithm="HS256",
                      headers={"alg": "HS256", "typ": "JWT"})

BASE = "https://api.klingai.com/v1"
HEADERS = {"Authorization": f"Bearer {get_token()}", "Content-Type": "application/json"}

# --- Step 1: Create task ---
task = requests.post(f"{BASE}/videos/text2video", headers=HEADERS, json={
    "model_name": "kling-v2-master",
    "prompt": "A golden retriever running through autumn leaves in slow motion, cinematic lighting",
    "duration": "5",
    "aspect_ratio": "16:9",
    "mode": "standard",
}).json()

task_id = task["data"]["task_id"]
print(f"Task created: {task_id}")

# --- Step 2: Poll until complete ---
import time as t
while True:
    t.sleep(10)
    status = requests.get(f"{BASE}/videos/text2video/{task_id}", headers=HEADERS).json()
    state = status["data"]["task_status"]
    print(f"Status: {state}")
    if state == "succeed":
        video_url = status["data"]["task_result"]["videos"][0]["url"]
        print(f"Video ready: {video_url}")
        break
    elif state == "failed":
        print(f"Failed: {status['data']['task_status_msg']}")
        break
```

## Minimal Example — Node.js

```javascript
import jwt from "jsonwebtoken";

const BASE = "https://api.klingai.com/v1";

function getHeaders() {
  const token = jwt.sign(
    { iss: process.env.KLING_ACCESS_KEY, exp: Math.floor(Date.now() / 1000) + 1800,
      nbf: Math.floor(Date.now() / 1000) - 5 },
    process.env.KLING_SECRET_KEY,
    { algorithm: "HS256", header: { typ: "JWT" } }
  );
  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
}

// Create task
const res = await fetch(`${BASE}/videos/text2video`, {
  method: "POST",
  headers: getHeaders(),
  body: JSON.stringify({
    model_name: "kling-v2-master",
    prompt: "A golden retriever running through autumn leaves in slow motion",
    duration: "5",
    aspect_ratio: "16:9",
    mode: "standard",
  }),
});
const { data } = await res.json();
console.log(`Task: ${data.task_id}`);

// Poll
const poll = setInterval(async () => {
  const r = await fetch(`${BASE}/videos/text2video/${data.task_id}`, { headers: getHeaders() });
  const s = await r.json();
  if (s.data.task_status === "succeed") {
    console.log("Video:", s.data.task_result.videos[0].url);
    clearInterval(poll);
  } else if (s.data.task_status === "failed") {
    console.error("Failed:", s.data.task_status_msg);
    clearInterval(poll);
  }
}, 10000);
```

## Response Shape

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "abc123...",
    "task_status": "succeed",
    "task_result": {
      "videos": [{
        "id": "vid_001",
        "url": "https://cdn.klingai.com/...",
        "duration": "5.0"
      }]
    }
  }
}
```

## Task Status Values

| Status | Meaning |
|--------|---------|
| `submitted` | Task queued, waiting for processing |
| `processing` | Video generation in progress |
| `succeed` | Complete — video URL available |
| `failed` | Generation failed — check `task_status_msg` |

## Common First-Run Issues

| Problem | Fix |
|---------|-----|
| `401` response | JWT token expired or AK/SK wrong |
| `task_status: failed` | Prompt too vague — add visual detail |
| Empty `videos` array | Task still processing — poll longer |
| Slow generation | Standard mode takes 60-120s; use `mode: "standard"` for first test |

## Cost

- 5-second standard video = 10 credits
- Free tier: 66 credits/day (refreshes daily, no rollover)

## Resources

- [Kling AI Text-to-Video API](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [Developer Portal](https://app.klingai.com/global/dev)
