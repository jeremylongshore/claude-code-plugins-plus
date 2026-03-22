---
name: speak-core-workflow-a
description: |
  Execute Speak primary workflow: AI Conversation Practice with real-time feedback.
  Use when implementing conversation practice features, building AI tutor interactions,
  or core language learning dialogue systems.
  Trigger with phrases like "speak conversation practice",
  "speak AI tutor", "speak dialogue", "primary speak workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, speak, workflow]

---
# Speak Core Workflow A: AI Conversation Practice

## Overview
Primary workflow for Speak: AI-powered conversation practice with real-time pronunciation feedback and adaptive tutoring. Speak uses GPT-4o for conversation generation and OpenAI's Realtime API for speech processing, delivering sub-second response times.

## Prerequisites
- Completed `speak-install-auth` setup
- Valid API credentials configured
- Audio handling capabilities (microphone or pre-recorded files)

## Instructions

### Step 1: Start a Conversation Session

```typescript
import { SpeakClient } from '@speak/language-sdk';

const client = new SpeakClient({
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
  language: 'es',
});

// Start a restaurant ordering scenario in Spanish
const session = await client.startConversation({
  scenario: 'ordering-food',
  language: 'es',
  level: 'intermediate',
  nativeLanguage: 'en',
  maxTurns: 10,
  feedbackDetail: 'phoneme', // 'word' or 'phoneme'
});

console.log('Session started:', session.id);
console.log('AI Tutor:', session.firstPrompt.text);
// "Bienvenido al restaurante. Soy tu camarero. Que le gustaria ordenar?"
```

### Step 2: Send Student Responses

```typescript
// Submit audio for pronunciation scoring
const turn1 = await client.sendTurn(session.id, {
  audioPath: './recordings/student-response-1.wav',
});

console.log('Tutor:', turn1.tutorText);
console.log('Pronunciation:', turn1.pronunciationScore); // 0-100
console.log('Grammar:', turn1.corrections);
// [{original: "yo quiero", suggestion: "quisiera", note: "More polite form for ordering"}]
console.log('Vocabulary:', turn1.vocabularyNotes);
// ["camarero = waiter", "ordenar = to order"]

// Or submit text (skips pronunciation scoring)
const turn2 = await client.sendTurn(session.id, {
  text: 'Quisiera una ensalada y un vaso de agua, por favor.',
});
```

### Step 3: Conversation Loop with Progress Tracking

```typescript
async function runConversationLesson(
  client: SpeakClient,
  scenario: string,
  language: string,
  level: string,
) {
  const session = await client.startConversation({
    scenario, language, level, nativeLanguage: 'en',
  });

  const turns: TurnResult[] = [];
  let isComplete = false;

  while (!isComplete && turns.length < 10) {
    // Display tutor prompt
    const prompt = turns.length === 0
      ? session.firstPrompt.text
      : turns[turns.length - 1].tutorText;
    console.log(`\nTutor: ${prompt}`);

    // Get student audio (mic input or file)
    const audioPath = await recordStudentAudio();

    // Submit and get feedback
    const turn = await client.sendTurn(session.id, { audioPath });
    turns.push(turn);

    // Show feedback
    if (turn.pronunciationScore < 60) {
      console.log(`Pronunciation needs work: ${turn.pronunciationScore}/100`);
      console.log('Try again with this phrase.');
    }
    if (turn.corrections.length > 0) {
      console.log('Grammar notes:', turn.corrections.map(c => c.note).join('; '));
    }

    isComplete = turn.sessionComplete;
  }

  // End session and get summary
  const summary = await client.endSession(session.id);
  return summary;
}
```

### Step 4: Multi-Topic Session

```typescript
const topics = ['greetings', 'directions', 'ordering-food', 'shopping'];
const results: SessionSummary[] = [];

for (const topic of topics) {
  console.log(`\n=== ${topic.toUpperCase()} ===`);
  const summary = await runConversationLesson(client, topic, 'es', 'intermediate');
  results.push(summary);
  console.log(`Score: ${summary.avgPronunciationScore}/100`);
}

// Overall progress report
console.log('\n=== Session Report ===');
console.table(results.map(r => ({
  topic: r.scenario,
  pronunciation: r.avgPronunciationScore,
  grammar: r.grammarAccuracy + '%',
  newWords: r.newWords.length,
  duration: r.durationMinutes + 'min',
})));
```

### Topic Categories
| Category | Scenarios | Level |
|----------|-----------|-------|
| Daily Life | greetings, introductions, weather | Beginner |
| Travel | directions, hotel, airport, transport | Beginner-Intermediate |
| Food & Drink | ordering-food, grocery, cooking | Intermediate |
| Business | meeting, presentation, negotiation | Intermediate-Advanced |
| Social | party, dating, opinions, debate | Advanced |

## Output
- Conversation session with AI tutor
- Real-time pronunciation feedback (0-100 score)
- Grammar corrections and suggestions
- Vocabulary notes for new words
- Session summary with progress metrics

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Session timeout | Exceeded 30 min | Auto-end with summary, start new session |
| Audio processing failed | Invalid format | Convert to WAV 16kHz mono |
| Tutor not responding | API latency | Implement 10s timeout with retry |
| Recognition failed | Poor audio quality | Prompt user to re-record in quiet environment |

## Resources
- [Speak Website](https://speak.com)
- [Speak GPT-4 Blog](https://speak.com/blog/speak-gpt-4)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [Live Roleplays](https://speak.com/blog/live-roleplays)

## Next Steps
For pronunciation-focused training, see `speak-core-workflow-b`.

## Examples

**Quick test**: Start a `greetings` scenario with `level: 'beginner'`, send 3 text responses, end session, and review the summary scores.

**Full lesson**: Run 4 topics in sequence, track pronunciation improvement across topics, and generate a progress report.
