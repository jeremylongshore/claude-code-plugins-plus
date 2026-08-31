---
name: hootsuite-upgrade-migration
description: 'Analyze, plan, and execute Hootsuite SDK upgrades with breaking change
  detection.

  Use when upgrading Hootsuite SDK versions, detecting deprecations,

  or migrating to new API versions.

  Trigger with phrases like "upgrade hootsuite", "hootsuite migration",

  "hootsuite breaking changes", "update hootsuite SDK", "analyze hootsuite version".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- hootsuite
- social-media
compatibility: Designed for Claude Code
---
# Hootsuite Upgrade & Migration

## Overview

Hootsuite REST API is versioned at `/v1/`. Monitor the developer changelog for deprecations and new endpoints.

## Instructions

### Step 1: Check Current API Usage

```bash
# List all Hootsuite API calls in your codebase
grep -r "platform.hootsuite.com" src/ --include="*.ts" --include="*.py"
```

### Step 2: Migration Patterns

```typescript
// If Hootsuite introduces v2 endpoints:
// BEFORE
const response = await fetch('https://platform.hootsuite.com/v1/messages', ...);
// AFTER
const API_VERSION = process.env.HOOTSUITE_API_VERSION || 'v1';
const response = await fetch(`https://platform.hootsuite.com/${API_VERSION}/messages`, ...);
```

### Step 3: Social Network Changes

When Hootsuite adds/removes social network support:

```typescript
const SUPPORTED_NETWORKS = ['TWITTER', 'FACEBOOK', 'INSTAGRAM', 'LINKEDIN', 'PINTEREST', 'YOUTUBE', 'TIKTOK'] as const;
type SocialNetwork = typeof SUPPORTED_NETWORKS[number];
```

## Prerequisites

- Pinned current/target versions, compatibility assessment, draft-only fixtures, and an owner for changed account or scheduling contracts.
- Versioned configuration backups plus approved downgrade, schedule-cancel, and integration-disable procedures.

## Output

Produce an upgrade receipt with from/to versions, affected contracts, fixture/draft-canary outcomes, approval/audience assertions, owner approval, compatibility decision, and rollback revision. Exclude copy, media, account identities, and credentials.

## Error Handling

Stop for incompatible scheduling/approval contracts, account-scope drift, unbounded replay, or a draft-canary that reaches a public path. Restore the pinned prior revision rather than forcing migration.

## Examples

`from=client-r12; to=client-r13; sandbox=pass; staging=pass; draft=pass; public_posts=0; rollback=r12` is a defensible upgrade record.

## Resources

- [Hootsuite Developer Changelog](https://developer.hootsuite.com/changelog)
- [API Guides](https://developer.hootsuite.com/docs/api-guides)

## Next Steps

For CI, see `hootsuite-ci-integration`.
