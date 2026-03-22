---
name: anima-upgrade-migration
description: |
  Upgrade @animaapp/anima-sdk versions and handle API changes.
  Use when upgrading SDK versions, migrating from the Figma plugin workflow
  to SDK-based automation, or adapting to new Anima API features.
  Trigger: "anima upgrade", "anima migration", "anima SDK update".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, migration]
compatible-with: claude-code
---

# Anima Upgrade & Migration

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

## Output

- SDK upgraded to latest version
- Migrated from manual plugin to automated SDK
- All generation tests passing after upgrade

## Resources

- [Anima SDK npm](https://www.npmjs.com/package/@animaapp/anima-sdk)
- [Anima SDK GitHub](https://github.com/AnimaApp/anima-sdk)

## Next Steps

For CI/CD setup, see `anima-ci-integration`.
