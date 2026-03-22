---
name: speak-sdk-patterns
description: |
  Production patterns for Speak language learning API: conversation sessions, pronunciation assessment, audio preprocessing, and batch operations.
  Use when implementing sdk patterns features,
  or troubleshooting Speak language learning integration issues.
  Trigger with phrases like "speak sdk patterns", "speak sdk patterns".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, speak, api]

---
# Speak SDK Patterns

## Overview
Production patterns for Speak language learning API: conversation sessions, pronunciation assessment, audio preprocessing, and batch operations.

## Prerequisites
- Completed `speak-install-auth` setup
- Valid API credentials configured
- ffmpeg installed for audio processing

## Instructions

### Pattern 1: Conversation Session Manager
```typescript
class ConversationManager {
  private client: SpeakClient;
  private sessions: Map<string, SessionState> = new Map();

  async startLesson(language: string, scenario: string, level: string) {
    const session = await this.client.startConversation({
      scenario, language, level, nativeLanguage: 'en',
    });
    this.sessions.set(session.id, {
      turns: [], startTime: Date.now(), language,
    });
    return session;
  }

  async submitResponse(sessionId: string, audioPath: string) {
    const turn = await this.client.sendTurn(sessionId, { audioPath });
    this.sessions.get(sessionId)?.turns.push(turn);
    return turn;
  }

  async endAndReport(sessionId: string) {
    const summary = await this.client.endSession(sessionId);
    const state = this.sessions.get(sessionId)!;
    return {
      ...summary,
      duration: (Date.now() - state.startTime) / 1000,
      totalTurns: state.turns.length,
      avgPronunciation: state.turns.reduce((s, t) =>
        s + (t.pronunciationScore || 0), 0) / state.turns.length,
    };
  }
}
```

### Pattern 2: Audio Preprocessor
```typescript
import { execSync } from 'child_process';

function preprocessAudio(inputPath: string): string {
  const outputPath = inputPath.replace(/\.[^.]+$/, '.processed.wav');
  // Convert to WAV 16kHz mono PCM — required by Speak API
  execSync(
    `ffmpeg -y -i "${inputPath}" -ar 16000 -ac 1 -c:a pcm_s16le "${outputPath}"`,
    { stdio: 'pipe' }
  );
  return outputPath;
}
```

### Pattern 3: Retry with Backoff
```typescript
async function withRetry<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (err: any) {
      if (err.response?.status === 429 && i < maxRetries - 1) {
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

### Pattern 4: Progress Tracker
```typescript
class LearningProgress {
  private history: SessionSummary[] = [];

  addSession(summary: SessionSummary) {
    this.history.push(summary);
  }

  getReport() {
    const recent = this.history.slice(-10);
    return {
      totalSessions: this.history.length,
      avgPronunciation: recent.reduce((s, h) => s + h.avgPronunciationScore, 0) / recent.length,
      totalMinutes: this.history.reduce((s, h) => s + h.durationMinutes, 0),
      vocabularyLearned: [...new Set(this.history.flatMap(h => h.newWords))].length,
    };
  }
}
```

## Output
- Patterns implementation complete
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

**Basic**: Apply sdk patterns with default configuration for a standard Speak integration.

**Advanced**: Customize for production with error recovery, monitoring, and team-specific requirements.
