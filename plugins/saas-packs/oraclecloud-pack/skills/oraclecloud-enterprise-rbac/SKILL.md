---
name: oraclecloud-enterprise-rbac
description: |
  Enterprise Rbac for Oracle Cloud.
  Trigger: "oraclecloud enterprise rbac".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Enterprise RBAC

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
- [Oracle Cloud Enterprise](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-migration-deep-dive`.
