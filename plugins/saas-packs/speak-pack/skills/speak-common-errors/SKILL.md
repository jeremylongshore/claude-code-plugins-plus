---
name: speak-common-errors
description: |
  Diagnose and fix Speak common errors and exceptions.
  Use when encountering Speak errors, debugging failed sessions,
  or troubleshooting language learning integration issues.
  Trigger with phrases like "speak error", "fix speak",
  "speak not working", "debug speak", "speak lesson failed".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Common Errors

## Overview
Quick reference for the top 10 most common Speak errors and their solutions.

## Prerequisites
- Speak SDK installed
- API credentials configured
- Access to error logs

## Instructions
1. **Quick Diagnostic Commands**
2. **Escalation Path**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Error | Solution |
|-------|----------|
| Authentication Failed | See implementation guide |
| Rate Limit Exceeded | See implementation guide |
| Audio Processing Failed | See implementation guide |
| Session Expired | See implementation guide |
| Language Not Supported | See implementation guide |
| Speech Recognition Failed | See implementation guide |
| Network Timeout | See implementation guide |
| Quota Exceeded | See implementation guide |

## Resources
- [Speak Status Page](https://status.speak.com)
- [Speak Support](https://support.speak.com)
- [Speak Error Codes](https://developer.speak.com/docs/errors)

## Next Steps
For comprehensive debugging, see `speak-debug-bundle`.

## Output

- Identified error root cause with matching error code
- Corrected configuration or code fix applied
- Verification that the fix resolves the error (e.g., successful API call)

See [debugging implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Examples

### Basic: Diagnose and Fix Authentication Errors
```bash
# Check if API key is set and valid
echo "SPEAK_API_KEY length: ${#SPEAK_API_KEY}"
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $SPEAK_API_KEY" \
  https://api.speak.com/v1/languages
# 200 = valid, 401 = invalid/expired, 403 = wrong permissions
```

```typescript
// Wrap Speak calls with error classification
async function withSpeakErrorHandling<T>(fn: () => Promise<T>): Promise<T> {
  try {
    return await fn();
  } catch (err: any) {
    const status = err.response?.status;
    const code = err.response?.data?.error?.code;
    switch (status) {
      case 401: throw new Error("Auth failed — check SPEAK_API_KEY");
      case 429: throw new Error(`Rate limited — retry after ${err.response.headers["retry-after"]}s`);
      case 400:
        if (code === "audio_format_invalid") throw new Error("Convert audio to WAV 16kHz mono");
        if (code === "language_not_supported") throw new Error(`Language "${err.response.data.error.lang}" not available`);
        throw err;
      default: throw err;
    }
  }
}
```

### Advanced: Structured Error Recovery with Retry and Fallback
```typescript
const ERROR_RECOVERY: Record<string, (ctx: any) => Promise<void>> = {
  "audio_format_invalid": async (ctx) => {
    // Auto-convert to supported format using ffmpeg
    const { execSync } = require("child_process");
    const wavPath = ctx.audioPath.replace(/\.\w+$/, ".wav");
    execSync(`ffmpeg -y -i "${ctx.audioPath}" -ar 16000 -ac 1 "${wavPath}"`);
    ctx.audioPath = wavPath;
  },
  "session_expired": async (ctx) => {
    // Re-create the session transparently
    ctx.session = await ctx.client.startConversation(ctx.sessionConfig);
  },
  "rate_limit_exceeded": async (ctx) => {
    const wait = parseInt(ctx.retryAfter || "5", 10);
    await new Promise((r) => setTimeout(r, wait * 1000));
  },
};

async function resilientSpeakCall<T>(fn: () => Promise<T>, ctx: any, maxRetries = 3): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (err: any) {
      const code = err.response?.data?.error?.code;
      const recovery = ERROR_RECOVERY[code];
      if (recovery && i < maxRetries - 1) {
        ctx.retryAfter = err.response?.headers?.["retry-after"];
        await recovery(ctx);
      } else {
        throw err;
      }
    }
  }
  throw new Error("Max retries exceeded");
}
```