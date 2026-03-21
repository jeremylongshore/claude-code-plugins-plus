---
name: severity-classify
description: Classify an issue, finding, or vulnerability by severity level (S1-S4)
shortcut: sev
---
# Severity Classification

Analyze the provided issue, bug report, or security finding and assign an appropriate severity level.

## Severity Levels

### S1 — Critical
- System completely down or unusable
- Active data loss or corruption
- Security breach with confirmed exploitation
- No workaround available
- **Response time:** Immediate

### S2 — High
- Major functionality broken for many users
- Security vulnerability with high exploitability
- Data integrity at risk
- Workaround exists but is impractical
- **Response time:** Within 4 hours

### S3 — Medium
- Functionality degraded but operational
- Security issue with limited scope
- Reasonable workaround available
- Affects subset of users or use cases
- **Response time:** Within 24 hours

### S4 — Low
- Minor issue or cosmetic defect
- Enhancement request
- Documentation improvement
- Edge case with minimal impact
- **Response time:** Backlog

## Classification Process

1. **Read the issue** — Understand the full context of the report
2. **Assess impact** — Determine scope, affected users, and business impact
3. **Evaluate exploitability** — For security issues, assess ease of exploitation
4. **Check for workarounds** — Determine if users can work around the issue
5. **Assign severity** — Apply the appropriate S1-S4 level
6. **Provide rationale** — Explain the classification with supporting evidence

## Output Format

```
## Severity: S[1-4] — [Critical|High|Medium|Low]

**Impact:** [Description of impact]
**Scope:** [How many users/systems affected]
**Workaround:** [Available|None|Impractical]
**Rationale:** [Why this severity was assigned]

### Recommended Actions
1. [First action]
2. [Second action]
```
