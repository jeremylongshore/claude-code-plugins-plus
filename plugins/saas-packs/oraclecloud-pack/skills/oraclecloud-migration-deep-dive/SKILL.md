---
name: oraclecloud-migration-deep-dive
description: |
  Migration Deep Dive for Oracle Cloud.
  Trigger: "oraclecloud migration deep dive".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Migration Deep Dive

## Migration Strategies
1. **Parallel run**: Run old and new systems simultaneously
2. **Strangler fig**: Gradually route traffic to Oracle Cloud
3. **Big bang**: Switch all at once (risky)

## Migration Checklist
- [ ] API mapping documented
- [ ] Data migration plan
- [ ] Rollback procedure
- [ ] Performance baseline
- [ ] Team training complete

## Resources
- [Oracle Cloud Migration Guide](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
Start with `oraclecloud-install-auth`.
