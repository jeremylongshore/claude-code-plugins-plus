---
name: speak-upgrade-migration
description: |
  Upgrade Speak SDK versions, migrate between language learning platforms, and handle API version changes.
  Use when implementing upgrade migration features,
  or troubleshooting Speak language learning integration issues.
  Trigger with phrases like "speak upgrade migration", "speak upgrade migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, speak, api]

---
# Speak Upgrade & Migration

## Overview
Upgrade Speak SDK versions, migrate between language learning platforms, and handle API version changes.

## Prerequisites
- Completed `speak-install-auth` setup
- Valid API credentials configured
- Understanding of Speak API patterns

## Instructions

## Current State
!`npm list @speak/language-sdk 2>/dev/null || echo 'Speak SDK not installed'`

### Step 1: Check Current Version
```bash
npm list @speak/language-sdk
npm outdated @speak/language-sdk
```

### Step 2: Upgrade SDK
```bash
npm install @speak/language-sdk@latest
npm test  # Run tests to verify compatibility
```

### Step 3: API Version Migration
```typescript
// Check for deprecated endpoints
const DEPRECATED_ENDPOINTS = [
  '/v1/lessons/start',      // Replaced by /v1/conversations/start
  '/v1/speech/score',       // Replaced by /v1/pronunciation/assess
];

// Migration map
const ENDPOINT_MIGRATION = {
  '/v1/lessons/start': '/v1/conversations/start',
  '/v1/speech/score': '/v1/pronunciation/assess',
};
```

### Step 4: Platform Migration (from Duolingo/Babbel APIs)
```typescript
// Map learning data between platforms
interface MigrationMapper {
  mapProficiencyLevel(source: string): 'beginner' | 'intermediate' | 'advanced';
  mapLanguageCode(source: string): string;
  mapProgress(source: any): SpeakProgress;
}

const duolingoMapper: MigrationMapper = {
  mapProficiencyLevel(crowns: string) {
    const c = parseInt(crowns);
    if (c < 3) return 'beginner';
    if (c < 6) return 'intermediate';
    return 'advanced';
  },
  mapLanguageCode: (code) => code, // Same ISO codes
  mapProgress: (duo) => ({
    vocabulary: duo.words_learned,
    level: duolingoMapper.mapProficiencyLevel(duo.crowns),
  }),
};
```

### Post-Upgrade Verification
```bash
npm test
node -e "const s = require('@speak/language-sdk'); console.log('SDK version:', s.version || 'loaded OK')"
```

## Output
- Migration implementation complete
- Speak API integration verified
- Production-ready patterns applied

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Verify SPEAK_API_KEY environment variable |
| 429 Rate Limited | Too many requests | Wait Retry-After seconds, use backoff |
| Audio format error | Wrong codec/sample rate | Convert to WAV 16kHz mono with ffmpeg |
| Session expired | Timeout after 30 min | Start a new conversation session |

## Resources
- [Speak Website](https://speak.com)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [Speak GPT-4 Blog](https://speak.com/blog/speak-gpt-4)

## Next Steps
See `speak-prod-checklist` for production readiness.

## Examples

**Basic**: Apply upgrade migration with default configuration for a standard Speak integration.

**Advanced**: Customize for production with error recovery, monitoring, and team-specific requirements.
