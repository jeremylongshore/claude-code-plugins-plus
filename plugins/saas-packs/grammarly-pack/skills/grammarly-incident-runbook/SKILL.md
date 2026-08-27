---
name: grammarly-incident-runbook
description: 'Follow Grammarly incident response runbook for API outages.

  Use when Grammarly API is down, experiencing errors,

  or when investigating service degradation.

  Trigger with phrases like "grammarly down", "grammarly outage",

  "grammarly incident", "grammarly not responding".

  '
allowed-tools: Read, Bash(curl:*), Grep
version: 1.8.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- grammarly
- writing
compatibility: Designed for Claude Code
---
# Grammarly Incident Runbook

## Overview

Incident response procedures for Grammarly writing API integration failures. Covers text check timeouts, suggestion quality degradation, OAuth token failures, and rate limit storms. Grammarly powers real-time writing assistance, so API incidents directly impact user-facing text checking, scoring workflows, and content quality pipelines. Classify severity immediately using the matrix below and follow the corresponding playbook.

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|-----------|---------------|---------|
| P1 - Critical | Full API outage, all scoring requests fail | 15 min | 5xx on `/v2/scores` for all requests |
| P2 - High | OAuth token failures or sustained timeouts | 30 min | All authenticated requests return 401 |
| P3 - Medium | Rate limit storms or elevated latency | 2 hours | 429 responses, scoring takes 10s+ per request |
| P4 - Low | Suggestion quality drift or single endpoint issue | 8 hours | Scores returning but correctness values seem off |

## Diagnostic Steps

```bash
# Test API health (unauthenticated)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  https://api.grammarly.com/ecosystem/api/v2/scores

# Test authenticated scoring
curl -s -w "\nHTTP %{http_code}\n" \
  -H "Authorization: Bearer $GRAMMARLY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST https://api.grammarly.com/ecosystem/api/v2/scores \
  -d '{"text": "Test sentence for Grammarly API diagnostic health check."}'

# Check OAuth token validity
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -H "Authorization: Bearer $GRAMMARLY_ACCESS_TOKEN" \
  https://api.grammarly.com/ecosystem/api/v2/account
```

## Incident Playbooks

### API Outage

1. Confirm with unauthenticated health check (see diagnostics)
2. Check Grammarly status page and developer announcements
3. Activate fallback mode — return placeholder scores to avoid blocking users
4. Queue text submissions for retry when API recovers
5. Notify downstream consumers that scores are unavailable

### Authentication Failure

1. Test token validity with the account endpoint diagnostic above
2. If 401: OAuth access token has expired — trigger token refresh flow
3. If refresh token also fails: re-authorize via OAuth consent flow
4. Verify client ID and client secret are correct in environment config
5. Deploy refreshed tokens and confirm scoring requests succeed

### Data Sync Failure

1. Identify if scoring results are stale or inconsistent across requests
2. Check if Grammarly updated their scoring model (review changelog)
3. Compare current scores against known baseline text samples
4. If quality drift confirmed: log evidence and file support ticket
5. Consider pinning API version if Grammarly supports versioned endpoints

## Communication Template

```markdown
**Incident**: Grammarly Integration [Outage/Degradation]
**Status**: [Investigating/Identified/Mitigating/Resolved]
**Started**: YYYY-MM-DD HH:MM UTC
**Impact**: [Text scoring unavailable / elevated latency / OAuth failure affecting N users]
**Current action**: [Fallback scores active / token refresh in progress / rate limit backoff enabled]
**Next update**: HH:MM UTC
```

## Post-Incident

- [ ] Document timeline from detection to resolution
- [ ] Identify root cause (Grammarly outage / token expiry / rate limit exceeded)
- [ ] Verify all scoring pipelines resumed with accurate results
- [ ] Add proactive token refresh before expiry (buffer by 10 min)
- [ ] Implement rate limit monitoring with alerting at 80% threshold
- [ ] Update fallback logic if edge cases were discovered

## Error Handling

| Incident Type | Detection | Resolution |
|--------------|-----------|------------|
| Text check timeout | Requests exceeding 10s SLA | Enable timeout + retry with exponential backoff |
| Suggestion quality degradation | Scores deviate from baseline samples | Log evidence, pin API version, file support ticket |
| OAuth token failure | 401 on all authenticated endpoints | Trigger refresh flow, re-authorize if refresh fails |
| Rate limit storm | 429 responses with Retry-After header | Implement request queuing, reduce concurrency |

## Prerequisites

- An incident owner, support path, and synthetic health input that contains no customer, employee, or unpublished text.
- Read-only diagnostics scoped to the affected environment, plus known-good baselines for availability, latency, quota, and authorization.
- A redaction standard that prohibits sending source text, suggestions, headers, or tokens to chat, tickets, or support bundles.

## Instructions

1. Open a timestamped incident record, classify impact, and reproduce once with the synthetic input.
2. Isolate the boundary—identity, endpoint, quota, client integration, or downstream storage—using status and correlation IDs only.
3. Freeze nonessential rollout changes, apply one reversible remediation, and monitor the synthetic probe and aggregate metrics.
4. Verify recovery with least-privilege and denied identities where applicable; stop if a change expands text access or logging scope.
5. Close with the remediation, rollback decision, and redacted evidence, then schedule any credential rotation or configuration follow-up.

## Output

Produce an incident receipt with severity, UTC window, affected integration, redacted error class, remediation/rollback decision, probe results, owner, and next action. Never include submitted text, suggestions, identities, or credentials.

## Examples

`P2; integration=staging-editor; error=429; action=bounded-backoff; probe=healthy; rollback=not-needed; followup=quota-review` is a safe incident summary.

## Resources

- Grammarly Developer Docs
- Grammarly API Support

## Next Steps

See `grammarly-observability` for monitoring setup and alerting thresholds.
