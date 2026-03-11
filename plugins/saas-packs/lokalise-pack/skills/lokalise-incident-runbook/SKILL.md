---
name: lokalise-incident-runbook
description: |
  Execute Lokalise incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Lokalise-related outages, investigating errors,
  or running post-incident reviews for Lokalise integration failures.
  Trigger with phrases like "lokalise incident", "lokalise outage",
  "lokalise down", "lokalise on-call", "lokalise emergency", "translations broken".
allowed-tools: Read, Grep, Bash(curl:*), Bash(lokalise2:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Incident Runbook

## Overview
Rapid incident response procedures for Lokalise-related outages and issues.

## Prerequisites
- Access to Lokalise dashboard and status page
- Application logs and monitoring dashboards
- Communication channels (Slack, PagerDuty)
- Rollback procedures documented

## Instructions
1. **Severity Levels**
2. **Quick Triage Commands**
3. **Decision Tree**
4. **Immediate Actions by Error Type**
5. **Communication Templates**
6. **Post-Incident**
7. **Rollback Procedures**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Issue identified and categorized
- Remediation applied
- Stakeholders notified
- Evidence collected for postmortem

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach status page | Network issue | Use mobile or VPN |
| Logs unavailable | Logging down | Check logging service |
| Fallback not working | Not configured | Enable static fallback |
| Token rotation fails | Permission denied | Escalate to admin |

## Examples
### One-Line Health Check
```bash
set -euo pipefail
curl -sf https://your-app.com/health/lokalise | jq '.status' || echo "UNHEALTHY"
```

### Quick Fallback Enable
```typescript
// Emergency fallback - use in incident
process.env.LOKALISE_FALLBACK_ENABLED = "true";

// Your translation loader should check this
const useFallback = process.env.LOKALISE_FALLBACK_ENABLED === "true";
if (useFallback) {
  return loadBundledTranslations(locale);
}
```

## Resources
- [Lokalise Status Page](https://status.lokalise.com)
- [Lokalise Support](mailto:support@lokalise.com)
- [Community Forum](https://community.lokalise.com)

## Next Steps
For data handling, see `lokalise-data-handling`.