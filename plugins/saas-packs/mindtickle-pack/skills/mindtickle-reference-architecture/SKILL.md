---
name: mindtickle-reference-architecture
description: |
  Reference Architecture for MindTickle.
  Trigger: "mindtickle reference architecture".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle Reference Architecture

## Architecture
```
Client → API Gateway → MindTickle Service → MindTickle API
                                ↓
                         Data Store → Analytics
```

## Components
```typescript
class MindTickleService {
  private client: any;
  constructor() { this.client = getClient(); }
  // Core business logic wrapping MindTickle API
}
```

## Resources
- [MindTickle Docs](https://www.mindtickle.com/platform/integrations/)

## Next Steps
See `mindtickle-multi-env-setup`.
