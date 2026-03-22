---
name: speak-prod-checklist
description: |
  Production readiness checklist for Speak language learning integrations: auth, audio pipeline, monitoring, and compliance.
  Use when implementing prod checklist features,
  or troubleshooting Speak language learning integration issues.
  Trigger with phrases like "speak prod checklist", "speak prod checklist".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, speak, api]

---
# Speak Production Checklist

## Overview
Production readiness checklist for Speak language learning integrations: auth, audio pipeline, monitoring, and compliance.

## Prerequisites
- Completed `speak-install-auth` setup
- Valid API credentials configured
- ffmpeg installed for audio processing

## Instructions

### Authentication
- [ ] API keys stored in secrets manager
- [ ] Key rotation schedule established (90 days)
- [ ] Separate keys for dev/staging/production
- [ ] Error handling for expired keys

### Audio Pipeline
- [ ] Audio preprocessor converts to WAV 16kHz mono
- [ ] File size validation (< 25MB)
- [ ] Duration validation (0.5s - 60s)
- [ ] Background noise detection/warning
- [ ] Fallback for unsupported audio formats

### Rate Limiting & Performance
- [ ] Rate-limited client wrapper implemented
- [ ] Retry logic with exponential backoff on 429
- [ ] Request queue for batch assessments
- [ ] Response caching where appropriate

### Monitoring & Alerting
- [ ] API response time tracking
- [ ] Error rate monitoring (target < 1%)
- [ ] Rate limit hit tracking
- [ ] Assessment score distribution monitoring
- [ ] Session completion rate tracking

### Compliance
- [ ] Student data privacy policy documented
- [ ] Audio data retention policy implemented
- [ ] COPPA compliance verified (if applicable)
- [ ] FERPA compliance verified (if educational)
- [ ] GDPR data processing agreement (if EU users)

### Verification Script
```bash
#!/bin/bash
set -euo pipefail
echo "Speak Production Readiness"
curl -sf -H "Authorization: Bearer $SPEAK_API_KEY" \
  https://api.speak.com/v1/health | jq '.status'
echo "  Auth: PASS"
ffmpeg -version > /dev/null 2>&1 && echo "  ffmpeg: PASS" || echo "  ffmpeg: FAIL"
echo "Checks complete."
```

## Output
- Checklist implementation complete
- Speak API integration verified
- Production-ready patterns applied

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Verify SPEAK_API_KEY environment variable |
| 429 Rate Limited | Too many requests | Wait Retry-After seconds, use backoff |
| Audio format error | Wrong codec/sample rate | Convert to WAV 16kHz mono with ffmpeg |
| Session expired | Timeout after 30 min | Start a new conversation session |

## Resources
- [Speak Website](https://speak.com)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [Speak GPT-4 Blog](https://speak.com/blog/speak-gpt-4)

## Next Steps
See `speak-prod-checklist` for production readiness.

## Examples

**Basic**: Apply prod checklist with default configuration for a standard Speak integration.

**Advanced**: Customize for production with error recovery, monitoring, and team-specific requirements.
