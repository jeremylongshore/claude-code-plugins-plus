---
name: hex-upgrade-migration
description: |
  Analyze, plan, and execute Hex SDK upgrades with breaking change detection.
  Use when upgrading Hex SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade hex", "hex migration",
  "hex breaking changes", "update hex SDK", "analyze hex version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
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

## Resources

- [Hex Changelog](https://learn.hex.tech/changelog)
- [API Reference](https://learn.hex.tech/docs/api/api-reference)
