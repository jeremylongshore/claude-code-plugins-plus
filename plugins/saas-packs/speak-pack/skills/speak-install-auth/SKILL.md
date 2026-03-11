---
name: speak-install-auth
description: |
  Install and configure Speak Language Learning SDK/API authentication.
  Use when setting up a new Speak integration, configuring API keys,
  or initializing Speak services in your language learning application.
  Trigger with phrases like "install speak", "setup speak",
  "speak auth", "configure speak API key", "speak language learning setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Install & Auth

## Overview
Set up Speak Language Learning SDK/API and configure authentication credentials for AI-powered language tutoring integration.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Speak developer account with API access
- API key from Speak developer dashboard

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Node.js
npm install @speak/language-sdk

# Python
pip install speak-language-sdk

# Alternative: Using OpenAI-compatible API
npm install openai  # Speak uses OpenAI's real-time API
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export SPEAK_API_KEY="your-api-key"
export SPEAK_APP_ID="your-app-id"

# Or create .env file
echo 'SPEAK_API_KEY=your-api-key' >> .env
echo 'SPEAK_APP_ID=your-app-id' >> .env
```

### Step 3: Initialize Client
```typescript
// src/speak/client.ts
import { SpeakClient } from '@speak/language-sdk';

const client = new SpeakClient({
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
  language: 'ko', // Target language: Korean, Spanish (es), Japanese (ja), etc.
});
```

### Step 4: Verify Connection
```typescript
async function verifyConnection() {
  try {
    const status = await client.health.check();
    console.log('Speak connection verified:', status);
    return true;
  } catch (error) {
    console.error('Connection failed:', error);
    return false;
  }
}
```

## Supported Languages
| Language | Code | Status |
|----------|------|--------|
| English | en | Available |
| Spanish | es | Available |
| French | fr | Available |
| German | de | Available |
| Portuguese (BR) | pt-BR | Available |
| Korean | ko | Available |
| Japanese | ja | Available |
| Mandarin (Traditional) | zh-TW | Available |
| Mandarin (Simplified) | zh-CN | Available |
| Indonesian | id | Available |

## Output
- Installed SDK package in node_modules or site-packages
- Environment variable or .env file with API credentials
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Verify key in Speak developer dashboard |
| App ID Mismatch | Wrong application identifier | Check app ID in project settings |
| Rate Limited | Exceeded quota | Check usage at developer.speak.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup with Speech Recognition
```typescript
import { SpeakClient, SpeechRecognizer } from '@speak/language-sdk';

const client = new SpeakClient({
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
  language: 'es',
});

const recognizer = new SpeechRecognizer(client, {
  onSpeechResult: (result) => {
    console.log('User said:', result.transcript);
    console.log('Pronunciation score:', result.pronunciationScore);
  },
  onError: (error) => console.error('Speech error:', error),
});
```

### Python Setup
```python
import os
from speak_sdk import SpeakClient, LessonSession

client = SpeakClient(
    api_key=os.environ.get('SPEAK_API_KEY'),
    app_id=os.environ.get('SPEAK_APP_ID'),
    language='ja'  # Japanese
)

# Verify connection
status = client.health.check()
print(f"Connected: {status.healthy}")
```

## Resources
- [Speak Developer Documentation](https://developer.speak.com/docs)
- [Speak API Reference](https://developer.speak.com/api)
- [Speak Status Page](https://status.speak.com)
- [OpenAI Real-time API (used by Speak)](https://platform.openai.com/docs/guides/realtime)

## Next Steps
After successful auth, proceed to `speak-hello-world` for your first lesson session.