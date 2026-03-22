---
name: linktree-security-basics
description: |
  Security Basics for Linktree.
  Trigger: "linktree security basics".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree Security Basics

## API Key Security
```bash
# .env (never commit)
LINKTREE_API_KEY=your-key
# .gitignore: .env
```

## Checklist
- [ ] Keys in environment variables
- [ ] Separate keys per environment
- [ ] Key rotation schedule
- [ ] Audit logging enabled

## Resources
- [Linktree Security](https://linktr.ee/marketplace/developer)

## Next Steps
See `linktree-prod-checklist`.
