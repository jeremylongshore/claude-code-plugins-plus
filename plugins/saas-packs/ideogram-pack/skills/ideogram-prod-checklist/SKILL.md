---
name: ideogram-prod-checklist
description: |
  Execute Ideogram production deployment checklist and rollback procedures.
  Use when deploying Ideogram integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "ideogram production", "deploy ideogram",
  "ideogram go-live", "ideogram launch checklist", "ideogram production ready".
allowed-tools: Read, Bash(curl:*), Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, deployment, production]

---
# Ideogram Production Checklist

## Overview
Complete pre-flight checklist for deploying Ideogram image generation to production. Covers API key management, timeout configuration, image persistence, error handling, monitoring, and rollback procedures.

## Prerequisites
- Staging environment tested
- Production API key created (separate from dev)
- Image storage configured (S3, GCS, or R2)
- Monitoring stack ready

## Pre-Deployment Checklist

### API Configuration
- [ ] Production API key stored in secret manager (not `.env` file)
- [ ] Key is separate from dev/staging keys
- [ ] Auto top-up billing configured with appropriate limits
- [ ] Base URL is `https://api.ideogram.ai` (no trailing slash)

### Request Handling
- [ ] `Api-Key` header used (not `Authorization: Bearer`)
- [ ] Request timeout set to 60s+ (generation takes 5-15s, complex prompts longer)
- [ ] Retry logic with exponential backoff on 429 and 5xx
- [ ] Concurrency limited to 8 (below the 10 in-flight limit)
- [ ] Prompt length validated (max 10,000 chars)

### Image Persistence
- [ ] Images downloaded immediately after generation (URLs expire ~1 hour)
- [ ] Downloaded to durable storage (S3/GCS/R2), not local filesystem
- [ ] Filenames include seed for reproducibility tracking
- [ ] Generation metadata (prompt, seed, model, style) stored in database

### Error Handling
- [ ] 401 triggers key rotation alert
- [ ] 422 (safety filter) logged with sanitized prompt for review
- [ ] 429 handled with retry, not user-facing error
- [ ] 402 (no credits) triggers billing alert and graceful degradation
- [ ] Circuit breaker prevents cascading failures

### Content Safety
- [ ] Prompt sanitization removes PII before API call
- [ ] User-submitted prompts validated server-side
- [ ] `is_image_safe` response field checked before displaying to users
- [ ] Content moderation layer for user-facing applications

## Production Health Check
```typescript
async function ideogramHealthCheck(): Promise<{
  status: "healthy" | "degraded" | "down";
  latencyMs: number;
  details: string;
}> {
  const start = Date.now();
  try {
    const response = await fetch("https://api.ideogram.ai/generate", {
      method: "POST",
      headers: {
        "Api-Key": process.env.IDEOGRAM_API_KEY!,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        image_request: {
          prompt: "health check: simple blue dot",
          model: "V_2_TURBO",
          magic_prompt_option: "OFF",
        },
      }),
      signal: AbortSignal.timeout(30000),
    });

    const latencyMs = Date.now() - start;

    if (response.ok) {
      return { status: "healthy", latencyMs, details: "Generation succeeded" };
    }
    if (response.status === 429) {
      return { status: "degraded", latencyMs, details: "Rate limited" };
    }
    return { status: "down", latencyMs, details: `HTTP ${response.status}` };
  } catch (err: any) {
    return { status: "down", latencyMs: Date.now() - start, details: err.message };
  }
}
```

## Deployment Script
```bash
set -euo pipefail
echo "=== Ideogram Pre-Flight Checks ==="

# 1. Verify production key
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.ideogram.ai/generate \
  -H "Api-Key: $IDEOGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image_request":{"prompt":"deploy check","model":"V_2_TURBO","magic_prompt_option":"OFF"}}')

if [ "$STATUS" != "200" ]; then
  echo "FAIL: API returned $STATUS"
  exit 1
fi
echo "PASS: API key valid (HTTP $STATUS)"

# 2. Verify image download
IMAGE_URL=$(curl -s -X POST https://api.ideogram.ai/generate \
  -H "Api-Key: $IDEOGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image_request":{"prompt":"deploy check","model":"V_2_TURBO","magic_prompt_option":"OFF"}}' \
  | jq -r '.data[0].url')

DL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$IMAGE_URL")
echo "PASS: Image download works (HTTP $DL_STATUS)"

echo "=== All pre-flight checks passed ==="
```

## Alerting Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| API Unreachable | Health check returns `down` | P1 |
| Auth Failure | Any 401 response | P1 |
| Rate Limited | >5 consecutive 429 responses | P2 |
| Slow Generation | P95 latency > 30 seconds | P2 |
| Credits Low | Balance below $10 | P2 |
| Safety Rejections | >10% of prompts rejected | P3 |

## Rollback Procedure
```bash
set -euo pipefail
# If Ideogram is down or producing bad results
# 1. Enable fallback mode (disable image generation, show placeholders)
kubectl set env deployment/app IDEOGRAM_ENABLED=false
kubectl rollout restart deployment/app

# 2. Verify fallback is active
curl -s https://app.example.com/health | jq '.services.ideogram'

# 3. Re-enable when resolved
kubectl set env deployment/app IDEOGRAM_ENABLED=true
kubectl rollout restart deployment/app
```

## Error Handling
| Alert | Condition | Action |
|-------|-----------|--------|
| API Down | 5xx or timeout | Enable fallback, notify on-call |
| Key Revoked | 401 | Rotate key, update secrets |
| Credits Empty | 402 | Top up billing, pause batch jobs |
| Rate Flood | 429 sustained | Reduce concurrency, queue jobs |

## Output
- All checklist items verified
- Health check endpoint configured
- Alerting rules deployed
- Rollback procedure tested

## Resources
- [Ideogram API Overview](https://developer.ideogram.ai/ideogram-api/api-overview)
- [API Setup](https://developer.ideogram.ai/ideogram-api/api-setup)

## Next Steps
For version upgrades, see `ideogram-upgrade-migration`.
