# Groq Upgrade & Migration — Full Walkthrough

The complete, copy-paste-ready command sequence for upgrading `groq-sdk` and
migrating deprecated Groq model IDs. `SKILL.md` summarizes this workflow at a
high level; this file carries every step verbatim.

## Authentication

Every Groq API call (including the live-model verification in Step 5) reads the
API key from the `GROQ_API_KEY` environment variable. The SDK constructor
(`new Groq()`) picks it up automatically; the `curl` verification passes it as a
bearer token. Never hard-code the key — export it in your shell or CI secret store:

```bash
export GROQ_API_KEY="gsk_..."   # from https://console.groq.com/keys
```

## Step 1: Check Current Version and Models

```bash
set -euo pipefail
# SDK version
npm list groq-sdk 2>/dev/null
npm view groq-sdk version  # latest on npm

# Find all model references in your code
grep -rn "model.*['\"]" src/ --include="*.ts" --include="*.js" | grep -i "groq\|llama\|mixtral\|gemma\|whisper"
```

## Step 2: Upgrade SDK

```bash
set -euo pipefail
# Create upgrade branch
git checkout -b chore/upgrade-groq-sdk

# Update to latest
npm install groq-sdk@latest

# Check for breaking changes
npm ls groq-sdk
```

## Step 3: Find and Replace Deprecated Models

Add a resolver map so deprecated model IDs are rewritten at runtime while you
migrate call sites. Use `Read`/`Edit` to fold this into your Groq client module:

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

## Step 4: Run Migration Scanner

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

## Step 5: Validate and Test

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

## Step 6: Rollback If Needed

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
