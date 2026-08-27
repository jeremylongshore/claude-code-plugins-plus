---
name: anima-upgrade-migration
description: 'Upgrade @animaapp/anima-sdk versions and handle API changes.

  Use when upgrading SDK versions, migrating from the Figma plugin workflow

  to SDK-based automation, or adapting to new Anima API features.

  Trigger: "anima upgrade", "anima migration", "anima SDK update".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.4.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- design
- figma
- anima
- migration
compatibility: Designed for Claude Code
---
# Anima Upgrade & Migration

## Overview

This workflow moves an Anima integration between SDK versions or from manual
Figma exports to automation while preserving a reviewable, reversible design
source of truth. It uses a pinned dependency and a staging canary so API or
generated-code changes are detected before production output is replaced.

## Prerequisites

- A clean working tree, committed lockfile, current SDK version, and a
  reviewed changelog or release note for the proposed target version.
- A fixture registry containing synthetic or approved design nodes, expected
  output paths, and a baseline artifact digest for the current workflow.
- Separate staging credentials with read-only design access, an owner for
  generated-code review, and a rollback revision that can restore the prior
  SDK and generated output.
- CI gates for install, lint, type checking, tests, and secret scanning; do
  not test an upgrade against customer designs or live production writes.

## Migration Paths

| From | To | Complexity |
|------|----|-----------|
| Figma plugin (manual) | SDK automation | Medium |
| SDK v1 → v2 | SDK latest | Low |
| Anima Playground | SDK API | Low |

## Instructions

### Step 1: Upgrade SDK

```bash
# Check current version
npm list @animaapp/anima-sdk

# Upgrade to latest
npm install @animaapp/anima-sdk@latest

# Check for breaking changes
npm info @animaapp/anima-sdk changelog
```

### Step 2: Migrate from Manual Plugin to SDK

```typescript
// BEFORE: Manual Figma plugin workflow
// 1. Open Figma → Plugins → Anima
// 2. Select component → Export → React
// 3. Copy-paste generated code into project
// 4. Manually repeat for each component change

// AFTER: Automated SDK workflow
import { Anima } from '@animaapp/anima-sdk';

const anima = new Anima({ auth: { token: process.env.ANIMA_TOKEN! } });

// Automated: runs in CI on Figma file version change
async function syncDesignToCode() {
  const { files } = await anima.generateCode({
    fileKey: process.env.FIGMA_FILE_KEY!,
    figmaToken: process.env.FIGMA_TOKEN!,
    nodesId: ['1:2', '3:4', '5:6'],  // All design system components
    settings: { language: 'typescript', framework: 'react', styling: 'tailwind' },
  });

  // Write to project, run through linter, create PR
  for (const file of files) {
    require('fs').writeFileSync(`src/components/generated/${file.fileName}`, file.content);
  }
}
```

### Step 3: API Changes Checklist

```typescript
// Common API changes between versions:
// - New settings options (e.g., uiLibrary: 'shadcn' added later)
// - New frameworks (e.g., Next.js-specific output)
// - Response format changes in files array
// - New authentication methods

// Test after upgrade:
async function testUpgrade() {
  const anima = new Anima({ auth: { token: process.env.ANIMA_TOKEN! } });
  const { files } = await anima.generateCode({
    fileKey: process.env.FIGMA_FILE_KEY!,
    figmaToken: process.env.FIGMA_TOKEN!,
    nodesId: ['1:2'],
    settings: { language: 'typescript', framework: 'react', styling: 'tailwind' },
  });
  console.log(`Upgrade test: ${files.length} files generated`);
}
```

## Error Handling

| Failure | Required response |
|---------|-------------------|
| Dependency resolution or lockfile changes are unexpected | Stop the migration, inspect the dependency tree, and restore the approved lockfile before retrying. |
| Authentication, file access, or API schema changes fail | Keep the old revision active; verify credentials and supported request fields without widening access. |
| Generated files move, disappear, or contain an unexpected diff | Quarantine the output, compare against the baseline fixture, and require owner review before any merge. |
| Lint, type, visual, or accessibility checks fail | Do not promote the SDK; retain the sanitized test receipt and return the failure to the design/code owner. |
| Staging canary fails or rollback is unavailable | Disable automated generation and restore the last known-good package and generated artifact. |

Never log tokens, full Figma payloads, or design content while comparing
versions. A migration is complete only after the pinned package, source
version, artifact digest, test result, and rollback reference are recorded.

## Output

- SDK upgraded to latest version
- Migrated from manual plugin to automated SDK
- All generation tests passing after upgrade

## Examples

Use an approved version and one synthetic, allowlisted component for a staged
canary; keep the lockfile and generated diff in the review boundary:

```bash
export APPROVED_ANIMA_VERSION="2.x.y"
npm install "@animaapp/anima-sdk@${APPROVED_ANIMA_VERSION}"
npm test
npm run lint
npm run generate:staging -- \
  --file-key synthetic-staging-file \
  --node-id 1:2 \
  --output-dir .tmp/anima-upgrade \
  --no-production-write
```

Compare the staged artifact with the baseline, review the source-version and
path changes, and promote only after owner approval. If the canary changes an
unexpected file or fails a quality gate, delete the temporary output and
restore the prior lockfile/package before rerunning.

## Resources

- [Anima SDK npm](https://www.npmjs.com/package/@animaapp/anima-sdk)
- [Anima SDK GitHub](https://github.com/AnimaApp/anima-sdk)

## Next Steps

For CI/CD setup, see `anima-ci-integration`.
