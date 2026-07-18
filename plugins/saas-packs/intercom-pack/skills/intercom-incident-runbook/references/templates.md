# Communication & Postmortem Templates

Deep reference for the communication and post-incident phases. Copy these verbatim
and fill in the bracketed fields.

## Communication Templates

### Internal Slack

```
[P1] INCIDENT: Intercom Integration
Status: INVESTIGATING
Impact: [Customer conversations not loading / messages not sending]
Cause: [Intercom API returning 5xx / our token expired / rate limited]
Action: [Enabling fallback / rotating token / pausing sync jobs]
Next update: [Time]
Commander: @[name]
```

### Postmortem Template

```markdown
## Incident: Intercom [Type]
**Date:** YYYY-MM-DD HH:MM - HH:MM UTC
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Intercom request_ids:** [req_abc123, req_def456]

### Summary
[1-2 sentences describing what happened and user impact]

### Timeline
- HH:MM - First alert: [what triggered]
- HH:MM - Triage started: [findings]
- HH:MM - Mitigation: [action taken]
- HH:MM - Resolution: [what fixed it]

### Root Cause
[Technical explanation of why it happened]

### Impact
- Conversations affected: N
- Users unable to reach support: N
- Duration of degraded service: Xm

### Action Items
- [ ] [Preventive measure] - Owner - Due
- [ ] [Monitoring gap to fill] - Owner - Due
- [ ] [Documentation to update] - Owner - Due
```
