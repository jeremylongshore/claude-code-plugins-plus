# Groq Performance Tuning — Worked Examples

Each example maps a real scenario to the tuning levers from
[implementation.md](implementation.md). Assumes a shared `new Groq()` client
plus the `tieredCompletion`, `streamWithMetrics`, `cachedCompletion`, and
`parallelCompletions` helpers defined there.

## Example 1: Latency-critical classification (cache + tiny max_tokens)

Sentiment classification on a hot path. Use the `instant` tier, a one-word
prompt, `max_tokens: 5`, and the deterministic cache so repeat inputs return
instantly.

```typescript
const label = await cachedCompletion(
  [
    { role: "system", content: "Classify as positive/negative/neutral. One word only." },
    { role: "user", content: "This product exceeded every expectation." },
  ],
  "llama-3.1-8b-instant"
);
// => "positive"  (first call ~50ms TTFT; subsequent identical calls ~0ms from cache)
```

## Example 2: Interactive chat (streaming for perceived speed)

A chat surface where the user watches tokens arrive. Stream with the
`balanced` 70b model and surface live metrics.

```typescript
const { content, ttftMs, tokPerSec } = await streamWithMetrics(
  [{ role: "user", content: "Explain LPU inference in two sentences." }],
  (token) => process.stdout.write(token)
);
console.log(`\n[TTFT ${ttftMs}ms | ${tokPerSec} tok/s]`);
```

## Example 3: Bulk processing under rate limits (parallel + queue)

Classify 500 records without tripping the RPM/TPM ceiling. `parallelCompletions`
wraps each call in a `p-queue` that caps concurrency and per-minute volume, and
reuses the cache for duplicate rows.

```typescript
const rows = await loadRecords();               // string[] of 500 items
const labels = await parallelCompletions(
  rows.map((r) => `Classify as positive/negative/neutral. One word only.\n${r}`),
  "llama-3.1-8b-instant"
);
```

## Example 4: Picking a model empirically (benchmark then commit)

Before hardcoding a model, measure the three speed tiers against your real
prompt shape and pick the fastest that meets your quality bar.

```typescript
await benchmarkModels("Summarize this support ticket in one line: ...");
// llama-3.1-8b-instant     |  61ms avg | 548 tok/s avg
// llama-3.3-70b-versatile  | 148ms avg | 279 tok/s avg
// llama-3.3-70b-specdec    | 103ms avg | 401 tok/s avg
```

## Reading the numbers

- **TTFT dominates perceived latency** for short outputs — favor `8b-instant`
  or `70b-specdec` on interactive paths.
- **Throughput dominates total time** for long generations — streaming hides
  TTFT but not total wall-clock.
- **Cache hit rate** is the single biggest win for repeated deterministic
  prompts; normalize prompts so semantically-identical requests hash the same.
