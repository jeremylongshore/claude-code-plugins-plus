---
name: speak-ci-integration
description: |
  GitHub Actions pipeline for Speak integrations with mocked API tests and audio validation.
  Use when implementing ci integration,
  or managing Speak language learning platform operations.
  Trigger with phrases like "speak ci integration", "speak ci integration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, speak, api]

---
# Speak CI Integration

## Overview
GitHub Actions pipeline for Speak integrations with mocked API tests and audio validation.

## Prerequisites
- Completed `speak-install-auth` setup
- Valid API credentials configured
- Understanding of Speak API patterns

## Instructions

### Step 1: Configuration

Configure ci integration for your Speak integration. Speak uses OpenAI's GPT-4o for AI tutoring and Whisper for speech recognition.

```typescript
// speak_ci_integration_config.ts
const config = {
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
  environment: process.env.NODE_ENV || 'development',
};
```

### Step 2: Implementation

```typescript
// Core implementation for speak ci integration
import { SpeakClient } from '@speak/language-sdk';

const client = new SpeakClient(config);

// CI test with mocked responses
async function runCITests() {
  const mockClient = new MockSpeakClient();
  await mockClient.assessPronunciation({ audioPath: "test.wav", targetText: "hello", language: "en" });
  console.log("CI tests passed");
}
```

### Step 3: Verification

```bash
npm test
```

## Output
- Speak CI Integration configured and verified
- CI pipeline with mocked Speak API tests
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
For deployment, see `speak-deploy-integration`.

## Examples

**Basic**: Apply ci integration with default settings for a standard Speak integration.

**Production**: Configure with monitoring, alerting, and team-specific language learning requirements.
