---
name: apollo-local-dev-loop
description: |
  Configure Apollo.io local development workflow.
  Use when setting up development environment, testing API calls locally,
  or establishing team development practices.
  Trigger with phrases like "apollo local dev", "apollo development setup",
  "apollo dev environment", "apollo testing locally".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Local Dev Loop

## Overview
Set up efficient local development workflow for Apollo.io integrations with proper environment management, testing, and debugging.

## Prerequisites
- Completed `apollo-install-auth` setup
- Node.js 18+ or Python 3.10+
- Git repository initialized

## Instructions
Follow these high-level steps to implement apollo-local-dev-loop:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-local-dev-loop/references/implementation-guide.md)`

## Output
- Environment file structure (.env, .env.example)
- Development client with logging interceptors
- Mock server for testing without API calls
- npm scripts for development workflow
- Quota monitoring utility

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Missing API Key | .env not loaded | Run `source .env` or use dotenv |
| Mock Not Working | MSW not configured | Ensure setupServer is called |
| Rate Limited in Dev | Too many test calls | Use mock server for tests |
| Stale Credentials | Key rotated | Update .env with new key |

## Resources
- [MSW (Mock Service Worker)](https://mswjs.io/)
- [Vitest Testing Framework](https://vitest.dev/)
- [dotenv Documentation](https://github.com/motdotla/dotenv)

## Next Steps
Proceed to `apollo-sdk-patterns` for production-ready code patterns.

## Examples

**Basic usage**: Apply apollo local dev loop to a standard project setup with default configuration options.

**Advanced scenario**: Customize apollo local dev loop for production environments with multiple constraints and team-specific requirements.