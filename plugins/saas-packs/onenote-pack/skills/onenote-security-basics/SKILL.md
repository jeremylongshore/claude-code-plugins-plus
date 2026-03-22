---
name: onenote-security-basics
description: |
  Security Basics for OneNote.
  Trigger: "onenote security basics".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, onenote, microsoft]
compatible-with: claude-code
---

# OneNote Security Basics

## API Key Security
```bash
# .env (never commit)
MICROSOFT_GRAPH_TOKEN=your-key
# .gitignore: .env
```

## Checklist
- [ ] Keys in environment variables
- [ ] Separate keys per environment
- [ ] Key rotation schedule
- [ ] Audit logging enabled

## Resources
- [OneNote Security](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)

## Next Steps
See `onenote-prod-checklist`.
