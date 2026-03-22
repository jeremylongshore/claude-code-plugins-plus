---
name: speak-core-workflow-b
description: |
  Execute Speak secondary workflow: Pronunciation Training with phoneme-level analysis.
  Use when implementing pronunciation drills, speech scoring,
  or targeted pronunciation improvement features.
  Trigger with phrases like "speak pronunciation training",
  "speak speech scoring", "speak phoneme analysis".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, speak, voice-ai, workflow]

---
# Speak Core Workflow B: Pronunciation Training

## Overview
Secondary workflow for Speak: detailed pronunciation training with phoneme-level analysis and adaptive practice. Uses OpenAI's speech recognition with Speak's proprietary proficiency graph to identify and drill weak phonemes.

## Prerequisites
- Completed `speak-core-workflow-a`
- Audio recording capability (WAV 16kHz mono)
- ffmpeg installed for audio preprocessing

## Instructions

### Step 1: Pronunciation Assessment

```typescript
import { SpeakClient } from '@speak/language-sdk';

const client = new SpeakClient({
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
  language: 'es',
});

// Assess pronunciation of a specific phrase
const result = await client.assessPronunciation({
  audioPath: './recordings/hola-como-estas.wav',
  targetText: 'Hola, como estas?',
  language: 'es',
  detailLevel: 'phoneme',
});

console.log(`Overall score: ${result.score}/100`);
for (const word of result.words) {
  const flag = word.score < 70 ? 'WEAK' : 'OK';
  console.log(`  [${flag}] "${word.text}": ${word.score}/100`);
  if (word.phonemes) {
    for (const p of word.phonemes.filter(p => p.score < 70)) {
      console.log(`    Phoneme "${p.symbol}": ${p.score} — ${p.suggestion}`);
    }
  }
}
```

### Step 2: Adaptive Drill Loop

```typescript
async function pronunciationDrill(
  client: SpeakClient,
  phrases: string[],
  language: string,
  targetScore: number = 80,
  maxAttempts: number = 3,
) {
  const weakPoints: Map<string, number[]> = new Map();
  const results: DrillResult[] = [];

  for (const phrase of phrases) {
    let bestScore = 0;
    let attempts = 0;

    while (bestScore < targetScore && attempts < maxAttempts) {
      const audioPath = await recordStudentAudio(phrase);
      const result = await client.assessPronunciation({
        audioPath, targetText: phrase, language, detailLevel: 'phoneme',
      });

      bestScore = Math.max(bestScore, result.score);
      attempts++;

      // Track weak phonemes
      for (const word of result.words) {
        for (const p of (word.phonemes || []).filter(p => p.score < 70)) {
          const scores = weakPoints.get(p.symbol) || [];
          scores.push(p.score);
          weakPoints.set(p.symbol, scores);
        }
      }

      if (result.score >= targetScore) {
        console.log(`"${phrase}": PASSED (${result.score}/100, ${attempts} attempts)`);
      } else if (attempts < maxAttempts) {
        console.log(`"${phrase}": ${result.score}/100 — try again`);
      }
    }

    results.push({ phrase, bestScore, attempts });
  }

  return { results, weakPoints };
}
```

### Step 3: Weakness Report

```typescript
function generateWeaknessReport(weakPoints: Map<string, number[]>) {
  const report = [...weakPoints.entries()]
    .map(([phoneme, scores]) => ({
      phoneme,
      avgScore: Math.round(scores.reduce((a, b) => a + b, 0) / scores.length),
      occurrences: scores.length,
    }))
    .sort((a, b) => a.avgScore - b.avgScore);

  console.log('\\n=== Pronunciation Weakness Report ===');
  for (const entry of report.slice(0, 10)) {
    const bar = '█'.repeat(Math.round(entry.avgScore / 10));
    console.log(`  ${entry.phoneme.padEnd(5)} ${bar} ${entry.avgScore}/100 (${entry.occurrences}x)`);
  }
  return report;
}
```

### Step 4: Targeted Practice Generator

```typescript
async function generateTargetedPractice(
  client: SpeakClient,
  weakPhonemes: string[],
  language: string,
) {
  // Request phrases that emphasize specific phonemes
  const practice = await client.getPracticePhrasesForPhonemes({
    phonemes: weakPhonemes,
    language,
    difficulty: 'progressive', // Start easy, increase complexity
    count: 10,
  });

  console.log('Targeted practice phrases:');
  for (const phrase of practice.phrases) {
    console.log(`  "${phrase.text}" — targets: ${phrase.targetPhonemes.join(', ')}`);
  }
  return practice;
}
```

### Workflow Comparison
| Aspect | Workflow A (Conversation) | Workflow B (Pronunciation) |
|--------|--------------------------|---------------------------|
| Focus | Natural dialogue | Phoneme accuracy |
| Feedback | Grammar + vocabulary | Phoneme scores + mouth position |
| Sessions | 5-15 min conversations | 2-5 min drills |
| Scoring | Overall fluency | Per-phoneme breakdown |
| Use case | Communication practice | Accent reduction |

## Output
- Phoneme-level pronunciation scores
- Adaptive drill loop with retry on weak phrases
- Weakness report showing problematic phonemes
- Targeted practice phrase generation
- Progress tracking over multiple sessions

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Audio too short | Recording < 0.5s | Minimum 0.5s audio required |
| Background noise | Poor recording environment | Prompt for quieter location |
| Phoneme not detected | Unclear speech | Slow down and articulate |
| Score always low | Microphone quality | Test with known-good audio first |

## Resources
- [Speak Website](https://speak.com)
- [OpenAI Whisper](https://platform.openai.com/docs/guides/speech-to-text)
- [IPA Phoneme Chart](https://www.internationalphoneticassociation.org/content/ipa-chart)

## Next Steps
For common errors, see `speak-common-errors`.

## Examples

**Basic drill**: Assess pronunciation of 5 common Spanish phrases, identify weak phonemes, and generate a targeted practice set.

**Progress tracking**: Run daily pronunciation drills, track phoneme scores over time, and visualize improvement trends.
