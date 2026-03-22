---
name: juicebox-multi-env-setup
description: |
  Configure Juicebox multi-environment.
  Trigger: "juicebox environments", "juicebox staging".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Multi-Environment Setup

## Configuration
```typescript
const configs = {
  development: { apiKey: process.env.JB_KEY_DEV, limit: 5 },
  staging: { apiKey: process.env.JB_KEY_STG, limit: 20 },
  production: { apiKey: process.env.JB_KEY_PROD, limit: 50 },
};
const cfg = configs[process.env.NODE_ENV || 'development'];
const client = new JuiceboxClient({ apiKey: cfg.apiKey });
```

## Resources
- [Juicebox Docs](https://docs.juicebox.work)

## Next Steps
See `juicebox-observability`.
