---
name: juicebox-enterprise-rbac
description: |
  Configure Juicebox team access.
  Trigger: "juicebox rbac", "juicebox team roles".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Enterprise RBAC

## Roles
| Role | Search | Enrich | Contact | Outreach |
|------|--------|--------|---------|----------|
| Recruiter | Yes | Yes | Yes | Yes |
| Sourcer | Yes | Yes | No | No |
| Manager | Yes | Yes | Yes | Yes |
| Viewer | Read | No | No | No |

## Implementation
```typescript
const PERMS = {
  recruiter: { search: true, enrich: true, contact: true, outreach: true },
  sourcer: { search: true, enrich: true, contact: false, outreach: false },
  viewer: { search: true, enrich: false, contact: false, outreach: false },
};
function check(role: string, action: string) { return PERMS[role]?.[action] ?? false; }
```

## Resources
- [Enterprise](https://juicebox.ai/enterprise)

## Next Steps
See `juicebox-migration-deep-dive`.
