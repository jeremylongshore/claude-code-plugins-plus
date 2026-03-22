---
name: veeva-sdk-patterns
description: |
  Veeva Vault sdk patterns for REST API and clinical operations.
  Use when working with Veeva Vault document management and CRM.
  Trigger: "veeva sdk patterns".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, life-sciences, crm, veeva]
compatible-with: claude-code
---

# Veeva Vault Sdk Patterns

## Overview

Guidance for sdk patterns with Veeva Vault REST API, VQL queries, and VAPIL Java SDK.

## Instructions

### Key Vault API Concepts

- **Authentication**: Session-based (username/password or OAuth 2.0)
- **Base URL**: `https://{vault}.veevavault.com/api/v24.1/`
- **VQL**: SQL-like query language for Vault data
- **VAPIL**: Open-source Java SDK covering all Platform APIs
- **Lifecycle**: Documents flow through states (Draft > In Review > Approved)

### Common VQL Patterns

```sql
-- List documents by type
SELECT id, name__v FROM documents WHERE type__v = 'Trial Document'

-- Find objects
SELECT id, name__v FROM site__v WHERE status__v = 'active__v'

-- Join related objects
SELECT id, name__v, study__vr.name__v FROM study_country__v
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `INVALID_SESSION_ID` | Session expired | Re-authenticate |
| `INSUFFICIENT_ACCESS` | Missing permissions | Check security profile |
| `INVALID_DATA` | Bad VQL or field name | Validate against metadata |
| `OPERATION_NOT_ALLOWED` | Lifecycle state conflict | Check document state |

## Resources

- [Vault API Reference](https://developer.veevavault.com/api/)
- [VQL Reference](https://developer.veevavault.com/vql/)
- [VAPIL SDK](https://developer.veevavault.com/sdk/)
- [Developer Portal](https://developer.veevavault.com/)

## Next Steps

See related Veeva Vault skills for more patterns.
