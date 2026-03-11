---
name: twinmind-common-errors
description: |
  Diagnose and fix TwinMind common errors and exceptions.
  Use when encountering transcription errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "twinmind error", "fix twinmind",
  "twinmind not working", "debug twinmind", "transcription failed".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Common Errors

## Overview
Quick reference for the most common TwinMind errors and their solutions.

## Prerequisites
- TwinMind extension or API configured
- Access to error logs or console
- API credentials for testing

## Instructions

### Step 1: Identify the Error
Check error message in console, extension popup, or API response.

### Step 2: Find Matching Error Below
Match your error to one of the documented cases.

### Step 3: Apply Solution
Follow the solution steps for your specific error.

## Error Reference

### Authentication Failed
**Error Message:**
```
Error: Authentication failed - Invalid or expired API key
Status: 401 Unauthorized  # HTTP 401 Unauthorized
```

**Cause:** API key is missing, expired, or incorrect.

**Solution:**
```bash
set -euo pipefail
# Verify API key is set correctly
echo $TWINMIND_API_KEY

# Test authentication
curl -H "Authorization: Bearer $TWINMIND_API_KEY" \
  https://api.twinmind.com/v1/health

# Regenerate key if expired
# Visit: https://twinmind.com/settings/api
```

---

### Microphone Access Denied
**Error Message:**
```
Error: Microphone permission denied
NotAllowedError: Permission denied
```

**Cause:** Browser or OS hasn't granted microphone access.

**Solution:**

Chrome:
```
1. Click lock icon in address bar
2. Site Settings > Microphone > Allow
3. Reload the page
```

macOS:
```bash
# Check current permissions
tccutil list com.google.Chrome

# Reset permissions (requires re-grant)
tccutil reset Microphone com.google.Chrome
```

Windows:
```
Settings > Privacy > Microphone > Allow apps to access microphone
```

---

### Transcription Timeout
**Error Message:**
```
Error: Transcription timeout after 300000ms
RequestTimeoutError: Request exceeded timeout
```

**Cause:** Audio file too large or network issues.

**Solution:**
```typescript
// Increase timeout for large files
const client = new TwinMindClient({
  apiKey: process.env.TWINMIND_API_KEY,
  timeout: 600000, // 10 minutes  # 600000 = configured value
});

// Or use async processing with webhooks
const response = await client.post('/transcribe', {
  audio_url: audioUrl,
  async: true,
  webhook_url: 'https://your-server.com/webhook/twinmind',
});
```

---

### Rate Limit Exceeded
**Error Message:**
```
Error: Rate limit exceeded. Please retry after 60 seconds.
Status: 429 Too Many Requests  # HTTP 429 Too Many Requests
X-RateLimit-Remaining: 0
```

**Cause:** Too many API requests in a short period.

**Solution:**
```typescript
// Implement exponential backoff
async function withBackoff<T>(operation: () => Promise<T>): Promise<T> {
  const maxRetries = 5;
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (error.response?.status !== 429) throw error;  # HTTP 429 Too Many Requests

      const retryAfter = parseInt(error.response.headers['retry-after'] || '60');
      console.log(`Rate limited. Waiting ${retryAfter}s...`);
      await new Promise(r => setTimeout(r, retryAfter * 1000));  # 1000: 1 second in ms
    }
  }
  throw new Error('Max retries exceeded');
}
```

See `twinmind-rate-limits` for detailed rate limiting strategies.

---

### Audio Format Not Supported
**Error Message:**
```
Error: Unsupported audio format
AudioFormatError: Format 'xyz' is not supported
```

**Cause:** Audio file in incompatible format.

**Solution:**
```bash
# Convert to supported format using ffmpeg
ffmpeg -i input.xyz -acodec libmp3lame -q:a 2 output.mp3

# Supported formats: MP3, WAV, M4A, WebM, OGG, FLAC
```

Supported formats:
| Format | Extension | Notes |
|--------|-----------|-------|
| MP3 | .mp3 | Recommended, good compression |
| WAV | .wav | Best quality, larger files |
| M4A | .m4a | iOS recordings |
| WebM | .webm | Browser recordings |
| OGG | .ogg | Open format |
| FLAC | .flac | Lossless audio |

---

### No Audio Detected
**Error Message:**
```
Error: No audio detected in input
TranscriptionError: Empty or silent audio
```

**Cause:** Audio file is silent, corrupted, or too quiet.

**Solution:**
```bash
# Check audio file properties
ffprobe -i audio.mp3 -show_streams -select_streams a

# Check audio levels
ffmpeg -i audio.mp3 -filter:a volumedetect -f null /dev/null

# Amplify quiet audio
ffmpeg -i quiet.mp3 -filter:a "volume=2.0" amplified.mp3
```

---

### Speaker Diarization Failed
**Error Message:**
```
Error: Speaker diarization failed
DiarizationError: Unable to identify distinct speakers
```

**Cause:** Single speaker, overlapping speech, or poor audio quality.

**Solution:**
```typescript
// Retry without diarization
const transcript = await client.transcribe(audioUrl, {
  diarization: false, // Disable diarization
});

// Or provide speaker count hint
const transcript = await client.transcribe(audioUrl, {
  diarization: true,
  expected_speakers: 3, // Help the model
});
```

---

### Calendar Sync Failed
**Error Message:**
```
Error: Calendar sync failed
OAuth2Error: Token expired or revoked
```

**Cause:** Google/Microsoft OAuth token expired.

**Solution:**
```
1. Open TwinMind extension
2. Go to Settings > Integrations
3. Click "Disconnect" for calendar
4. Click "Connect" to re-authorize
5. Grant all requested permissions
```

---

### Summary Generation Failed
**Error Message:**
```
Error: Summary generation failed
GenerationError: Transcript too short for summarization
```

**Cause:** Transcript doesn't have enough content.

**Solution:**
```typescript
// Check transcript length before summarization
const minWordsForSummary = 50;
const wordCount = transcript.text.split(/\s+/).length;

if (wordCount < minWordsForSummary) {
  console.log('Transcript too short for summary');
  return null;
}

const summary = await client.summarize(transcript.id);
```

---

### Extension Not Loading
**Error Message:**
```
Extension error: Unable to establish connection
Chrome error: Extension context invalidated
```

**Cause:** Extension crashed, outdated, or Chrome issue.

**Solution:**
```
1. Disable and re-enable extension:
   chrome://extensions/ > TwinMind > Toggle off/on

2. Clear extension data:
   Right-click extension > Manage Extensions > Clear data

3. Reinstall extension:
   Remove > Visit Chrome Web Store > Reinstall

4. Check for conflicts:
   Disable other extensions temporarily
```

---

### Network Error
**Error Message:**
```
Error: Network request failed
TypeError: Failed to fetch
ERR_CONNECTION_REFUSED
```

**Cause:** Network connectivity issues or firewall blocking.

**Solution:**
```bash
set -euo pipefail
# Test API connectivity
curl -v https://api.twinmind.com/v1/health

# Check if firewall is blocking
telnet api.twinmind.com 443  # 443: HTTPS port

# Test with different DNS
curl --resolve api.twinmind.com:443:$(dig +short api.twinmind.com) \  # HTTPS port
  https://api.twinmind.com/v1/health
```

## Quick Diagnostic Commands

```bash
set -euo pipefail
# Check TwinMind API status
curl -s https://status.twinmind.com/api/v2/status.json | jq '.status'

# Verify API connectivity
curl -I https://api.twinmind.com/v1/health

# Test authentication
curl -H "Authorization: Bearer $TWINMIND_API_KEY" \
  https://api.twinmind.com/v1/me

# Check local environment
env | grep TWINMIND

# Validate audio file
ffprobe -v error -show_format -show_streams audio.mp3
```

## Escalation Path

1. Collect evidence with `twinmind-debug-bundle`
2. Check TwinMind status page: https://status.twinmind.com
3. Search community forum: https://community.twinmind.com
4. Contact support with request ID: support@twinmind.com

## Resources
- [TwinMind Status Page](https://status.twinmind.com)
- [TwinMind Support](https://twinmind.com/support)
- [TwinMind Community](https://community.twinmind.com)
- [Error Code Reference](https://twinmind.com/docs/errors)

## Next Steps
For comprehensive debugging, see `twinmind-debug-bundle`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with debugging |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply twinmind common errors to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind common errors for production environments with multiple constraints and team-specific requirements.