---
name: navan-security-basics
description: |
  Security Basics for Navan.
  Trigger: "navan security basics".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan Security Basics

## API Key Security
```bash
# .env (never commit)
NAVAN_API_KEY=your-key
# .gitignore: .env
```

## Checklist
- [ ] Keys in environment variables
- [ ] Separate keys per environment
- [ ] Key rotation schedule
- [ ] Audit logging enabled

## Resources
- [Navan Security](https://app.navan.com/app/helpcenter)

## Next Steps
See `navan-prod-checklist`.
