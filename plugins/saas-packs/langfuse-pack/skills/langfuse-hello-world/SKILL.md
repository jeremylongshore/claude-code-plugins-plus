---
name: langfuse-hello-world
description: |
  Create a minimal working Langfuse trace example.
  Use when starting a new Langfuse integration, testing your setup,
  or learning basic Langfuse tracing patterns.
  Trigger with phrases like "langfuse hello world", "langfuse example",
  "langfuse quick start", "first langfuse trace", "simple langfuse code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, testing, tracing]

---
# Langfuse Hello World

## Overview
Create your first Langfuse trace with real SDK calls. Demonstrates the trace/span/generation hierarchy, the `observe` wrapper, and the OpenAI drop-in integration.

## Prerequisites
- Completed `langfuse-install-auth` setup
- Valid API credentials in environment variables
- OpenAI API key (for the OpenAI integration example)

## Instructions

### Step 1: Hello World with v4+ Modular SDK

```typescript
// hello-langfuse.ts
import { startActiveObservation, observe, updateActiveObservation } from "@langfuse/tracing";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";

// Register OpenTelemetry processor (once at startup)
const sdk = new NodeSDK({
  spanProcessors: [new LangfuseSpanProcessor()],
});
sdk.start();

async function main() {
  // Create a top-level trace with startActiveObservation
  await startActiveObservation("hello-world", async (span) => {
    span.update({
      input: { message: "Hello, Langfuse!" },
      metadata: { source: "hello-world-example" },
    });

    // Nested span -- automatically linked to parent
    await startActiveObservation("process-input", async (child) => {
      child.update({ input: { text: "processing..." } });
      await new Promise((r) => setTimeout(r, 100));
      child.update({ output: { result: "done" } });
    });

    // Nested generation (LLM call tracking)
    await startActiveObservation(
      { name: "llm-response", asType: "generation" },
      async (gen) => {
        gen.update({
          model: "gpt-4o",
          input: [{ role: "user", content: "Say hello" }],
          output: { content: "Hello! How can I help you today?" },
          usage: { promptTokens: 5, completionTokens: 10, totalTokens: 15 },
        });
      }
    );

    span.update({ output: { status: "completed" } });
  });

  // Allow time for the span processor to flush
  await sdk.shutdown();
  console.log("Trace created! Check your Langfuse dashboard.");
}

main().catch(console.error);
```

### Step 2: Hello World with `observe` Wrapper

The `observe` wrapper traces existing functions without modifying internals:

```typescript
import { observe, updateActiveObservation } from "@langfuse/tracing";

// Wrap any async function -- it becomes a traced span
const processQuery = observe(async (query: string) => {
  updateActiveObservation({ input: { query } });

  // Simulate processing
  const result = `Processed: ${query}`;

  updateActiveObservation({ output: { result } });
  return result;
});

// Wrap an LLM call as a generation
const generateAnswer = observe(
  { name: "generate-answer", asType: "generation" },
  async (prompt: string) => {
    updateActiveObservation({
      model: "gpt-4o",
      input: [{ role: "user", content: prompt }],
    });

    const answer = "Langfuse is an open-source LLM observability platform.";

    updateActiveObservation({
      output: answer,
      usage: { promptTokens: 10, completionTokens: 20 },
    });
    return answer;
  }
);

// Both functions auto-nest when called within an observed context
const pipeline = observe(async () => {
  await processQuery("What is Langfuse?");
  await generateAnswer("Explain Langfuse in one sentence.");
});

await pipeline();
```

### Step 3: Hello World with Legacy v3 SDK

```typescript
import { Langfuse } from "langfuse";

const langfuse = new Langfuse();

async function helloLangfuse() {
  const trace = langfuse.trace({
    name: "hello-world",
    userId: "demo-user",
    metadata: { source: "hello-world-example" },
    tags: ["demo", "getting-started"],
  });

  // Span: child operation
  const span = trace.span({
    name: "process-input",
    input: { message: "Hello, Langfuse!" },
  });
  await new Promise((r) => setTimeout(r, 100));
  span.end({ output: { result: "Processed successfully!" } });

  // Generation: LLM call tracking
  trace.generation({
    name: "llm-response",
    model: "gpt-4o",
    input: [{ role: "user", content: "Say hello" }],
    output: { content: "Hello! How can I help you today?" },
    usage: { promptTokens: 5, completionTokens: 10, totalTokens: 15 },
  });

  await langfuse.flushAsync();
  console.log("Trace URL:", trace.getTraceUrl());
}

helloLangfuse();
```

### Step 4: Python Hello World

```python
from langfuse.decorators import observe, langfuse_context

@observe()
def process_query(query: str) -> str:
    return f"Processed: {query}"

@observe(as_type="generation")
def generate_response(prompt: str) -> str:
    langfuse_context.update_current_observation(
        model="gpt-4o",
        usage={"prompt_tokens": 10, "completion_tokens": 20},
    )
    return "Hello from Langfuse!"

@observe()
def main():
    result = process_query("Hello!")
    response = generate_response("Say hello")
    return response

main()
```

## Trace Hierarchy

```
Trace: hello-world
  ├── Span: process-input
  │     input: { message: "Hello, Langfuse!" }
  │     output: { result: "Processed successfully!" }
  └── Generation: llm-response
        model: gpt-4o
        input: [{ role: "user", content: "Say hello" }]
        output: "Hello! How can I help you today?"
        usage: { promptTokens: 5, completionTokens: 10 }
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Import error | SDK not installed | `npm install @langfuse/tracing @langfuse/otel @opentelemetry/sdk-node` |
| Auth error (401) | Invalid credentials | Verify `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` |
| Trace not appearing | Data not flushed | Call `sdk.shutdown()` (v4+) or `langfuse.flushAsync()` (v3) |
| Network error | Host unreachable | Check `LANGFUSE_BASE_URL` value |
| No auto-nesting | Missing OTel setup | Register `LangfuseSpanProcessor` with `NodeSDK` |

## Resources
- [Langfuse JS/TS SDK Cookbook](https://langfuse.com/guides/cookbook/js_langfuse_sdk)
- [TypeScript SDK Instrumentation](https://langfuse.com/docs/observability/sdk/typescript/instrumentation)
- [Python Decorators Guide](https://langfuse.com/docs/sdk/python/decorators)
- [Observation Types](https://langfuse.com/docs/observability/features/observation-types)

## Next Steps
Proceed to `langfuse-core-workflow-a` for real OpenAI/Anthropic tracing, or `langfuse-local-dev-loop` for development workflow setup.
