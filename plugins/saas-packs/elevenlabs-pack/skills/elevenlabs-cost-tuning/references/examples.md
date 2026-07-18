# ElevenLabs Cost Tuning — Worked Examples

Concrete end-to-end scenarios built from the helpers in
[implementation.md](implementation.md). Each example wires the same functions together to
solve a real cost problem.

## Example 1: Check quota before a batch run

Print the current quota picture and bail out early if the run would exceed the remaining
character budget.

```typescript
import { getQuotaStatus } from "./elevenlabs/quota-monitor";

const q = await getQuotaStatus();
console.log(`Plan: ${q.plan} — ${q.pctUsed}% used, ${q.remaining.toLocaleString()} chars left`);

const batch = ["Welcome!", "Your order shipped.", "Thanks for calling."];
const batchChars = batch.reduce((sum, t) => sum + t.length, 0);

if (batchChars > q.remaining) {
  console.error(`Batch needs ${batchChars} chars, only ${q.remaining} remain — aborting.`);
} else {
  console.log(`Safe to run: ${batchChars} of ${q.remaining} remaining chars.`);
}
```

## Example 2: Route content to the cheapest acceptable model

Use `selectCostEffectiveModel` to send functional audio through Flash (0.5x) while
reserving full-price models for premium, customer-facing output.

```typescript
import { guardedTTS } from "./elevenlabs/cost-aware-tts";

// Notifications go through Flash automatically → 50% savings
await guardedTTS("Your table is ready.", VOICE_ID, "notification");

// Premium greeting keeps eleven_v3 quality — unless quota is critically low,
// in which case guardedTTS() downgrades to Flash to avoid an overage.
await guardedTTS("Welcome to the Grand Hotel.", VOICE_ID, "premium");
```

## Example 3: Trim characters before billing counts them

`optimizeTextForTTS` strips markdown, HTML, and redundant whitespace/punctuation — every
removed character is a character you are not billed for.

```typescript
import { optimizeTextForTTS } from "./elevenlabs/text-optimizer";

const raw = "**Welcome!!!**   Visit [our site](https://example.com) for   more...";
const { optimized, originalLength, savedCharacters } = optimizeTextForTTS(raw);

console.log(optimized);        // "Welcome! Visit our site for more."
console.log(`${savedCharacters} of ${originalLength} characters saved`);
```

## Example 4: Roll up spend for the last 30 days

Feed each request through `trackUsage`, then summarize with `getUsageSummary` to see where
credits actually go and how well caching is working.

```typescript
const summary = getUsageSummary(30);
console.log(`Total credits: ${summary.totalCredits.toLocaleString()}`);
console.log(`Cache hit rate: ${(summary.cacheHitRate * 100).toFixed(1)}%`);
console.log("Credits by model:", summary.byModel);
```
