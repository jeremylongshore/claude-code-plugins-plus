---
name: langchain-performance-tuning
description: |
  Optimize LangChain application performance: latency, throughput,
  streaming, caching, batch processing, and connection pooling.
  Trigger: "langchain performance", "langchain optimization",
  "langchain latency", "langchain slow", "speed up langchain".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, performance]

---
# LangChain Performance Tuning

## Overview

Optimize LangChain apps for production: measure baseline latency, implement caching, batch with concurrency control, stream for perceived speed, optimize prompts for fewer tokens, and select the right model for each task.

## Step 1: Benchmark Baseline

```typescript
async function benchmark(
  chain: { invoke: (input: any) => Promise<any> },
  input: any,
  iterations = 5,
) {
  const times: number[] = [];

  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    await chain.invoke(input);
    times.push(performance.now() - start);
  }

  times.sort((a, b) => a - b);
  return {
    mean: (times.reduce((a, b) => a + b, 0) / times.length).toFixed(0) + "ms",
    median: times[Math.floor(times.length / 2)].toFixed(0) + "ms",
    p95: times[Math.floor(times.length * 0.95)].toFixed(0) + "ms",
    min: times[0].toFixed(0) + "ms",
    max: times[times.length - 1].toFixed(0) + "ms",
  };
}

// Usage
const results = await benchmark(chain, { input: "test" }, 10);
console.table(results);
```

## Step 2: Streaming (Perceived Performance)

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const chain = ChatPromptTemplate.fromTemplate("{input}")
  .pipe(new ChatOpenAI({ model: "gpt-4o-mini", streaming: true }))
  .pipe(new StringOutputParser());

// Non-streaming: user waits 2-3s for full response
// Streaming: first token in ~200ms, user sees progress immediately

const stream = await chain.stream({ input: "Explain LCEL" });
for await (const chunk of stream) {
  process.stdout.write(chunk);
}

// Express SSE endpoint for web apps
app.post("/api/chat/stream", async (req, res) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");

  const stream = await chain.stream({ input: req.body.input });
  for await (const chunk of stream) {
    res.write(`data: ${JSON.stringify({ text: chunk })}\n\n`);
  }
  res.write("data: [DONE]\n\n");
  res.end();
});
```

## Step 3: Batch Processing with Concurrency

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const chain = ChatPromptTemplate.fromTemplate("Summarize: {text}")
  .pipe(new ChatOpenAI({ model: "gpt-4o-mini" }))
  .pipe(new StringOutputParser());

const inputs = articles.map((text) => ({ text }));

// Sequential: ~10s for 10 items (1s each)
// const results = [];
// for (const input of inputs) results.push(await chain.invoke(input));

// Batch: ~2s for 10 items (parallel API calls)
const results = await chain.batch(inputs, {
  maxConcurrency: 10,
});

// Benchmark comparison
console.time("sequential");
for (const i of inputs.slice(0, 5)) await chain.invoke(i);
console.timeEnd("sequential");

console.time("batch");
await chain.batch(inputs.slice(0, 5), { maxConcurrency: 5 });
console.timeEnd("batch");
```

## Step 4: Caching

```typescript
// In-memory cache (single process, resets on restart)
const cache = new Map<string, string>();

async function cachedInvoke(
  chain: any,
  input: Record<string, any>,
): Promise<string> {
  const key = JSON.stringify(input);
  const cached = cache.get(key);
  if (cached) return cached;

  const result = await chain.invoke(input);
  cache.set(key, result);
  return result;
}

// Cache hit: ~0ms (vs ~500-2000ms for API call)
```

```python
# Python — built-in caching
from langchain_core.globals import set_llm_cache
from langchain_community.cache import SQLiteCache, InMemoryCache

# Option 1: In-memory (single process)
set_llm_cache(InMemoryCache())

# Option 2: SQLite (persistent, survives restarts)
set_llm_cache(SQLiteCache(database_path=".langchain_cache.db"))

# Option 3: Redis (distributed, production)
from langchain_community.cache import RedisCache
import redis
set_llm_cache(RedisCache(redis.Redis.from_url("redis://localhost:6379")))
```

## Step 5: Model Selection by Task

```typescript
import { ChatOpenAI } from "@langchain/openai";

// Fast + cheap: simple tasks, classification, extraction
const fast = new ChatOpenAI({
  model: "gpt-4o-mini",    // ~200ms TTFT, $0.15/1M input
  temperature: 0,
});

// Powerful + slower: complex reasoning, code generation
const powerful = new ChatOpenAI({
  model: "gpt-4o",          // ~400ms TTFT, $2.50/1M input
  temperature: 0,
});

// Route based on task
import { RunnableBranch } from "@langchain/core/runnables";

const router = RunnableBranch.from([
  [(input: any) => input.task === "classify", classifyChain],
  [(input: any) => input.task === "reason", reasoningChain],
  defaultChain,
]);
```

## Step 6: Prompt Optimization

```typescript
// Shorter prompts = fewer input tokens = lower latency + cost

// BEFORE (150+ tokens):
const verbose = `You are an expert AI assistant specialized in software
engineering. Your task is to carefully analyze the following code and
provide a comprehensive review covering all aspects including...`;

// AFTER (20 tokens, same quality):
const concise = "Review this code. List issues and fixes:\n\n{code}";

// Token counting (Python)
// import tiktoken
// enc = tiktoken.encoding_for_model("gpt-4o-mini")
// print(len(enc.encode(prompt)))  # check before deploying
```

## Performance Impact Summary

| Optimization | Latency Improvement | Cost Impact |
|-------------|---------------------|-------------|
| Streaming | First token 80% faster | Neutral |
| Caching | 99% on cache hit | Major savings |
| Batch processing | 50-80% for bulk ops | Neutral |
| gpt-4o-mini vs gpt-4o | ~2x faster TTFT | ~17x cheaper |
| Shorter prompts | 10-30% | 10-50% cheaper |
| maxConcurrency tuning | Linear scaling | Neutral |

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Batch partially fails | Rate limit on some items | Lower `maxConcurrency`, add `maxRetries` |
| Stream hangs | Network timeout | Set `timeout` on model, handle disconnect |
| Cache stale data | Content changed upstream | Add TTL or version key to cache |
| High memory usage | Large cache | Use LRU eviction or Redis |

## Resources

- [LangChain Streaming Guide](https://js.langchain.com/docs/how_to/streaming/)
- [Batch Processing](https://js.langchain.com/docs/how_to/batch/)
- [OpenAI Latency Guide](https://platform.openai.com/docs/guides/latency-optimization)

## Next Steps

Use `langchain-cost-tuning` for cost optimization alongside performance.
