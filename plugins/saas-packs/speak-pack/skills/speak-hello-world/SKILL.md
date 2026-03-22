---
name: speak-hello-world
description: |
  Create your first Speak AI tutoring session with pronunciation feedback.
  Use when starting a new Speak integration, testing your setup,
  or learning basic language learning API patterns.
  Trigger with phrases like "speak hello world", "speak example",
  "speak quick start", "first speak lesson".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, speak, api, testing]

---
# Speak Hello World

## Overview
Create your first AI tutoring session with Speak. Demonstrates conversation practice, pronunciation assessment, and real-time feedback using GPT-4o-powered tutoring.

## Prerequisites
- Completed `speak-install-auth` setup
- Valid API credentials configured
- Microphone access (optional for testing)

## Instructions

### Step 1: Start a Conversation Session
```typescript
import { SpeakClient } from '@speak/language-sdk';

const client = new SpeakClient({
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
  language: 'es',
});

// Start a beginner Spanish lesson
const session = await client.startConversation({
  scenario: 'greetings',
  language: 'es',
  level: 'beginner',
  nativeLanguage: 'en',
});

console.log('Session ID:', session.id);
console.log('AI Tutor:', session.firstPrompt.text);
// Output: "Hola! Bienvenido a tu leccion de espanol. Como te llamas?"
console.log('Audio URL:', session.firstPrompt.audioUrl);
```

### Step 2: Send a Student Response
```typescript
// Submit text response (or audio file for pronunciation scoring)
const turn = await client.sendTurn(session.id, {
  text: 'Hola, me llamo Juan. Mucho gusto.',
  // Or: audioPath: './recordings/response.wav'
});

console.log('Tutor response:', turn.tutorText);
console.log('Pronunciation score:', turn.pronunciationScore); // 0-100
console.log('Grammar corrections:', turn.corrections);
// Output: [{original: "me llamo", suggestion: null, correct: true}]
console.log('Vocabulary notes:', turn.vocabularyNotes);
```

### Step 3: Pronunciation Assessment
```typescript
// Assess pronunciation of a specific phrase
const assessment = await client.assessPronunciation({
  audioPath: './recordings/hola-como-estas.wav',
  targetText: 'Hola, como estas?',
  language: 'es',
  detailLevel: 'phoneme', // 'word' or 'phoneme'
});

console.log(`Overall score: ${assessment.score}/100`);
for (const word of assessment.words) {
  console.log(`  "${word.text}": ${word.score}/100`);
  if (word.phonemes) {
    for (const p of word.phonemes.filter(p => p.score < 70)) {
      console.log(`    Weak phoneme: ${p.symbol} (${p.score}) - ${p.suggestion}`);
    }
  }
}
```

### Step 4: End Session and Review
```typescript
const summary = await client.endSession(session.id);
console.log('Session Summary:');
console.log(`  Duration: ${summary.durationMinutes} min`);
console.log(`  Turns: ${summary.totalTurns}`);
console.log(`  Pronunciation: ${summary.avgPronunciationScore}/100`);
console.log(`  Grammar: ${summary.grammarAccuracy}%`);
console.log(`  New vocabulary: ${summary.newWords.join(', ')}`);
```

## Output
- Working conversation session with AI tutor
- Pronunciation assessment with phoneme-level feedback
- Session summary with learning metrics
- Console output showing scores and corrections

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Session timeout | Exceeded max duration | Start a new session |
| Audio format invalid | Wrong codec or sample rate | Convert to WAV 16kHz mono |
| Language not supported | Invalid language code | Use supported codes (es, ko, ja, fr, de) |
| Low pronunciation score | Background noise | Record in a quiet environment |
| Rate limit exceeded | Too many requests | Wait and retry with backoff |

## Resources
- [Speak Website](https://speak.com)
- [Speak GPT-4 Blog](https://speak.com/blog/speak-gpt-4)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)

## Next Steps
Proceed to `speak-local-dev-loop` for development workflow setup.

## Examples

**Text-only test**: Skip audio and use text responses to test the conversation flow before integrating microphone input.

**Multi-language**: Start sessions in different languages by changing the `language` parameter to `ko` (Korean), `ja` (Japanese), or `fr` (French).
