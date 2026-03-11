---
name: speak-incident-runbook
description: |
  Execute Speak incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Speak-related outages, investigating errors,
  or running post-incident reviews for language learning feature failures.
  Trigger with phrases like "speak incident", "speak outage",
  "speak down", "speak on-call", "speak emergency", "speak broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Speak Incident Runbook

## Overview
Rapid incident response procedures for Speak language learning-related outages.

## Prerequisites
- Access to Speak dashboard and status page
- kubectl access to production cluster
- Prometheus/Grafana access
- Communication channels (Slack, PagerDuty)

## Instructions
1. **Severity Levels**
2. **Quick Triage**
3. **Decision Tree**
4. **Immediate Actions by Error Type**
5. **Communication Templates**
6. **Fallback Modes**
7. **Post-Incident**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Issue identified and categorized
- Mitigation applied
- Stakeholders notified
- Evidence collected for postmortem
- Fallback modes enabled if needed

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach status page | Network issue | Use mobile or VPN |
| kubectl fails | Auth expired | Re-authenticate |
| Metrics unavailable | Prometheus down | Check backup metrics |
| Fallback not working | Cache empty | Pre-warm cache |

## Examples
### One-Line Health Check
```bash
curl -sf https://api.yourapp.com/health | jq '.services.speak.status' || echo "UNHEALTHY"
```

### Quick Fallback Toggle
```bash
# Enable fallback
kubectl set env deployment/speak-integration SPEAK_FALLBACK_MODE=true

# Disable fallback (restore normal)
kubectl set env deployment/speak-integration SPEAK_FALLBACK_MODE-
```

## Resources
- [Speak Status Page](https://status.speak.com)
- [Speak Support](https://support.speak.com)
- [Internal Runbook Wiki](#)

## Next Steps
For data handling, see `speak-data-handling`.
