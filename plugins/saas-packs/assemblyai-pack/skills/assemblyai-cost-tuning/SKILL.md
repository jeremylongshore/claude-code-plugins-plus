---
name: assemblyai-cost-tuning
description: |
  Optimize AssemblyAI costs through model selection, feature budgeting, and usage monitoring.
  Use when analyzing AssemblyAI billing, reducing transcription costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "assemblyai cost", "assemblyai billing",
  "reduce assemblyai costs", "assemblyai pricing", "assemblyai budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription, cost]
compatible-with: claude-code
---

# AssemblyAI Cost Tuning

## Overview
Optimize AssemblyAI costs through model selection, feature-aware billing, and usage monitoring. AssemblyAI charges per audio hour with add-on pricing for intelligence features.

## Prerequisites
- Access to AssemblyAI billing dashboard at https://www.assemblyai.com/app
- Understanding of current usage patterns

## Actual Pricing (Pay-As-You-Go)

### Speech-to-Text (Async)
| Model | Price per Hour | Best For |
|-------|---------------|----------|
| **Best** (Universal-3) | $0.37/hr | Highest accuracy, production |
| **Nano** | $0.12/hr | High volume, cost-sensitive |

### Streaming Speech-to-Text
| Model | Price per Hour |
|-------|---------------|
| Universal Streaming | $0.47/hr |

### Audio Intelligence Add-Ons
| Feature | Additional Cost per Hour |
|---------|-------------------------|
| Speaker Diarization | $0.02/hr |
| Sentiment Analysis | $0.02/hr |
| Entity Detection | $0.08/hr |
| Auto Highlights | Included |
| Content Safety | $0.02/hr |
| IAB Categories | $0.02/hr |
| Summarization | Included (uses LeMUR) |
| PII Redaction | $0.02/hr |
| PII Audio Redaction | +processing time |

### LeMUR
| Model | Price per Input Token | Price per Output Token |
|-------|----------------------|----------------------|
| Default | ~$0.003/1K tokens | ~$0.015/1K tokens |

## Instructions

### Step 1: Cost Estimation Calculator

```typescript
interface CostEstimate {
  baseTranscriptionCost: number;
  featuresCost: number;
  totalCost: number;
  breakdown: Record<string, number>;
}

function estimateTranscriptionCost(
  audioHours: number,
  options: {
    model?: 'best' | 'nano';
    speakerLabels?: boolean;
    sentimentAnalysis?: boolean;
    entityDetection?: boolean;
    contentSafety?: boolean;
    iabCategories?: boolean;
    piiRedaction?: boolean;
  } = {}
): CostEstimate {
  const model = options.model ?? 'best';
  const baseRate = model === 'best' ? 0.37 : 0.12;
  const baseCost = audioHours * baseRate;

  const breakdown: Record<string, number> = {
    [`transcription (${model})`]: baseCost,
  };

  let featuresCost = 0;

  if (options.speakerLabels) {
    const cost = audioHours * 0.02;
    breakdown['speaker_labels'] = cost;
    featuresCost += cost;
  }
  if (options.sentimentAnalysis) {
    const cost = audioHours * 0.02;
    breakdown['sentiment_analysis'] = cost;
    featuresCost += cost;
  }
  if (options.entityDetection) {
    const cost = audioHours * 0.08;
    breakdown['entity_detection'] = cost;
    featuresCost += cost;
  }
  if (options.contentSafety) {
    const cost = audioHours * 0.02;
    breakdown['content_safety'] = cost;
    featuresCost += cost;
  }
  if (options.iabCategories) {
    const cost = audioHours * 0.02;
    breakdown['iab_categories'] = cost;
    featuresCost += cost;
  }
  if (options.piiRedaction) {
    const cost = audioHours * 0.02;
    breakdown['pii_redaction'] = cost;
    featuresCost += cost;
  }

  return {
    baseTranscriptionCost: baseCost,
    featuresCost,
    totalCost: baseCost + featuresCost,
    breakdown,
  };
}

// Example: 100 hours with Best model + diarization + sentiment
const estimate = estimateTranscriptionCost(100, {
  model: 'best',
  speakerLabels: true,
  sentimentAnalysis: true,
});
// Result: $37 (transcription) + $2 (speakers) + $2 (sentiment) = $41
```

### Step 2: Model Selection Strategy

```typescript
import { AssemblyAI } from 'assemblyai';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

// Use Nano for high-volume, cost-sensitive workloads
// - 3x cheaper than Best ($0.12 vs $0.37)
// - Good enough for search indexing, keyword detection
const cheapTranscript = await client.transcripts.transcribe({
  audio: audioUrl,
  speech_model: 'nano',
});

// Use Best for critical, accuracy-sensitive workloads
// - Medical transcription, legal proceedings, compliance
// - Supports word_boost for domain terminology
const accurateTranscript = await client.transcripts.transcribe({
  audio: audioUrl,
  speech_model: 'best',
  word_boost: ['specialized', 'domain', 'terms'],
  boost_param: 'high',
});
```

### Step 3: Feature Budget — Only Enable What You Need

```typescript
// EXPENSIVE: All features enabled ($0.37 + $0.16 = $0.53/hr)
const expensive = await client.transcripts.transcribe({
  audio: audioUrl,
  speech_model: 'best',        // $0.37/hr
  speaker_labels: true,         // +$0.02/hr
  sentiment_analysis: true,     // +$0.02/hr
  entity_detection: true,       // +$0.08/hr
  content_safety: true,         // +$0.02/hr
  iab_categories: true,         // +$0.02/hr
});

// CHEAP: Only what's needed ($0.12 + $0.02 = $0.14/hr)
const cheap = await client.transcripts.transcribe({
  audio: audioUrl,
  speech_model: 'nano',         // $0.12/hr
  speaker_labels: true,         // +$0.02/hr
  // Skip features you don't use
});
```

### Step 4: Usage Tracking

```typescript
class AssemblyAIUsageTracker {
  private totalAudioHours = 0;
  private totalCost = 0;
  private transcriptionCount = 0;

  track(audioDurationSeconds: number, model: 'best' | 'nano', features: string[]) {
    const hours = audioDurationSeconds / 3600;
    this.totalAudioHours += hours;
    this.transcriptionCount++;

    const estimate = estimateTranscriptionCost(hours, {
      model,
      speakerLabels: features.includes('speaker_labels'),
      sentimentAnalysis: features.includes('sentiment_analysis'),
      entityDetection: features.includes('entity_detection'),
      contentSafety: features.includes('content_safety'),
      iabCategories: features.includes('iab_categories'),
      piiRedaction: features.includes('redact_pii'),
    });

    this.totalCost += estimate.totalCost;

    return estimate;
  }

  getSummary() {
    return {
      totalAudioHours: this.totalAudioHours.toFixed(2),
      totalCost: `$${this.totalCost.toFixed(2)}`,
      transcriptionCount: this.transcriptionCount,
      avgCostPerTranscription: `$${(this.totalCost / this.transcriptionCount).toFixed(4)}`,
    };
  }
}
```

### Step 5: Cost Reduction Strategies

| Strategy | Savings | Trade-off |
|----------|---------|-----------|
| Use Nano instead of Best | 68% cheaper | Slightly lower accuracy |
| Disable unused features | Up to $0.16/hr | Missing insights |
| Cache transcript results | Eliminate re-fetch costs | Stale data risk |
| Use LeMUR instead of per-feature AI | Often cheaper for summaries | Different output format |
| Pre-filter audio (skip silence) | Proportional savings | Requires preprocessing |
| Batch with webhooks | No savings, but better throughput | More complex architecture |

### Step 6: Budget Alerts

```typescript
const MONTHLY_BUDGET = 100; // $100
const tracker = new AssemblyAIUsageTracker();

// After each transcription
const estimate = tracker.track(transcript.audio_duration ?? 0, 'best', ['speaker_labels']);
const summary = tracker.getSummary();

if (parseFloat(summary.totalCost.replace('$', '')) > MONTHLY_BUDGET * 0.8) {
  console.warn(`Budget warning: ${summary.totalCost} of $${MONTHLY_BUDGET} used`);
  // Send alert to Slack, email, etc.
}
```

## Output
- Accurate cost estimation with feature-level breakdown
- Model selection strategy (Best vs. Nano)
- Feature budgeting to eliminate unnecessary costs
- Usage tracking with budget alerts
- Cost reduction strategies ranked by impact

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected high bill | Entity detection enabled everywhere | Audit features per endpoint |
| Nano accuracy too low | Wrong model for use case | Switch critical paths to Best |
| Budget exceeded | No monitoring | Implement usage tracker + alerts |
| Double billing | Re-transcribing same audio | Cache transcript IDs, check before submitting |

## Resources
- [AssemblyAI Pricing](https://www.assemblyai.com/pricing)
- [AssemblyAI Billing Dashboard](https://www.assemblyai.com/app)
- [Speech Model Comparison](https://www.assemblyai.com/docs/speech-to-text/speech-recognition)

## Next Steps
For architecture patterns, see `assemblyai-reference-architecture`.
