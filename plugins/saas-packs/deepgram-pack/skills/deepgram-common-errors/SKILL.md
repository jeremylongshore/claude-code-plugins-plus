---
name: deepgram-common-errors
description: |
  Diagnose and fix common Deepgram errors and issues.
  Use when troubleshooting Deepgram API errors, debugging transcription failures,
  or resolving integration issues.
  Trigger: "deepgram error", "deepgram not working", "fix deepgram",
  "deepgram troubleshoot", "transcription failed", "deepgram 401".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, api, debugging, transcription]

---
# Deepgram Common Errors

## Overview
Comprehensive error reference for Deepgram API integration. Covers HTTP error codes, WebSocket errors, transcription quality issues, SDK-specific problems, and audio format debugging with real diagnostic commands.

## Prerequisites
- Deepgram API key configured
- `curl` available for API testing
- Access to application logs

## Instructions

### Step 1: Quick Diagnostic

```bash
# Test API key validity
curl -s -w "\nHTTP %{http_code}\n" \
  'https://api.deepgram.com/v1/projects' \
  -H "Authorization: Token $DEEPGRAM_API_KEY"

# Test transcription endpoint
curl -s -w "\nHTTP %{http_code}\n" \
  -X POST 'https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true' \
  -H "Authorization: Token $DEEPGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://static.deepgram.com/examples/Bueller-Life-moves-702702706.wav"}'
```

### Step 2: HTTP Error Reference

| Code | Error | Cause | Solution |
|------|-------|-------|----------|
| 400 | Bad Request | Invalid audio format, bad params | Check audio headers, validate query params |
| 401 | Unauthorized | Invalid/expired API key | Regenerate in Console > API Keys |
| 403 | Forbidden | Key lacks scope | Create key with `listen` scope for STT |
| 404 | Not Found | Wrong endpoint URL | Use `api.deepgram.com/v1/listen` |
| 408 | Timeout | Audio too long for sync | Use `callback` param for async |
| 413 | Payload Too Large | File exceeds 2GB | Split with `ffmpeg -f segment -segment_time 3600` |
| 429 | Too Many Requests | Concurrency limit hit | Implement backoff, check plan limits |
| 500 | Internal Error | Deepgram server error | Retry with backoff, check status.deepgram.com |
| 502 | Bad Gateway | Upstream failure | Retry after 5-10 seconds |
| 503 | Service Unavailable | Maintenance/overload | Check status.deepgram.com, retry later |

### Step 3: WebSocket Errors

```typescript
import { LiveTranscriptionEvents } from '@deepgram/sdk';

connection.on(LiveTranscriptionEvents.Error, (error) => {
  console.error('WebSocket error:', {
    message: error.message,
    type: error.type,
  });
});

// Common WebSocket issues:
// 1. Connection closes after ~10s of silence
//    Fix: Send keepAlive() every 8 seconds
connection.keepAlive();

// 2. "Could not process audio" errors
//    Fix: Verify encoding matches what you send
//    Must match: encoding, sample_rate, channels in listen.live() options

// 3. Connection refused / ECONNREFUSED
//    Fix: Check firewall allows wss://api.deepgram.com:443

// 4. Immediate disconnect with 1008 (Policy Violation)
//    Fix: API key invalid or lacks live streaming scope
```

### Step 4: Transcription Quality Issues

```bash
# Check audio properties with ffprobe
ffprobe -v quiet -print_format json -show_format -show_streams input.wav

# Optimal audio for Deepgram:
# - Sample rate: 8000-48000 Hz (16000 recommended)
# - Channels: 1 (mono) or 2 (stereo for multichannel)
# - Bit depth: 16-bit
# - Format: WAV, MP3, FLAC, OGG, M4A, WebM

# Fix audio quality
ffmpeg -i noisy.wav \
  -af "highpass=f=200,lowpass=f=3000,volume=2" \
  -ar 16000 -ac 1 -acodec pcm_s16le \
  clean.wav
```

| Quality Issue | Likely Cause | Fix |
|--------------|--------------|-----|
| Empty transcript | No speech / too quiet | Boost volume: `-af "volume=3"` |
| Garbled output | Wrong encoding parameter | Match `encoding` to actual audio format |
| Missing words | Background noise | Apply noise filter before transcription |
| Wrong language | Language not specified | Set `language: 'en'` (or correct ISO code) |
| Low confidence | Poor audio quality | Preprocess to 16kHz mono, noise-reduce |
| Speaker mismatch | Diarization off | Enable `diarize: true` |

### Step 5: SDK-Specific Errors

```typescript
// TypeError: createClient is not a function
// You have SDK v5 installed. Use:
import { DeepgramClient } from '@deepgram/sdk';
const dg = new DeepgramClient({ apiKey: process.env.DEEPGRAM_API_KEY });

// TypeError: Cannot read properties of undefined (reading 'prerecorded')
// v5 uses versioned namespaces:
await dg.listen.v1.media.transcribeUrl(source, options);

// "error": { "message": "..." } in result
// Always check the error field:
const { result, error } = await dg.listen.prerecorded.transcribeUrl(source, opts);
if (error) {
  console.error('Deepgram error:', error.message);
  // Don't try to access result — it may be undefined
}

// Python: deepgram.errors.DeepgramApiError
// Catch with try/except:
try:
    response = client.listen.rest.v("1").transcribe_url(source, options)
except Exception as e:
    print(f"API error: {e}")
```

### Step 6: Retry Pattern for Transient Errors

```typescript
async function transcribeWithRetry(
  client: any,
  source: any,
  options: any,
  maxRetries = 3
) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const { result, error } = await client.listen.prerecorded.transcribeUrl(
        source, options
      );
      if (error) {
        // 429 and 5xx are retryable
        if (error.status === 429 || error.status >= 500) {
          throw new Error(`Retryable: ${error.status}`);
        }
        throw new Error(`Non-retryable: ${error.message}`);
      }
      return result;
    } catch (err: any) {
      if (attempt === maxRetries || !err.message.startsWith('Retryable')) {
        throw err;
      }
      const delay = Math.min(1000 * Math.pow(2, attempt) + Math.random() * 1000, 30000);
      console.log(`Retry ${attempt + 1}/${maxRetries} in ${Math.round(delay)}ms`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

## Output
- API diagnostic curl commands
- HTTP error reference with solutions
- WebSocket error handling patterns
- Audio quality debugging with ffprobe/ffmpeg
- SDK version-specific error fixes
- Retry pattern for transient failures

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `ECONNRESET` | Network interruption | Implement retry with backoff |
| `ETIMEDOUT` | Slow network or large file | Increase timeout, use callback |
| `ERR_INVALID_ARG_TYPE` | Passing string instead of Buffer to transcribeFile | Use `readFileSync(path)` |
| `CORS error` (browser) | API called from client-side | Proxy through your server |

## Resources
- [Deepgram Error Handling](https://developers.deepgram.com/docs/error-handling)
- [API Rate Limits](https://developers.deepgram.com/reference/api-rate-limits)
- [Status Page](https://status.deepgram.com)
- [Deepgram Community](https://github.com/orgs/deepgram/discussions)
