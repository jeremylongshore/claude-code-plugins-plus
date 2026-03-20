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
---
# Speak Core Workflow A

## Overview
Primary workflow for Speak: AI-powered conversation practice with real-time pronunciation feedback and adaptive tutoring.

## Prerequisites
- Completed `speak-install-auth` setup
- Understanding of Speak core concepts
- Valid API credentials configured
- Audio handling capabilities (for speech input)

## Instructions
1. **Complete Workflow Example**
2. **Topic Categories**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Completed conversation practice session
- Real-time pronunciation feedback
- Grammar corrections and suggestions
- Session summary with progress metrics
- Next lesson recommendations

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Session Timeout | Exceeded duration | Auto-end with summary |
| Audio Processing Failed | Invalid audio format | Validate audio before submit |
| Tutor Not Responding | API latency | Implement timeout and retry |
| Recognition Failed | Poor audio quality | Prompt user to re-record |

## Resources
- [Speak Conversation API](https://developer.speak.com/api/conversation)
- [Topic Reference](https://developer.speak.com/docs/topics)
- [Audio Requirements](https://developer.speak.com/docs/audio)

## Next Steps
For pronunciation-focused training, see `speak-core-workflow-b`.

## Examples

### Basic: Start a Conversation Practice Session
```typescript
import { SpeakClient } from "./speak-client";

const client = new SpeakClient(process.env.SPEAK_API_KEY!);

// Start a restaurant ordering scenario in Spanish
const session = await client.startConversation({
  scenario: "ordering-food",
  language: "es",
  level: "intermediate",
});

// Send a student audio turn and get AI tutor feedback
const turn = await client.sendTurn(session.id, "./audio/student-turn-1.wav");
console.log("Tutor response:", turn.tutorText);
console.log("Grammar notes:", turn.corrections);
console.log("Pronunciation score:", turn.pronunciationScore);
```

### Advanced: Multi-Topic Session with Progress Tracking
```typescript
const topics = ["greetings", "directions", "ordering-food"];
const results: SessionResult[] = [];

for (const topic of topics) {
  const session = await client.startConversation({
    scenario: topic,
    language: "es",
    level: "intermediate",
    maxTurns: 6,
    feedbackDetail: "phoneme",
  });

  let turnCount = 0;
  while (!session.isComplete && turnCount < 6) {
    const audioPath = await recordStudentAudio(); // capture mic input
    const turn = await client.sendTurn(session.id, audioPath);
    turnCount++;
    if (turn.pronunciationScore < 60) {
      console.warn(`Low score on turn ${turnCount} — suggest retry`);
    }
  }

  const summary = await client.endSession(session.id);
  results.push({ topic, score: summary.overallScore, turns: turnCount });
}

console.table(results);
```