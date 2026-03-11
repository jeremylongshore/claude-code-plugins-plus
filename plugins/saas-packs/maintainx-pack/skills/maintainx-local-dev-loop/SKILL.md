---
name: maintainx-local-dev-loop
description: |
  Set up a local development loop for MaintainX integration development.
  Use when configuring dev environment, testing API calls locally,
  or setting up a sandbox workflow for MaintainX.
  Trigger with phrases like "maintainx dev setup", "maintainx local",
  "maintainx development environment", "maintainx testing setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(docker:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# MaintainX Local Dev Loop

## Overview
Set up an efficient local development workflow for building and testing MaintainX integrations.

## Prerequisites
- Completed `maintainx-install-auth` setup
- Node.js 18+ installed
- Docker (optional, for local testing)
- VS Code or preferred IDE

## Instructions
Follow these high-level steps to implement maintainx-local-dev-loop:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-local-dev-loop/references/implementation-guide.md)`

## Output
- Fully configured development environment
- TypeScript project with hot reload
- Mock server for offline testing
- Jest test suite configured
- Interactive REPL for exploration

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [MaintainX API Documentation](https://maintainx.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)

## Next Steps
For SDK patterns and best practices, see `maintainx-sdk-patterns`.
