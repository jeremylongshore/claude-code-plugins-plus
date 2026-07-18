# Post-Incident Evidence & Communication

Use these once the incident is mitigated: capture forensic evidence from the
error window, then keep stakeholders informed and write up the postmortem.

## Post-Incident Evidence Collection

```sql
-- Export error window from query log
SELECT *
FROM system.query_log
WHERE event_time BETWEEN '2025-01-15 14:00:00' AND '2025-01-15 15:00:00'
  AND (type = 'ExceptionWhileProcessing' OR query_duration_ms > 10000)
FORMAT JSONEachRow
INTO OUTFILE '/tmp/incident-queries.json';

-- Metrics snapshot during incident window
SELECT metric, value
FROM system.metrics
FORMAT TabSeparatedWithNames
INTO OUTFILE '/tmp/incident-metrics.tsv';
```

## Communication Templates

**Internal (Slack):**

```
[P1] INCIDENT: ClickHouse [Issue Type]
Status: INVESTIGATING / MITIGATING / RESOLVED
Impact: [What users see]
Root cause: [If known]
Actions taken: [What you did]
Next update: [Time]
Commander: @[name]
```

**Postmortem Template:**

```markdown
## ClickHouse Incident: [Title]
- Date: YYYY-MM-DD
- Duration: X hours Y minutes
- Severity: P[1-4]

### Timeline
- HH:MM — [Event/action]

### Root Cause
[Technical explanation]

### Resolution
[What fixed it]

### Action Items
- [ ] [Preventive measure] — Owner — Due date
```
