---
name: cohere-webhooks-events
description: |
  Implement Cohere streaming event handling, SSE patterns, and connector webhooks.
  Use when building streaming UIs, handling chat/tool events,
  or registering Cohere connectors for RAG.
  Trigger with phrases like "cohere streaming", "cohere events",
  "cohere SSE", "cohere connectors", "cohere webhook".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Streaming Events & Connectors

## Overview
Handle Cohere's streaming chat events (SSE), tool-call events, citation events, and register data connectors for RAG. Cohere does not use traditional webhooks — its event model is streaming-based.

## Prerequisites
- `cohere-ai` SDK v7+
- Understanding of Server-Sent Events (SSE)
- For connectors: HTTPS endpoint accessible from internet

## Instructions

### Step 1: Chat Streaming Events

Cohere's `chatStream` returns a stream of typed events:

```typescript
import { CohereClientV2 } from 'cohere-ai';

const cohere = new CohereClientV2();

async function handleStream(userMessage: string) {
  const stream = await cohere.chatStream({
    model: 'command-a-03-2025',
    messages: [{ role: 'user', content: userMessage }],
  });

  for await (const event of stream) {
    switch (event.type) {
      // Text content streaming
      case 'content-start':
        console.log('--- Generation started ---');
        break;

      case 'content-delta':
        const text = event.delta?.message?.content?.text ?? '';
        process.stdout.write(text);
        break;

      case 'content-end':
        console.log('\n--- Generation complete ---');
        break;

      // Citation events (when using documents)
      case 'citation-start':
        console.log('Citation:', event.delta?.message?.citations);
        break;

      // Tool call events (when using tools)
      case 'tool-call-start':
        console.log('Tool call started:', event.delta?.message?.toolCalls?.function?.name);
        break;

      case 'tool-call-delta':
        // Streaming tool arguments
        break;

      case 'tool-call-end':
        console.log('Tool call complete');
        break;

      // Message lifecycle
      case 'message-start':
        console.log('Message ID:', event.id);
        break;

      case 'message-end':
        console.log('Finish reason:', event.delta?.finishReason);
        console.log('Usage:', event.delta?.usage);
        break;
    }
  }
}
```

### Step 2: RAG Streaming with Citations

```typescript
async function streamRAG(query: string, docs: string[]) {
  const stream = await cohere.chatStream({
    model: 'command-a-03-2025',
    messages: [{ role: 'user', content: query }],
    documents: docs.map((text, i) => ({
      id: `doc-${i}`,
      data: { text },
    })),
  });

  let fullText = '';
  const citations: Array<{ start: number; end: number; text: string; sources: string[] }> = [];

  for await (const event of stream) {
    if (event.type === 'content-delta') {
      const chunk = event.delta?.message?.content?.text ?? '';
      fullText += chunk;
      process.stdout.write(chunk);
    }

    if (event.type === 'citation-start') {
      const cite = event.delta?.message?.citations;
      if (cite) {
        citations.push({
          start: cite.start,
          end: cite.end,
          text: cite.text,
          sources: cite.sources?.map((s: any) => s.id) ?? [],
        });
      }
    }
  }

  return { fullText, citations };
}
```

### Step 3: Streaming Tool Use

```typescript
const tools = [{
  type: 'function' as const,
  function: {
    name: 'get_price',
    description: 'Get stock price',
    parameters: {
      type: 'object' as const,
      properties: { ticker: { type: 'string' } },
      required: ['ticker'],
    },
  },
}];

async function streamToolUse(query: string) {
  const stream = await cohere.chatStream({
    model: 'command-a-03-2025',
    messages: [{ role: 'user', content: query }],
    tools,
  });

  let currentToolName = '';
  let currentToolArgs = '';

  for await (const event of stream) {
    switch (event.type) {
      case 'tool-call-start':
        currentToolName = event.delta?.message?.toolCalls?.function?.name ?? '';
        currentToolArgs = '';
        console.log(`Calling tool: ${currentToolName}`);
        break;

      case 'tool-call-delta':
        currentToolArgs += event.delta?.message?.toolCalls?.function?.arguments ?? '';
        break;

      case 'tool-call-end':
        console.log(`Tool args: ${currentToolArgs}`);
        // Execute tool here, then send results back
        break;

      case 'content-delta':
        process.stdout.write(event.delta?.message?.content?.text ?? '');
        break;
    }
  }
}
```

### Step 4: SSE Endpoint for Frontend

```typescript
// Express endpoint that proxies Cohere stream as SSE
import express from 'express';

const app = express();
app.use(express.json());

app.post('/api/chat/stream', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const cohere = new CohereClientV2();

  try {
    const stream = await cohere.chatStream({
      model: 'command-a-03-2025',
      messages: req.body.messages,
    });

    for await (const event of stream) {
      if (event.type === 'content-delta') {
        const text = event.delta?.message?.content?.text ?? '';
        res.write(`data: ${JSON.stringify({ type: 'text', text })}\n\n`);
      }

      if (event.type === 'citation-start') {
        res.write(`data: ${JSON.stringify({ type: 'citation', data: event.delta })}\n\n`);
      }

      if (event.type === 'message-end') {
        res.write(`data: ${JSON.stringify({ type: 'done', usage: event.delta?.usage })}\n\n`);
      }
    }

    res.write('data: [DONE]\n\n');
    res.end();
  } catch (err) {
    res.write(`data: ${JSON.stringify({ type: 'error', message: String(err) })}\n\n`);
    res.end();
  }
});
```

### Step 5: Cohere Connectors (Data Source Registration)

```typescript
// Register a custom data source for RAG queries
// Connectors allow Cohere to fetch documents from your APIs

// Create a connector
const connector = await cohere.connectors.create({
  name: 'internal-docs',
  url: 'https://api.yourapp.com/search',
  description: 'Internal documentation search',
});

// Use connector in chat for automatic retrieval
const response = await cohere.chat({
  model: 'command-a-03-2025',
  messages: [{ role: 'user', content: 'How do I reset my password?' }],
  connectors: [{ id: connector.connector.id }],
});

// List registered connectors
const connectors = await cohere.connectors.list();
console.log('Registered connectors:', connectors.connectors.length);
```

**Connector endpoint contract:** Your URL receives `POST { query: string }` and must return `{ results: [{ id, text, title?, url? }] }`.

## Event Type Reference

| Event | When | Contains |
|-------|------|----------|
| `message-start` | Stream begins | Message ID |
| `content-start` | Text generation starts | Content index |
| `content-delta` | Each text token | Text chunk |
| `content-end` | Text generation ends | - |
| `citation-start` | Citation found | Source, position |
| `tool-call-start` | Tool call begins | Tool name |
| `tool-call-delta` | Tool args streaming | Argument chunk |
| `tool-call-end` | Tool call complete | - |
| `message-end` | Stream ends | Finish reason, usage |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Stream drops mid-response | Network timeout | Set higher timeout, add reconnect |
| No citation events | No documents passed | Include `documents` param |
| Tool events but no content | Tool call in progress | Wait for tool results, re-stream |
| Connector returns empty | Bad search endpoint | Test endpoint with `curl` |

## Resources
- [Cohere Streaming Guide](https://docs.cohere.com/docs/streaming)
- [RAG Streaming](https://docs.cohere.com/docs/rag-streaming)
- [Tool Use Streaming](https://docs.cohere.com/docs/tool-use-streaming)
- [Connectors API](https://docs.cohere.com/reference/create-connector)

## Next Steps
For performance optimization, see `cohere-performance-tuning`.
