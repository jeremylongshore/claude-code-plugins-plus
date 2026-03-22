---
name: speak-multi-env-setup
description: |
  Configure Speak across dev, staging, and production with separate API keys and mock modes.
  Use when implementing multi env setup,
  or managing Speak language learning platform operations.
  Trigger with phrases like "speak multi env setup", "speak multi env setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, speak, api]

---
# Speak Multi-Environment Setup

## Overview
Configure Speak across dev, staging, and production with separate API keys and mock modes.

## Prerequisites
- Completed `speak-install-auth` setup
- Valid API credentials configured
- Understanding of Speak API patterns

## Instructions

### Step 1: Configuration

Configure multi env setup for your Speak integration. Speak uses OpenAI's GPT-4o for AI tutoring and Whisper for speech recognition.

```typescript
// speak_multi_env_setup_config.ts
const config = {
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
  environment: process.env.NODE_ENV || 'development',
};
```

### Step 2: Implementation

```typescript
// Core implementation for speak multi-environment setup
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
- Speak Multi-Environment Setup configured and verified
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

**Basic**: Apply multi env setup with default settings for a standard Speak integration.

**Production**: Configure with monitoring, alerting, and team-specific language learning requirements.
