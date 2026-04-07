---
name: glean-incident-runbook
description: |
  Triage: Is search returning results? Check Glean status page.
  Trigger: "glean incident runbook", "incident-runbook".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Incident Runbook

## Overview

Incident response procedures for Glean enterprise search integration failures. Covers search degradation, connector sync failures, indexing backlogs, and permission sync drift. Glean aggregates knowledge across all company tools, so incidents impact employee productivity across the entire organization. When search breaks or returns stale results, teams lose access to critical institutional knowledge. Classify severity immediately and follow the matching playbook below.

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|-----------|---------------|---------|
| P1 - Critical | Search fully down or returning zero results | 15 min | All queries return empty, API 5xx errors |
| P2 - High | Connector sync failed, content going stale | 30 min | Google Drive connector last synced 24h ago |
| P3 - Medium | Indexing backlog or partial result degradation | 2 hours | New documents not appearing for 4+ hours |
| P4 - Low | Permission sync drift or single datasource issue | 8 hours | One user sees docs they shouldn't access |

## Diagnostic Steps

```bash
# Test search API health
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -H "Authorization: Bearer $GLEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST https://your-domain.glean.com/api/v1/search \
  -d '{"query": "test", "pageSize": 1}'

# Check datasource connector status
curl -s -H "Authorization: Bearer $GLEAN_API_TOKEN" \
  https://your-domain.glean.com/api/v1/getdatasourceconfig \
  -d '{"datasource": "DATASOURCE_NAME"}' | jq '.status'

# Verify indexing queue depth
curl -s -H "Authorization: Bearer $GLEAN_API_TOKEN" \
  https://your-domain.glean.com/api/index/v1/getstatus | jq '.statistics'
```

## Incident Playbooks

### API Outage
1. Confirm outage with diagnostic curl above and check Glean status page
2. Verify your Glean instance URL resolves and TLS cert is valid
3. Test from multiple networks to rule out local DNS or firewall issues
4. Notify users that search is temporarily unavailable
5. Contact Glean support with instance name, timestamps, and error codes

### Authentication Failure
1. Verify API token is set: `echo $GLEAN_API_TOKEN | wc -c`
2. Check token expiry — Glean tokens may have a TTL configured by your admin
3. Test with a minimal search request (see diagnostics above)
4. If 401: regenerate token in Glean admin console under API settings
5. If 403: verify token scopes include search and indexing permissions

### Data Sync Failure
1. Identify which connector failed via `getdatasourceconfig` for each source
2. Check connector credentials — OAuth tokens for Google/Slack/Confluence may have expired
3. Review connector error logs in Glean admin under Datasource Management
4. Re-authorize the connector if credentials expired
5. Trigger a manual re-crawl for the affected datasource
6. Monitor indexing status until backlog clears

## Communication Template

```markdown
**Incident**: Glean Search [Outage/Degradation]
**Status**: [Investigating/Identified/Mitigating/Resolved]
**Started**: YYYY-MM-DD HH:MM UTC
**Impact**: [Search unavailable / results stale since HH:MM / N datasources not syncing]
**Current action**: [Connector re-auth in progress / Glean support engaged / manual re-crawl running]
**Next update**: HH:MM UTC
```

## Post-Incident

- [ ] Document timeline from detection to resolution
- [ ] Identify root cause (connector auth expiry / Glean platform issue / indexing bottleneck)
- [ ] Audit all connector credentials for upcoming expirations
- [ ] Verify permission sync is accurate post-recovery
- [ ] Add alerting for connector sync age thresholds
- [ ] Schedule review of datasource health dashboard weekly

## Error Handling

| Incident Type | Detection | Resolution |
|--------------|-----------|------------|
| Search degradation | Empty results or low relevance scores | Check API health, verify index freshness |
| Connector sync failure | Stale content, `getdatasourceconfig` shows error | Re-authorize connector, trigger manual crawl |
| Indexing backlog | New docs not searchable after 4+ hours | Monitor queue depth, contact Glean if persistent |
| Permission sync drift | Users see restricted docs or miss accessible ones | Audit datasource permissions, trigger permission re-sync |

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)

## Next Steps

See `glean-observability` for monitoring setup and connector health dashboards.
