---
name: apollo-upgrade-migration
description: |
  Plan and execute Apollo.io SDK upgrades.
  Use when upgrading Apollo API versions, migrating to new endpoints,
  or updating deprecated API usage.
  Trigger with phrases like "apollo upgrade", "apollo migration",
  "update apollo api", "apollo breaking changes", "apollo deprecation".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Apollo Upgrade Migration

## Overview
Plan and execute safe upgrades for Apollo.io API integrations, handling breaking changes and deprecated endpoints.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-upgrade-migration:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-upgrade-migration/references/implementation-guide.md)`

## Output
- Pre-upgrade audit results
- Compatibility layer for gradual migration
- Feature flag controlled rollout
- Parallel testing verification
- Cleanup procedures

## Error Handling
| Issue | Resolution |
|-------|------------|
| Audit finds errors | Fix before proceeding |
| Compat layer fails | Check mapping logic |
| Results differ | Investigate API changes |
| Canary issues | Immediate rollback |

## Resources
- [Apollo API Changelog](https://apolloio.github.io/apollo-api-docs/#changelog)
- [Apollo Migration Guides](https://knowledge.apollo.io/)
- [Feature Flag Best Practices](https://martinfowler.com/articles/feature-toggles.html)

## Next Steps
Proceed to `apollo-ci-integration` for CI/CD setup.
