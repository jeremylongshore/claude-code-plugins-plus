---
name: adobe-incident-runbook
description: |
  Execute Adobe incident response procedures with triage, mitigation,
  and postmortem for Firefly Services, PDF Services, and I/O Events outages.
  Use when responding to Adobe-related incidents, investigating API failures,
  or running post-incident reviews.
  Trigger with phrases like "adobe incident", "adobe outage",
  "adobe down", "adobe on-call", "adobe emergency".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Incident Runbook

## Overview

Rapid incident response procedures for Adobe API-related outages, covering IMS authentication failures, Firefly/Photoshop API downtime, PDF Services quota exhaustion, and I/O Events delivery failures.

## Prerequisites

- Access to Adobe Developer Console and Admin Console
- Access to application monitoring (Grafana, Datadog, etc.)
- kubectl access to production cluster (if applicable)
- Communication channels (Slack, PagerDuty)

## Severity Matrix

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| P1 | Complete Adobe integration failure | < 15 min | IMS auth broken, all APIs down |
| P2 | Single API degraded | < 1 hour | Firefly 429s, Photoshop timeouts |
| P3 | Minor impact | < 4 hours | Webhook delays, slow PDF extraction |
| P4 | No user impact | Next business day | Monitoring gap, metric anomaly |

## Quick Triage (Run These First)

```bash
# 1. Is Adobe itself down?
curl -s -o /dev/null -w "Adobe Status: %{http_code}\n" https://status.adobe.com

# 2. Can we generate an access token?
curl -s -o /dev/null -w "IMS Auth: %{http_code}\n" -X POST \
  'https://ims-na1.adobelogin.com/ims/token/v3' \
  -d "client_id=${ADOBE_CLIENT_ID}&client_secret=${ADOBE_CLIENT_SECRET}&grant_type=client_credentials&scope=${ADOBE_SCOPES}"

# 3. Can we reach each API endpoint?
for endpoint in firefly-api.adobe.io image.adobe.io pdf-services.adobe.io; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "https://$endpoint" 2>/dev/null || echo "UNREACHABLE")
  echo "$endpoint: $CODE"
done

# 4. Check our app health
curl -sf https://your-app.com/health | python3 -m json.tool

# 5. Recent errors in our logs (last 5 min)
kubectl logs -l app=adobe-service --since=5m 2>/dev/null | grep -i "error\|failed\|429\|401\|500" | tail -20
```

## Decision Tree

```
Adobe APIs returning errors?
├── YES: Is status.adobe.com reporting an incident?
│   ├── YES → Adobe-side outage. Enable fallback mode. Monitor status page.
│   └── NO → Check our credentials and config.
│       ├── 401 errors → Credentials expired/rotated. See "Auth Recovery" below.
│       ├── 429 errors → Rate limited. See "Rate Limit Recovery" below.
│       └── 500/503 errors → Adobe server issue (unreported). Open support ticket.
└── NO: Is our application healthy?
    ├── YES → Likely resolved or intermittent. Continue monitoring.
    └── NO → Our infrastructure issue. Check pods, memory, network.
```

## Recovery Procedures

### Auth Recovery (401/403)

```bash
# 1. Verify credentials are still valid in Developer Console
#    https://developer.adobe.com/console → Your Project → Credentials

# 2. Test credential directly
curl -v -X POST 'https://ims-na1.adobelogin.com/ims/token/v3' \
  -d "client_id=${ADOBE_CLIENT_ID}&client_secret=${ADOBE_CLIENT_SECRET}&grant_type=client_credentials&scope=${ADOBE_SCOPES}" 2>&1 | grep -E "HTTP|error"

# 3. If credentials were rotated, update in secret manager
gcloud secrets versions add adobe-client-secret --data-file=- <<< "new_p8_secret"
# OR
aws secretsmanager update-secret --secret-id adobe/production/credentials \
  --secret-string '{"client_id":"...","client_secret":"new_secret"}'

# 4. Restart application to clear cached token
kubectl rollout restart deployment/adobe-service

# 5. Verify recovery
curl -sf https://your-app.com/health | jq '.services.adobe'
```

### Rate Limit Recovery (429)

```bash
# 1. Check if rate limiting is transient or sustained
# Look at 429 error rate over last 30 min

# 2. Reduce throughput immediately
# Option A: Scale down workers
kubectl scale deployment/adobe-batch-worker --replicas=1

# Option B: Enable rate limit queue mode
kubectl set env deployment/adobe-service ADOBE_RATE_LIMIT_MODE=queue

# 3. For sustained rate limiting, contact Adobe for limit increase
# Include: client_id, typical request volume, business justification
```

### Fallback Mode

```bash
# Enable fallback mode (app continues working without Adobe)
kubectl set env deployment/adobe-service ADOBE_FALLBACK_MODE=true

# Verify fallback is working
curl -sf https://your-app.com/health | jq '.services.adobe'
# Should return { "status": "degraded", "mode": "fallback" }
```

## Communication Templates

### Internal (Slack)

```
P[1-4] INCIDENT: Adobe [API Name] Integration
Status: INVESTIGATING / IDENTIFIED / MONITORING / RESOLVED
Impact: [User-facing description]
Root cause: [Adobe outage / credential issue / rate limit / our bug]
Current action: [What you're doing right now]
Next update: [Time]
Commander: @[name]
```

### Postmortem Template

```markdown
## Incident: Adobe [API] [Error Type]
**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P[1-4]

### Summary
[1-2 sentence description of what happened]

### Timeline
- HH:MM UTC — Alert fired: adobe_api_errors_total spike
- HH:MM UTC — On-call acknowledged, began triage
- HH:MM UTC — Root cause identified: [description]
- HH:MM UTC — Mitigation applied: [action taken]
- HH:MM UTC — Full recovery confirmed

### Root Cause
[Technical explanation — was it Adobe-side, credential issue, our bug?]

### Impact
- Users affected: N
- API calls failed: N
- Revenue impact: $X (if applicable)

### Action Items
- [ ] [Preventive measure] — Owner — Due date
- [ ] [Monitoring improvement] — Owner — Due date
- [ ] [Documentation update] — Owner — Due date
```

## Output

- Incident severity classified
- Root cause identified via decision tree
- Recovery procedure executed
- Stakeholders notified with template
- Evidence collected for postmortem

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach status.adobe.com | Network issue | Use mobile data or check @AdobeCare on Twitter |
| kubectl auth expired | Token timeout | Re-authenticate with cloud provider |
| Secret manager access denied | IAM policy | Use break-glass admin account |
| Fallback mode not implemented | Missing code path | Return cached/default data |

## Resources

- [Adobe Status Page](https://status.adobe.com)
- [Adobe Developer Support](https://developer.adobe.com/support)
- [Adobe Developer Console](https://developer.adobe.com/console)

## Next Steps

For data handling, see `adobe-data-handling`.
