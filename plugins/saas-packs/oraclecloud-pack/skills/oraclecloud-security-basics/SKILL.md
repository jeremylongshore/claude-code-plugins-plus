---
name: oraclecloud-security-basics
description: |
  Security Basics for Oracle Cloud.
  Trigger: "oraclecloud security basics".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Security Basics

## API Key Security
```bash
# .env (never commit)
OCI_CONFIG_FILE=your-key
# .gitignore: .env
```

## Checklist
- [ ] Keys in environment variables
- [ ] Separate keys per environment
- [ ] Key rotation schedule
- [ ] Audit logging enabled

## Resources
- [Oracle Cloud Security](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-prod-checklist`.
