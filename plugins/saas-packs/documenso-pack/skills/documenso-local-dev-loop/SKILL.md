---
name: documenso-local-dev-loop
description: |
  Set up local development environment and testing workflow for Documenso.
  Use when configuring dev environment, setting up test workflows,
  or establishing rapid iteration patterns with Documenso.
  Trigger with phrases like "documenso local dev", "documenso development",
  "test documenso locally", "documenso dev environment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(docker:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Documenso Local Dev Loop

## Overview
Configure a productive local development environment for Documenso integrations with fast iteration cycles.

## Prerequisites
- Completed `documenso-install-auth` setup
- Node.js 18+ or Python 3.10+
- Docker (optional, for self-hosted testing)
- Code editor with TypeScript support

## Instructions

### Step 1: Project Structure

### Step 2: Environment Configuration

**.env.development:**
**.env.test:**
### Step 3: Client Wrapper with Dev Helpers

### Step 4: Development Scripts

**package.json:**
### Step 5: Quick Verification Script

### Step 6: Test Cleanup Script

### Step 7: Integration Test Example

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Self-Hosted Local Development

For testing against a local Documenso instance:

**.env.local (for self-hosted):**
## Output
- Configured development environment
- Verification script passing
- Integration tests running against staging
- Cleanup script for test documents

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Connection refused | Wrong base URL | Check DOCUMENSO_BASE_URL |
| 401 on staging | Wrong API key | Get staging-specific key |
| Tests failing | Stale test data | Run cleanup script |
| Rate limited | Too many requests | Add delays between tests |

## Resources
- [Documenso Staging Environment](https://stg-app.documenso.com)
- [Self-Hosting Guide](https://docs.documenso.com/developers/self-hosting)
- [Developer Quickstart](https://docs.documenso.com/developers/local-development/quickstart)

## Next Steps
Apply patterns in `documenso-sdk-patterns` for production-ready code.

## Examples

**Basic usage**: Apply documenso local dev loop to a standard project setup with default configuration options.

**Advanced scenario**: Customize documenso local dev loop for production environments with multiple constraints and team-specific requirements.