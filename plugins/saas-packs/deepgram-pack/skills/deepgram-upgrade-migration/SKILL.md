---
name: deepgram-upgrade-migration
description: |
  Plan and execute Deepgram SDK upgrades and migrations.
  Use when upgrading SDK versions, migrating to new API versions,
  or transitioning between Deepgram models.
  Trigger with phrases like "upgrade deepgram", "deepgram migration",
  "update deepgram SDK", "deepgram version upgrade", "migrate deepgram".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Deepgram Upgrade Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Guide for planning and executing Deepgram SDK upgrades (v2 to v3), model migrations (Nova to Nova-2), and API version transitions with A/B testing, validation, and rollback procedures.

## Prerequisites
- Current SDK version documented
- Test environment available
- Rollback plan prepared
- Changelog reviewed

## Instructions

### Assess current configuration
Document current SDK version (`npm list @deepgram/sdk`), model in use, and configuration. Review GitHub releases for breaking changes.

### Step 2: Apply SDK v3 Breaking Changes
Update imports (`createClient` instead of `new Deepgram`), method calls (`listen.prerecorded.transcribeUrl` instead of `transcription.preRecorded`), and response handling (destructured `{ result, error }`).

### Step 3: Migrate Models
Switch from Nova to Nova-2 for improved accuracy (47 languages vs 36). The model parameter is a simple config change; all other options remain the same.

### Step 4: A/B Test Models
Compare models side-by-side on test audio: measure confidence scores, processing times, and transcript quality before committing.

### Step 5: Validate and Deploy
Run automated validation: test API connectivity, pre-recorded transcription, and live transcription connection. Monitor dashboards for 30 minutes post-deploy.

### Step 6: Prepare Rollback
Record deployment versions. Keep rollback instructions ready: revert package version, reinstall, verify tests, redeploy.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- SDK v3 migration checklist
- Model comparison results
- Automated validation suite
- Rollback procedures and scripts

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Import errors | Old import syntax | Update to `{ createClient }` |
| Method not found | API change | Use `listen.prerecorded.transcribeUrl` |
| Response structure | Destructuring change | Use `{ result, error }` pattern |
| Quality regression | Model change | A/B test before committing |

## Examples

### Migration Types
| Type | Description | Risk |
|------|-------------|------|
| SDK Version | v2.x to v3.x | Medium (breaking changes) |
| Model Migration | Nova to Nova-2 | Low (config change) |
| API Version | v1 to v2 | High (endpoint changes) |

### v3 Quick Reference
```typescript
// Old: import Deepgram from '@deepgram/sdk'
// New:
import { createClient } from '@deepgram/sdk';
const deepgram = createClient(apiKey);
const { result, error } = await deepgram.listen.prerecorded.transcribeUrl(
  { url: audioUrl }, { model: 'nova-2', smart_format: true }
);
```

## Resources
- [Deepgram SDK Changelog](https://github.com/deepgram/deepgram-js-sdk/releases)
- [Model Migration Guide](https://developers.deepgram.com/docs/model-migration)
- [API Deprecation Schedule](https://developers.deepgram.com/docs/deprecation)