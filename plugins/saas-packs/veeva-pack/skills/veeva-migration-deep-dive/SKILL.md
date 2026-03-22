---
name: veeva-migration-deep-dive
description: |
  Veeva Vault migration deep dive for enterprise operations.
  Use when implementing advanced Veeva Vault patterns.
  Trigger: "veeva migration deep dive".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, life-sciences, crm, veeva]
compatible-with: claude-code
---

# Veeva Vault Migration Deep Dive

## Overview

Enterprise-grade migration deep dive patterns for Veeva Vault deployments.

## Instructions

### Key Considerations

- Veeva Vault is purpose-built for regulated life sciences
- All API changes should be validated against compliance requirements
- Use VQL for efficient data retrieval
- VAPIL provides Java-native API coverage

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Access denied | Security profile | Update profile permissions |
| Data validation | Required fields | Check object metadata |

## Resources

- [Vault API Reference](https://developer.veevavault.com/api/)
- [Vault Documentation](https://developer.veevavault.com/docs/)

## Next Steps

See related Veeva Vault skills.
