---
name: deepgram-cost-tuning
description: |
  Optimize Deepgram costs and usage for budget-conscious deployments.
  Use when reducing transcription costs, implementing usage controls,
  or optimizing pricing tier utilization.
  Trigger: "deepgram cost", "reduce deepgram spending", "deepgram pricing",
  "deepgram budget", "optimize deepgram usage", "deepgram billing".
allowed-tools: Read, Write, Edit, Bash(ffmpeg:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, cost-optimization, billing]

---
# Deepgram Cost Tuning

## Overview
Optimize Deepgram API costs through smart model selection, audio preprocessing to reduce billable minutes, usage monitoring via the Deepgram API, budget guardrails, and feature-aware cost estimation. Deepgram bills per audio minute processed.

## Deepgram Pricing (2026)

| Product | Model | Price/Minute | Notes |
|---------|-------|-------------|-------|
| STT (Batch) | Nova-3 | $0.0043 | Best accuracy |
| STT (Batch) | Nova-2 | $0.0043 | Proven stable |
| STT (Streaming) | Nova-3 | $0.0059 | Real-time |
| STT (Streaming) | Nova-2 | $0.0059 | Real-time |
| STT (Batch) | Base | $0.0048 | Fastest |
| STT (Batch) | Whisper | $0.0048 | Multilingual |
| TTS | Aura-2 | Pay-per-character | See TTS pricing |
| Intelligence | Summarize/Topics/Sentiment | Included with STT | No extra cost |

**Add-on costs:**
- Diarization: +$0.0044/min
- Multichannel: billed per channel

## Instructions

### Step 1: Budget-Aware Transcription Service

```typescript
import { createClient } from '@deepgram/sdk';

interface BudgetConfig {
  monthlyLimitUsd: number;
  warningThreshold: number;  // 0.0-1.0 (e.g., 0.8 = warn at 80%)
  costPerMinute: number;     // Base STT cost
}

class BudgetAwareTranscriber {
  private client: ReturnType<typeof createClient>;
  private config: BudgetConfig;
  private monthlySpendUsd = 0;
  private monthlyMinutes = 0;

  constructor(apiKey: string, config: BudgetConfig) {
    this.client = createClient(apiKey);
    this.config = config;
  }

  async transcribe(source: any, options: any) {
    // Estimate cost before transcription
    const estimatedCost = this.estimateCost(options);
    const projected = this.monthlySpendUsd + estimatedCost;

    if (projected > this.config.monthlyLimitUsd) {
      throw new Error(
        `Budget exceeded: $${this.monthlySpendUsd.toFixed(2)} spent, ` +
        `$${this.config.monthlyLimitUsd} limit`
      );
    }

    if (projected > this.config.monthlyLimitUsd * this.config.warningThreshold) {
      console.warn(
        `Budget warning: ${((projected / this.config.monthlyLimitUsd) * 100).toFixed(0)}% ` +
        `of $${this.config.monthlyLimitUsd} limit`
      );
    }

    const { result, error } = await this.client.listen.prerecorded.transcribeUrl(
      source, options
    );
    if (error) throw error;

    // Track actual usage
    const duration = result.metadata.duration / 60;  // Convert to minutes
    const actualCost = this.calculateCost(duration, options);
    this.monthlyMinutes += duration;
    this.monthlySpendUsd += actualCost;

    return result;
  }

  private estimateCost(options: any): number {
    // Conservative estimate — assume 5 minutes per file
    return this.calculateCost(5, options);
  }

  private calculateCost(minutes: number, options: any): number {
    let cost = minutes * this.config.costPerMinute;
    if (options.diarize) cost += minutes * 0.0044;  // Diarization add-on
    return cost;
  }

  getUsageSummary() {
    return {
      minutesUsed: this.monthlyMinutes.toFixed(1),
      spentUsd: this.monthlySpendUsd.toFixed(4),
      remainingUsd: (this.config.monthlyLimitUsd - this.monthlySpendUsd).toFixed(4),
      utilizationPercent: ((this.monthlySpendUsd / this.config.monthlyLimitUsd) * 100).toFixed(1),
    };
  }
}

// Usage:
const transcriber = new BudgetAwareTranscriber(process.env.DEEPGRAM_API_KEY!, {
  monthlyLimitUsd: 100,
  warningThreshold: 0.8,
  costPerMinute: 0.0043,
});
```

### Step 2: Reduce Billable Minutes with Audio Preprocessing

```bash
# Remove silence — can save 10-40% of billable minutes
ffmpeg -i input.wav \
  -af "silenceremove=stop_periods=-1:stop_duration=0.5:stop_threshold=-30dB" \
  -ar 16000 -ac 1 -acodec pcm_s16le \
  trimmed.wav

# Speed up audio (1.25x) — saves 20% of billable minutes
# Deepgram handles slightly sped-up audio well
ffmpeg -i input.wav \
  -filter:a "atempo=1.25" \
  -ar 16000 -ac 1 -acodec pcm_s16le \
  faster.wav
```

```typescript
import { execSync } from 'child_process';

function measureSavings(inputPath: string) {
  // Get original duration
  const origDuration = parseFloat(
    execSync(`ffprobe -v quiet -show_entries format=duration -of csv=p=0 "${inputPath}"`)
      .toString().trim()
  );

  // Remove silence
  execSync(`ffmpeg -y -i "${inputPath}" \
    -af "silenceremove=stop_periods=-1:stop_duration=0.5:stop_threshold=-30dB" \
    -ar 16000 -ac 1 -acodec pcm_s16le /tmp/trimmed.wav 2>/dev/null`);

  const trimmedDuration = parseFloat(
    execSync(`ffprobe -v quiet -show_entries format=duration -of csv=p=0 /tmp/trimmed.wav`)
      .toString().trim()
  );

  const savings = ((1 - trimmedDuration / origDuration) * 100).toFixed(1);
  const costSaved = ((origDuration - trimmedDuration) / 60 * 0.0043).toFixed(4);

  console.log(`Original: ${origDuration.toFixed(1)}s`);
  console.log(`Trimmed: ${trimmedDuration.toFixed(1)}s`);
  console.log(`Savings: ${savings}% (${costSaved}/file at $0.0043/min)`);
}
```

### Step 3: Query Deepgram Usage API

```typescript
import { createClient } from '@deepgram/sdk';

async function getUsageDashboard(projectId: string) {
  const client = createClient(process.env.DEEPGRAM_API_KEY!);

  // Get usage for current month
  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

  const { result } = await client.manage.getUsage(projectId, {
    start: monthStart.toISOString(),
    end: now.toISOString(),
  });

  // Aggregate by model
  const byModel: Record<string, { minutes: number; cost: number }> = {};
  for (const entry of (result as any).results ?? []) {
    const model = entry.model ?? 'unknown';
    if (!byModel[model]) byModel[model] = { minutes: 0, cost: 0 };
    byModel[model].minutes += (entry.hours ?? 0) * 60 + (entry.minutes ?? 0);
  }

  console.log('=== Monthly Usage ===');
  for (const [model, data] of Object.entries(byModel)) {
    const cost = data.minutes * 0.0043;
    console.log(`${model}: ${data.minutes.toFixed(1)} min ($${cost.toFixed(2)})`);
  }

  // Monthly projection
  const dayOfMonth = now.getDate();
  const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  const totalMinutes = Object.values(byModel).reduce((s, d) => s + d.minutes, 0);
  const projectedMinutes = (totalMinutes / dayOfMonth) * daysInMonth;
  const projectedCost = projectedMinutes * 0.0043;

  console.log(`\nProjected monthly: ${projectedMinutes.toFixed(0)} min ($${projectedCost.toFixed(2)})`);
}
```

### Step 4: Cost-Optimized Model Selection

```typescript
function recommendModel(params: {
  qualityNeeded: 'high' | 'medium' | 'low';
  isRealtime: boolean;
  languages: string[];
  budgetPerMinute?: number;
}): { model: string; pricePerMin: number; reason: string } {
  const { qualityNeeded, isRealtime, languages, budgetPerMinute } = params;

  // Multilingual -> Whisper
  if (languages.length > 1 || !['en', 'es', 'fr', 'de'].includes(languages[0])) {
    return { model: 'whisper-large', pricePerMin: 0.0048, reason: 'Multilingual support' };
  }

  // Budget constraint
  if (budgetPerMinute !== undefined && budgetPerMinute < 0.005) {
    return { model: 'nova-2', pricePerMin: 0.0043, reason: 'Best price per quality' };
  }

  // Real-time -> Nova-3 (streaming price $0.0059/min)
  if (isRealtime) {
    return { model: 'nova-3', pricePerMin: 0.0059, reason: 'Best real-time accuracy' };
  }

  // Quality based
  switch (qualityNeeded) {
    case 'high':
      return { model: 'nova-3', pricePerMin: 0.0043, reason: 'Highest accuracy' };
    case 'medium':
      return { model: 'nova-2', pricePerMin: 0.0043, reason: 'Good accuracy, proven' };
    case 'low':
      return { model: 'base', pricePerMin: 0.0048, reason: 'Fastest processing' };
  }
}
```

### Step 5: Feature Cost Awareness

```typescript
// Feature cost breakdown per minute of audio
const featureCosts: Record<string, { cost: number; description: string }> = {
  // Free features (included with STT)
  smart_format:   { cost: 0,      description: 'Punctuation + paragraphs + numerals' },
  punctuate:      { cost: 0,      description: 'Punctuation only' },
  paragraphs:     { cost: 0,      description: 'Paragraph formatting' },
  summarize:      { cost: 0,      description: 'AI summary (included with STT)' },
  detect_topics:  { cost: 0,      description: 'Topic detection (included)' },
  sentiment:      { cost: 0,      description: 'Sentiment analysis (included)' },
  intents:        { cost: 0,      description: 'Intent recognition (included)' },
  redact:         { cost: 0,      description: 'PII redaction (included)' },

  // Paid add-ons
  diarize:        { cost: 0.0044, description: 'Speaker identification (+$0.0044/min)' },
  multichannel:   { cost: 0.0043, description: 'Per-channel billing (1x STT cost per channel)' },
};

function estimateJobCost(params: {
  durationMinutes: number;
  model: string;
  features: string[];
  channels?: number;
}): number {
  const baseCost = params.durationMinutes * 0.0043;
  let addOnCost = 0;

  for (const feature of params.features) {
    addOnCost += (featureCosts[feature]?.cost ?? 0) * params.durationMinutes;
  }

  // Multichannel: billed per channel
  const channelMultiplier = params.channels ?? 1;

  return (baseCost + addOnCost) * channelMultiplier;
}

// Example: 60 min meeting with diarization
// estimateJobCost({ durationMinutes: 60, model: 'nova-3', features: ['diarize'] })
// = (60 * 0.0043) + (60 * 0.0044) = $0.258 + $0.264 = $0.522
```

## Output
- Budget-aware transcription with auto-blocking
- Audio preprocessing to reduce billable minutes
- Usage dashboard via Deepgram API
- Cost-optimized model recommendation
- Feature cost breakdown with estimation

## Cost Optimization Quick Wins

| Strategy | Savings | Effort |
|----------|---------|--------|
| Remove silence from audio | 10-40% | Low (ffmpeg one-liner) |
| Disable diarization when not needed | ~50% | Low (remove option) |
| Use callback for long files | Indirect (no timeouts) | Low |
| Cache repeated transcriptions | 20-60% | Medium (Redis) |
| Speed up audio 1.25x | 20% | Low (ffmpeg) |
| Use Nova-2 instead of Nova-3 | 0% (same price) | None |
| Batch pre-recorded vs streaming | 37% ($0.0043 vs $0.0059) | Medium |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Budget exceeded | No controls | Enable budget check before transcription |
| Unexpected charges | Diarization always on | Make diarization opt-in |
| Usage API empty | Wrong project ID | Get ID from `getProjects()` |
| Cost spike | Batch job without limits | Set concurrency limits + budget cap |

## Resources
- [Deepgram Pricing](https://deepgram.com/pricing)
- [Usage API](https://developers.deepgram.com/reference/get-usage)
- [Cost Optimization Guide](https://developers.deepgram.com/docs/cost-optimization)
