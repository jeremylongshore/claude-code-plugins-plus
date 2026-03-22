---
name: framer-upgrade-migration
description: |
  Analyze, plan, and execute Framer SDK upgrades with breaking change detection.
  Use when upgrading Framer SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade framer", "framer migration",
  "framer breaking changes", "update framer SDK", "analyze framer version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer Upgrade & Migration

## Overview

Guide for upgrading Framer plugin SDK, Server API, and migrating between Framer platform versions. Check the Framer Developer Changelog for breaking changes before upgrading.

## Instructions

### Step 1: Check Current Versions

```bash
npm list framer-plugin framer-api framer
npm view framer-plugin version
npm view framer-api version
```

### Step 2: Review Changelog

Visit https://www.framer.com/developers/changelog for breaking changes.

Key migrations:
- **Plugin API 3.x**: Introduced Managed Collections, Code File APIs
- **Server API beta**: WebSocket-based programmatic access
- **Code Components v2**: Updated property control types

### Step 3: Upgrade Plugin SDK

```bash
git checkout -b upgrade/framer-plugin
npm install framer-plugin@latest
npm run build  # Check for type errors
npm test       # Run tests
```

### Step 4: Common Migration Patterns

```typescript
// Plugin API 2.x → 3.x: Collection APIs changed
// BEFORE: framer.createCollection(...)
// AFTER: framer.createManagedCollection(...)

// Code components: ControlType changes
// BEFORE: ControlType.FusedNumber
// AFTER: ControlType.Number (with min/max/step)

// Overrides: import path
// BEFORE: import { Override } from 'framer'
// AFTER: import { Override } from 'framer' (unchanged, but check type shape)
```

### Step 5: Rollback

```bash
# Pin to previous version
npm install framer-plugin@3.x.x --save-exact
```

## Resources

- [Framer Changelog](https://www.framer.com/developers/changelog)
- [Framer Upgrading Guide](https://www.framer.com/developers/upgrading)

## Next Steps

For CI integration, see `framer-ci-integration`.
