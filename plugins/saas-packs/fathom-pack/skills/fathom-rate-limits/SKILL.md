---
name: fathom-rate-limits
description: |
  Handle Fathom API rate limits (60 requests/minute per user).
  Trigger with phrases like "fathom rate limit", "fathom 429", "fathom throttle".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Rate Limits

## Limits

| Aspect | Value |
|--------|-------|
| Rate limit | 60 requests per minute |
| Scope | Per user, across all API keys |
| Higher limits | Not available |

## Backoff Pattern

```python
import time

def fathom_request_with_backoff(client, path, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.session.get(f"{client.config.base_url}{path}")
        except Exception as e:
            if "429" in str(e):
                delay = 2 ** attempt * 5
                time.sleep(delay)
            else:
                raise
    raise Exception("Max retries exceeded")
```

## Batch Processing

```python
import time

def process_all_meetings(client, meetings):
    for i, meeting in enumerate(meetings):
        transcript = client.get_transcript(meeting["id"])
        process(transcript)
        if (i + 1) % 50 == 0:
            time.sleep(60)  # Pause before next batch
```

## Next Steps

For security, see `fathom-security-basics`.
