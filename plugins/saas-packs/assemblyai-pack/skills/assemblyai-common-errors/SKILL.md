---
name: assemblyai-common-errors
description: |
  Diagnose and fix AssemblyAI common errors and exceptions.
  Use when encountering AssemblyAI errors, debugging failed transcriptions,
  or troubleshooting streaming and LeMUR issues.
  Trigger with phrases like "assemblyai error", "fix assemblyai",
  "assemblyai not working", "debug assemblyai", "transcription failed".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription]
compatible-with: claude-code
---

# AssemblyAI Common Errors

## Overview
Quick reference for the most common AssemblyAI errors across transcription, streaming, and LeMUR APIs with real error messages and solutions.

## Prerequisites
- `assemblyai` package installed
- API key configured
- Access to application logs or console

## Instructions

### Error 1: Authentication Failed

```
Error: Authentication error: Invalid API key
Status: 401
```

**Cause:** API key is missing, invalid, or revoked.

**Solution:**
```bash
# Verify key is set
echo $ASSEMBLYAI_API_KEY

# Test directly
curl -H "Authorization: $ASSEMBLYAI_API_KEY" \
  https://api.assemblyai.com/v2/transcript \
  -X GET
```

---

### Error 2: Transcription Status Error

```json
{ "status": "error", "error": "Download error: unable to download..." }
```

**Cause:** The `audio` URL is not publicly accessible, has expired, or returned non-audio content.

**Solution:**
```typescript
// Verify URL is accessible
const response = await fetch(audioUrl, { method: 'HEAD' });
console.log('Content-Type:', response.headers.get('content-type'));
console.log('Status:', response.status);
// Content-Type should be audio/* or video/*

// For private files, upload directly
const transcript = await client.transcripts.transcribe({
  audio: './local-file.mp3',  // SDK handles upload
});
```

---

### Error 3: Could Not Process Audio

```json
{ "status": "error", "error": "Audio file could not be processed" }
```

**Cause:** Corrupted file, unsupported codec, file too short (<200ms), or audio is entirely silent.

**Solution:**
```bash
# Check file with ffprobe
ffprobe -v quiet -print_format json -show_format -show_streams input.mp3

# Convert to a known-good format
ffmpeg -i input.unknown -ar 16000 -ac 1 -f wav output.wav
```

---

### Error 4: Rate Limit Exceeded

```
Error: Rate limit exceeded
Status: 429
Header: Retry-After: 30
```

**Cause:** Too many concurrent requests. Free tier: 5 streams/min. Paid: 100 streams/min (auto-scales).

**Solution:**
```typescript
import { AssemblyAI } from 'assemblyai';

async function transcribeWithBackoff(audioUrl: string, retries = 3) {
  const client = new AssemblyAI({ apiKey: process.env.ASSEMBLYAI_API_KEY! });

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await client.transcripts.transcribe({ audio: audioUrl });
    } catch (err: any) {
      if (err.status !== 429 || attempt === retries) throw err;
      const delay = Math.pow(2, attempt) * 1000 + Math.random() * 500;
      console.warn(`Rate limited. Retrying in ${delay.toFixed(0)}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
}
```

---

### Error 5: Streaming WebSocket Errors

```
WebSocket error: 4001 Not Authorized
WebSocket error: 4008 Session limit reached
WebSocket error: 4100 Endpoint not found
```

| Code | Meaning | Solution |
|------|---------|----------|
| `4001` | Bad API key or expired token | Refresh token via `client.streaming.createTemporaryToken()` |
| `4008` | Max concurrent streams reached | Wait for existing streams to close |
| `4100` | Wrong WebSocket URL | Use `wss://api.assemblyai.com/v2/realtime/ws` |
| `4010` | Audio too short/no speech | Ensure microphone is capturing audio |

---

### Error 6: LeMUR Errors

```json
{ "error": "Transcript not found" }
{ "error": "Input text exceeds maximum length" }
```

**Cause:** Invalid `transcript_ids` or total audio exceeds 100-hour limit.

**Solution:**
```typescript
// Verify transcript exists before LeMUR call
const transcript = await client.transcripts.get(transcriptId);
if (transcript.status !== 'completed') {
  throw new Error(`Transcript ${transcriptId} status: ${transcript.status}`);
}

// For large inputs, chunk transcript_ids
const chunks = [];
for (let i = 0; i < transcriptIds.length; i += 10) {
  chunks.push(transcriptIds.slice(i, i + 10));
}
for (const chunk of chunks) {
  const { response } = await client.lemur.task({
    transcript_ids: chunk,
    prompt: 'Summarize key points.',
  });
}
```

---

### Error 7: Unsupported Language

```json
{ "status": "error", "error": "Language not supported" }
```

**Cause:** Specified `language_code` is not available for the selected model.

**Solution:**
```typescript
// Use automatic language detection (recommended)
const transcript = await client.transcripts.transcribe({
  audio: audioUrl,
  language_detection: true,  // Auto-detect from 99+ languages
});

console.log('Detected language:', transcript.language_code);
```

---

### Error 8: Word Boost Not Working

**Symptom:** Custom terms are still transcribed incorrectly despite `word_boost`.

**Solution:**
```typescript
const transcript = await client.transcripts.transcribe({
  audio: audioUrl,
  word_boost: ['LeMUR', 'AssemblyAI', 'Nova-3'],  // Max 1000 terms
  boost_param: 'high',  // 'low' | 'default' | 'high'
  speech_model: 'best',  // Word boost works with Best model tier
});
```

## Quick Diagnostic Commands

```bash
# Check API status
curl -s https://status.assemblyai.com/api/v2/status.json | jq '.status.description'

# Test API connectivity
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: $ASSEMBLYAI_API_KEY" \
  https://api.assemblyai.com/v2/transcript

# Check installed SDK version
npm list assemblyai

# Verify env variable
node -e "console.log(process.env.ASSEMBLYAI_API_KEY ? 'SET' : 'NOT SET')"
```

## Error Handling
| Error | HTTP Code | Retryable | Action |
|-------|-----------|-----------|--------|
| Auth error | 401 | No | Fix API key |
| Not found | 404 | No | Check transcript ID |
| Rate limit | 429 | Yes | Exponential backoff |
| Server error | 500-503 | Yes | Retry after delay |
| Download error | N/A | Maybe | Check audio URL accessibility |

## Resources
- [AssemblyAI Status Page](https://status.assemblyai.com)
- [AssemblyAI API Error Codes](https://www.assemblyai.com/docs/api-reference/overview)
- [AssemblyAI Support](https://support.assemblyai.com)

## Next Steps
For comprehensive debugging, see `assemblyai-debug-bundle`.
