---
name: openevidence-enterprise-rbac
description: |
  Enterprise Rbac for OpenEvidence.
  Trigger: "openevidence enterprise rbac".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Enterprise RBAC

## Role Matrix
| Role | Read | Write | Admin |
|------|------|-------|-------|
| Viewer | Yes | No | No |
| Editor | Yes | Yes | No |
| Admin | Yes | Yes | Yes |

## Implementation
```typescript
const PERMS = {
  viewer: { read: true, write: false, admin: false },
  editor: { read: true, write: true, admin: false },
  admin: { read: true, write: true, admin: true },
};
```

## Resources
- [OpenEvidence Enterprise](https://www.openevidence.com)

## Next Steps
See `openevidence-migration-deep-dive`.
