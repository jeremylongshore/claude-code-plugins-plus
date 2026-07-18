---
name: elevenlabs-install-auth
description: |
  Install and configure ElevenLabs SDK authentication for Node.js or Python.
  Use when setting up a new ElevenLabs project, configuring API keys, or
  initializing the elevenlabs npm/pip package.
  Trigger with "install elevenlabs", "setup elevenlabs", "elevenlabs auth",
  "configure elevenlabs API key", "elevenlabs credentials".
allowed-tools: Write, Bash(npm:*), Bash(pip:*), Bash(pnpm:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- tts
- audio
compatibility: Designed for Claude Code
---
# ElevenLabs Install & Auth

## Overview

Set up the ElevenLabs SDK and configure API key authentication. ElevenLabs uses a single API key (`xi-api-key` header) for all endpoints at `api.elevenlabs.io`.

## Prerequisites

- Node.js 18+ or Python 3.10+
- ElevenLabs account (free tier works) at https://elevenlabs.io
- API key from Profile > API Keys in the ElevenLabs dashboard

## Instructions

### Step 1: Install the SDK

**Node.js** (official package: `@elevenlabs/elevenlabs-js`):

```bash
npm install @elevenlabs/elevenlabs-js
# or
pnpm add @elevenlabs/elevenlabs-js
```

**Python** (official package: `elevenlabs`):

```bash
pip install elevenlabs
```

### Step 2: Configure API Key

```bash
# Set environment variable (all SDKs auto-detect this)
export ELEVENLABS_API_KEY="sk_your_key_here"

# Or create .env file
echo 'ELEVENLABS_API_KEY=sk_your_key_here' >> .env
```

Add to `.gitignore`:

```gitignore
.env
.env.local
.env.*.local
```

### Step 3: Initialize the Client

Both SDKs auto-detect `ELEVENLABS_API_KEY`. Minimal TypeScript skeleton:

```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

const client = new ElevenLabsClient({
  apiKey: process.env.ELEVENLABS_API_KEY,
});
```

The Python client mirrors this with `ElevenLabsClient(api_key=...)`. For retry,
timeout, and the full Python skeleton, see
[implementation.md](references/implementation.md).

### Step 4: Verify Connection

Confirm auth by listing voices — a successful call proves the key is valid and
not over quota:

```typescript
const voices = await client.voices.getAll();
console.log(`Connected. ${voices.voices.length} voices available.`);
```

Full TypeScript + Python + cURL verification (including subscription/quota
inspection) is in [implementation.md](references/implementation.md).

## Output

- SDK installed in `node_modules` or `site-packages`
- API key stored in `.env` (git-ignored)
- Successful voice listing confirms authentication
- Subscription tier and character quota displayed

## Error Handling

| Error | HTTP | Cause | Solution |
|-------|------|-------|----------|
| `invalid_api_key` | 401 | Key missing, expired, or malformed | Regenerate at elevenlabs.io > Profile > API Keys |
| `ENOTFOUND api.elevenlabs.io` | N/A | DNS/network failure | Check internet; ensure outbound HTTPS on port 443 |
| `MODULE_NOT_FOUND` | N/A | SDK not installed | Run `npm install @elevenlabs/elevenlabs-js` |
| `quota_exceeded` | 401 | Character limit reached for billing period | Upgrade plan or wait for reset |

## Examples

Two full setup walkthroughs (Node.js and Python) plus a no-SDK CI smoke test
live in [examples.md](references/examples.md). The shortest complete path for a
new Node.js project:

```bash
npm install @elevenlabs/elevenlabs-js
echo 'ELEVENLABS_API_KEY=sk_your_key_here' >> .env
printf '.env\n' >> .gitignore
```

```typescript
import "dotenv/config";
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

const client = new ElevenLabsClient({ apiKey: process.env.ELEVENLABS_API_KEY });
const voices = await client.voices.getAll();
console.log(`Connected. ${voices.voices.length} voices available.`);
```

See [examples.md](references/examples.md) for the Python equivalent and the
`curl`-only pipeline gate.

## API Key Best Practices

- Never hardcode keys in source files
- Use separate keys for dev/staging/prod
- Rotate keys quarterly via the dashboard
- Free tier: 10,000 characters/month, Starter: 30,000, Creator: 100,000

Full best-practices notes are in [implementation.md](references/implementation.md).

## Resources

- [ElevenLabs API Introduction](https://elevenlabs.io/docs/api-reference/introduction)
- [ElevenLabs JS SDK](https://github.com/elevenlabs/elevenlabs-js)
- [ElevenLabs Python SDK](https://pypi.org/project/elevenlabs/)
- [API Key Management](https://elevenlabs.io/app/settings/api-keys)

## Next Steps

After auth is confirmed, proceed to the `elevenlabs-hello-world` skill for your first text-to-speech generation, then explore voice listing and streaming in the rest of the ElevenLabs pack.
