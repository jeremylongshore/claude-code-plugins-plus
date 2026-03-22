---
name: deepgram-install-auth
description: |
  Install and configure Deepgram SDK authentication.
  Use when setting up a new Deepgram integration, configuring API keys,
  or initializing Deepgram in your project.
  Trigger: "install deepgram", "setup deepgram", "deepgram auth",
  "configure deepgram API key", "deepgram credentials".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, api, authentication, setup]

---
# Deepgram Install & Auth

## Current State
!`npm list @deepgram/sdk 2>/dev/null || echo '@deepgram/sdk not installed'`
!`pip show deepgram-sdk 2>/dev/null | grep Version || echo 'deepgram-sdk (Python) not installed'`

## Overview
Install the Deepgram SDK and configure API key authentication. Deepgram provides speech-to-text (Nova-3, Nova-2), text-to-speech (Aura-2), and audio intelligence APIs. The JS SDK uses `createClient()` (v3/v4) or `new DeepgramClient()` (v5+).

## Prerequisites
- Node.js 18+ or Python 3.10+
- Deepgram account at [console.deepgram.com](https://console.deepgram.com)
- API key from Console > Settings > API Keys

## Instructions

### Step 1: Install SDK

**Node.js (v3/v4 — current stable):**
```bash
npm install @deepgram/sdk
# or
pnpm add @deepgram/sdk
```

**Python:**
```bash
pip install deepgram-sdk
```

### Step 2: Configure API Key

```bash
# Option A: Environment variable (recommended)
export DEEPGRAM_API_KEY="your-api-key-here"

# Option B: .env file (add .env to .gitignore)
echo 'DEEPGRAM_API_KEY=your-api-key-here' >> .env
```

**Never hardcode keys.** Use `dotenv` for local dev, secret managers in production.

### Step 3: Initialize Client (TypeScript)

```typescript
import { createClient } from '@deepgram/sdk';

// Reads DEEPGRAM_API_KEY from env automatically
const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);
```

**SDK v5+ uses a different constructor:**
```typescript
import { DeepgramClient } from '@deepgram/sdk';
const deepgram = new DeepgramClient({ apiKey: process.env.DEEPGRAM_API_KEY });
```

### Step 4: Initialize Client (Python)

```python
from deepgram import DeepgramClient, PrerecordedOptions, LiveOptions
import os

client = DeepgramClient(os.environ["DEEPGRAM_API_KEY"])
```

### Step 5: Verify Connection

```typescript
// TypeScript — list projects to verify key is valid
async function verify() {
  const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);
  const { result, error } = await deepgram.manage.getProjects();
  if (error) {
    console.error('Auth failed:', error.message);
    process.exit(1);
  }
  console.log(`Connected. Projects: ${result.projects.length}`);
  result.projects.forEach(p => console.log(`  - ${p.name} (${p.project_id})`));
}
verify();
```

```python
# Python — verify connection
from deepgram import DeepgramClient
import os

client = DeepgramClient(os.environ["DEEPGRAM_API_KEY"])
response = client.manage.v("1").get_projects()
print(f"Connected. Projects: {len(response.projects)}")
for p in response.projects:
    print(f"  - {p.name} ({p.project_id})")
```

### Step 6: Configure for Production

```typescript
// Singleton client with custom options
import { createClient, DeepgramClient } from '@deepgram/sdk';

let client: DeepgramClient | null = null;

export function getDeepgramClient(): DeepgramClient {
  if (!client) {
    const apiKey = process.env.DEEPGRAM_API_KEY;
    if (!apiKey) throw new Error('DEEPGRAM_API_KEY is required');
    client = createClient(apiKey);
  }
  return client;
}
```

## API Key Scopes

| Scope | Permission | Use Case |
|-------|-----------|----------|
| `member` | Full access | Development only |
| `listen` | STT transcription | Production transcription services |
| `speak` | TTS synthesis | Voice generation services |
| `manage` | Project management | Admin tools |
| `usage` | Usage data | Monitoring dashboards |

Create scoped keys in Console > Settings > API Keys > Create Key.

## Output
- Installed `@deepgram/sdk` (Node.js) or `deepgram-sdk` (Python)
- API key configured via environment variable or `.env`
- Verified connection with project listing
- Singleton client pattern for production use

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired API key | Regenerate key in Console > API Keys |
| `403 Forbidden` | Key lacks required scope | Create new key with correct scopes |
| `MODULE_NOT_FOUND` | SDK not installed | Run `npm install @deepgram/sdk` |
| `ENOTFOUND api.deepgram.com` | Network/DNS issue | Check internet, verify no proxy blocking |
| `TypeError: createClient is not a function` | SDK v5 installed | Use `new DeepgramClient()` instead |

## Resources
- [Deepgram Console](https://console.deepgram.com)
- [JavaScript SDK](https://developers.deepgram.com/docs/js-sdk)
- [Python SDK](https://developers.deepgram.com/docs/node-sdk)
- [API Key Management](https://developers.deepgram.com/docs/api-key-management)
- [SDK Feature Matrix](https://developers.deepgram.com/sdks/sdk-features)

## Next Steps
Proceed to `deepgram-hello-world` for your first transcription.
