---
name: klingai-batch-processing
description: 'Process multiple video generation requests efficiently with Kling AI.
  Use when generating

  batches of videos or building content pipelines. Trigger with phrases like ''klingai
  batch'',

  ''kling ai bulk'', ''multiple videos klingai'', ''klingai parallel generation''.

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.18.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- kling-ai
- batch
- pipelines
compatibility: Designed for Claude Code
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

## Prerequisites

- An approved batch manifest with a unique batch ID, a bounded count, model, duration, mode, destination, and credit ceiling.
- Prompts and reference media must be synthetic or rights-cleared, and the request must pass the provider's content policy review. Do not submit real people's likenesses, private data, or copyrighted material without documented permission.
- Use a sandbox project and draft/watermarked outputs for the first canary. Store `KLING_ACCESS_KEY` and `KLING_SECRET_KEY` in the approved secret manager; never place them in prompts, source control, or logs.

## Instructions

1. Validate the manifest before any request: reject missing rights/consent, disallowed content, unapproved destinations, duplicate batch IDs, and a projected credit total above the approved ceiling.
2. Run one synthetic canary with the lowest-cost permitted mode. Confirm the model, duration, aspect ratio, callback destination, watermark/draft status, and `contacts_exported=0`-style no-export invariant before expanding the batch.
3. Submit only the approved count with bounded concurrency and pacing. Record opaque task IDs and an idempotency key; never log prompts, source media, callback secrets, or result URLs.
4. Poll or receive callbacks with a timeout and a retry budget. Hold successful outputs in quarantine until an owner reviews content policy, rights, quality, and cost results.
5. Promote approved outputs to the allowlisted destination, then expire temporary artifacts and access. Keep only a redacted receipt and the rollback reference.

## Output

Return a batch receipt containing the opaque batch ID, model/mode/duration, requested and completed counts, success/failure counts, credit estimate and actual, canary result, policy/rights review state, destination class, retention deadline, and rollback/removal action. The receipt must exclude prompts, media, personal data, credentials, and signed URLs.

## Error Handling

- Retry only bounded transient transport or rate-limit failures with exponential backoff; do not retry policy refusals, rights failures, authentication failures, or invalid parameters.
- If the credit ceiling, concurrency limit, policy probe, or destination allowlist check fails, stop new submissions and mark the batch paused. Reconcile unknown task states before deciding whether to retry.
- On a failed canary or review, cancel pending tasks where supported, remove quarantined outputs, revoke temporary callback access, and record the redacted removal receipt. Restore the last approved batch configuration rather than silently changing scope.

## Examples

For a safe dry run, use `batch_id=synthetic-launch-01`, 3 synthetic prompts, `model=kling-v2-5-turbo`, `duration=5`, `mode=standard`, `destination=sandbox-review`, `watermark=draft`, `credits_max=30`, and `contacts_exported=0`. Promote only after the owner records `policy=pass`, `rights=pass`, and `approval=granted`; otherwise remove the canary outputs.

## Resources

- [API Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [Developer Portal](https://app.klingai.com/global/dev)
