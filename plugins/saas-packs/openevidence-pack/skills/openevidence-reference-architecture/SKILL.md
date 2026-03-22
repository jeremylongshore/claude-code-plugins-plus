---
name: openevidence-reference-architecture
description: |
  Reference Architecture for OpenEvidence.
  Trigger: "openevidence reference architecture".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Reference Architecture

## Architecture
```
Client → API Gateway → OpenEvidence Service → OpenEvidence API
                                ↓
                         Data Store → Analytics
```

## Components
```typescript
class OpenEvidenceService {
  private client: any;
  constructor() { this.client = getClient(); }
  // Core business logic wrapping OpenEvidence API
}
```

## Resources
- [OpenEvidence Docs](https://www.openevidence.com)

## Next Steps
See `openevidence-multi-env-setup`.
