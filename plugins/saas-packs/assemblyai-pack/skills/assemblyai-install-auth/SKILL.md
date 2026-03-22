---
name: assemblyai-install-auth
description: |
  Install and configure AssemblyAI SDK authentication.
  Use when setting up a new AssemblyAI integration, configuring API keys,
  or initializing the assemblyai npm package in your project.
  Trigger with phrases like "install assemblyai", "setup assemblyai",
  "assemblyai auth", "configure assemblyai API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription]
compatible-with: claude-code
---

# AssemblyAI Install & Auth

## Overview
Install the `assemblyai` npm package and configure API key authentication for transcription, LeMUR, and streaming APIs.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, yarn, or pip)
- AssemblyAI account — sign up at https://www.assemblyai.com/dashboard/signup
- API key from https://www.assemblyai.com/app/account

## Instructions

### Step 1: Install the SDK

```bash
# Node.js (official SDK)
npm install assemblyai

# Python
pip install assemblyai
```

### Step 2: Configure API Key

```bash
# Set environment variable (recommended)
export ASSEMBLYAI_API_KEY="your-api-key-here"

# Or add to .env file
echo 'ASSEMBLYAI_API_KEY=your-api-key-here' >> .env
```

Add to `.gitignore`:
```
.env
.env.local
.env.*.local
```

### Step 3: Initialize the Client

```typescript
// src/assemblyai/client.ts
import { AssemblyAI } from 'assemblyai';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

export default client;
```

### Step 4: Verify Connection

```typescript
// verify-connection.ts
import { AssemblyAI } from 'assemblyai';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

async function verify() {
  // Transcribe a short public audio to confirm everything works
  const transcript = await client.transcripts.transcribe({
    audio: 'https://storage.googleapis.com/aai-web-samples/5_common_sports_702.wav',
  });

  if (transcript.status === 'error') {
    console.error('Transcription failed:', transcript.error);
    process.exit(1);
  }

  console.log('Connection verified. Transcript ID:', transcript.id);
  console.log('Status:', transcript.status);
  console.log('Text preview:', transcript.text?.slice(0, 100));
}

verify().catch(console.error);
```

### Python Setup

```python
import assemblyai as aai
import os

# Configure globally
aai.settings.api_key = os.environ["ASSEMBLYAI_API_KEY"]

# Or pass per-client
transcriber = aai.Transcriber()
transcript = transcriber.transcribe(
    "https://storage.googleapis.com/aai-web-samples/5_common_sports_702.wav"
)
print(transcript.text)
```

## Output
- Installed `assemblyai` package in node_modules or site-packages
- API key stored in environment variable or `.env` file
- Client initialized and connection verified with a test transcription

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Authentication error` | Invalid or missing API key | Verify key at https://www.assemblyai.com/app/account |
| `Cannot find module 'assemblyai'` | SDK not installed | Run `npm install assemblyai` |
| `transcript.status === 'error'` | Invalid audio URL or format | Check audio URL is publicly accessible |
| `ENOTFOUND api.assemblyai.com` | Network/firewall issue | Ensure outbound HTTPS to api.assemblyai.com is allowed |

## Resources
- [AssemblyAI Getting Started](https://www.assemblyai.com/docs/getting-started/transcribe-an-audio-file)
- [AssemblyAI Node SDK](https://github.com/AssemblyAI/assemblyai-node-sdk)
- [AssemblyAI Python SDK](https://github.com/AssemblyAI/assemblyai-python-sdk)
- [API Key Dashboard](https://www.assemblyai.com/app/account)

## Next Steps
After successful auth, proceed to `assemblyai-hello-world` for your first transcription.
