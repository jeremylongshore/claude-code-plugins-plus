---
name: langfuse-sdk-patterns
description: |
  Langfuse SDK best practices, patterns, and idiomatic usage.
  Use when learning Langfuse SDK patterns, implementing proper tracing,
  or following best practices for LLM observability.
  Trigger with phrases like "langfuse patterns", "langfuse best practices",
  "langfuse SDK guide", "how to use langfuse", "langfuse idioms".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, observability, llm, tracing]

---
# Langfuse SDK Patterns

## Overview
Production-quality patterns for the Langfuse SDK: singleton clients, the `observe` wrapper, `startActiveObservation` for nested traces, session tracking, graceful shutdown, and error-safe tracing.

## Prerequisites
- Completed `langfuse-install-auth` setup
- Understanding of async/await patterns
- For v4+: `@langfuse/tracing`, `@langfuse/otel`, `@opentelemetry/sdk-node`

## Instructions

### Pattern 1: Singleton Client with Graceful Shutdown

```typescript
// src/lib/langfuse.ts -- single file, import everywhere
import { LangfuseClient } from "@langfuse/client";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";

// Singleton client for prompts, datasets, scores
let client: LangfuseClient | null = null;
export function getLangfuseClient(): LangfuseClient {
  if (!client) {
    client = new LangfuseClient();
  }
  return client;
}

// One-time OTel setup (call at app entry point)
let sdk: NodeSDK | null = null;
export function initTracing(): NodeSDK {
  if (!sdk) {
    sdk = new NodeSDK({
      spanProcessors: [new LangfuseSpanProcessor()],
    });
    sdk.start();

    // Graceful shutdown on process exit
    const shutdown = async () => {
      await sdk?.shutdown();
      process.exit(0);
    };
    process.on("SIGTERM", shutdown);
    process.on("SIGINT", shutdown);
  }
  return sdk;
}
```

**Legacy v3 singleton:**
```typescript
import { Langfuse } from "langfuse";

let instance: Langfuse | null = null;

export function getLangfuse(): Langfuse {
  if (!instance) {
    instance = new Langfuse({
      flushAt: 15,
      flushInterval: 10000,
    });
    process.on("beforeExit", () => instance?.shutdownAsync());
  }
  return instance;
}
```

### Pattern 2: `observe` Wrapper for Existing Functions

The `observe` wrapper is the most ergonomic way to add tracing. It wraps any function and auto-creates a span.

```typescript
import { observe, updateActiveObservation } from "@langfuse/tracing";

// Wrap existing functions -- no internal changes needed
const fetchUserProfile = observe(async (userId: string) => {
  updateActiveObservation({ input: { userId } });
  const profile = await db.users.findById(userId);
  updateActiveObservation({ output: { found: !!profile } });
  return profile;
});

// Mark LLM calls as generations
const summarize = observe(
  { name: "summarize-text", asType: "generation" },
  async (text: string) => {
    updateActiveObservation({ model: "gpt-4o-mini", input: text });
    const result = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: `Summarize: ${text}` }],
    });
    const output = result.choices[0].message.content;
    updateActiveObservation({
      output,
      usage: {
        promptTokens: result.usage?.prompt_tokens,
        completionTokens: result.usage?.completion_tokens,
      },
    });
    return output;
  }
);

// When called inside another observed function, spans auto-nest
const pipeline = observe(async (userId: string) => {
  const profile = await fetchUserProfile(userId);
  const summary = await summarize(profile.bio);
  return { profile, summary };
});
```

### Pattern 3: `startActiveObservation` for Inline Control

Use when you need fine-grained control over observation lifecycle within a function:

```typescript
import { startActiveObservation, updateActiveObservation } from "@langfuse/tracing";

async function processOrder(orderId: string) {
  return await startActiveObservation("process-order", async () => {
    updateActiveObservation({ input: { orderId } });

    // Nested spans are automatic
    const validated = await startActiveObservation("validate", async () => {
      const result = await validateOrder(orderId);
      updateActiveObservation({ output: { valid: result.valid } });
      return result;
    });

    if (!validated.valid) {
      updateActiveObservation({ output: { error: "validation failed" } });
      return { success: false };
    }

    // Generation span for LLM call
    const description = await startActiveObservation(
      { name: "generate-confirmation", asType: "generation" },
      async () => {
        updateActiveObservation({ model: "gpt-4o-mini" });
        const result = await generateConfirmation(orderId);
        updateActiveObservation({ output: result });
        return result;
      }
    );

    updateActiveObservation({ output: { success: true } });
    return { success: true, description };
  });
}
```

### Pattern 4: Session and User Tracking

Link traces across conversation turns for user-level analytics:

```typescript
// v4+: Set session/user via observation metadata
await startActiveObservation("chat-turn", async () => {
  updateActiveObservation({
    metadata: {
      sessionId: "session-abc-123",
      userId: "user-456",
    },
  });
  // All nested observations inherit this context
  await handleUserMessage(message);
});

// v3: Set directly on trace
const trace = langfuse.trace({
  name: "chat-turn",
  sessionId: "session-abc-123", // Groups traces into a session
  userId: "user-456",           // Links to user analytics
  input: { message },
});
```

### Pattern 5: Error-Safe Tracing

Never let tracing failures break your application:

```typescript
import { observe, updateActiveObservation } from "@langfuse/tracing";

const safeObserve = <T extends (...args: any[]) => Promise<any>>(
  name: string,
  fn: T
): T => {
  return (async (...args: Parameters<T>) => {
    try {
      return await observe({ name }, async () => {
        updateActiveObservation({ input: args });
        const result = await fn(...args);
        updateActiveObservation({ output: result });
        return result;
      })();
    } catch (tracingError) {
      // If tracing fails, still run the function
      console.warn(`Tracing error in ${name}:`, tracingError);
      return fn(...args);
    }
  }) as T;
};

// Usage -- function works even if Langfuse is down
const processRequest = safeObserve("process-request", async (input: string) => {
  return await callLLM(input);
});
```

### Pattern 6: Legacy v3 -- Always End Spans

```typescript
// Always use try/finally to ensure .end() is called
const span = trace.span({ name: "risky-operation", input: data });
try {
  const result = await riskyOperation(data);
  span.end({ output: result });
  return result;
} catch (error) {
  span.end({ level: "ERROR", statusMessage: String(error) });
  throw error;
}
```

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Correct Pattern |
|-------------|---------|-----------------|
| `new Langfuse()` per request | Memory leaks, duplicate traces | Singleton client |
| Awaiting flush in hot path | Adds latency to every request | Background flush, shutdown handler |
| Logging full request bodies | Trace payloads too large | Truncate/summarize inputs |
| Missing `.end()` on spans (v3) | Spans show "in progress" forever | Use `try/finally` or `observe` wrapper |
| Hardcoding API keys | Security risk | Environment variables only |

## Resources
- [TypeScript SDK Instrumentation](https://langfuse.com/docs/observability/sdk/typescript/instrumentation)
- [Advanced SDK Configuration](https://langfuse.com/docs/observability/sdk/typescript/advanced-usage)
- [Python Decorators](https://langfuse.com/docs/sdk/python/decorators)
- [Event Queuing/Batching](https://langfuse.com/docs/observability/features/queuing-batching)

## Next Steps
For OpenAI/LangChain tracing examples, see `langfuse-core-workflow-a`.
