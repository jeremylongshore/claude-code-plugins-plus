---
name: navan-enterprise-rbac
description: |
  Enterprise Rbac for Navan.
  Trigger: "navan enterprise rbac".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan Enterprise RBAC

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
- [Navan Enterprise](https://app.navan.com/app/helpcenter)

## Next Steps
See `navan-migration-deep-dive`.
