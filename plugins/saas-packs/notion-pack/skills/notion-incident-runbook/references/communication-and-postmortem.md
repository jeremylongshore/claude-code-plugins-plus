# Communication and Postmortem Templates

Step 3 detail: copy-paste templates for internal Slack updates, external status-page
notices, and the structured postmortem you file after the incident is resolved.

## Internal Slack notification template

```
:rotating_light: P[1-4] INCIDENT: Notion Integration
Status: [INVESTIGATING | MITIGATING | RESOLVED]
Impact: [specific user-facing impact]
Root Cause: [Notion outage | Token expired | Rate limited | Schema change]
Action: [current remediation step]
ETA: [estimated resolution or "monitoring"]
Dashboard: [link to monitoring dashboard]
Thread: [link to incident channel thread]
```

## External status page update

```
Notion Integration Service Disruption

We are experiencing [brief description of impact]. [Specific feature]
may be unavailable or show stale data.

Workaround: [if available, e.g., "Cached data is being served"]
Next update: [time, e.g., "in 30 minutes or sooner if resolved"]

[ISO 8601 timestamp]
```

## Postmortem template

```markdown
## Incident: Notion [Error Type] — [Date]
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Detection:** [Alert name] / [User report]

### Summary
[1-2 sentence description of what happened and the user impact]

### Timeline (all times UTC)
- HH:MM — First alert fired ([alert name])
- HH:MM — On-call acknowledged, began triage
- HH:MM — Root cause identified: [description]
- HH:MM — Mitigation applied: [action taken]
- HH:MM — Service fully restored

### Root Cause
[Technical explanation — e.g., "Integration token was rotated in Notion
dashboard by a team member without updating the secret manager, causing
all API calls to return 401 Unauthorized."]

### Impact
- Users affected: N
- Duration of degraded service: X minutes
- Data loss: [none | description]

### Action Items
| Priority | Action | Owner | Due |
|----------|--------|-------|-----|
| P1 | [Preventive measure] | @name | YYYY-MM-DD |
| P2 | [Detection improvement] | @name | YYYY-MM-DD |
| P3 | [Process improvement] | @name | YYYY-MM-DD |
```
