---
name: flexport-incident-runbook
description: 'Execute Flexport incident response for API outages, webhook failures,

  and supply chain data sync issues with triage and mitigation steps.

  Trigger: "flexport incident", "flexport outage", "flexport down", "flexport emergency".

  '
allowed-tools: Read, Bash(curl:*), Bash(jq:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- logistics
- flexport
compatibility: Designed for Claude Code
---
# Flexport Incident Runbook

## Overview

Incident response procedures for Flexport logistics API integration failures. Covers shipment tracking outages, customs data sync failures, webhook delivery loss, and API degradation scenarios. Flexport powers real-time supply chain visibility, so incidents directly impact shipment tracking, booking workflows, and customs compliance reporting. Classify severity immediately using the matrix below, then follow the matching playbook.

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|-----------|---------------|---------|
| P1 - Critical | Full API outage or customs data loss | 15 min | Flexport API returns 5xx on all endpoints |
| P2 - High | Partial failure or webhook delivery loss | 30 min | Webhook events not arriving, stale shipment data |
| P3 - Medium | Degraded performance or rate limiting | 2 hours | 429 responses, elevated latency on tracking calls |
| P4 - Low | Single endpoint issue or key rotation | 8 hours | One shipment query failing, API key nearing expiry |

## Diagnostic Steps

```bash
# Check API health
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -H "Authorization: Bearer $FLEXPORT_API_KEY" \
  -H "Flexport-Version: 2" \
  https://api.flexport.com/shipments?per=1

# Check platform status
curl -s https://status.flexport.com/api/v2/status.json | jq -r '.status.description'

# Check rate limit remaining
curl -s -D - -o /dev/null \
  -H "Authorization: Bearer $FLEXPORT_API_KEY" \
  -H "Flexport-Version: 2" \
  https://api.flexport.com/shipments?per=1 2>/dev/null | grep -i "x-ratelimit"
```

## Incident Playbooks

### API Outage
1. Confirm via status.flexport.com and diagnostic script above
2. Enable circuit breaker to serve cached shipment data
3. Notify downstream consumers that tracking data is stale
4. Queue failed requests for replay once API recovers
5. Monitor status page for Flexport resolution updates

### Authentication Failure
1. Verify API key is set and not expired: check `$FLEXPORT_API_KEY`
2. Test with a minimal authenticated request (see diagnostics)
3. If 401: rotate API key in Flexport portal, deploy new key
4. If 403: check API key scopes match required permissions
5. Revoke compromised keys after new key is confirmed working

### Data Sync Failure
1. Check webhook endpoint health — is your receiver returning 200?
2. Query `/webhooks` to verify subscription is active
3. Identify missed events by comparing last processed timestamp
4. Trigger manual sync for affected shipments via `/shipments` polling
5. Replay missed webhook events using Flexport's retry mechanism

## Communication Template

```markdown
**Incident**: Flexport Integration [Outage/Degradation]
**Status**: [Investigating/Identified/Mitigating/Resolved]
**Started**: YYYY-MM-DD HH:MM UTC
**Impact**: [N shipments affected / tracking data stale since HH:MM]
**Current action**: [Circuit breaker active / manual sync running / key rotation in progress]
**Next update**: HH:MM UTC
```

## Post-Incident

- [ ] Document timeline from detection to resolution
- [ ] Identify root cause (Flexport outage / key expiry / webhook endpoint failure)
- [ ] Calculate impact: affected shipments, stale data duration, missed customs deadlines
- [ ] Add monitoring for the specific failure mode that was missed
- [ ] Implement or verify circuit breaker covers the failed endpoint
- [ ] Replay any missed webhook events and reconcile data

## Error Handling

| Incident Type | Detection | Resolution |
|--------------|-----------|------------|
| Shipment tracking outage | 5xx on `/shipments` endpoints | Circuit breaker + cached data fallback |
| Customs data sync failure | Stale customs docs, webhook gaps | Manual sync + webhook replay |
| Webhook delivery loss | Missing events in processing queue | Verify endpoint, replay from last checkpoint |
| API rate limiting | 429 responses, `Retry-After` header | Reduce concurrency, implement request queuing |
| API key compromise | Unexpected 401 after working state | Rotate key immediately, audit access logs |

## Resources

- [Flexport Status](https://status.flexport.com)
- [Flexport API Docs](https://developers.flexport.com)

## Next Steps

See `flexport-observability` for monitoring setup and alerting thresholds.
