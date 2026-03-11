---
name: apollo-data-handling
description: |
  Apollo.io data management and compliance.
  Use when handling contact data, implementing GDPR compliance,
  or managing data exports and retention.
  Trigger with phrases like "apollo data", "apollo gdpr", "apollo compliance",
  "apollo data export", "apollo data retention", "apollo pii".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Apollo Data Handling

## Overview
Data management, compliance, and governance practices for Apollo.io contact data including GDPR, data retention, and secure handling.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-data-handling:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-data-handling/references/implementation-guide.md)`

## Output
- GDPR compliance (access, erasure, consent)
- Data retention policies
- Secure data export
- Column-level encryption
- Comprehensive audit logging

## Error Handling
| Issue | Resolution |
|-------|------------|
| Export too large | Implement streaming |
| Encryption key lost | Use key management service |
| Audit log gaps | Implement retry queue |
| Consent conflicts | Use latest consent record |

## Resources
- [GDPR Official Text](https://gdpr.eu/)
- [CCPA Requirements](https://oag.ca.gov/privacy/ccpa)
- [Apollo Privacy Policy](https://www.apollo.io/privacy-policy)

## Next Steps
Proceed to `apollo-enterprise-rbac` for access control.
