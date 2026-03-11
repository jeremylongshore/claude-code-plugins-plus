---
name: customerio-install-auth
description: |
  Install and configure Customer.io SDK/CLI authentication.
  Use when setting up a new Customer.io integration, configuring API keys,
  or initializing Customer.io in your project.
  Trigger with phrases like "install customer.io", "setup customer.io",
  "customer.io auth", "configure customer.io API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Customer.io Install & Auth

## Overview
Set up Customer.io SDK and configure authentication credentials for email, push, SMS, and in-app messaging automation.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Customer.io account with API access
- Site ID and API Key from Customer.io dashboard

## Instructions

### Step 1: Install SDK
### Step 2: Configure Authentication
### Step 3: Verify Connection

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Installed SDK package in node_modules or site-packages
- Environment variables or .env file with Site ID and API Key
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Verify key in Customer.io Settings > API Credentials |
| Invalid Site ID | Wrong site identifier | Check Site ID in Customer.io Settings |
| 401 Unauthorized | Authentication failed | Ensure both Site ID and API Key are correct |
| Network Error | Firewall blocking | Ensure outbound HTTPS to track.customer.io allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
### Python Setup
## Resources
- [Customer.io Documentation](https://customer.io/docs/)
- [Track API Reference](https://customer.io/docs/api/track/)
- [Customer.io Status](https://status.customer.io/)

## Next Steps
After successful auth, proceed to `customerio-hello-world` for your first API call.
