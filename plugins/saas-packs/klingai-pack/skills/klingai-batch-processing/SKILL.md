---
name: klingai-batch-processing
description: |
  Process multiple video generation requests efficiently with Kling AI. Use when generating
  batches of videos or building content pipelines. Trigger with phrases like 'klingai batch',
  'kling ai bulk', 'multiple videos klingai', 'klingai parallel generation'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, batch, pipelines]

---
# Kling AI Batch Processing

## Overview

Generate multiple videos efficiently using controlled parallelism, rate-limit-aware submission, progress tracking, and result collection. All requests go through `https://api.klingai.com/v1`.

## Batch Submission with Rate Limiting

```python
import jwt, time, os, requests

BASE = "https://api.klingai.com/v1"

def get_headers():
    ak, sk = os.environ["KLING_ACCESS_KEY"], os.environ["KLING_SECRET_KEY"]
    token = jwt.encode(
        {"iss": ak, "exp": int(time.time()) + 1800, "nbf": int(time.time()) - 5},
        sk, algorithm="HS256", headers={"alg": "HS256", "typ": "JWT"}
    )
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def submit_batch(prompts, model="kling-v2-master", duration="5",
                 mode="standard", max_concurrent=3, delay=2.0):
    """Submit batch with controlled concurrency and pacing."""
    tasks = []
    active = []

    for i, prompt in enumerate(prompts):
        # Wait if at concurrency limit
        while len(active) >= max_concurrent:
            active = [t for t in active if not check_complete(t["task_id"])]
            if len(active) >= max_concurrent:
                time.sleep(5)

        response = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
            "model_name": model,
            "prompt": prompt,
            "duration": duration,
            "mode": mode,
        })
        data = response.json()["data"]
        task = {"task_id": data["task_id"], "prompt": prompt, "index": i}
        tasks.append(task)
        active.append(task)
        print(f"[{i+1}/{len(prompts)}] Submitted: {data['task_id']}")
        time.sleep(delay)  # pace requests

    return tasks

def check_complete(task_id):
    r = requests.get(f"{BASE}/videos/text2video/{task_id}", headers=get_headers()).json()
    return r["data"]["task_status"] in ("succeed", "failed")
```

## Collect Results

```python
def collect_results(tasks, timeout=600):
    """Wait for all tasks and collect results."""
    results = {}
    start = time.monotonic()

    while len(results) < len(tasks) and time.monotonic() - start < timeout:
        for task in tasks:
            if task["task_id"] in results:
                continue
            r = requests.get(
                f"{BASE}/videos/text2video/{task['task_id']}", headers=get_headers()
            ).json()
            status = r["data"]["task_status"]
            if status == "succeed":
                results[task["task_id"]] = {
                    "status": "succeed",
                    "url": r["data"]["task_result"]["videos"][0]["url"],
                    "prompt": task["prompt"],
                }
            elif status == "failed":
                results[task["task_id"]] = {
                    "status": "failed",
                    "error": r["data"].get("task_status_msg", "Unknown"),
                    "prompt": task["prompt"],
                }
        if len(results) < len(tasks):
            time.sleep(15)

    return results
```

## Async Batch with asyncio

```python
import asyncio
import aiohttp

async def async_batch(prompts, max_concurrent=3):
    """Async batch processing with semaphore-controlled concurrency."""
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}

    async def generate_one(prompt, index):
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                # Submit
                async with session.post(
                    f"{BASE}/videos/text2video",
                    headers=get_headers(),
                    json={"model_name": "kling-v2-master", "prompt": prompt,
                          "duration": "5", "mode": "standard"},
                ) as resp:
                    data = (await resp.json())["data"]
                    task_id = data["task_id"]

                # Poll
                while True:
                    await asyncio.sleep(10)
                    async with session.get(
                        f"{BASE}/videos/text2video/{task_id}",
                        headers=get_headers(),
                    ) as resp:
                        data = (await resp.json())["data"]
                        if data["task_status"] == "succeed":
                            results[index] = data["task_result"]["videos"][0]["url"]
                            return
                        elif data["task_status"] == "failed":
                            results[index] = f"FAILED: {data.get('task_status_msg')}"
                            return

    await asyncio.gather(*[generate_one(p, i) for i, p in enumerate(prompts)])
    return results
```

## Batch with Callbacks (No Polling)

```python
def submit_batch_with_callbacks(prompts, callback_url):
    """Submit batch with webhook callbacks -- no polling needed."""
    tasks = []
    for prompt in prompts:
        r = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
            "model_name": "kling-v2-master",
            "prompt": prompt,
            "duration": "5",
            "mode": "standard",
            "callback_url": callback_url,
        }).json()
        tasks.append(r["data"]["task_id"])
        time.sleep(2)  # rate limit pacing
    return tasks
```

## Cost Estimation Before Batch

```python
def estimate_batch_cost(count, duration=5, mode="standard", audio=False):
    credits_map = {(5, "standard"): 10, (5, "professional"): 35,
                   (10, "standard"): 20, (10, "professional"): 70}
    per_video = credits_map.get((duration, mode), 10)
    if audio:
        per_video *= 5
    total = count * per_video
    print(f"Batch: {count} videos x {per_video} credits = {total} credits")
    print(f"Estimated cost: ${total * 0.14:.2f}")
    return total

# Check before submitting
needed = estimate_batch_cost(50, duration=5, mode="standard")
```

## Resources

- [API Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [Developer Portal](https://app.klingai.com/global/dev)
