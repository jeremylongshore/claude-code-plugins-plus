# Speak Common Errors - Implementation Guide

Detailed implementation reference for the speak-common-errors skill.

## Instructions

### Step 1: Identify the Error
Check error message and code in your logs or console.

### Step 2: Find Matching Error Below
Match your error to one of the documented cases.

### Step 3: Apply Solution
Follow the solution steps for your specific error.


## Quick Diagnostic Commands

```bash
# Check Speak service status
curl -s https://status.speak.com/api/status | jq

# Verify API connectivity
curl -X POST https://api.speak.com/v1/health \
  -H "Authorization: Bearer ${SPEAK_API_KEY}" \
  -H "X-App-ID: ${SPEAK_APP_ID}"

# Check local configuration
env | grep SPEAK

# List active sessions (if CLI available)
speak sessions list --status active
```


## Escalation Path
1. Collect evidence with `speak-debug-bundle`
2. Check Speak status page: https://status.speak.com
3. Contact support with request ID from error


## Error Reference
### 1. Authentication Failed
**Error Message:**
```
SpeakAuthError: Invalid API key or App ID
Code: AUTH_001
```

**Cause:** API key is missing, expired, or invalid. App ID mismatch.

**Solution:**
```bash
# Verify API key is set
echo $SPEAK_API_KEY
echo $SPEAK_APP_ID

# Test authentication
curl -X POST https://api.speak.com/v1/health \
  -H "Authorization: Bearer ${SPEAK_API_KEY}" \
  -H "X-App-ID: ${SPEAK_APP_ID}"
```

---

### 2. Rate Limit Exceeded
**Error Message:**
```
SpeakRateLimitError: Rate limit exceeded. Retry after 60 seconds.
Code: RATE_001
Headers: X-RateLimit-Reset: 1699876543
```

**Cause:** Too many API requests in a short period.

**Solution:**
Implement exponential backoff. See `speak-rate-limits` skill.

```typescript
// Quick fix: Add delay between requests
await new Promise(resolve => setTimeout(resolve, 1000));
```

---

### 3. Audio Processing Failed
**Error Message:**
```
SpeakAudioError: Invalid audio format or corrupted audio data
Code: AUDIO_001
```

**Cause:** Audio file is in wrong format, too short, or corrupted.

**Solution:**
```typescript
// Validate audio before sending
function validateAudio(audioData: ArrayBuffer): boolean {
  // Check minimum length (0.5 seconds at 16kHz = 16000 samples)
  if (audioData.byteLength < 16000) {
    console.error('Audio too short');
    return false;
  }

  // Check format (WAV header magic number)
  const view = new DataView(audioData);
  const magic = String.fromCharCode(
    view.getUint8(0), view.getUint8(1),
    view.getUint8(2), view.getUint8(3)
  );
  if (magic !== 'RIFF') {
    console.error('Invalid audio format (expected WAV)');
    return false;
  }

  return true;
}
```

**Supported formats:**
- WAV (PCM, 16-bit, mono, 16kHz) - Recommended
- MP3 (128kbps minimum)
- WebM (Opus codec)

---

### 4. Session Expired
**Error Message:**
```
SpeakSessionError: Session expired or not found
Code: SESSION_001
SessionId: sess_abc123
```

**Cause:** Lesson session timed out or was ended.

**Solution:**
```typescript
// Check session status before operations
async function safeSessionOperation(
  session: LessonSession,
  operation: () => Promise<any>
) {
  const status = await session.getStatus();

  if (status === 'expired' || status === 'ended') {
    // Start new session
    console.log('Session expired, starting new session...');
    return await startNewSession();
  }

  return await operation();
}
```

---

### 5. Language Not Supported
**Error Message:**
```
SpeakLanguageError: Language 'xyz' is not supported
Code: LANG_001
```

**Cause:** Requested language code is invalid or not available.

**Solution:**
```typescript
const SUPPORTED_LANGUAGES = [
  'en', 'es', 'fr', 'de', 'pt-BR',
  'ko', 'ja', 'zh-TW', 'zh-CN', 'id'
];

function validateLanguage(lang: string): boolean {
  if (!SUPPORTED_LANGUAGES.includes(lang)) {
    console.error(`Unsupported language: ${lang}`);
    console.log(`Supported: ${SUPPORTED_LANGUAGES.join(', ')}`);
    return false;
  }
  return true;
}
```

---

### 6. Speech Recognition Failed
**Error Message:**
```
SpeakRecognitionError: Could not recognize speech
Code: RECOGNITION_001
Confidence: 0.12
```

**Cause:** Audio quality too poor, background noise, or unclear speech.

**Solution:**
```typescript
// Check recognition confidence
async function recognizeWithRetry(
  client: SpeakClient,
  audioData: ArrayBuffer,
  minConfidence: number = 0.5
): Promise<RecognitionResult> {
  const result = await client.speech.recognize(audioData);

  if (result.confidence < minConfidence) {
    console.log('Low confidence. Please try again with clearer speech.');
    throw new Error('Recognition confidence too low');
  }

  return result;
}
```

**Tips for better recognition:**
- Use a high-quality microphone
- Reduce background noise
- Speak clearly and at normal pace
- Maintain consistent distance from mic

---

### 7. Network Timeout
**Error Message:**
```
SpeakNetworkError: Request timeout after 30000ms
Code: NETWORK_001
```

**Cause:** Network connectivity or server latency issues.

**Solution:**
```typescript
// Increase timeout for large audio files
const client = new SpeakClient({
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
  timeout: 60000, // 60 seconds
  retries: 3,
});
```

---

### 8. Quota Exceeded
**Error Message:**
```
SpeakQuotaError: Monthly API quota exceeded
Code: QUOTA_001
Usage: 100000/100000
```

**Cause:** Exceeded monthly API call limit for your plan.

**Solution:**
```typescript
// Monitor usage before operations
async function checkQuota(client: SpeakClient): Promise<boolean> {
  const usage = await client.account.getUsage();

  console.log(`Usage: ${usage.current}/${usage.limit}`);
  console.log(`Remaining: ${usage.remaining}`);

  if (usage.remaining < 100) {
    console.warn('Low quota warning!');
  }

  return usage.remaining > 0;
}
```

---

### 9. Invalid Response Format
**Error Message:**
```
SpeakParseError: Invalid response from AI tutor
Code: PARSE_001
```

**Cause:** AI tutor returned unexpected response format.

**Solution:**
```typescript
// Validate tutor responses
function validateTutorResponse(response: any): TutorResponse {
  const required = ['text', 'type'];

  for (const field of required) {
    if (!(field in response)) {
      throw new Error(`Missing required field: ${field}`);
    }
  }

  return response as TutorResponse;
}
```

---

### 10. Concurrent Session Limit
**Error Message:**
```
SpeakLimitError: Maximum concurrent sessions reached
Code: LIMIT_001
MaxSessions: 5
CurrentSessions: 5
```

**Cause:** Too many active sessions for your account.

**Solution:**
```typescript
// Clean up old sessions before starting new ones
async function ensureSessionSlot(
  client: SpeakClient
): Promise<void> {
  const sessions = await client.sessions.list({ status: 'active' });

  if (sessions.length >= 5) {
    // End oldest session
    const oldest = sessions.sort((a, b) =>
      a.createdAt.getTime() - b.createdAt.getTime()
    )[0];

    await oldest.end();
    console.log(`Ended old session: ${oldest.id}`);
  }
}
```
