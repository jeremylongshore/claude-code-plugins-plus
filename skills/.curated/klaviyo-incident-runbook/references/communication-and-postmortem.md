# Communication Templates and Postmortem

Ready-to-fill templates for keeping stakeholders informed during a Klaviyo
incident and for producing a durable post-incident record afterward.

## Communication Templates

### Internal (Slack)

```
P[1/2] INCIDENT: Klaviyo Integration
Status: INVESTIGATING / MITIGATING / RESOLVED
Impact: [What users are experiencing]
Root cause: [Klaviyo outage / Our key expired / Rate limit exceeded]
Current action: [What we're doing right now]
ETA: [When we expect resolution]
Incident lead: @[name]
```

### External (Status Page)

```
Klaviyo Integration -- Degraded Performance

Some features powered by Klaviyo (email subscriptions, event tracking)
are experiencing delays. Customer data is being queued and will be
processed once the issue is resolved.

No data loss is expected. We are monitoring the situation.

Last updated: [timestamp]
```

## Post-Incident

### Evidence Collection

```bash
# Generate debug bundle
bash klaviyo-debug-bundle.sh

# Export application logs
# (adjust for your logging setup)
journalctl -u my-app --since "2 hours ago" | grep -i klaviyo > incident-logs.txt

# Capture metrics snapshot
curl -s "localhost:9090/api/v1/query?query=klaviyo_api_errors_total" > metrics-snapshot.json
```

### Postmortem Template

```markdown
## Incident: Klaviyo [Error Type]
**Date:** YYYY-MM-DD HH:MM - HH:MM UTC
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Incident Lead:** [Name]

### Summary
[1-2 sentence description of what happened]

### Timeline (UTC)
- HH:MM - Alert fired: [description]
- HH:MM - Incident acknowledged by [name]
- HH:MM - Root cause identified: [description]
- HH:MM - Mitigation applied: [what was done]
- HH:MM - Service restored
- HH:MM - Monitoring confirmed stable

### Root Cause
[Technical explanation]

### Impact
- Affected users: [number/percentage]
- Failed API calls: [count]
- Data queued for retry: [count]

### Action Items
- [ ] [Action] - Owner: [name] - Due: [date]
- [ ] [Action] - Owner: [name] - Due: [date]

### Lessons Learned
- What went well: [...]
- What could improve: [...]
```
