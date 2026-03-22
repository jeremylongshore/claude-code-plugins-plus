---
name: perplexity-upgrade-migration
description: |
  Migrate between Perplexity model generations and API parameter changes.
  Use when upgrading to new Sonar models, handling deprecated parameters,
  or migrating from legacy pplx-api models.
  Trigger with phrases like "upgrade perplexity", "perplexity migration",
  "perplexity model change", "update perplexity", "perplexity deprecated".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, api, migration]

---
# Perplexity Upgrade & Migration

## Current State
!`npm list openai 2>/dev/null | grep openai || echo 'openai not installed'`
!`pip show openai 2>/dev/null | grep Version || echo 'N/A'`

## Overview
Guide for migrating between Perplexity model generations and API changes. Perplexity has evolved from pplx-api with third-party models to the Sonar family with built-in web search.

## Model Evolution

| Era | Models | Status |
|-----|--------|--------|
| Legacy (pre-2025) | `pplx-7b-online`, `pplx-70b-online`, `llama-3.1-sonar-*` | Deprecated |
| Current (2025) | `sonar`, `sonar-pro` | Active |
| Extended (2025+) | `sonar-reasoning-pro`, `sonar-deep-research` | Active |

## Instructions

### Step 1: Identify Legacy Patterns to Update

```bash
set -euo pipefail
# Find deprecated model names in your codebase
grep -rn "pplx-7b\|pplx-70b\|llama.*sonar\|sonar-small\|sonar-medium\|sonar-huge" \
  --include="*.ts" --include="*.py" --include="*.js" --include="*.json" \
  . 2>/dev/null || echo "No legacy models found"

# Find old base URLs
grep -rn "api.perplexity.com\|pplx.readme.io" \
  --include="*.ts" --include="*.py" --include="*.js" \
  . 2>/dev/null || echo "No legacy URLs found"
```

### Step 2: Model Name Migration Map

```typescript
// Migration map: old model name -> new model name
const MODEL_MIGRATION: Record<string, string> = {
  // Legacy pplx-api models (fully deprecated)
  "pplx-7b-online": "sonar",
  "pplx-70b-online": "sonar-pro",
  "pplx-7b-chat": "sonar",
  "pplx-70b-chat": "sonar",

  // Llama-era Sonar models (deprecated)
  "llama-3.1-sonar-small-128k-online": "sonar",
  "llama-3.1-sonar-large-128k-online": "sonar-pro",
  "llama-3.1-sonar-huge-128k-online": "sonar-pro",
  "sonar-small-online": "sonar",
  "sonar-medium-online": "sonar-pro",

  // Current models (no migration needed)
  "sonar": "sonar",
  "sonar-pro": "sonar-pro",
  "sonar-reasoning-pro": "sonar-reasoning-pro",
  "sonar-deep-research": "sonar-deep-research",
};

function migrateModel(model: string): string {
  const migrated = MODEL_MIGRATION[model];
  if (!migrated) {
    console.warn(`Unknown Perplexity model: ${model}. Defaulting to sonar.`);
    return "sonar";
  }
  if (migrated !== model) {
    console.warn(`Perplexity model ${model} is deprecated. Using ${migrated}.`);
  }
  return migrated;
}
```

### Step 3: URL Migration

```typescript
// Old URLs -> New URL
const BASE_URL_MIGRATION: Record<string, string> = {
  "https://api.perplexity.com": "https://api.perplexity.ai",
  "https://pplx-api.perplexity.ai": "https://api.perplexity.ai",
};

// Current canonical base URL
const PERPLEXITY_BASE_URL = "https://api.perplexity.ai";
```

### Step 4: Parameter Changes

```typescript
// Parameters that changed between API versions
// OLD: return_citations: true
// NEW: Citations are always returned in the response object

// OLD: No search_recency_filter
// NEW: search_recency_filter: "hour" | "day" | "week" | "month"

// OLD: No search_domain_filter
// NEW: search_domain_filter: string[] (max 20, prefix with - to exclude)

// OLD: No return_related_questions
// NEW: return_related_questions: true (closed beta)

// OLD: No return_images
// NEW: return_images: true (Tier-2+ only)

// OLD: No search_after_date_filter / search_before_date_filter
// NEW: search_after_date_filter: "3/1/2025" (mm/dd/yyyy format)
```

### Step 5: Upgrade OpenAI SDK
```bash
set -euo pipefail
# Create upgrade branch
git checkout -b upgrade/perplexity-sonar-migration

# Upgrade OpenAI SDK to latest
npm install openai@latest
# or
pip install --upgrade openai

# Run tests
npm test

# Verify connection with new models
node -e "
const OpenAI = require('openai');
const c = new OpenAI({apiKey: process.env.PERPLEXITY_API_KEY, baseURL: 'https://api.perplexity.ai'});
c.chat.completions.create({model:'sonar', messages:[{role:'user',content:'test'}], max_tokens:5})
  .then(r => console.log('OK:', r.model))
  .catch(e => console.error('FAIL:', e.message));
"
```

## Rollback
```bash
set -euo pipefail
# If the upgrade breaks things, revert
git checkout main -- package.json package-lock.json
npm install
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `Invalid model` error | Using deprecated model name | Apply model migration map |
| `Connection refused` | Wrong base URL | Use `https://api.perplexity.ai` |
| Missing citations | Expecting old response format | Citations are in `response.citations` array |
| Parameter rejected | Using old parameter names | Check current parameter list |

## Output
- Updated model names to current Sonar family
- Corrected base URL to `api.perplexity.ai`
- Updated parameters to current API spec
- Passing test suite

## Resources
- [Perplexity Model Cards](https://docs.perplexity.ai/getting-started/models)
- [API Changelog](https://docs.perplexity.ai)
- [Meet New Sonar (Blog)](https://www.perplexity.ai/hub/blog/meet-new-sonar)

## Next Steps
For CI integration during upgrades, see `perplexity-ci-integration`.
