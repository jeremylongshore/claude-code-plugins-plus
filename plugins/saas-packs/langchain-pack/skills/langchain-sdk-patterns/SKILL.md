---
name: langchain-sdk-patterns
description: |
  Apply production-ready LangChain SDK patterns for structured output,
  fallbacks, batch processing, streaming, and caching.
  Trigger: "langchain SDK patterns", "langchain best practices",
  "idiomatic langchain", "langchain architecture", "withStructuredOutput",
  "withFallbacks", "abatch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, langchain-sdk]

---
# LangChain SDK Patterns

## Overview

Production-grade patterns every LangChain application should use: type-safe structured output, provider fallbacks, async batch processing, streaming, caching, and retry logic.

## Pattern 1: Structured Output with Zod

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { z } from "zod";

const ExtractedData = z.object({
  entities: z.array(z.object({
    name: z.string(),
    type: z.enum(["person", "org", "location"]),
    confidence: z.number().min(0).max(1),
  })),
  language: z.string(),
  summary: z.string(),
});

const model = new ChatOpenAI({ model: "gpt-4o-mini" });
const structuredModel = model.withStructuredOutput(ExtractedData);

const prompt = ChatPromptTemplate.fromTemplate(
  "Extract entities from this text:\n\n{text}"
);

const chain = prompt.pipe(structuredModel);

const result = await chain.invoke({
  text: "Satya Nadella announced Microsoft's new AI lab in Seattle.",
});
// result is fully typed: { entities: [...], language: "en", summary: "..." }
```

## Pattern 2: Provider Fallbacks

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";

const primary = new ChatOpenAI({
  model: "gpt-4o",
  maxRetries: 2,
  timeout: 10000,
});

const fallback = new ChatAnthropic({
  model: "claude-sonnet-4-20250514",
});

// Automatically falls back on any error (rate limit, timeout, 500)
const robustModel = primary.withFallbacks({
  fallbacks: [fallback],
});

// Works identically to a normal model
const chain = prompt.pipe(robustModel).pipe(new StringOutputParser());
```

## Pattern 3: Async Batch Processing

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const chain = ChatPromptTemplate.fromTemplate("Summarize: {text}")
  .pipe(new ChatOpenAI({ model: "gpt-4o-mini" }))
  .pipe(new StringOutputParser());

const texts = ["Article 1...", "Article 2...", "Article 3..."];
const inputs = texts.map((text) => ({ text }));

// Process all inputs with controlled concurrency
const results = await chain.batch(inputs, {
  maxConcurrency: 5,   // max 5 parallel API calls
});
// results: string[] — one summary per input
```

## Pattern 4: Streaming with Token Callbacks

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const chain = ChatPromptTemplate.fromTemplate("{input}")
  .pipe(new ChatOpenAI({ model: "gpt-4o-mini", streaming: true }))
  .pipe(new StringOutputParser());

// Stream string chunks
const stream = await chain.stream({ input: "Tell me a story" });
for await (const chunk of stream) {
  process.stdout.write(chunk);  // each chunk is a string fragment
}
```

## Pattern 5: Retry with Exponential Backoff

```typescript
import { ChatOpenAI } from "@langchain/openai";

// Built-in retry handles transient failures
const model = new ChatOpenAI({
  model: "gpt-4o-mini",
  maxRetries: 3,        // retries with exponential backoff
  timeout: 30000,       // 30s timeout per request
});

// Manual retry wrapper for custom logic
async function invokeWithRetry<T>(
  chain: { invoke: (input: any) => Promise<T> },
  input: any,
  maxRetries = 3,
): Promise<T> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await chain.invoke(input);
    } catch (error: any) {
      if (attempt === maxRetries - 1) throw error;
      const delay = Math.min(1000 * 2 ** attempt, 30000);
      console.warn(`Retry ${attempt + 1}/${maxRetries} after ${delay}ms`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}
```

## Pattern 6: Caching (Python)

```python
from langchain_openai import ChatOpenAI
from langchain_core.globals import set_llm_cache
from langchain_community.cache import SQLiteCache

# Enable persistent caching — identical inputs skip the API
set_llm_cache(SQLiteCache(database_path=".langchain_cache.db"))

llm = ChatOpenAI(model="gpt-4o-mini")

# First call: hits API (~500ms)
r1 = llm.invoke("What is 2+2?")

# Second identical call: cache hit (~0ms, no cost)
r2 = llm.invoke("What is 2+2?")
```

## Pattern 7: RunnableLambda for Custom Logic

```typescript
import { RunnableLambda } from "@langchain/core/runnables";

// Wrap any function as a Runnable to use in chains
const cleanInput = RunnableLambda.from((input: { text: string }) => ({
  text: input.text.trim().toLowerCase(),
}));

const addMetadata = RunnableLambda.from((result: string) => ({
  answer: result,
  timestamp: new Date().toISOString(),
  model: "gpt-4o-mini",
}));

const chain = cleanInput
  .pipe(prompt)
  .pipe(model)
  .pipe(new StringOutputParser())
  .pipe(addMetadata);
```

## Anti-Patterns to Avoid

| Anti-Pattern | Why | Better |
|-------------|-----|--------|
| Hardcoded API keys | Security risk | Use env vars + `dotenv` |
| No error handling | Silent failures | Use `.withFallbacks()` + try/catch |
| Sequential when parallel works | Slow | Use `RunnableParallel` or `.batch()` |
| Parsing raw LLM text | Fragile | Use `.withStructuredOutput(zodSchema)` |
| No timeout | Hanging requests | Set `timeout` on model constructor |
| No streaming in UIs | Bad UX | Use `.stream()` for user-facing output |

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `ZodError` | LLM output doesn't match schema | Improve prompt or relax schema with `.optional()` |
| `RateLimitError` | API quota exceeded | Add `maxRetries`, use `.withFallbacks()` |
| `TimeoutError` | Slow response | Increase `timeout`, try smaller model |
| `OutputParserException` | Unparseable output | Switch to `.withStructuredOutput()` |

## Resources

- [LCEL How-To](https://js.langchain.com/docs/how_to/)
- [Structured Output](https://js.langchain.com/docs/how_to/structured_output/)
- [Fallbacks](https://js.langchain.com/docs/how_to/fallbacks/)
- [Streaming](https://js.langchain.com/docs/how_to/streaming/)

## Next Steps

Proceed to `langchain-data-handling` for data privacy patterns.
