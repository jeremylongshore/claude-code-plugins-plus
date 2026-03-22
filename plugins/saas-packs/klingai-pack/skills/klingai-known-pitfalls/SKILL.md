---
name: klingai-known-pitfalls
description: |
  Avoid common mistakes when using Kling AI API. Use when troubleshooting or learning best
  practices. Trigger with phrases like 'klingai pitfalls', 'kling ai mistakes', 'klingai gotchas',
  'klingai best practices'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, troubleshooting, best-practices]

---
# Kling AI Known Pitfalls

## Overview

Documented mistakes, gotchas, and anti-patterns from real Kling AI integrations. Each pitfall includes the symptom, root cause, and tested fix.

## Pitfall 1: Duration as Integer

**Symptom:** `400 Bad Request` on valid-looking requests.

```python
# WRONG -- duration as integer
{"duration": 5}

# CORRECT -- duration as string
{"duration": "5"}
```

The API requires `duration` as a string `"5"` or `"10"`, not an integer.

## Pitfall 2: JWT Without Explicit Headers

**Symptom:** `401 Unauthorized` even with correct AK/SK.

```python
# WRONG -- missing headers parameter
token = jwt.encode(payload, sk, algorithm="HS256")

# CORRECT -- explicit JWT headers
token = jwt.encode(payload, sk, algorithm="HS256",
                   headers={"alg": "HS256", "typ": "JWT"})
```

Some JWT libraries don't include `typ: "JWT"` by default. Kling requires it.

## Pitfall 3: Token Generated Once at Import Time

**Symptom:** Works for 30 minutes, then all requests fail with `401`.

```python
# WRONG -- token generated once
TOKEN = generate_token()  # at module import
headers = {"Authorization": f"Bearer {TOKEN}"}

# CORRECT -- generate fresh token per request (or auto-refresh)
def get_headers():
    return {"Authorization": f"Bearer {generate_token()}"}
```

JWT tokens expire after 30 minutes. Always implement auto-refresh.

## Pitfall 4: Polling Without Timeout

**Symptom:** Script hangs forever on a failed task.

```python
# WRONG -- infinite loop
while True:
    result = check_status(task_id)
    if result["status"] == "succeed":
        break
    time.sleep(10)

# CORRECT -- with timeout and failure check
start = time.monotonic()
while time.monotonic() - start < 600:  # 10 min max
    result = check_status(task_id)
    if result["status"] == "succeed":
        break
    elif result["status"] == "failed":
        raise RuntimeError(result["error"])
    time.sleep(10)
else:
    raise TimeoutError("Generation timed out")
```

## Pitfall 5: Not Downloading Videos Promptly

**Symptom:** Video URLs return `404` or `403` after a day.

Kling CDN URLs are **temporary** (24-72 hours). Always download and store on your own infrastructure immediately after generation completes.

```python
# WRONG -- storing only the Kling URL
db.save(video_url=kling_cdn_url)  # will expire

# CORRECT -- download and rehost
local_path = download_video(kling_cdn_url)
permanent_url = upload_to_s3(local_path, bucket)
db.save(video_url=permanent_url)
```

## Pitfall 6: Mixing Mutually Exclusive Features (I2V)

**Symptom:** `400 Bad Request` on image-to-video with multiple features.

These are **mutually exclusive** for image-to-video:
- `camera_control`
- `dynamic_masks` / `static_mask`
- `image_tail`

You can only use ONE group per request.

## Pitfall 7: Wrong Model for Text-to-Video

**Symptom:** `400` or unexpected behavior.

```python
# WRONG -- kling-v2-1 is I2V-only
{"model_name": "kling-v2-1", "prompt": "A sunset..."}  # fails

# CORRECT -- use models that support T2V
{"model_name": "kling-v2-master", "prompt": "A sunset..."}
{"model_name": "kling-v2-5-turbo", "prompt": "A sunset..."}
```

Check the model catalog: `kling-v1-5` and `kling-v2-1` support image-to-video only.

## Pitfall 8: No Error Handling on Task Status

**Symptom:** Silent failures, missing videos.

```python
# WRONG -- only check for success
if result["task_status"] == "succeed":
    process(result)
# silently ignores failures

# CORRECT -- handle all terminal states
if result["task_status"] == "succeed":
    process(result)
elif result["task_status"] == "failed":
    log_failure(result["task_status_msg"])
    retry_or_alert(task_id)
```

## Pitfall 9: Ignoring Credit Costs with Audio

**Symptom:** Credits depleted 5x faster than expected.

Native audio (v2.6, `motion_has_audio: true`) multiplies credit cost by 5x:
- 5s standard without audio: 10 credits
- 5s standard WITH audio: 50 credits

Always check `motion_has_audio` in cost estimates.

## Pitfall 10: Vague Prompts

**Symptom:** Low-quality, incoherent video output.

```python
# WEAK -- too vague
"A nice video of nature"

# STRONG -- specific and descriptive
"Close-up of a monarch butterfly landing on a lavender flower, "
"soft bokeh background, golden hour lighting, macro lens, 4K"
```

Good prompts: specific subject, clear action, lighting, camera angle, style.

## Quick Reference

| Pitfall | Fix |
|---------|-----|
| Duration as int | Use string: `"5"` |
| JWT headers missing | Add `headers={"alg":"HS256","typ":"JWT"}` |
| Token not refreshed | Auto-refresh with 5-min buffer |
| No poll timeout | Max 600s with failure check |
| Kling URLs as permanent | Download and rehost immediately |
| Mixed I2V features | One feature group per request |
| Wrong model for T2V | Check model supports text-to-video |
| No failure handling | Check for `"failed"` status |
| Audio cost surprise | 5x multiplier with `motion_has_audio` |
| Vague prompts | Specific subject, action, style, lighting |

## Resources

- [API Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [Developer Portal](https://app.klingai.com/global/dev)
