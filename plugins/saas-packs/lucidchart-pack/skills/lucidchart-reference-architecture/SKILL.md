---
name: lucidchart-reference-architecture
description: |
  Reference Architecture for Lucidchart.
  Trigger: "lucidchart reference architecture".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Reference Architecture

## Architecture
```
Client → API Gateway → Lucidchart Service → Lucidchart API
                                ↓
                         Data Store → Analytics
```

## Components
```typescript
class LucidchartService {
  private client: any;
  constructor() { this.client = getClient(); }
  // Core business logic wrapping Lucidchart API
}
```

## Resources
- [Lucidchart Docs](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-multi-env-setup`.
