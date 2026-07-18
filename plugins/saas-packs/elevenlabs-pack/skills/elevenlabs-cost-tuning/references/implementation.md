# ElevenLabs Cost Tuning — Full Implementation

Deep, copy-pasteable code for every cost-reduction lever. The SKILL.md body summarizes
the workflow and the billing model; this file carries the complete implementation for
Steps 2–6.

## Step 2: Model-Based Cost Reduction

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

## Step 3: Character-Efficient Text Processing

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
  optimized = optimized.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1"); // link → link

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

## Step 4: Real-Time Quota Monitoring

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

## Step 5: Cost-Aware Request Guard

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

## Step 6: Usage Tracking Dashboard

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
