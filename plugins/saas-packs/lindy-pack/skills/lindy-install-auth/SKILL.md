---
name: lindy-install-auth
description: |
  Install and configure Lindy AI SDK/CLI authentication.
  Use when setting up a new Lindy integration, configuring API keys,
  or initializing Lindy in your project.
  Trigger with phrases like "install lindy", "setup lindy",
  "lindy auth", "configure lindy API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lindy Install & Auth

## Overview
Set up Lindy AI SDK and configure authentication credentials for AI agent automation.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Lindy account with API access
- API key from Lindy dashboard (https://app.lindy.ai)

## Instructions

### Step 1: Install SDK

### Step 2: Configure Authentication

### Step 3: Verify Connection


For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Installed SDK package in node_modules or site-packages
- Environment variable or .env file with API key
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Verify key in Lindy dashboard |
| Rate Limited | Exceeded quota | Check quota at https://app.lindy.ai |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup

### Python Setup

## Resources
- [Lindy Documentation](https://docs.lindy.ai)
- [Lindy Dashboard](https://app.lindy.ai)
- [Lindy API Reference](https://docs.lindy.ai/api)

## Next Steps
After successful auth, proceed to `lindy-hello-world` for your first AI agent.
