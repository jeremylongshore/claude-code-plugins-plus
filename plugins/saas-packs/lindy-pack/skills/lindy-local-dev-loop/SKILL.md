---
name: lindy-local-dev-loop
description: |
  Set up local development workflow for Lindy AI agents.
  Use when configuring local testing, hot reload, or development environment.
  Trigger with phrases like "lindy local dev", "lindy development",
  "lindy hot reload", "test lindy locally".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy Local Dev Loop

## Overview
Configure efficient local development workflow for Lindy AI agent development.

## Prerequisites
- Completed `lindy-install-auth` setup
- Node.js 18+ with npm/pnpm
- Code editor with TypeScript support

## Instructions

### Step 1: Set Up Project Structure
### Step 2: Configure TypeScript
### Step 3: Create Development Script
### Step 4: Create Agent Test Harness

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Configured development environment
- Hot reload enabled for agent code
- Test harness for rapid iteration
- TypeScript support with type checking

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| ts-node not found | Dev deps missing | `npm install -D ts-node` |
| ENV not loaded | dotenv not configured | Add `import 'dotenv/config'` |
| Type errors | Missing types | `npm install -D @types/node` |

## Examples

### Watch Mode Development
### Environment Setup
## Resources
- [Lindy SDK Reference](https://docs.lindy.ai/sdk)
- [TypeScript Best Practices](https://docs.lindy.ai/typescript)

## Next Steps
Proceed to `lindy-sdk-patterns` for SDK best practices.