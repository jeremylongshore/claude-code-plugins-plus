---
name: navan-data-handling
description: |
  Data Handling for Navan.
  Trigger: "navan data handling".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan Data Handling

## Data Classification
| Type | Handling |
|------|----------|
| API responses | Cache with TTL |
| User data | Encrypt at rest |
| Credentials | Secret manager |

## Compliance Checklist
- [ ] Data encrypted at rest and in transit
- [ ] Retention policies documented
- [ ] Audit trail for data access
- [ ] Data subject access requests supported

## Resources
- [Navan Privacy](https://app.navan.com/app/helpcenter)

## Next Steps
See `navan-enterprise-rbac`.
