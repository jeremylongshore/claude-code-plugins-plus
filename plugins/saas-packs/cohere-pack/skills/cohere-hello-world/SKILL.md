---
name: cohere-hello-world
description: |
  Create a minimal working Cohere example with Chat, Embed, and Rerank.
  Use when starting a new Cohere integration, testing your setup,
  or learning basic Cohere API v2 patterns.
  Trigger with phrases like "cohere hello world", "cohere example",
  "cohere quick start", "simple cohere code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Hello World

## Overview
Three minimal working examples: Chat completion, text embedding, and search reranking. Each demonstrates a core Cohere API v2 endpoint.

## Prerequisites
- Completed `cohere-install-auth` setup
- `cohere-ai` package installed
- `CO_API_KEY` environment variable set

## Instructions

### Example 1: Chat Completion

```typescript
import { CohereClientV2 } from 'cohere-ai';

const cohere = new CohereClientV2();

async function chat() {
  const response = await cohere.chat({
    model: 'command-a-03-2025',
    messages: [
      { role: 'system', content: 'You are a helpful coding assistant.' },
      { role: 'user', content: 'Explain what a closure is in JavaScript in 2 sentences.' },
    ],
  });

  console.log(response.message?.content?.[0]?.text);
}

chat().catch(console.error);
```

### Example 2: Text Embedding

```typescript
async function embed() {
  const response = await cohere.embed({
    model: 'embed-v4.0',
    texts: ['Cohere builds enterprise AI', 'LLMs power modern search'],
    inputType: 'search_document',
    embeddingTypes: ['float'],
  });

  const vectors = response.embeddings.float;
  console.log(`Generated ${vectors.length} embeddings`);
  console.log(`Dimensions: ${vectors[0].length}`);
}

embed().catch(console.error);
```

### Example 3: Search Reranking

```typescript
async function rerank() {
  const response = await cohere.rerank({
    model: 'rerank-v3.5',
    query: 'What is machine learning?',
    documents: [
      'Machine learning is a subset of artificial intelligence.',
      'The weather today is sunny and warm.',
      'Deep learning uses neural networks with many layers.',
      'I enjoy cooking Italian food on weekends.',
    ],
    topN: 2,
  });

  for (const result of response.results) {
    console.log(`[${result.relevanceScore.toFixed(3)}] ${result.index}`);
  }
}

rerank().catch(console.error);
```

### Example 4: Streaming Chat

```typescript
async function streamChat() {
  const stream = await cohere.chatStream({
    model: 'command-a-03-2025',
    messages: [
      { role: 'user', content: 'Write a haiku about APIs.' },
    ],
  });

  for await (const event of stream) {
    if (event.type === 'content-delta') {
      process.stdout.write(event.delta?.message?.content?.text ?? '');
    }
  }
  console.log(); // newline
}

streamChat().catch(console.error);
```

## Python Equivalents

```python
import cohere

co = cohere.ClientV2()

# Chat
response = co.chat(
    model="command-a-03-2025",
    messages=[{"role": "user", "content": "Hello, Cohere!"}],
)
print(response.message.content[0].text)

# Embed
response = co.embed(
    model="embed-v4.0",
    texts=["Hello world", "Goodbye world"],
    input_type="search_document",
    embedding_types=["float"],
)
print(f"Vectors: {len(response.embeddings.float)}")

# Rerank
response = co.rerank(
    model="rerank-v3.5",
    query="best programming language",
    documents=["Python is versatile", "Rust is fast", "SQL manages data"],
    top_n=2,
)
for r in response.results:
    print(f"[{r.relevance_score:.3f}] doc {r.index}")
```

## Output
- Chat: Text response from Command A model
- Embed: Float vectors (1024 dimensions for v4)
- Rerank: Sorted documents with relevance scores (0.0-1.0)
- Stream: Token-by-token text output via SSE

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `model is required` | Missing model param | Always pass `model` in API v2 |
| `embedding_types is required` | Missing for embed | Add `embeddingTypes: ['float']` |
| `invalid api token` | Bad CO_API_KEY | Check key at dashboard.cohere.com |
| `rate limit exceeded` | Too many trial requests | Wait 60s or upgrade key |

## Resources
- [Cohere Chat API](https://docs.cohere.com/reference/chat)
- [Cohere Embed API](https://docs.cohere.com/reference/embed)
- [Cohere Rerank API](https://docs.cohere.com/reference/rerank)

## Next Steps
Proceed to `cohere-local-dev-loop` for development workflow setup.
