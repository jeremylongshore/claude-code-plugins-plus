---
name: oraclecloud-multi-env-setup
description: |
  Multi Env Setup for Oracle Cloud.
  Trigger: "oraclecloud multi env setup".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Multi-Environment Setup

## Configuration
```typescript
const configs = {
  development: { apiKey: process.env.OCI_CONFIG_FILE_DEV },
  staging: { apiKey: process.env.OCI_CONFIG_FILE_STG },
  production: { apiKey: process.env.OCI_CONFIG_FILE_PROD },
};
```

## Resources
- [Oracle Cloud Docs](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-observability`.
