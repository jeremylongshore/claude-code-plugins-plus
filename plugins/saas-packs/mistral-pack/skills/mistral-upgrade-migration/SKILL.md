---
name: mistral-upgrade-migration
description: |
  Analyze, plan, and execute Mistral AI SDK upgrades with breaking change detection.
  Use when upgrading Mistral SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade mistral", "mistral migration",
  "mistral breaking changes", "update mistral SDK", "analyze mistral version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Mistral AI Upgrade & Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Guide for upgrading Mistral AI SDK versions and handling breaking changes.

## Prerequisites
- Current Mistral AI SDK installed
- Git for version control
- Test suite available
- Staging environment

## Instructions

### Step 1: Check Current Version

```bash
set -euo pipefail
# Node.js SDK
npm list @mistralai/mistralai
npm view @mistralai/mistralai versions --json | jq '.[-5:]'

# Python SDK
pip show mistralai
pip index versions mistralai 2>/dev/null || pip install mistralai==

# Check for outdated
npm outdated @mistralai/mistralai
```

### Step 2: Review Changelog

```bash
set -euo pipefail
# Check GitHub releases
open https://github.com/mistralai/client-js/releases
open https://github.com/mistralai/client-python/releases

# Check npm changelog
npm info @mistralai/mistralai
```

### Step 3: Create Upgrade Branch

```bash
set -euo pipefail
# Create feature branch
git checkout -b upgrade/mistral-sdk-vX.Y.Z

# Backup current lock file
cp package-lock.json package-lock.json.bak

# Upgrade SDK
npm install @mistralai/mistralai@latest

# Or specific version
npm install @mistralai/mistralai@1.2.0

# Check what changed
npm diff @mistralai/mistralai
```

### Step 4: Handle Breaking Changes

**Common Migration Patterns:**

**Import Changes (v0.x to v1.x)**
```typescript
// Before (v0.x)
import MistralClient from '@mistralai/mistralai';
const client = new MistralClient(apiKey);

// After (v1.x)
import Mistral from '@mistralai/mistralai';
const client = new Mistral({ apiKey });
```

**Method Changes**
```typescript
// Before
const response = await client.chat(params);

// After (v1.x)
const response = await client.chat.complete(params);
```

**Streaming Changes**
```typescript
// Before
const stream = await client.chatStream(params);
for await (const chunk of stream) { ... }

// After (v1.x)
const stream = await client.chat.stream(params);
for await (const event of stream) {
  const chunk = event.data;
  ...
}
```

### Step 5: Run Tests

```bash
set -euo pipefail
# Type check
npm run typecheck

# Unit tests
npm test

# Integration tests
MISTRAL_API_KEY=$MISTRAL_API_KEY_TEST npm run test:integration

# Compare outputs
npm run test -- --updateSnapshot # if using snapshots
```

### Step 6: Create Migration Script

```typescript
// scripts/migrate-mistral.ts
import { readFileSync, writeFileSync } from 'fs';
import { glob } from 'glob';

const MIGRATIONS: Array<{ pattern: RegExp; replacement: string }> = [
  // Import statement
  {
    pattern: /import MistralClient from '@mistralai\/mistralai'/g,
    replacement: "import Mistral from '@mistralai/mistralai'",
  },
  // Client instantiation
  {
    pattern: /new MistralClient\((\w+)\)/g,
    replacement: 'new Mistral({ apiKey: $1 })',
  },
  // Chat method
  {
    pattern: /\.chat\(/g,
    replacement: '.chat.complete(',
  },
  // Streaming method
  {
    pattern: /\.chatStream\(/g,
    replacement: '.chat.stream(',
  },
];

async function migrate() {
  const files = await glob('src/**/*.{ts,js}');

  for (const file of files) {
    let content = readFileSync(file, 'utf-8');
    let modified = false;

    for (const { pattern, replacement } of MIGRATIONS) {
      if (pattern.test(content)) {
        content = content.replace(pattern, replacement);
        modified = true;
      }
    }

    if (modified) {
      writeFileSync(file, content);
      console.log(`Migrated: ${file}`);
    }
  }
}

migrate();
```

### Step 7: Document Changes

```markdown
## Mistral SDK Upgrade: v0.x → v1.x

### Breaking Changes Applied
1. Updated import statement
2. Changed client instantiation
3. Updated chat method calls
4. Modified streaming interface

### Files Modified
- src/mistral/client.ts
- src/services/chat.ts
- tests/mistral.test.ts

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Staging deployment verified
- [ ] Performance benchmarked

### Rollback
```bash
npm install @mistralai/mistralai@0.x.x
git checkout -- src/
```
```

## Output
- Updated SDK version
- Fixed breaking changes
- Passing test suite
- Documented rollback procedure

## Version Compatibility

| SDK Version | Node.js | API Version | Notable Changes |
|-------------|---------|-------------|-----------------|
| 1.x | 18+ | Latest | New client interface |
| 0.5.x | 16+ | v1 | Stable, legacy |
| 0.4.x | 16+ | v1 | Streaming improvements |

## Error Handling

| Error After Upgrade | Cause | Solution |
|---------------------|-------|----------|
| Import error | Changed exports | Update import statement |
| Type errors | Interface changes | Update types |
| Runtime error | Method signature changed | Check migration guide |
| Test failures | Response format changed | Update assertions |

## Examples

### Deprecation Handling
```typescript
// Monitor for deprecation warnings
if (process.env.NODE_ENV === 'development') {
  process.on('warning', (warning) => {
    if (warning.name === 'DeprecationWarning') {
      console.warn('[Mistral SDK]', warning.message);
    }
  });
}
```

### Gradual Migration with Feature Flag
```typescript
const USE_NEW_SDK = process.env.MISTRAL_SDK_V1 === 'true';

async function chat(messages: Message[]): Promise<string> {
  if (USE_NEW_SDK) {
    // New SDK interface
    const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });
    const response = await client.chat.complete({ model, messages });
    return response.choices?.[0]?.message?.content ?? '';
  } else {
    // Legacy interface
    const client = new MistralClient(process.env.MISTRAL_API_KEY);
    const response = await client.chat({ model, messages });
    return response.choices?.[0]?.message?.content ?? '';
  }
}
```

### Rollback Procedure
```bash
set -euo pipefail
# Quick rollback
npm install @mistralai/mistralai@0.5.0 --save-exact

# Verify rollback
npm list @mistralai/mistralai
npm test
```

## Resources
- [Mistral AI Changelog](https://github.com/mistralai/client-js/releases)
- [Mistral AI Migration Guide](https://docs.mistral.ai/guides/migration/)

## Next Steps
For CI integration during upgrades, see `mistral-ci-integration`.