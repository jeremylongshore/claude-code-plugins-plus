---
name: klingai-prod-checklist
description: |
  Production readiness checklist for Kling AI integrations. Use before going live or during
  deployment review. Trigger with phrases like 'klingai production ready', 'kling ai go live',
  'klingai checklist', 'deploy klingai'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, production, deployment]

---
# Kling AI Production Checklist

## Overview

Checklist covering authentication, error handling, cost controls, monitoring, security, and content policy before deploying Kling AI video generation to production.

## Authentication

- [ ] AK/SK stored in secrets manager (not `.env` in repo)
- [ ] JWT auto-refresh with 5-min buffer before 30-min expiry
- [ ] Separate API keys per environment (dev/staging/prod)
- [ ] Key rotation schedule (quarterly minimum)
- [ ] `Authorization: Bearer <token>` format verified

## Error Handling

- [ ] HTTP 400/401/402/403/429/5xx all handled
- [ ] Exponential backoff with jitter for 429/5xx retries
- [ ] Max retry limit set (3-5, not infinite)
- [ ] `task_status: "failed"` logs `task_status_msg`
- [ ] 30s timeout on all HTTP calls
- [ ] `duration` sent as string `"5"` not integer `5`

## Cost Controls

- [ ] Daily credit budget enforced in code
- [ ] Alert at 80% daily budget consumption
- [ ] `standard` mode used for non-final renders
- [ ] Max poll attempts cap (no infinite loops)
- [ ] Credit estimate before batch submission

```python
# Pre-batch credit check
credits_needed = len(prompts) * 10  # 10 credits per 5s standard
if credits_needed > DAILY_BUDGET:
    raise RuntimeError(f"Batch needs {credits_needed}, budget is {DAILY_BUDGET}")
```

## Task Management

- [ ] All task_ids logged with timestamp
- [ ] Stuck task detection (>10 min in processing)
- [ ] `callback_url` used instead of polling in production
- [ ] Failed tasks queued for retry
- [ ] Video URLs downloaded promptly (Kling CDN URLs expire)

## Content Safety

- [ ] Prompts validated before API submission
- [ ] User-generated prompts sanitized
- [ ] Default negative prompt includes safety terms
- [ ] Content moderation on user-facing apps
- [ ] Policy violation errors handled gracefully

## Security

- [ ] API keys never logged (redacted in debug output)
- [ ] Video URLs treated as temporary (store on own CDN)
- [ ] Webhook endpoints HTTPS-only
- [ ] Rate limiting on your API layer
- [ ] No sensitive data in prompt strings

## Monitoring

- [ ] API latency tracked per endpoint
- [ ] Success/failure rate dashboard
- [ ] Credit consumption metrics
- [ ] Alert on >5% failure rate
- [ ] Structured JSON logs for all API calls

## Performance

- [ ] Connection pooling via `requests.Session()`
- [ ] Concurrent tasks within API tier limit
- [ ] Video downloads async/background
- [ ] Generated videos CDN-cached

```python
# Connection pooling
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=10)
session.mount("https://", adapter)
```

## Pre-Launch Smoke Test

```python
from kling_client import KlingClient

c = KlingClient()
result = c.text_to_video("test: blue sky with clouds", duration=5, mode="standard")
assert result["videos"][0]["url"], "No video URL"
print("READY FOR PRODUCTION")
```

## Resources

- [API Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [Content Policy](https://app.klingai.com/global/dev/document-api/protocols/paidServiceProtocol)
- [Developer Portal](https://app.klingai.com/global/dev)
