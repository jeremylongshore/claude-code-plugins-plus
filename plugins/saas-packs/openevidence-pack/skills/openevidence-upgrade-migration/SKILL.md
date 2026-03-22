---
name: openevidence-upgrade-migration
description: |
  Upgrade Migration for OpenEvidence.
  Trigger: "openevidence upgrade migration".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Upgrade & Migration

## Check Version
```bash
npm list | grep openevidence
pip show openevidence 2>/dev/null
```

## Upgrade
```bash
git checkout -b upgrade/openevidence
npm update  # or pip install --upgrade
npm test
```

## Rollback
```bash
git checkout main -- package.json
npm install
```

## Resources
- [OpenEvidence Changelog](https://www.openevidence.com)

## Next Steps
See `openevidence-ci-integration`.
