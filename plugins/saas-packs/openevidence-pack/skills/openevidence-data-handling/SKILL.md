---
name: openevidence-data-handling
description: |
  Data Handling for OpenEvidence.
  Trigger: "openevidence data handling".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Data Handling

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
- [OpenEvidence Privacy](https://www.openevidence.com)

## Next Steps
See `openevidence-enterprise-rbac`.
