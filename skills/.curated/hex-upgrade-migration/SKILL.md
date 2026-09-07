---
name: hex-upgrade-migration
description: 'Analyze, plan, and execute Hex SDK upgrades with breaking change detection.

  Use when upgrading Hex SDK versions, detecting deprecations,

  or migrating to new API versions.

  Trigger with phrases like "upgrade hex", "hex migration",

  "hex breaking changes", "update hex SDK", "analyze hex version".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- hex
- data
- analytics
compatibility: Designed for Claude Code
---
# Hex Upgrade & Migration

## Overview

Hex API is versioned at `/api/v1/`. Monitor the Hex changelog for new endpoints and deprecations.

## Instructions

### Check API Usage

```bash
grep -r "app.hex.tech" src/ --include="*.ts" --include="*.py"
```

### Airflow Provider Updates

```bash
pip install --upgrade airflow-provider-hex
```

## Prerequisites

- Pinned current and target versions, a compatibility assessment, sandbox project fixtures, and an owner for each changed contract.
- Versioned configuration backups plus approved downgrade, cancellation, and integration-disable procedures.

## Output

Produce an upgrade receipt with from/to versions, affected contracts, fixture/canary outcomes, aggregate assertions, owner approval, compatibility decision, and rollback revision. Exclude SQL, workspace output, and credentials.

## Error Handling

Stop for incompatible parameter/output contracts, authorization drift, unbounded replays, or a failed canary assertion. Restore the exact pinned prior revision and retain redacted evidence rather than forcing migration.

## Examples

`from=client-r12; to=client-r13; sandbox=pass; staging=pass; assertions=pass; canary=held; rollback=r12` is a defensible upgrade record.

## Resources

- [Hex Changelog](https://learn.hex.tech/changelog)
- [API Reference](https://learn.hex.tech/docs/api/api-reference)
