---
name: oraclecloud-data-handling
description: |
  Data Handling for Oracle Cloud.
  Trigger: "oraclecloud data handling".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Data Handling

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
- [Oracle Cloud Privacy](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-enterprise-rbac`.
