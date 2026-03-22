---
name: anth-upgrade-migration
description: |
  Upgrade Anthropic SDK versions and migrate between Claude API versions.
  Use when upgrading the Python/TypeScript SDK, migrating from Text Completions
  to Messages API, or adopting new API features like tool use or batches.
  Trigger with phrases like "upgrade anthropic sdk", "anthropic migration",
  "update claude sdk", "migrate to messages api".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Upgrade & Migration

## Overview

Guide for upgrading the Anthropic SDK and migrating between API versions. The SDK follows semver — major versions may have breaking changes.

## Check Current Versions

```bash
# Python
pip show anthropic | grep Version
# Version: 0.40.0

# TypeScript
npm list @anthropic-ai/sdk
# @anthropic-ai/sdk@0.35.0

# Check latest available
pip index versions anthropic 2>/dev/null | head -1
npm view @anthropic-ai/sdk version
```

## Upgrade Path

### Step 1: Create Upgrade Branch

```bash
git checkout -b upgrade/anthropic-sdk
```

### Step 2: Upgrade SDK

```bash
# Python
pip install --upgrade anthropic
pip show anthropic | grep Version

# TypeScript
npm install @anthropic-ai/sdk@latest
```

### Step 3: Review Breaking Changes

Key breaking changes by version:

**Python SDK 0.20+ (anthropic-version: 2023-06-01)**
```python
# OLD: Text Completions API (deprecated)
response = client.completions.create(
    model="claude-2",
    prompt="\n\nHuman: Hello\n\nAssistant:",
    max_tokens_to_sample=256
)

# NEW: Messages API
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=256,
    messages=[{"role": "user", "content": "Hello"}]
)
```

**Python SDK 0.30+ (streaming changes)**
```python
# OLD: Manual SSE parsing
response = client.messages.create(..., stream=True)
for line in response.iter_lines():
    ...

# NEW: High-level streaming
with client.messages.stream(...) as stream:
    for text in stream.text_stream:
        print(text)
```

**TypeScript SDK 0.20+ (import path change)**
```typescript
// OLD
import Anthropic from 'anthropic';

// NEW
import Anthropic from '@anthropic-ai/sdk';
```

### Step 4: Update API Version Header

```python
# The SDK sends anthropic-version header automatically
# To pin a specific version:
client = anthropic.Anthropic(
    default_headers={"anthropic-version": "2023-06-01"}
)

# For beta features:
client = anthropic.Anthropic(
    default_headers={"anthropic-beta": "token-counting-2024-11-01"}
)
```

### Step 5: Run Tests and Verify

```bash
# Run your test suite
python -m pytest tests/ -v
npm test

# Verify a live call
python3 -c "
import anthropic
c = anthropic.Anthropic()
m = c.messages.create(model='claude-haiku-4-20250514', max_tokens=8, messages=[{'role':'user','content':'hi'}])
print(f'OK: {m.model} {m.usage}')
"
```

## Migration: Text Completions to Messages

| Text Completions | Messages API |
|-----------------|--------------|
| `client.completions.create()` | `client.messages.create()` |
| `prompt` (string) | `messages` (array) |
| `max_tokens_to_sample` | `max_tokens` |
| `model: "claude-2"` | `model: "claude-sonnet-4-20250514"` |
| `\n\nHuman:...\n\nAssistant:` | `[{role: "user"}, {role: "assistant"}]` |
| `response.completion` | `response.content[0].text` |

## Rollback

```bash
# Python — pin to previous version
pip install anthropic==0.39.0

# TypeScript — pin to previous version
npm install @anthropic-ai/sdk@0.34.0

# Git rollback
git checkout main -- package.json package-lock.json
npm install
```

## Resources

- [Python SDK Changelog](https://github.com/anthropics/anthropic-sdk-python/releases)
- [TypeScript SDK Changelog](https://github.com/anthropics/anthropic-sdk-typescript/releases)
- [API Versioning](https://docs.anthropic.com/en/api/versioning)

## Next Steps

For CI integration during upgrades, see `anth-ci-integration`.
