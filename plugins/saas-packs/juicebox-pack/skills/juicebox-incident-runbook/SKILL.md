---
name: juicebox-incident-runbook
description: |
  Juicebox incident response.
  Trigger: "juicebox incident", "juicebox outage".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Incident Runbook

## Overview

Incident response procedures for Juicebox AI analysis platform integration failures. Covers analysis timeouts, dataset corruption, quota exhaustion, and export failures. Juicebox powers AI-driven people search and candidate analysis, so incidents disrupt recruiting pipelines, talent intelligence workflows, and automated sourcing. Classify severity immediately using the matrix below and follow the corresponding playbook.

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|-----------|---------------|---------|
| P1 - Critical | Full API outage or dataset corruption | 15 min | Health endpoint returns 5xx, analysis results missing |
| P2 - High | Analysis timeouts or export failures | 30 min | Search queries hang beyond 30s, CSV exports fail |
| P3 - Medium | Quota exhaustion or rate limiting | 2 hours | 429 responses, account quota at 100% usage |
| P4 - Low | Partial data or degraded result quality | 8 hours | Search returns fewer results than expected |

## Diagnostic Steps

```bash
# Check API health
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -H "Authorization: Bearer $JUICEBOX_API_KEY" \
  https://api.juicebox.ai/v1/health

# Check account quota usage
curl -s -H "Authorization: Bearer $JUICEBOX_API_KEY" \
  https://api.juicebox.ai/v1/account/quota | jq '.used, .limit, .remaining'

# Test a minimal search request
curl -s -w "\nHTTP %{http_code}\n" \
  -H "Authorization: Bearer $JUICEBOX_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST https://api.juicebox.ai/v1/search \
  -d '{"query": "software engineer", "limit": 1}'
```

## Incident Playbooks

### API Outage
1. Confirm via health endpoint and status.juicebox.ai
2. Activate fallback mode — serve cached search results to active users
3. Pause any automated sourcing pipelines to avoid wasting quota on retries
4. Notify recruiting team that live search is temporarily unavailable
5. Monitor status page and resume operations once health check passes

### Authentication Failure
1. Verify API key is set: `echo $JUICEBOX_API_KEY | wc -c`
2. Test with health endpoint (see diagnostics above)
3. If 401: API key may be revoked — regenerate in Juicebox dashboard
4. If 403: check account tier permissions for the requested endpoint
5. Deploy new key and verify search requests succeed

### Data Sync Failure
1. Check if recent analysis results are returning stale or incomplete data
2. Verify export endpoints are responding — test a small CSV export
3. If exports fail: check if the analysis job completed successfully first
4. For dataset corruption: re-trigger the analysis with fresh parameters
5. Contact Juicebox support with job IDs and error responses

## Communication Template

```markdown
**Incident**: Juicebox Integration [Outage/Degradation]
**Status**: [Investigating/Identified/Mitigating/Resolved]
**Started**: YYYY-MM-DD HH:MM UTC
**Impact**: [Search unavailable / exports failing / quota exhausted / N recruiting workflows paused]
**Current action**: [Cached results active / quota upgrade requested / re-analysis running]
**Next update**: HH:MM UTC
```

## Post-Incident

- [ ] Document timeline from detection to resolution
- [ ] Identify root cause (Juicebox outage / quota burn / export bug / auth expiry)
- [ ] Calculate impact: missed candidates, paused pipelines, stale data duration
- [ ] Add quota usage alerting at 80% threshold to prevent exhaustion
- [ ] Implement request caching to reduce redundant API calls
- [ ] Review automated pipeline frequency to avoid quota spikes

## Error Handling

| Incident Type | Detection | Resolution |
|--------------|-----------|------------|
| Analysis timeout | Requests exceeding 30s SLA | Reduce query complexity, retry with smaller scope |
| Dataset corruption | Missing or inconsistent analysis results | Re-trigger analysis job, verify input parameters |
| Quota exhaustion | 429 responses, quota endpoint shows 0 remaining | Pause automation, request quota increase, optimize usage |
| Export failure | CSV/JSON export returns error or empty payload | Verify analysis job completed, retry export with job ID |

## Resources

- [Juicebox Status](https://status.juicebox.ai)
- [Juicebox API Docs](https://docs.juicebox.ai)

## Next Steps

See `juicebox-observability` for monitoring setup and quota tracking dashboards.
