---
name: speak-install-auth
description: |
  Set up Speak language learning API integration and authentication.
  Use when configuring Speak API access, setting up OAuth with OpenAI
  Realtime API for speech, or initializing a language tutoring application.
  Trigger with phrases like "install speak", "setup speak",
  "speak auth", "configure speak API", "speak language learning setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, speak, api, authentication]

---
# Speak Install & Auth

## Overview
Set up the Speak language learning platform integration. Speak uses OpenAI's GPT-4o and Realtime API for AI tutoring with real-time pronunciation feedback. Supports 14+ languages including Korean, Spanish, Japanese, French, and Mandarin.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Speak developer account with API access
- Microphone for speech input testing

## Instructions

### Step 1: Install Dependencies
```bash
set -euo pipefail
# Core Speak SDK
npm install @speak/language-sdk

# Audio processing dependencies
npm install openai          # OpenAI Realtime API for speech
npm install fluent-ffmpeg   # Audio format conversion
npm install node-record-lpcm16  # Microphone capture
```

### Step 2: Configure Authentication
```bash
# Speak API credentials
export SPEAK_API_KEY="your-speak-api-key"
export SPEAK_APP_ID="your-app-id"

# OpenAI key for Realtime API (used by Speak for speech processing)
export OPENAI_API_KEY="your-openai-key"

# Create .env file
cat << 'EOF' >> .env
SPEAK_API_KEY=your-speak-api-key
SPEAK_APP_ID=your-app-id
OPENAI_API_KEY=your-openai-key
EOF
```

### Step 3: Initialize the Client
```typescript
// src/speak/client.ts
import { SpeakClient } from '@speak/language-sdk';

const client = new SpeakClient({
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
  language: 'es', // Target language: es, ko, ja, fr, de, pt, zh, id
});

// Verify connection
async function verifySetup() {
  const languages = await client.getLanguages();
  console.log('Available languages:', languages.map(l => l.code).join(', '));
  const health = await client.health.check();
  console.log('API status:', health.status);
}

verifySetup();
```

### Step 4: Configure Speech Recognition
```typescript
// OpenAI Realtime API for speech-to-text (used by Speak)
import OpenAI from 'openai';

const openai = new OpenAI();

async function transcribeAudio(audioPath: string): Promise<string> {
  const transcription = await openai.audio.transcriptions.create({
    file: fs.createReadStream(audioPath),
    model: 'whisper-1',
    language: 'es', // Match target language
  });
  return transcription.text;
}
```

### Step 5: Supported Languages
| Language | Code | Pronunciation | Conversation |
|----------|------|--------------|-------------|
| Korean | ko | Yes | Yes |
| Spanish | es | Yes | Yes |
| Japanese | ja | Yes | Yes |
| French | fr | Yes | Yes |
| German | de | Yes | Yes |
| Portuguese (BR) | pt | Yes | Yes |
| Mandarin (Simplified) | zh-CN | Yes | Yes |
| English | en | Yes | Yes |
| Indonesian | id | Yes | Yes |

## Output
- Speak SDK installed and configured
- API key and OpenAI credentials set
- Language support verified
- Speech recognition pipeline ready

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Wrong or expired key | Verify at developer.speak.com dashboard |
| App ID Mismatch | Wrong application ID | Check app settings in Speak dashboard |
| OpenAI auth failed | Invalid OpenAI key | Verify at platform.openai.com |
| Module not found | Installation failed | Run `npm install` again |
| Language not supported | Invalid language code | Use codes from supported languages table |

## Resources
- [Speak Website](https://speak.com)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [OpenAI Whisper](https://platform.openai.com/docs/guides/speech-to-text)
- [Speak Blog: GPT-4 Integration](https://speak.com/blog/speak-gpt-4)

## Next Steps
After successful auth, proceed to `speak-hello-world` for your first lesson session.

## Examples

**Quick test**: Set `SPEAK_API_KEY`, initialize the client with `language: 'ko'` for Korean, and call `client.health.check()` to verify connectivity.

**Python setup**: Install `speak-language-sdk` via pip, initialize with `api_key` from environment, and verify with a health check.
