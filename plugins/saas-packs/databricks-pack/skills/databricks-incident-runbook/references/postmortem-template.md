# Postmortem template

Fill in within 48 hours of incident resolution. Archive to your team's incident-archive tag at `/incidents/<YYYY-MM-DD>-<slug>.md`.

## Template

```markdown
## Incident: [Title]

**Date:** YYYY-MM-DD | **Duration:** Xh Ym | **Severity:** P[1-4]
**IC:** [Name]

### Summary
[1-2 sentences: what happened and what was the impact]

### Timeline (UTC)
| Time | Event |
|------|-------|
| HH:MM | Alert fired / issue detected |
| HH:MM | Investigation started |
| HH:MM | Root cause identified |
| HH:MM | Mitigation applied |
| HH:MM | Resolved |

### Root Cause
[Technical explanation. Be specific — "Spark OOM" is insufficient. "Bronze ingest job's executor was sized at 8GB but processed a 12GB Parquet partition after upstream API change increased per-record payload by 50%" is sufficient.]

### Impact
- Tables affected: [list]
- Data staleness: [hours]
- Users affected: [count/teams]

### Action Items
| Priority | Action | Owner | Due |
|----------|--------|-------|-----|
| P1 | [Preventive fix — close the gap that allowed this incident] | [Name] | [Date] |
| P2 | [Monitoring gap — alert that should have fired] | [Name] | [Date] |
| P3 | [Process improvement — what the team could do better next time] | [Name] | [Date] |
```

## Rules of the template

- **Blameless.** Document what the system allowed to happen, never what a person did wrong. If a person clicked the wrong button, the question is "why did the system let one click cause a P1?"
- **Specific.** Vague root causes ("data quality issue") don't help anyone. Specific root causes ("UTF-8 byte-order-mark in source CSV crashed PySpark CSV reader because `mode='FAILFAST'` was set in code path A but `mode='PERMISSIVE'` in code path B") prevent repeats.
- **Action items have owners and dates.** "Improve monitoring" is not an action item. "Add Datadog alert on `system.streaming.query_progress` p99 latency > 5s, owner @alice, due 2026-07-01" is.
- **48-hour deadline.** Memory degrades fast. Postmortems written 2 weeks later miss 60% of the timeline details.
- **Read in retro.** Add the link to your next sprint retro's pre-read. Action items get accountability when surfaced to the whole team, not just the IC.

## What NOT to include

- Stack traces longer than 20 lines (link to evidence-bundle tarball instead)
- Internal Slack messages copy-pasted (link to thread)
- Customer names or PII (anonymize: "Customer A reported", not "Acme Corp reported")
- Speculation labeled as fact ("The root cause might have been..." → only write what's verified)
