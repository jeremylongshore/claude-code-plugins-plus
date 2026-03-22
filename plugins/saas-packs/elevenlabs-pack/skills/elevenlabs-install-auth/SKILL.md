---
name: elevenlabs-install-auth
description: |
  Install and configure ElevenLabs SDK authentication for Node.js or Python.
  Use when setting up a new ElevenLabs project, configuring API keys,
  or initializing the elevenlabs npm/pip package.
  Trigger: "install elevenlabs", "setup elevenlabs", "elevenlabs auth",
  "configure elevenlabs API key", "elevenlabs credentials".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, tts, audio]
compatible-with: claude-code
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

**TypeScript:**
```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

const client = new ElevenLabsClient({
  apiKey: process.env.ELEVENLABS_API_KEY,
  // Optional: configure retries (default: 2)
  maxRetries: 3,
  // Optional: configure timeout in seconds
  timeoutInSeconds: 30,
});
```

**Python:**
```python
import os
from elevenlabs.client import ElevenLabsClient

client = ElevenLabsClient(
    api_key=os.environ.get("ELEVENLABS_API_KEY")
)
```

### Step 4: Verify Connection

**TypeScript:**
```typescript
async function verifyConnection() {
  // List available voices to confirm auth works
  const voices = await client.voices.getAll();
  console.log(`Connected. ${voices.voices.length} voices available.`);

  // Check subscription/quota
  const user = await client.user.get();
  console.log(`Plan: ${user.subscription.tier}`);
  console.log(`Characters used: ${user.subscription.character_count}/${user.subscription.character_limit}`);
}

verifyConnection().catch(console.error);
```

**Python:**
```python
def verify_connection():
    voices = client.voices.get_all()
    print(f"Connected. {len(voices.voices)} voices available.")

    user = client.user.get()
    print(f"Plan: {user.subscription.tier}")
    print(f"Characters used: {user.subscription.character_count}/{user.subscription.character_limit}")

verify_connection()
```

**cURL (raw API):**
```bash
curl -s https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" | jq '.subscription.tier'
```

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

## API Key Best Practices

- Never hardcode keys in source files
- Use separate keys for dev/staging/prod
- Rotate keys quarterly via the dashboard
- The `xi-api-key` header is used for REST calls; SDKs handle this automatically
- Free tier: 10,000 characters/month, Starter: 30,000, Creator: 100,000

## Resources

- [ElevenLabs API Introduction](https://elevenlabs.io/docs/api-reference/introduction)
- [ElevenLabs JS SDK](https://github.com/elevenlabs/elevenlabs-js)
- [ElevenLabs Python SDK](https://pypi.org/project/elevenlabs/)
- [API Key Management](https://elevenlabs.io/app/settings/api-keys)

## Next Steps

After auth is confirmed, proceed to `elevenlabs-hello-world` for your first text-to-speech generation.
