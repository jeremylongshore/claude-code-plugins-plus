---
name: speak-rate-limits
description: |
  Handle Speak API rate limits with exponential backoff, request queuing, and optimization strategies.
  Use when implementing rate limits features,
  or troubleshooting Speak language learning integration issues.
  Trigger with phrases like "speak rate limits", "speak rate limits".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, speak, api]

---
# Speak Rate Limits

## Overview
Handle Speak API rate limits with exponential backoff, request queuing, and optimization strategies.

## Prerequisites
- Completed `speak-install-auth` setup
- Valid API credentials configured
- Understanding of Speak API patterns

## Instructions

### Rate Limit Overview
| Tier | Assessments/min | Conversations/min | Audio upload/min |
|------|----------------|-------------------|-----------------|
| Free | 10 | 5 | 10 |
| Pro | 60 | 30 | 60 |
| Enterprise | 300 | 150 | 300 |

### Rate-Limited Client
```typescript
class RateLimitedSpeakClient {
  private lastRequest = 0;
  private minDelay: number;

  constructor(private client: SpeakClient, requestsPerMinute: number = 60) {
    this.minDelay = 60000 / requestsPerMinute;
  }

  private async throttle() {
    const elapsed = Date.now() - this.lastRequest;
    if (elapsed < this.minDelay) {
      await new Promise(r => setTimeout(r, this.minDelay - elapsed));
    }
    this.lastRequest = Date.now();
  }

  async assessPronunciation(config: PronunciationConfig) {
    await this.throttle();
    return this.retryOn429(() => this.client.assessPronunciation(config));
  }

  private async retryOn429<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await fn();
      } catch (err: any) {
        if (err.response?.status === 429 && i < maxRetries - 1) {
          const wait = parseInt(err.response.headers['retry-after'] || String(2 ** i));
          console.log(`Rate limited. Waiting ${wait}s...`);
          await new Promise(r => setTimeout(r, wait * 1000));
          continue;
        }
        throw err;
      }
    }
    throw new Error('Max retries exceeded');
  }
}
```

### Batch Assessment Queue
```typescript
async function batchAssess(client: RateLimitedSpeakClient, recordings: Recording[]) {
  const results = [];
  for (const rec of recordings) {
    const result = await client.assessPronunciation({
      audioPath: rec.path, targetText: rec.text, language: rec.lang,
    });
    results.push({ ...rec, score: result.score });
    console.log(`Assessed "${rec.text}": ${result.score}/100`);
  }
  return results;
}
```

## Output
- Limits implementation complete
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

**Basic**: Apply rate limits with default configuration for a standard Speak integration.

**Advanced**: Customize for production with error recovery, monitoring, and team-specific requirements.
