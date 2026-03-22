---
name: lucidchart-upgrade-migration
description: |
  Upgrade Migration for Lucidchart.
  Trigger: "lucidchart upgrade migration".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Upgrade & Migration

## Check Version
```bash
npm list | grep lucidchart
pip show lucidchart 2>/dev/null
```

## Upgrade
```bash
git checkout -b upgrade/lucidchart
npm update  # or pip install --upgrade
npm test
```

## Rollback
```bash
git checkout main -- package.json
npm install
```

## Resources
- [Lucidchart Changelog](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-ci-integration`.
