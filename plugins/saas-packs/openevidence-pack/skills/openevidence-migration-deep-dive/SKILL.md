---
name: openevidence-migration-deep-dive
description: |
  Migration Deep Dive for OpenEvidence.
  Trigger: "openevidence migration deep dive".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Migration Deep Dive

## Migration Strategies
1. **Parallel run**: Run old and new systems simultaneously
2. **Strangler fig**: Gradually route traffic to OpenEvidence
3. **Big bang**: Switch all at once (risky)

## Migration Checklist
- [ ] API mapping documented
- [ ] Data migration plan
- [ ] Rollback procedure
- [ ] Performance baseline
- [ ] Team training complete

## Resources
- [OpenEvidence Migration Guide](https://www.openevidence.com)

## Next Steps
Start with `openevidence-install-auth`.
