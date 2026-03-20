---
name: evernote-prod-checklist
description: |
  Production readiness checklist for Evernote integrations.
  Use when preparing to deploy Evernote integration to production,
  or auditing production readiness.
  Trigger with phrases like "evernote production", "deploy evernote",
  "evernote go live", "production checklist evernote".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Production Checklist

## Overview
Comprehensive checklist for deploying Evernote integrations to production, covering API key activation, security hardening, rate limit handling, monitoring, and go-live verification.

## Prerequisites
- Completed development and testing in sandbox
- Production API key approved by Evernote (requires review process)
- Production infrastructure provisioned

## Instructions

### API Key & Authentication
- [ ] Production API key requested and approved by Evernote
- [ ] `EVERNOTE_SANDBOX=false` in production config
- [ ] Consumer key and secret stored in secrets manager (not env files)
- [ ] OAuth callback URL uses HTTPS on production domain
- [ ] Token expiration tracking implemented (`edam_expires`)
- [ ] Token refresh/re-auth flow tested end-to-end

### Security
- [ ] Access tokens encrypted at rest (AES-256-GCM)
- [ ] CSRF protection on OAuth flow
- [ ] API credentials not in source control (`.env` in `.gitignore`)
- [ ] Log output redacts tokens and PII
- [ ] Input validation on all user-supplied content (ENML sanitization)
- [ ] Rate limit handling prevents API key suspension

### Rate Limits & Performance
- [ ] Exponential backoff on `RATE_LIMIT_REACHED` errors
- [ ] Minimum delay between API calls (100-200ms)
- [ ] Response caching for `listNotebooks()` and `listTags()` (5-10 min TTL)
- [ ] `findNotesMetadata()` used instead of `findNotes()` for listings
- [ ] Batch operations use sequential processing with delays

### Monitoring & Alerting
- [ ] Health check endpoint verifies Evernote API connectivity
- [ ] Metrics tracked: API call count, latency, error rate, rate limits
- [ ] Alerts configured for rate limits, auth failures, and high error rates
- [ ] Structured logging with correlation IDs
- [ ] Quota usage monitoring with threshold alerts (75%, 90%)

### Data Integrity
- [ ] ENML validation before every `createNote`/`updateNote` call
- [ ] Note titles sanitized (max 255 chars, no newlines)
- [ ] Tag names validated (max 100 chars, no commas)
- [ ] Resource hashes verified (MD5 match)
- [ ] Sync state (USN) tracked and persisted for incremental sync

### Deployment
- [ ] Production Docker image built with multi-stage build
- [ ] `NODE_ENV=production` set in container
- [ ] Graceful shutdown handles in-flight API calls
- [ ] Rollback plan documented and tested
- [ ] Deployment verification script runs post-deploy

### Verification Script

```bash
#!/bin/bash
set -euo pipefail

echo "Verifying Evernote production deployment..."

# 1. Health check
curl -sf "$APP_URL/health" | jq '.evernoteApi' | grep -q '"connected"'
echo "  Health check: PASS"

# 2. Create test note
GUID=$(curl -sf "$APP_URL/api/test-note" | jq -r '.guid')
echo "  Note creation: PASS (GUID: $GUID)"

# 3. Clean up test note
curl -sf -X DELETE "$APP_URL/api/notes/$GUID"
echo "  Cleanup: PASS"

echo "All checks passed."
```

For the complete checklist details and verification scripts, see [Implementation Guide](references/implementation-guide.md).

## Output
- Production readiness checklist (API keys, security, performance, monitoring)
- Verification script for post-deployment testing
- Security audit checklist for credential and token management
- Monitoring setup verification

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `INVALID_AUTH` in production | Using sandbox token with production endpoint | Verify `EVERNOTE_SANDBOX=false` matches production key |
| Verification script fails | Service not healthy after deploy | Check logs, rollback if needed |
| Rate limits on launch | Burst of API calls at startup | Add startup delay, warm caches gradually |
| `PERMISSION_DENIED` | Production key missing permissions | Contact Evernote developer support |

## Resources
- [Evernote Developer Portal](https://dev.evernote.com/)
- [API Key Request](https://dev.evernote.com/support/)
- [Rate Limits](https://dev.evernote.com/doc/articles/rate_limits.php)
- [OAuth Documentation](https://dev.evernote.com/doc/articles/authentication.php)

## Next Steps
For version upgrades, see `evernote-upgrade-migration`.

## Examples

**Go-live checklist**: Walk through each section, check off items, run the verification script, and sign off with the team before switching DNS to the production deployment.

**Security audit**: Review encrypted token storage, verify log redaction, confirm CSRF protection, and test token expiration handling before the production launch.
