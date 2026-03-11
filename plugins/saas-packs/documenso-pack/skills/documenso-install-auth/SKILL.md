---
name: documenso-install-auth
description: |
  Install and configure Documenso SDK/API authentication.
  Use when setting up a new Documenso integration, configuring API keys,
  or initializing Documenso in your project.
  Trigger with phrases like "install documenso", "setup documenso",
  "documenso auth", "configure documenso API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Documenso Install & Auth

## Overview
Set up Documenso SDK and configure API authentication for document signing integration.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, yarn, pip, or uv)
- Documenso account (cloud or self-hosted)
- API key from Documenso dashboard

## Instructions

### Step 1: Install SDK

**TypeScript/Node.js:**
**Python:**
### Step 2: Get API Key

1. Log into Documenso dashboard at https://app.documenso.com
2. Click your avatar in the top right corner
3. Select "User settings" (or "Team settings" for team APIs)
4. Navigate to "API tokens" tab
5. Click "Create API Key"
6. Copy the generated key (shown only once)

### Step 3: Configure Authentication

### Step 4: Verify Connection

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

**TypeScript:**
**Python:**
## Output
- Installed SDK package in node_modules or site-packages
- Environment variable or .env file with API key
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Generate new key in dashboard |
| 401 Unauthorized | Missing or malformed key | Check API key format and env var |
| 403 Forbidden | Key lacks required permissions | Use team API key for team resources |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |
| Network Error | Firewall blocking | Ensure outbound HTTPS to api.documenso.com |

## API Endpoints

| Environment | Base URL |
|-------------|----------|
| Production | `https://app.documenso.com/api/v2/` |
| Staging | `https://stg-app.documenso.com/api/v2/` |
| Self-hosted | `https://your-instance.com/api/v2/` |

## Custom Base URL (Self-Hosted)

## Resources
- [Documenso API Documentation](https://docs.documenso.com/developers/public-api)
- [TypeScript SDK](https://github.com/documenso/sdk-typescript)
- [Python SDK](https://github.com/documenso/sdk-python)
- [API Reference](https://openapi.documenso.com/)

## Next Steps
After successful auth, proceed to `documenso-hello-world` for your first document.
