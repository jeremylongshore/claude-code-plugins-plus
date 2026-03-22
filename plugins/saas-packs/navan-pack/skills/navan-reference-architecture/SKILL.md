---
name: navan-reference-architecture
description: |
  Reference Architecture for Navan.
  Trigger: "navan reference architecture".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan Reference Architecture

## Architecture
```
Client → API Gateway → Navan Service → Navan API
                                ↓
                         Data Store → Analytics
```

## Components
```typescript
class NavanService {
  private client: any;
  constructor() { this.client = getClient(); }
  // Core business logic wrapping Navan API
}
```

## Resources
- [Navan Docs](https://app.navan.com/app/helpcenter)

## Next Steps
See `navan-multi-env-setup`.
