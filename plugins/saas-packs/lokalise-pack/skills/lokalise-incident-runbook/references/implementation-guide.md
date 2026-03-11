# Lokalise Incident Runbook - Implementation Guide

Detailed implementation reference for the lokalise-incident-runbook skill.

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Complete outage | < 15 min | Lokalise API unreachable, all translations missing |
| P2 | Degraded service | < 1 hour | High latency, partial failures, key languages affected |
| P3 | Minor impact | < 4 hours | Webhook delays, non-critical translations missing |
| P4 | No user impact | Next business day | Monitoring gaps, sync delays |


## Quick Triage Commands

```bash
# 1. Check Lokalise API status
curl -s https://api.lokalise.com/api2/system/health | jq

# 2. Check Lokalise status page
curl -s https://status.lokalise.com/api/v2/status.json | jq '.status.description'

# 3. Test API authentication
curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN" \
  "https://api.lokalise.com/api2/projects?limit=1"

# 4. Check your app's translation health
curl -s https://your-app.com/health/lokalise | jq

# 5. Check recent error logs (last 5 min)
grep -i "lokalise" /var/log/app/*.log | tail -50
```


## Decision Tree

```
Translations missing/broken?
├─ YES: Is https://status.lokalise.com showing incident?
│   ├─ YES → Enable fallback translations. Monitor status page.
│   └─ NO → Check our integration. Continue triage below.
└─ NO: Is sync failing?
    ├─ YES → Check CI/CD pipeline, API token validity
    └─ NO → Likely localized issue. Check specific component.

API returning errors?
├─ 401 → Token expired/invalid. Rotate token.
├─ 403 → Permission denied. Check project access.
├─ 404 → Project/key not found. Verify IDs.
├─ 429 → Rate limited. Enable backoff/queuing.
└─ 5xx → Lokalise issue. Enable fallback, monitor status.
```


## Immediate Actions by Error Type

### 401/403 - Authentication/Authorization
```bash
# Verify token is set
echo "Token set: ${LOKALISE_API_TOKEN:+YES}"

# Test token validity
curl -s -H "X-Api-Token: $LOKALISE_API_TOKEN" \
  "https://api.lokalise.com/api2/projects?limit=1" | jq '.projects[0].name // .error'

# If token is invalid:
# 1. Generate new token in Lokalise Profile Settings
# 2. Update in secret manager
# 3. Restart affected services
```

### 429 - Rate Limited
```bash
# Check current rate limit status
curl -s -I -H "X-Api-Token: $LOKALISE_API_TOKEN" \
  "https://api.lokalise.com/api2/projects" | grep -i "x-ratelimit"

# Immediate mitigation:
# 1. Reduce concurrent requests
# 2. Add delays between API calls
# 3. Enable request queuing

# Application config
export LOKALISE_RATE_LIMIT_MODE=queue
export LOKALISE_REQUEST_DELAY_MS=200
```

### 5xx - Lokalise Server Errors
```bash
# Check Lokalise status
curl -s https://status.lokalise.com/api/v2/status.json | jq

# Enable graceful degradation
export LOKALISE_FALLBACK_ENABLED=true

# Use bundled translations as fallback
# Your app should fall back to static locale files

# Monitor for resolution
watch -n 60 'curl -s https://status.lokalise.com/api/v2/status.json | jq ".status.description"'
```

### Missing Translations
```bash
# Check if translations exist in Lokalise
lokalise2 --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  key list --filter-untranslated-any 1 | head -20

# Check local translation files
ls -la src/locales/
cat src/locales/en.json | jq 'keys | length'

# If files missing, re-download
npm run i18n:pull
```


## Communication Templates

### Internal (Slack)
```
:red_circle: P1 INCIDENT: Lokalise Integration
Status: INVESTIGATING
Impact: [Translations not loading for all users]
Current action: [Checking API status and enabling fallback]
Next update: [Time + 15 min]
Incident commander: @[name]
```

### External (Status Page)
```
Translation Service Issue

We're experiencing issues with our translation service.
Some users may see English text instead of their preferred language.

We're actively investigating and will provide updates.

Last updated: [timestamp]
```


## Post-Incident

### Evidence Collection
```bash
# Generate debug bundle
bash scripts/lokalise-debug-bundle.sh

# Export relevant logs
grep -i "lokalise" /var/log/app/*.log > incident-logs.txt

# Export metrics snapshot
curl "http://prometheus:9090/api/v1/query_range?query=lokalise_errors_total&start=-2h" > metrics.json

# Screenshot dashboards
# Document timeline in incident channel
```

### Postmortem Template
```markdown
## Incident: Lokalise [Error Type]
**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Incident Commander:** [Name]

### Summary
[1-2 sentence description of what happened]

### Timeline (all times UTC)
- HH:MM - [Alert triggered / Issue reported]
- HH:MM - [Investigation started]
- HH:MM - [Root cause identified]
- HH:MM - [Mitigation applied]
- HH:MM - [Service restored]

### Root Cause
[Technical explanation of what went wrong]

### Impact
- Users affected: [N]
- Duration of user impact: [X minutes]
- Translations affected: [Languages/keys]

### What Went Well
- [Positive aspects of response]

### What Could Be Improved
- [Areas for improvement]

### Action Items
- [ ] [Preventive measure] - Owner - Due date
- [ ] [Documentation update] - Owner - Due date
- [ ] [Monitoring improvement] - Owner - Due date
```


## Rollback Procedures

### Revert to Bundled Translations
```bash
# If translations are corrupted, revert to last known good
git checkout HEAD~1 -- src/locales/

# Rebuild and deploy
npm run build
npm run deploy

# Disable auto-sync temporarily
export LOKALISE_AUTO_SYNC=false
```

### Re-download from Lokalise
```bash
# Download reviewed translations only
lokalise2 --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  file download \
  --format json \
  --filter-data reviewed \
  --unzip-to ./src/locales
```

