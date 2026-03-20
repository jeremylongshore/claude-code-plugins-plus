---
name: evernote-incident-runbook
description: |
  Manage incident response for Evernote integration issues.
  Use when troubleshooting production incidents, handling outages,
  or responding to Evernote service issues.
  Trigger with phrases like "evernote incident", "evernote outage",
  "evernote emergency", "troubleshoot evernote production".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Incident Runbook

## Overview
Step-by-step procedures for responding to Evernote integration incidents including API outages, rate limit escalations, authentication failures, data sync issues, and quota exhaustion.

## Prerequisites
- Access to monitoring dashboards and production logs
- Production Evernote API credentials
- Communication channels for escalation (Slack, PagerDuty)

## Instructions

### Incident Classification

| Severity | Symptoms | Response Time |
|----------|----------|---------------|
| P1 - Critical | All Evernote API calls failing, data loss risk | 15 minutes |
| P2 - High | Persistent rate limits, auth failures for multiple users | 1 hour |
| P3 - Medium | Intermittent errors, degraded sync performance | 4 hours |
| P4 - Low | Single user issues, non-critical feature affected | Next business day |

### Step 1: Triage

Check Evernote's status page first. If Evernote is down, activate the circuit breaker and wait.

```bash
# Check Evernote service status
curl -sf https://status.evernote.com/api/v2/status.json | jq '.status'

# Check your API connectivity
curl -sf -H "Authorization: Bearer $EVERNOTE_TOKEN" \
  https://www.evernote.com/shard/s1/notestore | head -20

# Check error rate in logs (last 15 min)
grep -c 'EDAMSystemException' /var/log/evernote-app.log
```

### Step 2: Rate Limit Escalation

If rate limits are persistent: reduce API call frequency, increase delays between batch operations, and contact Evernote developer support for a rate limit increase.

### Step 3: Authentication Failure

For auth failures: verify tokens are not expired (`edam_expires`), check that production credentials match the production endpoint (`sandbox: false`), and test with a fresh Developer Token to isolate the issue.

### Step 4: Sync Failure Recovery

For sync issues: compare local USN with server USN via `getSyncState()`. If gap is too large, reset to full sync from USN 0. Verify data integrity after re-sync.

### Step 5: Mitigation Strategies

- **Circuit breaker**: Disable Evernote API calls after N consecutive failures. Retry after cooldown period.
- **Graceful degradation**: Serve cached data when API is unavailable. Queue writes for retry.
- **Failover**: Switch to polling-based sync if webhooks stop arriving.

### Post-Incident

- Document root cause and timeline
- Update runbook with new failure modes discovered
- Adjust alert thresholds if false positive or missed detection
- Review and improve circuit breaker settings

For the complete diagnostic scripts, mitigation implementations, and communication templates, see [Implementation Guide](references/implementation-guide.md).

## Output
- Incident severity classification table
- Triage diagnostic commands for quick assessment
- Rate limit, auth, and sync failure response procedures
- Circuit breaker and graceful degradation patterns
- Post-incident review checklist

## Error Handling
| Incident Type | Diagnostic | Mitigation |
|---------------|------------|------------|
| API outage | Check `status.evernote.com` | Activate circuit breaker, serve cached data |
| Rate limit storm | Check `evernote_rate_limits_total` metric | Reduce batch sizes, increase delays |
| Mass auth failure | Verify token expiration dates in DB | Trigger re-auth flow for affected users |
| Sync data loss | Compare local vs server note counts | Full re-sync from USN 0 |

## Resources
- [Evernote Status Page](https://status.evernote.com/)
- [Evernote Developer Support](https://dev.evernote.com/support/)
- [Error Handling](https://dev.evernote.com/doc/articles/error_handling.php)

## Next Steps
For data handling best practices, see `evernote-data-handling`.

## Examples

**API outage response**: Alert fires, on-call checks status page, confirms Evernote outage, activates circuit breaker, posts status update to internal Slack, monitors for recovery, then gradually re-enables API calls.

**Rate limit recovery**: Persistent `RATE_LIMIT_REACHED` errors detected. Reduce batch size from 100 to 10, increase delay to 500ms, clear the request queue, and contact Evernote support if limits continue after 1 hour.
