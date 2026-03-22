---
name: langfuse-core-workflow-a
description: |
  Execute Langfuse primary workflow: Tracing LLM calls and spans.
  Use when implementing LLM tracing, building traced AI features,
  or adding observability to existing LLM applications.
  Trigger with phrases like "langfuse tracing", "trace LLM calls",
  "add langfuse to openai", "langfuse spans", "track llm requests".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, observability, llm, workflow]

---
# Langfuse Core Workflow A: Tracing LLM Calls

## Overview
End-to-end tracing of LLM calls, chains, and agents. Covers the OpenAI drop-in wrapper, manual tracing with `startActiveObservation`, RAG pipeline instrumentation, streaming response tracking, and LangChain integration.

## Prerequisites
- Completed `langfuse-install-auth` setup
- OpenAI SDK installed (`npm install openai`)
- For v4+: `@langfuse/openai`, `@langfuse/tracing`, `@langfuse/otel`, `@opentelemetry/sdk-node`

## Instructions

### Step 1: OpenAI Drop-In Wrapper (Zero-Code Tracing)

```typescript
import OpenAI from "openai";
import { observeOpenAI } from "@langfuse/openai";

// Wrap the OpenAI client -- all calls are now traced automatically
const openai = observeOpenAI(new OpenAI());

// Every call captures: model, input, output, tokens, latency, cost
const response = await openai.chat.completions.create({
  model: "gpt-4o",
  messages: [
    { role: "system", content: "You are a helpful assistant." },
    { role: "user", content: "What is Langfuse?" },
  ],
});

// Add metadata to traces
const res = await observeOpenAI(new OpenAI(), {
  generationName: "product-description",
  generationMetadata: { feature: "onboarding" },
  sessionId: "session-abc",
  userId: "user-123",
  tags: ["production", "onboarding"],
}).chat.completions.create({
  model: "gpt-4o-mini",
  messages: [{ role: "user", content: "Describe this product" }],
});
```

### Step 2: Manual Tracing -- RAG Pipeline (v4+ SDK)

```typescript
import { startActiveObservation, updateActiveObservation } from "@langfuse/tracing";

async function ragPipeline(query: string) {
  return await startActiveObservation("rag-pipeline", async () => {
    updateActiveObservation({ input: { query }, metadata: { pipeline: "rag-v2" } });

    // Span: Query embedding
    const embedding = await startActiveObservation("embed-query", async () => {
      updateActiveObservation({ input: { text: query } });
      const vector = await embedText(query);
      updateActiveObservation({
        output: { dimensions: vector.length },
        metadata: { model: "text-embedding-3-small" },
      });
      return vector;
    });

    // Span: Vector search
    const documents = await startActiveObservation("vector-search", async () => {
      updateActiveObservation({ input: { dimensions: embedding.length } });
      const docs = await searchVectorDB(embedding);
      updateActiveObservation({
        output: { documentCount: docs.length, topScore: docs[0]?.score },
      });
      return docs;
    });

    // Generation: LLM call with context
    const answer = await startActiveObservation(
      { name: "generate-answer", asType: "generation" },
      async () => {
        updateActiveObservation({
          model: "gpt-4o",
          input: { query, context: documents.map((d) => d.content) },
        });

        const result = await generateAnswer(query, documents);

        updateActiveObservation({
          output: result.content,
          usage: {
            promptTokens: result.usage.prompt_tokens,
            completionTokens: result.usage.completion_tokens,
          },
        });
        return result.content;
      }
    );

    updateActiveObservation({ output: { answer } });
    return answer;
  });
}
```

### Step 3: Manual Tracing -- RAG Pipeline (v3 Legacy)

```typescript
import { Langfuse } from "langfuse";

const langfuse = new Langfuse();

async function ragPipeline(query: string) {
  const trace = langfuse.trace({
    name: "rag-pipeline",
    input: { query },
    metadata: { pipeline: "rag-v1" },
  });

  const embedSpan = trace.span({ name: "embed-query", input: { text: query } });
  const embedding = await embedText(query);
  embedSpan.end({ output: { dimensions: embedding.length } });

  const searchSpan = trace.span({ name: "vector-search" });
  const documents = await searchVectorDB(embedding);
  searchSpan.end({ output: { count: documents.length, topScore: documents[0]?.score } });

  const generation = trace.generation({
    name: "generate-answer",
    model: "gpt-4o",
    modelParameters: { temperature: 0.7, maxTokens: 500 },
    input: { query, context: documents.map((d) => d.content) },
  });

  const answer = await generateAnswer(query, documents);

  generation.end({
    output: answer.content,
    usage: {
      promptTokens: answer.usage.prompt_tokens,
      completionTokens: answer.usage.completion_tokens,
      totalTokens: answer.usage.total_tokens,
    },
  });

  trace.update({ output: { answer: answer.content } });
  await langfuse.flushAsync();
  return answer.content;
}
```

### Step 4: Streaming Response Tracking

```typescript
import OpenAI from "openai";
import { observeOpenAI } from "@langfuse/openai";

// The wrapper handles streaming automatically
const openai = observeOpenAI(new OpenAI());

const stream = await openai.chat.completions.create({
  model: "gpt-4o",
  messages: [{ role: "user", content: "Tell me a story" }],
  stream: true,
  stream_options: { include_usage: true }, // Required for token tracking
});

let fullContent = "";
for await (const chunk of stream) {
  const content = chunk.choices[0]?.delta?.content || "";
  fullContent += content;
  process.stdout.write(content);
}
// Token usage and latency are captured automatically by the wrapper
```

### Step 5: Anthropic Claude Tracing (Manual)

```typescript
import Anthropic from "@anthropic-ai/sdk";
import { startActiveObservation, updateActiveObservation } from "@langfuse/tracing";

const anthropic = new Anthropic();

async function callClaude(prompt: string) {
  return await startActiveObservation(
    { name: "claude-call", asType: "generation" },
    async () => {
      updateActiveObservation({
        model: "claude-sonnet-4-20250514",
        input: [{ role: "user", content: prompt }],
      });

      const response = await anthropic.messages.create({
        model: "claude-sonnet-4-20250514",
        max_tokens: 1024,
        messages: [{ role: "user", content: prompt }],
      });

      updateActiveObservation({
        output: response.content[0].text,
        usage: {
          promptTokens: response.usage.input_tokens,
          completionTokens: response.usage.output_tokens,
        },
      });

      return response.content[0].text;
    }
  );
}
```

### Step 6: LangChain Integration (Python)

```python
from langfuse.callback import CallbackHandler
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

langfuse_handler = CallbackHandler()

llm = ChatOpenAI(model="gpt-4o")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{input}"),
])

chain = prompt | llm

# All LangChain operations are automatically traced
result = chain.invoke(
    {"input": "What is Langfuse?"},
    config={"callbacks": [langfuse_handler]},
)
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing generations | OpenAI wrapper not applied | Use `observeOpenAI()` from `@langfuse/openai` |
| Orphaned spans | Missing end or callback finish | Use `startActiveObservation` (auto-ends) or `.end()` in `finally` |
| No token usage on stream | Stream usage not requested | Add `stream_options: { include_usage: true }` |
| Flat trace (no nesting) | Missing OTel context | Ensure `NodeSDK` is started with `LangfuseSpanProcessor` |

## Resources
- [OpenAI JS Integration](https://langfuse.com/integrations/model-providers/openai-js)
- [TypeScript Instrumentation](https://langfuse.com/docs/observability/sdk/typescript/instrumentation)
- [LangChain Integration](https://langfuse.com/integrations/frameworks/langchain)
- [Observation Types](https://langfuse.com/docs/observability/features/observation-types)

## Next Steps
For evaluation and scoring workflows, see `langfuse-core-workflow-b`.
