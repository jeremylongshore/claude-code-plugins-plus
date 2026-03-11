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
---
# Langfuse Core Workflow A: Tracing LLM Calls

## Overview
Primary workflow for Langfuse: end-to-end tracing of LLM calls, chains, and agents.

## Prerequisites
- Completed `langfuse-install-auth` setup
- Understanding of Langfuse trace hierarchy
- LLM provider SDK (OpenAI, Anthropic, etc.)

## Instructions

### Step 1: Set Up Automatic OpenAI Tracing

```typescript
import { observeOpenAI } from "langfuse";
import OpenAI from "openai";

// Wrap OpenAI client for automatic tracing
const openai = observeOpenAI(new OpenAI());

// All calls are now automatically traced
const response = await openai.chat.completions.create({
  model: "gpt-4",
  messages: [
    { role: "system", content: "You are a helpful assistant." },
    { role: "user", content: "What is Langfuse?" },
  ],
});
```

### Step 2: Manual Tracing for Complex Flows

```typescript
import { Langfuse } from "langfuse";

const langfuse = new Langfuse();

async function ragPipeline(query: string) {
  // Create top-level trace
  const trace = langfuse.trace({
    name: "rag-pipeline",
    input: { query },
    metadata: { pipeline: "rag-v1" },
  });

  // Span: Query embedding
  const embedSpan = trace.span({
    name: "embed-query",
    input: { text: query },
  });

  const queryEmbedding = await embedText(query);

  embedSpan.end({
    output: { dimensions: queryEmbedding.length },
    metadata: { model: "text-embedding-ada-002" },
  });

  // Span: Vector search
  const searchSpan = trace.span({
    name: "vector-search",
    input: { embedding: "vector[1536]" },  # 1536 = configured value
  });

  const documents = await searchVectorDB(queryEmbedding);

  searchSpan.end({
    output: {
      documentCount: documents.length,
      topScore: documents[0]?.score,
    },
  });

  // Generation: LLM call with context
  const generation = trace.generation({
    name: "generate-answer",
    model: "gpt-4",
    modelParameters: { temperature: 0.7, maxTokens: 500 },  # HTTP 500 Internal Server Error
    input: {
      query,
      context: documents.map((d) => d.content),
    },
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

  // Update trace with final output
  trace.update({
    output: { answer: answer.content },
  });

  return answer.content;
}
```

### Step 3: Trace Streaming Responses

```typescript
async function streamingChat(messages: ChatMessage[]) {
  const trace = langfuse.trace({
    name: "streaming-chat",
    input: { messages },
  });

  const generation = trace.generation({
    name: "stream-response",
    model: "gpt-4",
    input: messages,
  });

  const stream = await openai.chat.completions.create({
    model: "gpt-4",
    messages,
    stream: true,
  });

  let fullContent = "";
  let usage = { promptTokens: 0, completionTokens: 0 };

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || "";
    fullContent += content;

    // Track usage from final chunk
    if (chunk.usage) {
      usage = {
        promptTokens: chunk.usage.prompt_tokens,
        completionTokens: chunk.usage.completion_tokens,
      };
    }

    yield content;
  }

  // End generation after stream completes
  generation.end({
    output: fullContent,
    usage,
  });

  trace.update({ output: { response: fullContent } });
}
```

### Step 4: Link Traces to Parent Operations

```typescript
// API endpoint that creates parent trace
async function handleChatRequest(req: Request) {
  const trace = langfuse.trace({
    name: "api/chat",
    userId: req.userId,
    sessionId: req.sessionId,
    input: req.body,
  });

  // Pass trace to child operations
  const response = await processChat(trace, req.body.message);

  return response;
}

// Child function receives parent trace
async function processChat(
  parentTrace: ReturnType<typeof langfuse.trace>,
  message: string
) {
  // Create child span under parent trace
  const span = parentTrace.span({
    name: "process-chat",
    input: { message },
  });

  // OpenAI call linked to parent
  const response = await openai.chat.completions.create(
    {
      model: "gpt-4",
      messages: [{ role: "user", content: message }],
    },
    { langfuseParent: span } // Link generation to span
  );

  span.end({ output: response.choices[0].message });
  return response.choices[0].message.content;
}
```

## Output
- Automatic OpenAI tracing with zero code changes
- Manual tracing for RAG and complex pipelines
- Streaming response tracking
- Linked parent-child trace hierarchy

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing generations | Wrapper not applied | Use `observeOpenAI()` wrapper |
| Orphaned spans | Missing `.end()` call | Always end spans in finally block |
| No token usage | Stream without usage | Use `stream_options: {include_usage: true}` |
| Broken hierarchy | Missing parent link | Pass `langfuseParent` option |

## Examples

### Anthropic Claude Tracing
```typescript
import Anthropic from "@anthropic-ai/sdk";
import { Langfuse } from "langfuse";

const anthropic = new Anthropic();
const langfuse = new Langfuse();

async function callClaude(prompt: string) {
  const trace = langfuse.trace({ name: "claude-call", input: { prompt } });

  const generation = trace.generation({
    name: "claude-response",
    model: "claude-3-sonnet-20240229",  # 20240229 = configured value
    input: [{ role: "user", content: prompt }],
  });

  const response = await anthropic.messages.create({
    model: "claude-3-sonnet-20240229",
    max_tokens: 1024,  # 1024: 1 KB
    messages: [{ role: "user", content: prompt }],
  });

  generation.end({
    output: response.content[0].text,
    usage: {
      promptTokens: response.usage.input_tokens,
      completionTokens: response.usage.output_tokens,
    },
  });

  return response.content[0].text;
}
```

### LangChain Integration
```python
from langchain.callbacks import LangfuseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

# Create callback handler
langfuse_handler = LangfuseCallbackHandler()

# Pass to LLM
llm = ChatOpenAI(callbacks=[langfuse_handler])

# All LangChain operations are now traced
response = llm([HumanMessage(content="Hello!")])
```

### Tool/Function Calling Tracing
```typescript
async function tracedToolCall(trace: Trace, toolName: string, args: any) {
  const span = trace.span({
    name: `tool/${toolName}`,
    input: args,
    metadata: { type: "tool-call" },
  });

  try {
    const result = await executeTool(toolName, args);
    span.end({ output: result });
    return result;
  } catch (error) {
    span.end({
      level: "ERROR",
      statusMessage: String(error),
    });
    throw error;
  }
}
```

## Resources
- [Langfuse Tracing Guide](https://langfuse.com/docs/tracing)
- [OpenAI Integration](https://langfuse.com/docs/integrations/openai)
- [LangChain Integration](https://langfuse.com/docs/integrations/langchain)
- [Streaming Guide](https://langfuse.com/docs/tracing-features/sessions)

## Next Steps
For evaluation and scoring workflows, see `langfuse-core-workflow-b`.