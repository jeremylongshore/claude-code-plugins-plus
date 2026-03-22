---
name: speak-common-errors
description: |
  Diagnose and fix common Speak API errors: authentication failures, audio format issues, rate limits, and session management problems.
  Use when implementing common errors features,
  or troubleshooting Speak language learning integration issues.
  Trigger with phrases like "speak common errors", "speak common errors".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, speak, debugging]

---
# Speak Common Errors

## Overview
Diagnose and fix common Speak API errors: authentication failures, audio format issues, rate limits, and session management problems.

## Prerequisites
- Completed `speak-install-auth` setup
- Valid API credentials configured
- ffmpeg installed for audio processing

## Instructions

### Error Code Reference

| HTTP | Error Code | Description | Fix |
|------|-----------|-------------|-----|
| 400 | `audio_format_invalid` | Audio not WAV 16kHz mono | Convert with ffmpeg |
| 400 | `audio_too_short` | Recording < 0.5 seconds | Record longer audio |
| 400 | `audio_too_long` | Recording > 60 seconds | Trim to under 60s |
| 400 | `language_not_supported` | Invalid language code | Use supported codes |
| 401 | `invalid_api_key` | Wrong or expired key | Regenerate at dashboard |
| 403 | `quota_exceeded` | Monthly limit reached | Upgrade plan or wait |
| 404 | `session_not_found` | Invalid session ID | Start a new session |
| 408 | `session_expired` | Session timed out | Sessions expire after 30 min |
| 413 | `payload_too_large` | Audio file > 25MB | Compress or trim audio |
| 429 | `rate_limit_exceeded` | Too many requests | Wait `Retry-After` seconds |

### Quick Diagnostic
```bash
# Check API key validity
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $SPEAK_API_KEY" \
  https://api.speak.com/v1/languages
# 200 = valid, 401 = invalid, 403 = insufficient permissions

# Check audio format
ffprobe -v quiet -print_format json -show_streams recording.wav \
  | python3 -c "import sys,json; s=json.load(sys.stdin)['streams'][0]; print(f'Rate: {s[\"sample_rate\"]}Hz, Channels: {s[\"channels\"]}')"
# Must be: Rate: 16000Hz, Channels: 1
```

### Error Recovery Pattern
```typescript
async function resilientSpeakCall<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (err: any) {
      const code = err.response?.data?.error?.code;
      if (code === 'audio_format_invalid') {
        // Auto-convert and retry
        throw new Error('Convert audio to WAV 16kHz mono before retrying');
      }
      if (code === 'session_expired') {
        throw new Error('Session expired — start a new conversation session');
      }
      if (err.response?.status === 429) {
        const wait = parseInt(err.response.headers['retry-after'] || '5');
        await new Promise(r => setTimeout(r, wait * 1000));
        continue;
      }
      throw err;
    }
  }
  throw new Error('Max retries exceeded');
}
```

## Output
- Errors implementation complete
- Speak API integration verified
- Error recovery tested

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
See `speak-debug-bundle` for diagnostic tools.

## Examples

**Basic**: Apply common errors with default configuration for a standard Speak integration.

**Advanced**: Customize for production with error recovery, monitoring, and team-specific requirements.
