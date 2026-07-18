# Communication & Post-Incident

Templates for stakeholder communication during an incident and for the review afterward.

## Communication Templates

### Internal Alert (Slack/PagerDuty)

```
P[1-4] INCIDENT: Groq API [Error Type]
Status: INVESTIGATING | MITIGATING | RESOLVED
Impact: [What users see]
Current action: [What we're doing]
Fallback: [Enabled/Disabled]
Next update in: [Time]
Commander: @[name]
```

### Status Page (External)

```
AI Feature Performance Issue

We're experiencing [degraded performance / intermittent errors] with our AI features.
[Feature X] may respond slower than usual.
We've activated backup systems and are monitoring the situation.

Last updated: [timestamp]
```

## Post-Incident

### Evidence Collection

```bash
set -euo pipefail
INCIDENT_DIR="groq-incident-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$INCIDENT_DIR"

# API diagnostics
curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" > "$INCIDENT_DIR/models.json"

# Application logs (redacted)
kubectl logs -l app=your-app --since=1h 2>/dev/null | \
  grep -i "groq\|429\|error\|timeout" | \
  sed 's/gsk_[a-zA-Z0-9]*/gsk_REDACTED/g' | \
  tail -100 > "$INCIDENT_DIR/app-logs.txt"

tar -czf "$INCIDENT_DIR.tar.gz" "$INCIDENT_DIR"
echo "Evidence bundle: $INCIDENT_DIR.tar.gz"
```

### Postmortem Template

```markdown
## Incident: Groq [Error Type] — [Date]
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Impact:** [N users affected, feature X degraded]

### Timeline
- HH:MM — First alert fired
- HH:MM — On-call acknowledged, began triage
- HH:MM — Root cause identified: [cause]
- HH:MM — Mitigation applied: [what]
- HH:MM — Resolved, monitoring

### Root Cause
[Was it Groq-side or our side? Rate limit hit? Model deprecated? Key expired?]

### What Went Well
- [Fallback activated automatically]

### What Could Improve
- [Alert fired too late / fallback didn't work / no runbook]

### Action Items
- [ ] [Action] — Owner — Due date
```
