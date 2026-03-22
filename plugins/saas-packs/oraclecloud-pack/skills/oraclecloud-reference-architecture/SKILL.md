---
name: oraclecloud-reference-architecture
description: |
  Reference Architecture for Oracle Cloud.
  Trigger: "oraclecloud reference architecture".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Reference Architecture

## Architecture
```
Client → API Gateway → Oracle Cloud Service → Oracle Cloud API
                                ↓
                         Data Store → Analytics
```

## Components
```typescript
class OracleCloudService {
  private client: any;
  constructor() { this.client = getClient(); }
  // Core business logic wrapping Oracle Cloud API
}
```

## Resources
- [Oracle Cloud Docs](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-multi-env-setup`.
