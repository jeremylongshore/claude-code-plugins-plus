---
name: linktree-reference-architecture
description: |
  Reference Architecture for Linktree.
  Trigger: "linktree reference architecture".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree Reference Architecture

## Architecture
```
Client → API Gateway → Linktree Service → Linktree API
                                ↓
                         Data Store → Analytics
```

## Components
```typescript
class LinktreeService {
  private client: any;
  constructor() { this.client = getClient(); }
  // Core business logic wrapping Linktree API
}
```

## Resources
- [Linktree Docs](https://linktr.ee/marketplace/developer)

## Next Steps
See `linktree-multi-env-setup`.
