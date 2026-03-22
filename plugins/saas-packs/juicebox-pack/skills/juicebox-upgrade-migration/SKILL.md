---
name: juicebox-upgrade-migration
description: |
  Plan Juicebox SDK upgrades.
  Trigger: "upgrade juicebox", "juicebox migration".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Upgrade & Migration

## Check Version
```bash
npm list @juicebox/sdk
npm view @juicebox/sdk version
```

## Upgrade
```bash
git checkout -b upgrade/juicebox-sdk
npm install @juicebox/sdk@latest
npm test
```

## Rollback
```bash
npm install @juicebox/sdk@previous-version --save-exact
```

## Resources
- [Changelog](https://docs.juicebox.work/changelog)

## Next Steps
See `juicebox-ci-integration`.
