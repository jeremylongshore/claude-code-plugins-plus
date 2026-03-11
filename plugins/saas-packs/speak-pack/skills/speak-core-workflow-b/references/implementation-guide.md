# Speak Core Workflow B - Implementation Guide

Detailed implementation reference for the speak-core-workflow-b skill.

## Instructions

### Step 1: Initialize Pronunciation Session
```typescript
// src/workflows/pronunciation-training.ts
import {
  SpeakClient,
  PronunciationTrainer,
  PhonemeAnalyzer,
} from '@speak/language-sdk';

interface PronunciationConfig {
  targetLanguage: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  focusPhonemes?: string[]; // Specific sounds to practice
  category?: 'vowels' | 'consonants' | 'tones' | 'all';
}

async function initializePronunciationTraining(
  client: SpeakClient,
  config: PronunciationConfig
): Promise<PronunciationTrainer> {
  const trainer = new PronunciationTrainer(client, {
    language: config.targetLanguage,
    difficulty: config.difficulty,
    adaptiveMode: true, // Adjusts based on user performance
  });

  // Pre-load phoneme models for target language
  await trainer.initialize();

  // Set focus areas if specified
  if (config.focusPhonemes) {
    trainer.setFocusPhonemes(config.focusPhonemes);
  }

  return trainer;
}
```

### Step 2: Implement Drill Session
```typescript
interface DrillItem {
  id: string;
  text: string;
  romanization?: string; // For non-Latin scripts
  translation: string;
  audioUrl: string;
  targetPhonemes: string[];
  difficulty: number;
}

interface DrillResult {
  item: DrillItem;
  userAudio: ArrayBuffer;
  scores: PronunciationScores;
  phonemeDetails: PhonemeResult[];
  feedback: string[];
}

async function runPronunciationDrill(
  trainer: PronunciationTrainer,
  drillCount: number = 10
): Promise<DrillSession> {
  const session = await trainer.startDrillSession({
    itemCount: drillCount,
    repeatOnMistake: true,
    minScore: 70, // Repeat until 70% or better
  });

  const results: DrillResult[] = [];

  while (!session.isComplete) {
    // Get next drill item
    const item = await session.getNextItem();

    console.log('\n--- Pronunciation Drill ---');
    console.log(`Say: "${item.text}"`);
    if (item.romanization) {
      console.log(`Romanization: ${item.romanization}`);
    }
    console.log(`Meaning: ${item.translation}`);
    console.log('Listen to native pronunciation...');

    // Play native audio for reference
    await playAudio(item.audioUrl);

    // Record user attempt
    const userAudio = await recordUserAudio();

    // Analyze pronunciation
    const result = await session.submitAttempt({
      itemId: item.id,
      audioData: userAudio,
    });

    results.push({
      item,
      userAudio,
      scores: result.scores,
      phonemeDetails: result.phonemeDetails,
      feedback: result.feedback,
    });

    // Display detailed feedback
    displayPronunciationFeedback(result);

    // Check if need to repeat
    if (result.scores.overall < 70 && session.shouldRepeat) {
      console.log('\nLet\'s try that one again...');
    }
  }

  return session.getSummary();
}
```

### Step 3: Phoneme-Level Analysis
```typescript
interface PhonemeResult {
  phoneme: string;
  expected: string;
  actual: string;
  score: number;
  issues: PhonemeIssue[];
  visualGuide?: string; // Mouth position diagram URL
}

interface PhonemeIssue {
  type: 'substitution' | 'omission' | 'addition' | 'distortion';
  description: string;
  tip: string;
}

function displayPronunciationFeedback(result: DrillResult) {
  console.log(`\n📊 Pronunciation Score: ${result.scores.overall}/100`);
  console.log(`   Accuracy: ${result.scores.accuracy}/100`);
  console.log(`   Fluency: ${result.scores.fluency}/100`);
  console.log(`   Intonation: ${result.scores.intonation}/100`);

  // Show problem phonemes
  const problemPhonemes = result.phonemeDetails.filter(p => p.score < 70);
  if (problemPhonemes.length > 0) {
    console.log('\n🔍 Phonemes to improve:');
    for (const p of problemPhonemes) {
      console.log(`   [${p.phoneme}] Score: ${p.score}/100`);
      for (const issue of p.issues) {
        console.log(`      ⚠️ ${issue.type}: ${issue.description}`);
        console.log(`      💡 Tip: ${issue.tip}`);
      }
    }
  }

  // Show overall feedback
  if (result.feedback.length > 0) {
    console.log('\n💬 Feedback:');
    result.feedback.forEach(f => console.log(`   • ${f}`));
  }
}
```

### Step 4: Adaptive Practice Generation
```typescript
interface WeaknessAnalysis {
  phoneme: string;
  averageScore: number;
  attemptCount: number;
  trend: 'improving' | 'stable' | 'declining';
  suggestedDrills: DrillItem[];
}

async function generateAdaptivePractice(
  trainer: PronunciationTrainer,
  userHistory: DrillResult[]
): Promise<AdaptivePracticeSession> {
  // Analyze user's weaknesses
  const weaknesses = analyzeWeaknesses(userHistory);

  // Generate targeted practice
  const adaptiveSession = await trainer.createAdaptiveSession({
    targetWeaknesses: weaknesses.map(w => w.phoneme),
    intensity: 'focused', // or 'mixed' for variety
    maxDuration: 15 * 60 * 1000, // 15 minutes
  });

  console.log('\n🎯 Adaptive Practice Plan:');
  console.log(`Focus areas: ${weaknesses.map(w => w.phoneme).join(', ')}`);

  return adaptiveSession;
}

function analyzeWeaknesses(results: DrillResult[]): WeaknessAnalysis[] {
  const phonemeStats = new Map<string, number[]>();

  // Collect scores by phoneme
  for (const result of results) {
    for (const p of result.phonemeDetails) {
      if (!phonemeStats.has(p.phoneme)) {
        phonemeStats.set(p.phoneme, []);
      }
      phonemeStats.get(p.phoneme)!.push(p.score);
    }
  }

  // Identify weaknesses (average < 75)
  const weaknesses: WeaknessAnalysis[] = [];
  for (const [phoneme, scores] of phonemeStats) {
    const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
    if (avg < 75) {
      weaknesses.push({
        phoneme,
        averageScore: avg,
        attemptCount: scores.length,
        trend: calculateTrend(scores),
        suggestedDrills: [], // Populated by trainer
      });
    }
  }

  return weaknesses.sort((a, b) => a.averageScore - b.averageScore);
}
```


## Complete Workflow Example

```typescript
async function pronunciationTrainingWorkflow() {
  const client = getSpeakClient();

  // Configure for Korean pronunciation (challenging for English speakers)
  const config: PronunciationConfig = {
    targetLanguage: 'ko',
    difficulty: 'intermediate',
    focusPhonemes: ['ㄱ', 'ㅋ', 'ㄲ'], // Korean aspirated/tense consonants
    category: 'consonants',
  };

  console.log('Starting pronunciation training...');
  console.log(`Language: ${config.targetLanguage}`);
  console.log(`Focus: ${config.focusPhonemes?.join(', ') || 'General'}`);

  // Initialize trainer
  const trainer = await initializePronunciationTraining(client, config);

  // Run initial assessment
  console.log('\n📝 Initial Assessment...');
  const assessment = await trainer.runAssessment();
  console.log(`Baseline score: ${assessment.overallScore}/100`);

  // Run pronunciation drills
  const drillResults = await runPronunciationDrill(trainer, 10);

  // Generate adaptive practice based on results
  const adaptiveSession = await generateAdaptivePractice(
    trainer,
    drillResults.results
  );

  // Run adaptive practice
  await adaptiveSession.run();

  // Final summary
  const summary = await trainer.getSessionSummary();
  console.log('\n========== Training Complete ==========');
  console.log(`Items practiced: ${summary.totalItems}`);
  console.log(`Average score: ${summary.averageScore}/100`);
  console.log(`Improvement: +${summary.improvement}%`);

  return summary;
}
```


## Workflow Comparison

| Aspect | Workflow A (Conversation) | Workflow B (Pronunciation) |
|--------|---------------------------|----------------------------|
| Primary Focus | Communication | Accuracy |
| Feedback Type | Holistic | Phoneme-level |
| Session Style | Free-form dialogue | Structured drills |
| Pacing | User-driven | System-driven |
| Best For | Fluency building | Accent reduction |

