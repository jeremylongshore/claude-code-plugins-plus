---
name: framer-security-basics
description: |
  Apply Framer security best practices for secrets and access control.
  Use when securing API keys, implementing least privilege access,
  or auditing Framer security configuration.
  Trigger with phrases like "framer security", "framer secrets",
  "secure framer", "framer API key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer Security Basics

## Overview

Security best practices for Framer API keys, plugin development, and Server API access.

## Instructions

### Step 1: Credential Management

| Credential | Scope | Where to Store |
|-----------|-------|----------------|
| Server API Key (`framer_sk_*`) | Per-site | Secrets vault |
| Site ID | Per-site | Can be in config |
| Plugin auth tokens | Per-user session | Never persist |

```bash
# .env (never commit)
FRAMER_API_KEY=framer_sk_abc123...
FRAMER_SITE_ID=abc123

# .gitignore
.env
.env.local
```

### Step 2: Plugin Security

```tsx
// Plugins run in Framer's iframe sandbox — limited browser APIs
// Never store secrets in plugin code (it's client-side)

// Fetch external data through your own API proxy
const data = await fetch('https://your-api.com/framer-data', {
  headers: { 'Authorization': `Bearer ${sessionToken}` },
});
```

### Step 3: Server API Key Rotation

```bash
# 1. Generate new key in Framer site settings
# 2. Update in secrets vault
# 3. Test connection
node -e "
  const { framer } = require('framer-api');
  framer.connect({ apiKey: process.env.FRAMER_API_KEY, siteId: process.env.FRAMER_SITE_ID })
    .then(() => console.log('OK'))
    .catch(e => console.error('FAIL', e.message));
"
# 4. Revoke old key in site settings
```

### Step 4: Security Checklist

- [ ] API keys in environment variables, never in code
- [ ] `.env` in `.gitignore`
- [ ] Plugin never stores or exposes API keys
- [ ] Server API accessed only from backend, never client
- [ ] Pre-commit hook scans for `framer_sk_*` leaks
- [ ] HTTPS-only for all API communication

## Resources

- [Framer Server API](https://www.framer.com/developers/server-api-introduction)
- [Plugin Security](https://www.framer.com/developers/plugins-introduction)

## Next Steps

For production deployment, see `framer-prod-checklist`.
