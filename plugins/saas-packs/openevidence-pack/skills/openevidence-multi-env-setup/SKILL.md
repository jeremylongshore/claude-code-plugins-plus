---
name: openevidence-multi-env-setup
description: |
  Multi Env Setup for OpenEvidence.
  Trigger: "openevidence multi env setup".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Multi-Environment Setup

## Configuration
```typescript
const configs = {
  development: { apiKey: process.env.OPENEVIDENCE_API_KEY_DEV },
  staging: { apiKey: process.env.OPENEVIDENCE_API_KEY_STG },
  production: { apiKey: process.env.OPENEVIDENCE_API_KEY_PROD },
};
```

## Resources
- [OpenEvidence Docs](https://www.openevidence.com)

## Next Steps
See `openevidence-observability`.
