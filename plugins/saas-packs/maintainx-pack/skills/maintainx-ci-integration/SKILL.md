---
name: maintainx-ci-integration
description: |
  Integrate MaintainX API testing into CI/CD pipelines.
  Use when setting up automated testing, configuring CI workflows,
  or implementing continuous integration for MaintainX integrations.
  Trigger with phrases like "maintainx ci", "maintainx github actions",
  "maintainx pipeline", "maintainx automated testing", "maintainx ci/cd".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# MaintainX CI Integration

## Overview
Configure continuous integration pipelines for MaintainX integrations with automated testing, security scanning, and quality gates.

## Prerequisites
- Git repository with MaintainX integration
- CI/CD platform (GitHub Actions, GitLab CI, etc.)
- Test environment with API access

## Instructions
Follow these high-level steps to implement maintainx-ci-integration:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-ci-integration/references/implementation-guide.md)`

## Output
- GitHub Actions workflow configured
- GitLab CI pipeline configured
- Unit tests with mocks
- Integration tests with real API
- Security scanning enabled

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Jest Documentation](https://jestjs.io/)
- [MaintainX API Documentation](https://maintainx.dev/)

## Next Steps
For deployment automation, see `maintainx-deploy-integration`.
