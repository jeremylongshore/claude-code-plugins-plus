---
name: openevidence-incident-runbook
description: |
  Incident Runbook for OpenEvidence.
  Trigger: "openevidence incident runbook".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Incident Runbook

## Severity
| Level | Condition | Response |
|-------|-----------|----------|
| P1 | API down | Immediate |
| P2 | Degraded | 15 min |
| P3 | Intermittent | 1 hour |

## Triage
1. Check OpenEvidence status page
2. Verify API key is valid
3. Test connectivity with curl
4. Check error logs for patterns

## Mitigation
- Enable cached/fallback responses
- Queue requests for retry
- Notify affected teams

## Resources
- [OpenEvidence Status](https://www.openevidence.com)

## Next Steps
See `openevidence-data-handling`.
