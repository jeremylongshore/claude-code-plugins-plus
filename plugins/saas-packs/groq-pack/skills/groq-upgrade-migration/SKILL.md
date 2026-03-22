---
name: groq-upgrade-migration
description: |
  Upgrade groq-sdk versions and handle Groq model deprecations.
  Use when upgrading SDK versions, detecting deprecated models,
  or migrating to new Groq model IDs.
  Trigger with phrases like "upgrade groq", "groq migration",
  "groq breaking changes", "update groq SDK", "groq deprecated model".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, api, migration]

---
# Groq Upgrade & Migration

## Current State
!`npm list groq-sdk 2>/dev/null | grep groq-sdk || echo 'groq-sdk not installed'`
!`pip show groq 2>/dev/null | grep -E "Name|Version" || echo 'groq not installed (python)'`

## Overview
Guide for upgrading the `groq-sdk` package and migrating away from deprecated model IDs. Groq regularly deprecates older models in favor of newer, faster alternatives.

## Model Deprecation Timeline
Groq announces deprecations with advance notice. These models have been deprecated:

| Deprecated Model | Deprecation Date | Replacement |
|-----------------|-----------------|-------------|
| `mixtral-8x7b-32768` | 2025-03-05 | `llama-3.3-70b-versatile` or `llama-3.1-8b-instant` |
| `gemma2-9b-it` | 2025-08-08 | `llama-3.1-8b-instant` |
| `llama-3.1-70b-versatile` | 2024-12-06 | `llama-3.3-70b-versatile` |
| `llama-3.1-70b-specdec` | 2024-12-06 | `llama-3.3-70b-specdec` |
| `playai-tts` | 2025-12-23 | Orpheus TTS models |
| `playai-tts-arabic` | 2025-12-23 | Orpheus TTS models |
| `distil-whisper-large-v3-en` | — | `whisper-large-v3-turbo` |

## Current Model IDs (Use These)

| Model ID | Type | Context | Speed |
|----------|------|---------|-------|
| `llama-3.1-8b-instant` | Text | 128K | ~560 tok/s |
| `llama-3.3-70b-versatile` | Text | 128K | ~280 tok/s |
| `llama-3.3-70b-specdec` | Text | 128K | Faster |
| `meta-llama/llama-4-scout-17b-16e-instruct` | Vision+Text | 128K | ~460 tok/s |
| `meta-llama/llama-4-maverick-17b-128e-instruct` | Vision+Text | 128K | — |
| `whisper-large-v3` | Audio STT | — | 164x RT |
| `whisper-large-v3-turbo` | Audio STT | — | 216x RT |

Always verify at: `GET https://api.groq.com/openai/v1/models`

## Instructions

### Step 1: Check Current Version and Models
```bash
set -euo pipefail
# SDK version
npm list groq-sdk 2>/dev/null
npm view groq-sdk version  # latest on npm

# Find all model references in your code
grep -rn "model.*['\"]" src/ --include="*.ts" --include="*.js" | grep -i "groq\|llama\|mixtral\|gemma\|whisper"
```

### Step 2: Upgrade SDK
```bash
set -euo pipefail
# Create upgrade branch
git checkout -b chore/upgrade-groq-sdk

# Update to latest
npm install groq-sdk@latest

# Check for breaking changes
npm ls groq-sdk
```

### Step 3: Find and Replace Deprecated Models
```typescript
// Find-and-replace map for deprecated model IDs
const MODEL_MIGRATIONS: Record<string, string> = {
  "mixtral-8x7b-32768": "llama-3.3-70b-versatile",
  "gemma2-9b-it": "llama-3.1-8b-instant",
  "llama-3.1-70b-versatile": "llama-3.3-70b-versatile",
  "llama-3.1-70b-specdec": "llama-3.3-70b-specdec",
  "llama3-70b-8192": "llama-3.3-70b-versatile",
  "llama3-8b-8192": "llama-3.1-8b-instant",
  "distil-whisper-large-v3-en": "whisper-large-v3-turbo",
};

function resolveModel(model: string): string {
  if (model in MODEL_MIGRATIONS) {
    console.warn(`Model ${model} is deprecated. Using ${MODEL_MIGRATIONS[model]} instead.`);
    return MODEL_MIGRATIONS[model];
  }
  return model;
}
```

### Step 4: Run Migration Scanner
```bash
set -euo pipefail
# Automated scan for deprecated patterns
echo "=== Deprecated Model IDs ==="
grep -rn "mixtral-8x7b\|gemma2-9b\|llama-3.1-70b-versatile\|llama3-70b\|llama3-8b\|distil-whisper" \
  src/ --include="*.ts" --include="*.js" --include="*.py" || echo "None found"

echo ""
echo "=== Old Import Patterns ==="
grep -rn "from '@groq/sdk'\|from \"@groq/sdk\"\|require('@groq/sdk')" \
  src/ --include="*.ts" --include="*.js" || echo "None found (correct import is 'groq-sdk')"

echo ""
echo "=== Deprecated Method Calls ==="
grep -rn "\.ping()\|\.healthCheck()\|GroqClient\|GroqError" \
  src/ --include="*.ts" --include="*.js" || echo "None found"
```

### Step 5: Validate and Test
```bash
set -euo pipefail
# Run tests
npm test

# Verify models are current
curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" | \
  jq -r '.data[].id' | sort

# Integration test
node -e "
const Groq = require('groq-sdk').default;
const g = new Groq();
g.chat.completions.create({
  model: 'llama-3.1-8b-instant',
  messages: [{role: 'user', content: 'ping'}],
  max_tokens: 5
}).then(r => console.log('OK:', r.choices[0].message.content));
"
```

### Step 6: Rollback If Needed
```bash
set -euo pipefail
# Pin to previous version
npm install groq-sdk@0.11.0 --save-exact
npm test
```

## SDK Changelog Highlights
The `groq-sdk` package mirrors the OpenAI SDK structure. Key changes to watch:
- New model IDs added to type definitions
- Response type changes (e.g., new `usage` fields)
- Constructor options changes
- New endpoint support (vision, audio, TTS)

Always check the [GitHub releases](https://github.com/groq/groq-typescript/releases).

## Error Handling
| Issue | Symptom | Solution |
|-------|---------|----------|
| Deprecated model | `400 model_not_found` or `400 model_decommissioned` | Replace with current model ID |
| Type errors after upgrade | TypeScript compilation fails | Check SDK changelog for type changes |
| Auth format change | `401` after upgrade | Verify constructor uses `apiKey`, not `key` |
| New required fields | `400` on previously working requests | Check API docs for parameter changes |

## Resources
- [Groq Model Deprecations](https://console.groq.com/docs/deprecations)
- [Groq Changelog](https://console.groq.com/docs/changelog)
- [groq-sdk GitHub Releases](https://github.com/groq/groq-typescript/releases)
- [Groq Current Models](https://console.groq.com/docs/models)

## Next Steps
For CI integration during upgrades, see `groq-ci-integration`.
