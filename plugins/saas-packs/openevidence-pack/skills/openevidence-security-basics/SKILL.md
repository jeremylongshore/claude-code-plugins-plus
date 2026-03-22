---
name: openevidence-security-basics
description: |
  Security Basics for OpenEvidence.
  Trigger: "openevidence security basics".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Security Basics

## API Key Security
```bash
# .env (never commit)
OPENEVIDENCE_API_KEY=your-key
# .gitignore: .env
```

## Checklist
- [ ] Keys in environment variables
- [ ] Separate keys per environment
- [ ] Key rotation schedule
- [ ] Audit logging enabled

## Resources
- [OpenEvidence Security](https://www.openevidence.com)

## Next Steps
See `openevidence-prod-checklist`.
