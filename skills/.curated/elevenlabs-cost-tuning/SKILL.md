---
name: elevenlabs-cost-tuning
description: |
  Optimize ElevenLabs costs through model selection, character-efficient patterns,
  caching, and usage monitoring with budget alerts.
  Use when analyzing ElevenLabs billing, reducing character usage, hunting down bill
  shock, or implementing quota monitoring for TTS workloads.
  Trigger with "elevenlabs cost", "elevenlabs billing", "reduce elevenlabs costs",
  "elevenlabs pricing", "elevenlabs expensive", "elevenlabs budget",
  "elevenlabs characters", "elevenlabs quota".
allowed-tools: Read, Bash(curl:*), Bash(node:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- cost
- billing
compatibility: Designed for Claude Code
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

### Steps 2–6: Apply the cost levers

Work through the levers in order of savings-per-effort. Each ships as a small, drop-in
TypeScript helper — the full source for every step is in
[implementation.md](references/implementation.md).

1. **Model-based reduction** — route each request through `selectCostEffectiveModel()` so
   functional audio (greetings, notifications) uses Flash/Turbo at 0.5x while premium,
   customer-facing output keeps full-quality models. Biggest single win (50%).
2. **Character-efficient text** — run copy through `optimizeTextForTTS()` to strip
   markdown, HTML, and redundant whitespace/punctuation before billing counts it (5–15%).
3. **Real-time quota monitoring** — `getQuotaStatus()` returns used/remaining/percent, a
   per-day budget until reset, and a `projectedOverage` flag from the current usage rate.
4. **Cost-aware request guard** — `guardedTTS()` refuses a call that exceeds remaining
   quota and force-downgrades to Flash above 90% usage, preventing hard overages.
5. **Usage tracking** — `trackUsage()` + `getUsageSummary()` roll up credits by model and
   operation and compute a cache-hit rate so you can see where spend actually goes.

Minimal skeleton — the guard is the piece most workloads adopt first:

```typescript
import { guardedTTS } from "./elevenlabs/cost-aware-tts";

// Notifications auto-route to Flash (0.5x); guard blocks or downgrades near the limit.
const stream = await guardedTTS("Your table is ready.", VOICE_ID, "notification");
```

### Cost Optimization Checklist

| Strategy | Savings | Effort |
|----------|---------|--------|
| Flash/Turbo models for non-premium content | 50% | Low |
| Cache repeated audio (greetings, prompts) | 80-95% for cached | Medium |
| Text optimization (remove markdown, whitespace) | 5-15% | Low |
| Quota monitoring with budget alerts | Prevents overages | Medium |
| Usage-based billing (Creator+ plans) | Avoids hard cutoff | Low |
| Batch short texts into single requests | Reduces overhead | Low |

## Output

Applying this skill produces:

- **A cost-aware TTS layer** — `selectCostEffectiveModel()` + `guardedTTS()` that pick the
  cheapest acceptable model per content type and refuse/downgrade calls near the quota.
- **A text optimizer** — `optimizeTextForTTS()` returning `{ optimized, originalLength, savedCharacters }`.
- **A live quota picture** — `getQuotaStatus()` returning plan, used, limit, remaining,
  `pctUsed`, `dailyBudget`, and a `projectedOverage` boolean.
- **A usage roll-up** — `getUsageSummary()` reporting total credits/characters, spend by
  model and operation, and cache-hit rate over a trailing window.

Together these turn an unmonitored, single-model TTS integration into one with per-request
cost control, overage prevention, and a spend audit trail.

## Examples

Quick shape (full, runnable scenarios in [examples.md](references/examples.md)):

```typescript
import { getQuotaStatus } from "./elevenlabs/quota-monitor";

const q = await getQuotaStatus();
console.log(`${q.plan}: ${q.pctUsed}% used, ${q.remaining.toLocaleString()} chars left`);
if (q.projectedOverage) console.warn("On pace to exceed quota this cycle");
```

- **Check quota before a batch run** — abort early if the batch would exceed remaining chars.
- **Route content to the cheapest acceptable model** — Flash for notifications, `eleven_v3` for premium.
- **Trim characters before billing counts them** — strip markdown/HTML with `optimizeTextForTTS()`.
- **Roll up 30-day spend** — see credits by model and cache-hit rate with `getUsageSummary()`.

See [examples.md](references/examples.md) for the complete code of each.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `quota_exceeded` (401) | Monthly limit hit | Upgrade plan or enable usage-based billing |
| Unexpected high usage | No monitoring | Implement `getQuotaStatus()` guard |
| Bill shock | Wrong model in production | Audit `model_id` in all TTS calls |
| Cache not helping | Unique content | Cache only repeated content (greetings, errors) |

## Resources

- [Full implementation walkthrough](references/implementation.md) — Steps 2–6 source
- [Worked examples](references/examples.md) — end-to-end cost scenarios
- [ElevenLabs Pricing](https://elevenlabs.io/pricing)
- [Usage Dashboard](https://elevenlabs.io/app/usage)
- [Subscription Settings](https://elevenlabs.io/app/subscription)
- [Models Overview](https://elevenlabs.io/docs/overview/models)
- For architecture patterns, see the `elevenlabs-reference-architecture` skill.
