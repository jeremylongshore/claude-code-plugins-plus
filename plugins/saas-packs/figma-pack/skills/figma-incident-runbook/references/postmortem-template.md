# Step 5: Postmortem Template

Deep-dive reference for the `figma-incident-runbook` skill — extracted from the 'Step 5: Postmortem Template' step of the workflow.

```markdown
## Figma Incident Postmortem
**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P1/P2/P3

### Summary
[One sentence: what happened and what was the impact]

### Timeline
- HH:MM UTC - First alert fired (describe alert)
- HH:MM UTC - On-call acknowledged
- HH:MM UTC - Root cause identified
- HH:MM UTC - Mitigation applied
- HH:MM UTC - Full resolution confirmed

### Root Cause
[Technical explanation, e.g., "PAT expired after 90 days without rotation"]

### Action Items
- [ ] Set up PAT rotation reminder at 80-day mark
- [ ] Add 403 alert to PagerDuty
- [ ] Implement cached fallback for token data
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
