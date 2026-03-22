---
name: juicebox-security-basics
description: |
  Apply Juicebox security best practices.
  Trigger: "juicebox security", "juicebox api key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Security Basics

## API Key Security
```bash
# .env (never commit)
JUICEBOX_API_KEY=jb_live_...
# .gitignore: .env
```

## Data Privacy
- Juicebox sources from public professional profiles
- Contact data requires explicit enrichment request
- Comply with GDPR/CCPA for candidate data storage
- Implement data retention policies

## Security Checklist
- [ ] API keys in environment variables
- [ ] Separate keys per environment
- [ ] Candidate data encrypted at rest
- [ ] GDPR consent for EU candidates
- [ ] Data retention policy documented

## Resources
- [Juicebox Privacy](https://juicebox.ai/privacy)
- [Data Sources](https://docs.juicebox.work/data-sources)

## Next Steps
See `juicebox-prod-checklist`.
