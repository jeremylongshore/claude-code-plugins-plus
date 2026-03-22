---
name: mindtickle-upgrade-migration
description: |
  Upgrade Migration for MindTickle.
  Trigger: "mindtickle upgrade migration".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle Upgrade & Migration

## Check Version
```bash
npm list | grep mindtickle
pip show mindtickle 2>/dev/null
```

## Upgrade
```bash
git checkout -b upgrade/mindtickle
npm update  # or pip install --upgrade
npm test
```

## Rollback
```bash
git checkout main -- package.json
npm install
```

## Resources
- [MindTickle Changelog](https://www.mindtickle.com/platform/integrations/)

## Next Steps
See `mindtickle-ci-integration`.
