---
name: lindy-hello-world
description: |
  Create a minimal working Lindy AI agent example.
  Use when starting a new Lindy integration, testing your setup,
  or learning basic Lindy API patterns.
  Trigger with phrases like "lindy hello world", "lindy example",
  "lindy quick start", "simple lindy agent".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lindy Hello World

## Overview
Minimal working example demonstrating core Lindy AI agent functionality.

## Prerequisites
- Completed `lindy-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
### Step 3: Create Your First Agent

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Working code file with Lindy client initialization
- Created AI agent in your Lindy workspace
- Console output showing:
## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Import Error | SDK not installed | Verify with `npm list @lindy-ai/sdk` |
| Auth Error | Invalid credentials | Check environment variable is set |
| Timeout | Network issues | Increase timeout or check connectivity |
| Rate Limit | Too many requests | Wait and retry with exponential backoff |

## Examples

### TypeScript Example
### Python Example
## Resources
- [Lindy Getting Started](https://docs.lindy.ai/getting-started)
- [Lindy API Reference](https://docs.lindy.ai/api)
- [Lindy Examples](https://docs.lindy.ai/examples)

## Next Steps
Proceed to `lindy-local-dev-loop` for development workflow setup.
