---
name: elevenlabs-cost-tuning
description: |
  Optimize ElevenLabs costs through model selection, character-efficient patterns,
  caching, and usage monitoring with budget alerts.
  Use when analyzing ElevenLabs billing, reducing character usage,
  or implementing quota monitoring for TTS workloads.
  Trigger: "elevenlabs cost", "elevenlabs billing", "reduce elevenlabs costs",
  "elevenlabs pricing", "elevenlabs expensive", "elevenlabs budget",
  "elevenlabs characters", "elevenlabs quota".
allowed-tools: Read, Grep, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, cost, billing]
compatible-with: claude-code
---

# ElevenLabs Cost Tuning

## Overview

Optimize ElevenLabs costs through model selection (Flash = 50% savings), character-efficient text processing, audio caching, and real-time quota monitoring. ElevenLabs bills by character for TTS and by audio minute for STT.

## Prerequisites

- ElevenLabs account with usage dashboard access
- Understanding of your monthly character consumption
- Access to billing at https://elevenlabs.io/app/subscription

## Instructions

### Step 1: Understand the Billing Model

**TTS billing (by character):**

| Model | Credits per Character | 10K Chars Cost | Best For |
|-------|-----------------------|----------------|----------|
| `eleven_v3` | 1.0 | 10,000 credits | Maximum quality |
| `eleven_multilingual_v2` | 1.0 | 10,000 credits | High quality + multilingual |
| `eleven_flash_v2_5` | 0.5 | 5,000 credits | Real-time / budget-conscious |
| `eleven_turbo_v2_5` | 0.5 | 5,000 credits | Fast + affordable |

**Other feature billing:**

| Feature | Billing Basis |
|---------|--------------|
| Speech-to-Text (Scribe) | Per audio minute |
| Sound Effects | Per generation |
| Audio Isolation | 1,000 characters per minute of audio |
| Dubbing | Per source audio minute |

**Plan character limits:**

| Plan | Monthly | Price | Cost/1K Chars |
|------|---------|-------|---------------|
| Free | 10,000 | $0 | $0 |
| Starter | 30,000 | $5 | $0.17 |
| Creator | 100,000 | $22 | $0.22 |
| Pro | 500,000 | $99 | $0.20 |
| Scale | 2,000,000 | $330 | $0.17 |

### Step 2: Model-Based Cost Reduction

The easiest win: use Flash/Turbo models where quality difference is acceptable.

```typescript
// src/elevenlabs/cost-aware-tts.ts
type ContentType = "greeting" | "notification" | "narration" | "premium";

function selectCostEffectiveModel(contentType: ContentType): {
  modelId: string;
  costMultiplier: number;
} {
  switch (contentType) {
    case "greeting":
    case "notification":
      // Short, functional audio — Flash is fine
      return { modelId: "eleven_flash_v2_5", costMultiplier: 0.5 };

    case "narration":
      // Content creation — quality matters
      return { modelId: "eleven_multilingual_v2", costMultiplier: 1.0 };

    case "premium":
      // Customer-facing, high-value — max quality
      return { modelId: "eleven_v3", costMultiplier: 1.0 };
  }
}

// Estimate cost before generating
function estimateCharacterCost(text: string, modelId: string): number {
  const multiplier = modelId.includes("flash") || modelId.includes("turbo") ? 0.5 : 1.0;
  return text.length * multiplier;
}
```

### Step 3: Character-Efficient Text Processing

Reduce character count without losing meaning:

```typescript
// src/elevenlabs/text-optimizer.ts

/**
 * Optimize text for TTS to reduce character count.
 * ElevenLabs counts ALL characters including spaces and punctuation.
 */
export function optimizeTextForTTS(text: string): {
  optimized: string;
  originalLength: number;
  savedCharacters: number;
} {
  const original = text;
  let optimized = text;

  // Remove excessive whitespace (spaces count as characters)
  optimized = optimized.replace(/\s+/g, " ").trim();

  // Remove markdown formatting that doesn't affect speech
  optimized = optimized.replace(/[*_~`#]/g, "");
  optimized = optimized.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1"); // [link](url) → link

  // Remove HTML tags
  optimized = optimized.replace(/<[^>]+>/g, "");

  // Collapse multiple punctuation
  optimized = optimized.replace(/\.{2,}/g, ".");
  optimized = optimized.replace(/!{2,}/g, "!");

  return {
    optimized,
    originalLength: original.length,
    savedCharacters: original.length - optimized.length,
  };
}
```

### Step 4: Real-Time Quota Monitoring

```typescript
// src/elevenlabs/quota-monitor.ts
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

interface QuotaStatus {
  plan: string;
  used: number;
  limit: number;
  remaining: number;
  pctUsed: number;
  resetsAt: Date;
  daysUntilReset: number;
  dailyBudget: number;    // Characters per day until reset
  projectedOverage: boolean;
}

export async function getQuotaStatus(): Promise<QuotaStatus> {
  const client = new ElevenLabsClient();
  const user = await client.user.get();
  const sub = user.subscription;

  const now = new Date();
  const resetsAt = new Date(sub.next_character_count_reset_unix * 1000);
  const msUntilReset = resetsAt.getTime() - now.getTime();
  const daysUntilReset = Math.max(1, Math.ceil(msUntilReset / 86_400_000));

  const remaining = sub.character_limit - sub.character_count;
  const dailyBudget = Math.floor(remaining / daysUntilReset);

  // Project if current usage rate will exceed limit
  const daysSinceReset = 30 - daysUntilReset;
  const dailyRate = daysSinceReset > 0 ? sub.character_count / daysSinceReset : 0;
  const projectedUsage = dailyRate * 30;

  return {
    plan: sub.tier,
    used: sub.character_count,
    limit: sub.character_limit,
    remaining,
    pctUsed: Math.round((sub.character_count / sub.character_limit) * 1000) / 10,
    resetsAt,
    daysUntilReset,
    dailyBudget,
    projectedOverage: projectedUsage > sub.character_limit,
  };
}

// CLI usage
async function printQuota() {
  const q = await getQuotaStatus();
  console.log(`Plan: ${q.plan}`);
  console.log(`Used: ${q.used.toLocaleString()} / ${q.limit.toLocaleString()} (${q.pctUsed}%)`);
  console.log(`Remaining: ${q.remaining.toLocaleString()} characters`);
  console.log(`Daily budget: ${q.dailyBudget.toLocaleString()} chars/day`);
  console.log(`Resets: ${q.resetsAt.toISOString()} (${q.daysUntilReset} days)`);
  if (q.projectedOverage) {
    console.warn("WARNING: Projected to exceed quota at current usage rate");
  }
}
```

### Step 5: Cost-Aware Request Guard

```typescript
// Prevent expensive operations when quota is low
export async function guardedTTS(
  text: string,
  voiceId: string,
  contentType: ContentType = "notification"
): Promise<ReadableStream | null> {
  const client = new ElevenLabsClient();
  const { modelId, costMultiplier } = selectCostEffectiveModel(contentType);
  const charCost = text.length * costMultiplier;

  // Check quota
  const quota = await getQuotaStatus();

  if (charCost > quota.remaining) {
    console.error(`Insufficient quota: need ${charCost}, have ${quota.remaining}`);
    return null;
  }

  if (quota.pctUsed > 90) {
    // Force cheapest model when quota is critically low
    console.warn("Low quota — forcing Flash model");
    return client.textToSpeech.convert(voiceId, {
      text,
      model_id: "eleven_flash_v2_5",
    });
  }

  return client.textToSpeech.convert(voiceId, {
    text,
    model_id: modelId,
  });
}
```

### Step 6: Usage Tracking Dashboard

```typescript
// Track per-request costs for analysis
interface UsageEntry {
  timestamp: Date;
  operation: "tts" | "sts" | "stt" | "sfx" | "isolation";
  modelId: string;
  characterCount: number;
  creditCost: number;
  voiceId: string;
  cached: boolean;
}

const usageLog: UsageEntry[] = [];

function trackUsage(entry: Omit<UsageEntry, "timestamp">) {
  usageLog.push({ ...entry, timestamp: new Date() });
}

function getUsageSummary(days = 30) {
  const cutoff = new Date(Date.now() - days * 86_400_000);
  const recent = usageLog.filter(e => e.timestamp > cutoff);

  return {
    totalCredits: recent.reduce((sum, e) => sum + e.creditCost, 0),
    totalCharacters: recent.reduce((sum, e) => sum + e.characterCount, 0),
    byModel: Object.groupBy(recent, e => e.modelId),
    byOperation: Object.groupBy(recent, e => e.operation),
    cacheHitRate: recent.filter(e => e.cached).length / recent.length,
  };
}
```

## Cost Optimization Checklist

| Strategy | Savings | Effort |
|----------|---------|--------|
| Flash/Turbo models for non-premium content | 50% | Low |
| Cache repeated audio (greetings, prompts) | 80-95% for cached | Medium |
| Text optimization (remove markdown, whitespace) | 5-15% | Low |
| Quota monitoring with budget alerts | Prevents overages | Medium |
| Usage-based billing (Creator+ plans) | Avoids hard cutoff | Low |
| Batch short texts into single requests | Reduces overhead | Low |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `quota_exceeded` (401) | Monthly limit hit | Upgrade plan or enable usage-based billing |
| Unexpected high usage | No monitoring | Implement `getQuotaStatus()` guard |
| Bill shock | Wrong model in production | Audit `model_id` in all TTS calls |
| Cache not helping | Unique content | Cache only repeated content (greetings, errors) |

## Resources

- [ElevenLabs Pricing](https://elevenlabs.io/pricing)
- [Usage Dashboard](https://elevenlabs.io/app/usage)
- [Subscription Settings](https://elevenlabs.io/app/subscription)
- [Models Overview](https://elevenlabs.io/docs/overview/models)

## Next Steps

For architecture patterns, see `elevenlabs-reference-architecture`.
