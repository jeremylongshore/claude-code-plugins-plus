---
name: linktree-upgrade-migration
description: |
  Upgrade Migration for Linktree.
  Trigger: "linktree upgrade migration".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree Upgrade & Migration

## Check Version
```bash
npm list | grep linktree
pip show linktree 2>/dev/null
```

## Upgrade
```bash
git checkout -b upgrade/linktree
npm update  # or pip install --upgrade
npm test
```

## Rollback
```bash
git checkout main -- package.json
npm install
```

## Resources
- [Linktree Changelog](https://linktr.ee/marketplace/developer)

## Next Steps
See `linktree-ci-integration`.
