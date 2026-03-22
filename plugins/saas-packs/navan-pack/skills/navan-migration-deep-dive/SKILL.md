---
name: navan-migration-deep-dive
description: |
  Migration Deep Dive for Navan.
  Trigger: "navan migration deep dive".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan Migration Deep Dive

## Migration Strategies
1. **Parallel run**: Run old and new systems simultaneously
2. **Strangler fig**: Gradually route traffic to Navan
3. **Big bang**: Switch all at once (risky)

## Migration Checklist
- [ ] API mapping documented
- [ ] Data migration plan
- [ ] Rollback procedure
- [ ] Performance baseline
- [ ] Team training complete

## Resources
- [Navan Migration Guide](https://app.navan.com/app/helpcenter)

## Next Steps
Start with `navan-install-auth`.
