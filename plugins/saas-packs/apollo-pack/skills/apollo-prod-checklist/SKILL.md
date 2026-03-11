---
name: apollo-prod-checklist
description: |
  Execute Apollo.io production deployment checklist.
  Use when preparing to deploy Apollo integrations to production,
  doing pre-launch verification, or auditing production readiness.
  Trigger with phrases like "apollo production checklist", "deploy apollo",
  "apollo go-live", "apollo production ready", "apollo launch checklist".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Apollo Production Checklist

## Overview
Comprehensive checklist for deploying Apollo.io integrations to production with validation scripts and verification steps.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-prod-checklist:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-prod-checklist/references/implementation-guide.md)`

## Output
- Pre-deployment checklist completed
- Validation script results
- Post-deployment verification
- Rollback procedures documented

## Error Handling
| Issue | Resolution |
|-------|------------|
| Validation fails | Fix issues before deploy |
| Post-deploy fails | Execute rollback |
| Partial outage | Disable affected features |
| Full outage | Contact Apollo support |

## Resources
- [Apollo Status Page](https://status.apollo.io)
- [Apollo Support](https://support.apollo.io)
- [Apollo API Changelog](https://apolloio.github.io/apollo-api-docs/#changelog)

## Next Steps
Proceed to `apollo-upgrade-migration` for SDK upgrade procedures.
