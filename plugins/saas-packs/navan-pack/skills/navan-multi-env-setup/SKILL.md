---
name: navan-multi-env-setup
description: |
  Multi Env Setup for Navan.
  Trigger: "navan multi env setup".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan Multi-Environment Setup

## Configuration
```typescript
const configs = {
  development: { apiKey: process.env.NAVAN_API_KEY_DEV },
  staging: { apiKey: process.env.NAVAN_API_KEY_STG },
  production: { apiKey: process.env.NAVAN_API_KEY_PROD },
};
```

## Resources
- [Navan Docs](https://app.navan.com/app/helpcenter)

## Next Steps
See `navan-observability`.
