---
name: apollo-incident-runbook
description: |
  Apollo.io incident response procedures.
  Use when handling Apollo outages, debugging production issues,
  or responding to integration failures.
  Trigger with phrases like "apollo incident", "apollo outage",
  "apollo down", "apollo production issue", "apollo emergency".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Apollo Incident Runbook

## Overview
Structured incident response procedures for Apollo.io integration issues with diagnosis steps, mitigation actions, and recovery procedures.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-incident-runbook:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-incident-runbook/references/implementation-guide.md)`

## Output
- Incident classification matrix
- Quick diagnosis commands
- Response procedures by severity
- Circuit breaker implementation
- Post-incident template

## Error Handling
| Issue | Escalation |
|-------|------------|
| P1 > 30 min | Page on-call lead |
| P2 > 2 hours | Notify management |
| Recurring P3 | Create P2 tracking |
| Apollo outage | Open support ticket |

## Resources
- [Apollo Status Page](https://status.apollo.io)
- [Apollo Support](https://support.apollo.io)
- [On-Call Runbook Template](https://sre.google/workbook/on-call/)

## Next Steps
Proceed to `apollo-data-handling` for data management.
