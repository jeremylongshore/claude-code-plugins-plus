---
name: navan-upgrade-migration
description: |
  Upgrade Migration for Navan.
  Trigger: "navan upgrade migration".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan Upgrade & Migration

## Check Version
```bash
npm list | grep navan
pip show navan 2>/dev/null
```

## Upgrade
```bash
git checkout -b upgrade/navan
npm update  # or pip install --upgrade
npm test
```

## Rollback
```bash
git checkout main -- package.json
npm install
```

## Resources
- [Navan Changelog](https://app.navan.com/app/helpcenter)

## Next Steps
See `navan-ci-integration`.
