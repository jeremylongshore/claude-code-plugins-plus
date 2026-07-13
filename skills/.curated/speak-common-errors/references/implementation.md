# Speak Common Errors - Implementation

## 401 / 403 — Authentication

```typescript
// Validate key before use
const apiKey = process.env.SPEAK_API_KEY;
if (!apiKey) throw new Error('SPEAK_API_KEY environment variable not set');
const client = new SpeakClient({ apiKey });
```

## 429 — Rate Limit Retry

```typescript
async function withRetry<T>(fn: () => Promise<T>, retries = 3): Promise<T> {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (err: any) {
      if (err.status !== 429 || i === retries - 1) throw err;
      const wait = parseInt(err.headers?.['retry-after'] ?? '5') * 1000;
      console.log(`Rate limited. Retrying in ${wait}ms...`);
      await new Promise(r => setTimeout(r, wait));
    }
  }
  throw new Error('Max retries exceeded');
}

// Usage
const result = await withRetry(() => client.transcribe(audioBuffer));
```

## 413 / 415 — File Issues

```typescript
const SUPPORTED = ['mp3', 'mp4', 'wav', 'm4a', 'ogg', 'webm'];
const MAX_SIZE_MB = 100;

function validateFile(filename: string, sizeBytes: number): void {
  const ext = filename.split('.').pop()?.toLowerCase();
  if (!ext || !SUPPORTED.includes(ext)) {
    throw new Error(`Format not supported: ${ext}. Supported: ${SUPPORTED.join(', ')}`);
  }
  if (sizeBytes > MAX_SIZE_MB * 1024 * 1024) {
    throw new Error(`File too large: ${(sizeBytes/1024/1024).toFixed(1)}MB > ${MAX_SIZE_MB}MB limit`);
  }
}
```

## Timeout Handling

```typescript
const controller = new AbortController();
setTimeout(() => controller.abort(), 120_000); // 2-min timeout

try {
  const result = await client.transcribe(audio, { signal: controller.signal });
  return result;
} catch (err: any) {
  if (err.name === 'AbortError') throw new Error('Transcription timed out after 2 minutes');
  throw err;
}
```

## Error Reference

| Code | Cause | Fix |
|------|-------|-----|
| 401 | Invalid/missing API key | Check SPEAK_API_KEY |
| 403 | Insufficient permissions | Upgrade plan |
| 413 | File exceeds size limit | Compress or split audio |
| 415 | Unsupported audio format | Convert to mp3 or wav |
| 429 | Rate limit exceeded | Retry with backoff |
| 503 | Service unavailable | Retry after 30s |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
