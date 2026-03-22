---
name: lindy-prod-checklist
description: |
  Production readiness checklist for Lindy AI agent deployments.
  Use when preparing agents for production, auditing live agents,
  or validating go-live readiness.
  Trigger with phrases like "lindy production", "lindy prod ready",
  "lindy go live", "lindy deployment checklist".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, deployment, audit]

---
# Lindy Production Checklist

## Overview
Comprehensive go-live checklist for Lindy AI agents entering production. Covers
agent configuration, security, monitoring, error handling, and operational readiness.

## Prerequisites
- Agents tested in development/staging environment
- Production Lindy workspace configured
- Team members assigned appropriate roles
- Credit budget approved for production usage

## Production Checklist

### Authentication & Security
- [ ] Production API keys generated (separate from dev/staging)
- [ ] API keys stored in secret manager (not environment files)
- [ ] Webhook secrets generated for all webhook triggers
- [ ] Webhook receivers verify Bearer token on every request
- [ ] `.env` files excluded from version control
- [ ] Key rotation schedule documented (90-day max)
- [ ] Enterprise: SSO enabled, SCIM configured

### Agent Configuration
- [ ] Agent prompt reviewed for production quality
  - [ ] Clear identity and role definition
  - [ ] Numbered step-by-step instructions
  - [ ] Explicit constraints (no unauthorized promises, data limits)
  - [ ] Error handling instructions in prompt
  - [ ] Few-shot examples for consistent output format
- [ ] Model selection appropriate for each step:
  - [ ] Gemini Flash for simple routing/classification
  - [ ] Claude Sonnet/GPT-4o-mini for standard tasks
  - [ ] GPT-4/Claude Opus only where complex reasoning required
- [ ] Exit conditions defined with primary + fallback criteria
- [ ] Trigger filters configured to prevent over-firing
- [ ] Knowledge base sources current and synced

### Integration Health
- [ ] All integration OAuth tokens current (not expired)
- [ ] Gmail: correct account authorized, label filters set
- [ ] Slack: bot invited to required channels
- [ ] Webhooks: endpoint URLs use production domains (not ngrok/dev)
- [ ] HTTP Request actions: target URLs are production endpoints
- [ ] Phone numbers: provisioned and tested ($10/month each)

### Error Handling
- [ ] Agents have fallback behavior for common failures:
  - [ ] Integration auth expired -> notify admin
  - [ ] KB returns no results -> graceful fallback response
  - [ ] Condition matching fails -> default "other" branch
  - [ ] Agent step loops -> reasonable exit conditions
- [ ] Webhook receivers return 200 quickly (process async)
- [ ] HTTP Request action targets have health checks
- [ ] Credit usage alerts configured (50%, 80%, 95% thresholds)

### Monitoring & Observability
- [ ] Regular review of agent Tasks tab scheduled
- [ ] Failed task alerts configured (email or Slack)
- [ ] Credit consumption tracked per agent
- [ ] Task completion rate monitored (failures should be <5%)
- [ ] Response time baseline established for each agent

### Operational Readiness
- [ ] Runbook documented for common agent failures
- [ ] Escalation path defined (L1 -> L2 -> Lindy support)
- [ ] On-call schedule if agents are customer-facing
- [ ] Agent sharing configured (Edit/User/Template access)
- [ ] Team credit allocation set for team members ($19.99/seat on Pro)

### Compliance & Documentation
- [ ] Data handling practices documented per agent
- [ ] Agent prompts include PII redaction instructions
- [ ] Knowledge base content reviewed for accuracy
- [ ] HIPAA: BAA in place if handling healthcare data
- [ ] GDPR: data retention policies defined
- [ ] Agent purpose and scope documented for team reference

## Pre-Launch Validation Script
```bash
#!/bin/bash
echo "=== Lindy Production Validation ==="

# 1. API connectivity
echo "[1/4] Testing API connectivity..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $LINDY_API_KEY" \
  "https://public.lindy.ai/api/v1/webhooks/health" 2>/dev/null || echo "000")
[ "$API_STATUS" = "000" ] && echo "  WARN: Could not reach Lindy API" || echo "  OK: API reachable"

# 2. Webhook endpoint health
echo "[2/4] Testing webhook receiver..."
ENDPOINT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  "https://your-app.com/health" 2>/dev/null || echo "000")
[ "$ENDPOINT_STATUS" = "200" ] && echo "  OK: Webhook receiver healthy" || echo "  FAIL: Receiver returned $ENDPOINT_STATUS"

# 3. Environment variables
echo "[3/4] Checking environment..."
[ -n "$LINDY_API_KEY" ] && echo "  OK: LINDY_API_KEY set" || echo "  FAIL: LINDY_API_KEY missing"
[ -n "$LINDY_WEBHOOK_SECRET" ] && echo "  OK: LINDY_WEBHOOK_SECRET set" || echo "  FAIL: LINDY_WEBHOOK_SECRET missing"

# 4. Credit balance check
echo "[4/4] Credit status: Check at https://app.lindy.ai/settings/billing"

echo "=== Validation Complete ==="
```

## Go/No-Go Criteria

| Category | Go | No-Go |
|----------|-----|-------|
| Security | All keys in secret manager | Any hardcoded credentials |
| Auth | All integrations authorized | Any expired OAuth tokens |
| Prompt | Reviewed with constraints | Generic/placeholder prompt |
| Monitoring | Alerts configured | No failure notification |
| Credits | Budget approved | No credit plan |
| Testing | Agent tested end-to-end | Untested workflow paths |

## Error Handling

| Check Failure | Severity | Action |
|--------------|----------|--------|
| API key invalid | Critical | Block launch, regenerate key |
| Integration expired | High | Re-authorize before launch |
| No trigger filters | Medium | Add filters to prevent credit waste |
| No monitoring | Medium | Set up alerts before launch |
| Missing documentation | Low | Document within first week |

## Resources
- [Lindy Documentation](https://docs.lindy.ai)
- [Lindy Pricing](https://www.lindy.ai/pricing)
- [Lindy Security](https://www.lindy.ai/security)

## Next Steps
Proceed to `lindy-upgrade-migration` for version management.
