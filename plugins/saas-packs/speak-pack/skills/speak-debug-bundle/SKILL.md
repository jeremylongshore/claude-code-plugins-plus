---
name: speak-debug-bundle
description: |
  Collect diagnostic information for Speak API issues: auth verification, audio format validation, session inspection, and network testing.
  Use when implementing debug bundle features,
  or troubleshooting Speak language learning integration issues.
  Trigger with phrases like "speak debug bundle", "speak debug bundle".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, speak, debugging]

---
# Speak Debug Bundle

## Overview
Collect diagnostic information for Speak API issues: auth verification, audio format validation, session inspection, and network testing.

## Prerequisites
- Completed `speak-install-auth` setup
- Valid API credentials configured
- ffmpeg installed for audio processing

## Instructions

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`ffmpeg -version 2>/dev/null | head -1 || echo 'ffmpeg not installed'`

### Step 1: Auth Diagnostic
```bash
#!/bin/bash
set -euo pipefail
echo "=== Speak Debug Bundle ==="
echo "Time: $(date -u)"

echo -e "\n--- Auth Check ---"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $SPEAK_API_KEY" \
  https://api.speak.com/v1/languages)
echo "API Key Status: HTTP $STATUS"
[ "$STATUS" = "200" ] && echo "  Auth: OK" || echo "  Auth: FAILED"

echo -e "\n--- Environment ---"
echo "SPEAK_API_KEY set: $([ -n \"${SPEAK_API_KEY:-}\" ] && echo 'yes' || echo 'no')"
echo "SPEAK_APP_ID set: $([ -n \"${SPEAK_APP_ID:-}\" ] && echo 'yes' || echo 'no')"
```

### Step 2: Audio Format Validator
```typescript
import { execSync } from 'child_process';

function validateAudio(filePath: string): { valid: boolean; issues: string[] } {
  const issues: string[] = [];
  try {
    const info = JSON.parse(execSync(
      `ffprobe -v quiet -print_format json -show_streams "${filePath}"`,
      { encoding: 'utf-8' }
    ));
    const stream = info.streams[0];

    if (stream.codec_name !== 'pcm_s16le') issues.push(`Codec: ${stream.codec_name} (need pcm_s16le)`);
    if (parseInt(stream.sample_rate) !== 16000) issues.push(`Sample rate: ${stream.sample_rate} (need 16000)`);
    if (stream.channels !== 1) issues.push(`Channels: ${stream.channels} (need 1/mono)`);

    const size = parseInt(execSync(`stat -f%z "${filePath}"`, { encoding: 'utf-8' }));
    if (size > 25 * 1024 * 1024) issues.push(`File too large: ${(size/1024/1024).toFixed(1)}MB (max 25MB)`);
    if (size < 1000) issues.push('File too small — may be empty or corrupt');
  } catch (e) {
    issues.push(`Cannot read file: ${e}`);
  }
  return { valid: issues.length === 0, issues };
}
```

### Step 3: Network Connectivity
```bash
echo -e "\n--- Network ---"
curl -s -o /dev/null -w "API: HTTP %{http_code} in %{time_total}s\n" \
  -H "Authorization: Bearer $SPEAK_API_KEY" \
  https://api.speak.com/v1/health

curl -s -o /dev/null -w "OpenAI: HTTP %{http_code} in %{time_total}s\n" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

## Output
- Bundle implementation complete
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

**Basic**: Apply debug bundle with default configuration for a standard Speak integration.

**Advanced**: Customize for production with error recovery, monitoring, and team-specific requirements.
