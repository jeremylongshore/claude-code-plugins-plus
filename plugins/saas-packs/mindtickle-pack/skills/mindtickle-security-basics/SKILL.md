---
name: mindtickle-security-basics
description: |
  Security Basics for MindTickle.
  Trigger: "mindtickle security basics".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle Security Basics

## API Key Security
```bash
# .env (never commit)
MINDTICKLE_API_KEY=your-key
# .gitignore: .env
```

## Checklist
- [ ] Keys in environment variables
- [ ] Separate keys per environment
- [ ] Key rotation schedule
- [ ] Audit logging enabled

## Resources
- [MindTickle Security](https://www.mindtickle.com/platform/integrations/)

## Next Steps
See `mindtickle-prod-checklist`.
