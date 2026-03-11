---
name: apollo-ci-integration
description: |
  Configure Apollo.io CI/CD integration.
  Use when setting up automated testing, continuous integration,
  or deployment pipelines for Apollo integrations.
  Trigger with phrases like "apollo ci", "apollo github actions",
  "apollo pipeline", "apollo ci/cd", "apollo automated tests".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Apollo CI Integration

## Overview
Set up CI/CD pipelines for Apollo.io integrations with automated testing, secret management, and deployment workflows.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-ci-integration:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-ci-integration/references/implementation-guide.md)`

## Output
- GitHub Actions workflows for CI
- Secrets management configuration
- Test setup with MSW mocks
- Integration test suite
- Validation scripts

## Error Handling
| Issue | Resolution |
|-------|------------|
| Secret not found | Verify secret name in GitHub |
| Tests timeout | Increase timeout or mock API |
| Rate limited in CI | Use mocks for unit tests |
| Health check fails | Check Apollo status page |

## Resources
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [MSW (Mock Service Worker)](https://mswjs.io/)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps
Proceed to `apollo-deploy-integration` for deployment configuration.
