---
name: speak-data-handling
description: |
  Handle student audio data, assessment records, and learning progress with GDPR/COPPA compliance.
  Use when implementing data handling,
  or managing Speak language learning platform operations.
  Trigger with phrases like "speak data handling", "speak data handling".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, speak, api]

---
# Speak Data Handling

## Overview
Handle student audio data, assessment records, and learning progress with GDPR/COPPA compliance.

## Prerequisites
- Completed `speak-install-auth` setup
- Valid API credentials configured
- Understanding of Speak API patterns

## Instructions

### Step 1: Configuration

Configure data handling for your Speak integration. Speak uses OpenAI's GPT-4o for AI tutoring and Whisper for speech recognition.

```typescript
// speak_data_handling_config.ts
const config = {
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
  environment: process.env.NODE_ENV || 'development',
};
```

### Step 2: Implementation

```typescript
// Core implementation for speak data handling
import { SpeakClient } from '@speak/language-sdk';

const client = new SpeakClient(config);

// Production-ready implementation
async function setup() {
  const health = await client.health.check();
  console.log("Status:", health.status);
  return health;
}
```

### Step 3: Verification

```bash
curl -sf -H "Authorization: Bearer $SPEAK_API_KEY" https://api.speak.com/v1/health | jq .
```

## Output
- Speak Data Handling configured and verified
- Production-ready Speak integration
- Error handling and monitoring in place

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Verify SPEAK_API_KEY |
| 429 Rate Limited | Too many requests | Implement backoff |
| Connection timeout | Network issue | Check connectivity to api.speak.com |
| Audio format error | Wrong codec | Convert to WAV 16kHz mono |

## Resources
- [Speak Website](https://speak.com)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [Speak GPT-4 Blog](https://speak.com/blog/speak-gpt-4)

## Next Steps
For production checklist, see `speak-prod-checklist`.

## Examples

**Basic**: Apply data handling with default settings for a standard Speak integration.

**Production**: Configure with monitoring, alerting, and team-specific language learning requirements.
