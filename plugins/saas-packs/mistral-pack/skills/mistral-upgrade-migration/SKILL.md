---
name: mistral-upgrade-migration
description: |
  Analyze, plan, and execute Mistral AI SDK upgrades with breaking change detection.
  Use when upgrading Mistral SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade mistral", "mistral breaking changes",
  "update mistral SDK", "analyze mistral version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, api, migration]

---
# Mistral AI Upgrade & Migration

## Current State
!`npm list @mistralai/mistralai 2>/dev/null || echo 'not installed'`
!`pip show mistralai 2>/dev/null | grep -E "^(Name|Version)" || echo 'not installed'`

## Overview
Guide for upgrading the Mistral AI SDK between major versions. The TypeScript SDK (`@mistralai/mistralai`) moved from CommonJS to ESM-only in v1.x, with significant API surface changes. This skill covers version detection, breaking change migration, automated code transforms, and rollback.

## Prerequisites
- Current Mistral AI SDK installed
- Git for version control
- Test suite available

## Instructions

### Step 1: Check Versions

```bash
set -euo pipefail
# Current version
npm list @mistralai/mistralai 2>/dev/null

# Latest available
npm view @mistralai/mistralai version

# All versions
npm view @mistralai/mistralai versions --json | jq '.[-5:]'

# Python
pip show mistralai 2>/dev/null | grep Version
```

### Step 2: Known Breaking Changes (v0.x to v1.x)

| Change | v0.x (old) | v1.x (current) |
|--------|-----------|----------------|
| Module format | CommonJS + ESM | **ESM only** |
| Import | `import MistralClient from '...'` | `import { Mistral } from '...'` |
| Constructor | `new MistralClient(apiKey)` | `new Mistral({ apiKey })` |
| Chat method | `client.chat(params)` | `client.chat.complete(params)` |
| Streaming | `client.chatStream(params)` | `client.chat.stream(params)` |
| Stream events | `for await (const chunk of stream)` | `for await (const event of stream)` access `.data` |
| Embeddings | `client.embeddings(params)` | `client.embeddings.create(params)` |
| Response types | Longer names | Shorter type names |
| Enum values | String constants | Forward-compatible unions |

### Step 3: Automated Migration Script

```typescript
// scripts/migrate-mistral-v1.ts
import { readFileSync, writeFileSync } from 'fs';
import { glob } from 'glob';

const TRANSFORMS = [
  // Import statement
  {
    find: /import\s+MistralClient\s+from\s+['"]@mistralai\/mistralai['"]/g,
    replace: "import { Mistral } from '@mistralai/mistralai'",
  },
  // Constructor
  {
    find: /new\s+MistralClient\((\w+)\)/g,
    replace: 'new Mistral({ apiKey: $1 })',
  },
  // Chat method (careful: only top-level .chat(), not .chat.complete())
  {
    find: /\.chat\((?!\.)/g,
    replace: '.chat.complete(',
  },
  // Streaming
  {
    find: /\.chatStream\(/g,
    replace: '.chat.stream(',
  },
  // Embeddings
  {
    find: /\.embeddings\((?!\.)/g,
    replace: '.embeddings.create(',
  },
];

async function migrate() {
  const files = await glob('src/**/*.{ts,js}');
  let totalChanges = 0;

  for (const file of files) {
    let content = readFileSync(file, 'utf-8');
    let changes = 0;

    for (const { find, replace } of TRANSFORMS) {
      const newContent = content.replace(find, replace);
      if (newContent !== content) {
        changes++;
        content = newContent;
      }
    }

    if (changes > 0) {
      writeFileSync(file, content);
      console.log(`Migrated: ${file} (${changes} changes)`);
      totalChanges += changes;
    }
  }

  console.log(`\nTotal: ${totalChanges} changes across ${files.length} files`);
}

migrate();
```

### Step 4: Upgrade Procedure

```bash
set -euo pipefail
# Create branch
git checkout -b upgrade/mistral-sdk-v1

# Backup lock file
cp package-lock.json package-lock.json.bak

# Upgrade
npm install @mistralai/mistralai@latest

# Ensure package.json has "type": "module"
node -e "const p=require('./package.json'); if(p.type!=='module') console.warn('WARNING: Add \"type\": \"module\" to package.json for ESM')"

# Run migration script
npx tsx scripts/migrate-mistral-v1.ts

# Verify
npm run typecheck
npm test
```

### Step 5: Model Name Updates

Model names change over time. Update hardcoded references:

```typescript
// Model alias mapping — update when models deprecate
const MODEL_ALIASES: Record<string, string> = {
  // Deprecated → Current
  'mistral-tiny': 'mistral-small-latest',
  'mistral-medium': 'mistral-small-latest', // Deprecated Q1 2025
  'open-mistral-7b': 'mistral-small-latest',
  'open-mixtral-8x7b': 'mistral-small-latest',

  // Current (no change needed)
  'mistral-small-latest': 'mistral-small-latest',
  'mistral-large-latest': 'mistral-large-latest',
  'codestral-latest': 'codestral-latest',
  'mistral-embed': 'mistral-embed',
};

function resolveModel(model: string): string {
  const resolved = MODEL_ALIASES[model];
  if (resolved && resolved !== model) {
    console.warn(`Model "${model}" is deprecated, using "${resolved}"`);
  }
  return resolved ?? model;
}
```

### Step 6: Validation Tests

```typescript
import { describe, it, expect } from 'vitest';
import { Mistral } from '@mistralai/mistralai';

describe('SDK Upgrade Validation', () => {
  it('should import Mistral correctly', () => {
    expect(Mistral).toBeDefined();
    expect(typeof Mistral).toBe('function');
  });

  it('should construct client', () => {
    const client = new Mistral({ apiKey: 'test-key' });
    expect(client.chat).toBeDefined();
    expect(client.chat.complete).toBeDefined();
    expect(client.chat.stream).toBeDefined();
    expect(client.embeddings).toBeDefined();
    expect(client.embeddings.create).toBeDefined();
    expect(client.models).toBeDefined();
    expect(client.models.list).toBeDefined();
  });
});
```

### Step 7: Rollback

```bash
set -euo pipefail
# Quick rollback
npm install @mistralai/mistralai@0.5.0 --save-exact
git checkout -- src/  # Restore pre-migration code
npm test

# Or just revert the branch
git checkout main
git branch -D upgrade/mistral-sdk-v1
```

## Error Handling
| Error After Upgrade | Cause | Solution |
|---------------------|-------|----------|
| `ERR_REQUIRE_ESM` | Missing "type": "module" | Add to package.json |
| `Mistral is not a constructor` | Old import style | Use `import { Mistral }` |
| `.chat is not a function` | Old method call | Use `.chat.complete()` |
| Type errors | Interface changes | Update types to match v1.x |
| Test failures | Response shape changed | Update assertions and mocks |

## Resources
- [TypeScript SDK Releases](https://github.com/mistralai/client-ts/releases)
- [Python SDK Releases](https://github.com/mistralai/client-python/releases)
- [Changelog](https://docs.mistral.ai/getting-started/changelog/)
- [Models Deprecation](https://docs.mistral.ai/getting-started/models/)

## Output
- Updated SDK to latest version
- Automated code migration applied
- Model name references updated
- Test suite passing after upgrade
- Rollback procedure documented
