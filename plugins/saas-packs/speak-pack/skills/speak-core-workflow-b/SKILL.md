---
name: speak-core-workflow-b
description: |
  Execute Speak secondary workflow: Pronunciation Training with detailed phoneme analysis.
  Use when implementing pronunciation drills, speech scoring,
  or targeted pronunciation improvement features.
  Trigger with phrases like "speak pronunciation training",
  "speak speech scoring", "secondary speak workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Core Workflow B

## Overview
Secondary workflow for Speak: Detailed pronunciation training with phoneme-level analysis and targeted practice.

## Prerequisites
- Completed `speak-install-auth` setup
- Familiarity with `speak-core-workflow-a`
- Valid API credentials configured
- High-quality audio input capabilities

## Instructions
1. **Complete Workflow Example**
2. **Workflow Comparison**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Detailed phoneme-level scores
- Visual pronunciation guides
- Adaptive practice recommendations
- Progress tracking over time
- Weakness identification

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Audio Too Short | Brief recording | Minimum 0.5s audio |
| Background Noise | Poor recording conditions | Prompt for quieter environment |
| Phoneme Not Detected | Unclear speech | Slow down and articulate |
| Model Loading Failed | Network issue | Retry with fallback |

## Resources
- [Speak Pronunciation API](https://developer.speak.com/api/pronunciation)
- [Phoneme Reference](https://developer.speak.com/docs/phonemes)
- [Audio Recording Best Practices](https://developer.speak.com/docs/audio-quality)

## Next Steps
For common errors, see `speak-common-errors`.

## Examples

### Basic: Pronunciation Assessment with Phoneme Scores
```typescript
import { SpeakClient } from "./speak-client";

const client = new SpeakClient(process.env.SPEAK_API_KEY!);

const result = await client.assessPronunciation({
  audioPath: "./recordings/hello-spanish.wav",
  targetText: "Hola, como estas?",
  language: "es",
  detailLevel: "phoneme",
});

console.log(`Overall score: ${result.score}/100`);
for (const phoneme of result.phonemes) {
  if (phoneme.score < 70) {
    console.log(`  Weak phoneme: "${phoneme.symbol}" — score ${phoneme.score}, tip: ${phoneme.suggestion}`);
  }
}
```

### Advanced: Adaptive Pronunciation Drill Loop
```typescript
async function runPronunciationDrill(client: SpeakClient, phrases: string[], language: string) {
  const weakPoints: Map<string, number[]> = new Map();

  for (const phrase of phrases) {
    const audioPath = await recordStudentAudio(phrase);
    const result = await client.assessPronunciation({
      audioPath,
      targetText: phrase,
      language,
      detailLevel: "phoneme",
    });

    for (const phoneme of result.phonemes.filter((p) => p.score < 70)) {
      const scores = weakPoints.get(phoneme.symbol) || [];
      scores.push(phoneme.score);
      weakPoints.set(phoneme.symbol, scores);
    }

    // Re-drill if overall score is below threshold
    if (result.score < 60) {
      console.log(`Re-drilling: "${phrase}" (score: ${result.score})`);
      const retryAudio = await recordStudentAudio(phrase);
      await client.assessPronunciation({
        audioPath: retryAudio,
        targetText: phrase,
        language,
        detailLevel: "phoneme",
      });
    }
  }

  // Generate weakness report
  const report = [...weakPoints.entries()]
    .map(([phoneme, scores]) => ({
      phoneme,
      avgScore: scores.reduce((a, b) => a + b, 0) / scores.length,
      occurrences: scores.length,
    }))
    .sort((a, b) => a.avgScore - b.avgScore);

  console.log("Pronunciation weakness report:", report);
}
```