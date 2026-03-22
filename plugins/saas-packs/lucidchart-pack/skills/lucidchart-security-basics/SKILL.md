---
name: lucidchart-security-basics
description: |
  Security Basics for Lucidchart.
  Trigger: "lucidchart security basics".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Security Basics

## API Key Security
```bash
# .env (never commit)
LUCID_API_KEY=your-key
# .gitignore: .env
```

## Checklist
- [ ] Keys in environment variables
- [ ] Separate keys per environment
- [ ] Key rotation schedule
- [ ] Audit logging enabled

## Resources
- [Lucidchart Security](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-prod-checklist`.
