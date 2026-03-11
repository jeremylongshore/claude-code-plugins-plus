---
name: speak-prod-checklist
description: |
  Execute Speak production deployment checklist and rollback procedures.
  Use when deploying Speak integrations to production, preparing for launch,
  or implementing go-live procedures for language learning features.
  Trigger with phrases like "speak production", "deploy speak",
  "speak go-live", "speak launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Speak Prod Checklist

## Overview
Complete checklist for deploying Speak language learning integrations to production.

## Prerequisites
- Staging environment tested and verified
- Production API keys available
- Deployment pipeline configured
- Monitoring and alerting ready
- Audio infrastructure tested

## Instructions
1. **Health Check Implementation**
2. **Rollback Procedure**
3. **Alert Configuration**
4. **Production Monitoring Dashboard**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Deployed Speak integration
- Health checks passing
- Monitoring active
- Rollback procedure documented and tested
- Alerting configured

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Health check fails | Speak service down | Enable fallback mode |
| High latency | Audio processing slow | Scale audio workers |
| Session failures | API key issues | Verify credentials |
| Low completion rate | UX issues | Review user feedback |

## Examples
See `references/implementation-guide.md` for detailed examples.

## Resources
- [Speak Status](https://status.speak.com)
- [Speak Support](https://support.speak.com)
- [Speak Production Guide](https://developer.speak.com/docs/production)

## Next Steps
For version upgrades, see `speak-upgrade-migration`.
