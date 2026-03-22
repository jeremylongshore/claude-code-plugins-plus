---
name: oraclecloud-upgrade-migration
description: |
  Upgrade Migration for Oracle Cloud.
  Trigger: "oraclecloud upgrade migration".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Upgrade & Migration

## Check Version
```bash
npm list | grep oraclecloud
pip show oraclecloud 2>/dev/null
```

## Upgrade
```bash
git checkout -b upgrade/oraclecloud
npm update  # or pip install --upgrade
npm test
```

## Rollback
```bash
git checkout main -- package.json
npm install
```

## Resources
- [Oracle Cloud Changelog](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-ci-integration`.
