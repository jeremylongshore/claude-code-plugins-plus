---
name: onenote-upgrade-migration
description: |
  Upgrade Migration for OneNote.
  Trigger: "onenote upgrade migration".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, onenote, microsoft]
compatible-with: claude-code
---

# OneNote Upgrade & Migration

## Check Version
```bash
npm list | grep onenote
pip show onenote 2>/dev/null
```

## Upgrade
```bash
git checkout -b upgrade/onenote
npm update  # or pip install --upgrade
npm test
```

## Rollback
```bash
git checkout main -- package.json
npm install
```

## Resources
- [OneNote Changelog](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)

## Next Steps
See `onenote-ci-integration`.
