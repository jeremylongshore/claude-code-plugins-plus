# Groq Migration — Worked Examples & Compatibility

Concrete, runnable examples that go with the migration workflow: a
side-by-side quality/speed benchmark, and the full feature-compatibility
matrix between OpenAI and Groq so you know exactly what carries over and what
you must keep on your old provider.

## Example: Comparison Benchmark

Run the same prompts through both providers to compare quality AND latency
before you shift real traffic. This is how you justify the migration with
numbers rather than vibes.

```typescript
// Run the same prompts through both providers to compare quality + speed
async function migrationBenchmark(prompts: string[]) {
  const groq = new GroqProvider();
  const openai = new OpenAIProvider();

  for (const prompt of prompts) {
    const messages = [{ role: "user" as const, content: prompt }];

    const startGroq = performance.now();
    const groqResult = await groq.complete(messages, "llama-3.3-70b-versatile", 256);
    const groqMs = performance.now() - startGroq;

    const startOAI = performance.now();
    const oaiResult = await openai.complete(messages, "gpt-4o-mini", 256);
    const oaiMs = performance.now() - startOAI;

    console.log(`Prompt: "${prompt.slice(0, 50)}..."`);
    console.log(`  Groq:   ${groqMs.toFixed(0)}ms | ${groqResult.tokens.total} tokens`);
    console.log(`  OpenAI: ${oaiMs.toFixed(0)}ms | ${oaiResult.tokens.total} tokens`);
    console.log(`  Speedup: ${(oaiMs / groqMs).toFixed(1)}x faster with Groq`);
    console.log();
  }
}
```

## Key Differences to Handle

The feature-compatibility matrix. Most chat.completions usage ports 1:1;
the rows to watch are embeddings, fine-tuning, and image generation — Groq
does not offer these, so keep OpenAI (or a local model) for those paths.

| Feature | OpenAI | Groq |
|---------|--------|------|
| SDK import | `import OpenAI from "openai"` | `import Groq from "groq-sdk"` |
| Env var | `OPENAI_API_KEY` | `GROQ_API_KEY` |
| Models | `gpt-4o`, `gpt-4o-mini` | `llama-3.3-70b-versatile`, `llama-3.1-8b-instant` |
| Embeddings | `openai.embeddings.create()` | Not available (use OpenAI or local) |
| Fine-tuning | Supported | Not available |
| Image generation | `openai.images.generate()` | Not available |
| Audio (STT) | `openai.audio.transcriptions` | `groq.audio.transcriptions` (faster) |
| Structured outputs | `strict: true` | `strict: true` (same format) |
| Tool calling | Supported | Supported (same format) |
| JSON mode | `response_format: { type: "json_object" }` | Same |
| Vision | `gpt-4o` with images | Llama 4 Scout/Maverick |
| Streaming | Supported | Supported (same SSE format) |
| Response usage | Standard fields | Adds `queue_time`, `completion_time`, `total_time` |
