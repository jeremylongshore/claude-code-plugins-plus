---
name: mistral-core-workflow-b
description: |
  Execute Mistral AI embeddings, function calling, and RAG pipelines.
  Use when implementing semantic search, RAG applications,
  tool-augmented LLM interactions, or code embeddings.
  Trigger with phrases like "mistral embeddings", "mistral function calling",
  "mistral tools", "mistral RAG", "mistral semantic search".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, llm, embeddings, workflow]

---
# Mistral AI Core Workflow B: Embeddings & Function Calling

## Overview
Secondary workflows for Mistral AI: text/code embeddings with `mistral-embed` (1024 dimensions), function calling (tool use) with any chat model, and RAG pipeline combining both. Mistral supports `auto`, `any`, and `none` tool choice modes.

## Prerequisites
- Completed `mistral-install-auth` setup
- `MISTRAL_API_KEY` environment variable set
- Familiarity with `mistral-core-workflow-a`

## Instructions

### Step 1: Generate Text Embeddings

```typescript
import { Mistral } from '@mistralai/mistralai';

const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });

// Single text embedding
const response = await client.embeddings.create({
  model: 'mistral-embed',
  inputs: ['Machine learning is fascinating.'],
});

const vector = response.data[0].embedding;
console.log(`Dimensions: ${vector.length}`); // 1024
console.log(`Tokens used: ${response.usage.totalTokens}`);
```

### Step 2: Batch Embeddings with Rate Awareness

```typescript
async function batchEmbed(
  texts: string[],
  batchSize = 64,
): Promise<number[][]> {
  const allEmbeddings: number[][] = [];

  for (let i = 0; i < texts.length; i += batchSize) {
    const batch = texts.slice(i, i + batchSize);
    const response = await client.embeddings.create({
      model: 'mistral-embed',
      inputs: batch,
    });
    allEmbeddings.push(...response.data.map(d => d.embedding));
  }

  return allEmbeddings;
}

// Embed 1000 documents in batches of 64
const docs = ['doc1...', 'doc2...', /* ... */];
const embeddings = await batchEmbed(docs);
```

### Step 3: Semantic Search with Cosine Similarity

```typescript
function cosineSimilarity(a: number[], b: number[]): number {
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

class SemanticSearch {
  private documents: Array<{ text: string; embedding: number[] }> = [];
  private client: Mistral;

  constructor() {
    this.client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });
  }

  async index(texts: string[]): Promise<void> {
    const response = await this.client.embeddings.create({
      model: 'mistral-embed',
      inputs: texts,
    });
    this.documents = texts.map((text, i) => ({
      text,
      embedding: response.data[i].embedding,
    }));
  }

  async search(query: string, topK = 5): Promise<Array<{ text: string; score: number }>> {
    const qEmbed = await this.client.embeddings.create({
      model: 'mistral-embed',
      inputs: [query],
    });
    const qVec = qEmbed.data[0].embedding;

    return this.documents
      .map(doc => ({ text: doc.text, score: cosineSimilarity(qVec, doc.embedding) }))
      .sort((a, b) => b.score - a.score)
      .slice(0, topK);
  }
}
```

### Step 4: Function Calling (Tool Use)

```typescript
// 1. Define tools with JSON Schema
const tools = [
  {
    type: 'function' as const,
    function: {
      name: 'get_weather',
      description: 'Get current weather for a city',
      parameters: {
        type: 'object',
        properties: {
          city: { type: 'string', description: 'City name (e.g., "Paris")' },
          units: { type: 'string', enum: ['celsius', 'fahrenheit'], default: 'celsius' },
        },
        required: ['city'],
      },
    },
  },
  {
    type: 'function' as const,
    function: {
      name: 'search_database',
      description: 'Search product database by query',
      parameters: {
        type: 'object',
        properties: {
          query: { type: 'string' },
          limit: { type: 'integer', default: 10 },
        },
        required: ['query'],
      },
    },
  },
];

// 2. Send request with tools
const response = await client.chat.complete({
  model: 'mistral-large-latest', // Large recommended for complex tool use
  messages: [{ role: 'user', content: "What's the weather in Paris?" }],
  tools,
  toolChoice: 'auto', // 'auto' | 'any' | 'none'
});
```

### Step 5: Tool Execution Loop

```typescript
// Tool registry maps function names to implementations
const toolRegistry: Record<string, (args: any) => Promise<any>> = {
  get_weather: async ({ city, units }) => ({ city, temp: 22, units: units ?? 'celsius' }),
  search_database: async ({ query, limit }) => ({ results: [], total: 0 }),
};

async function chatWithTools(userMessage: string): Promise<string> {
  const messages: any[] = [{ role: 'user', content: userMessage }];

  while (true) {
    const response = await client.chat.complete({
      model: 'mistral-large-latest',
      messages,
      tools,
      toolChoice: 'auto',
    });

    const choice = response.choices?.[0];
    if (!choice) throw new Error('No response from model');

    // If model wants to call tools
    if (choice.message.toolCalls?.length) {
      messages.push(choice.message); // Add assistant message with tool_calls

      for (const call of choice.message.toolCalls) {
        const fn = toolRegistry[call.function.name];
        if (!fn) throw new Error(`Unknown tool: ${call.function.name}`);

        const args = JSON.parse(call.function.arguments);
        const result = await fn(args);

        messages.push({
          role: 'tool',
          name: call.function.name,
          content: JSON.stringify(result),
          toolCallId: call.id,
        });
      }
      continue; // Let model process tool results
    }

    // Model returned final text response
    return choice.message.content ?? '';
  }
}
```

### Step 6: RAG Pipeline (Retrieval-Augmented Generation)

```typescript
async function ragChat(
  query: string,
  searcher: SemanticSearch,
  topK = 3,
): Promise<{ answer: string; sources: string[] }> {
  // 1. Retrieve relevant documents
  const results = await searcher.search(query, topK);
  const context = results.map((r, i) => `[${i + 1}] ${r.text}`).join('\n\n');

  // 2. Generate answer grounded in context
  const response = await client.chat.complete({
    model: 'mistral-small-latest',
    messages: [
      {
        role: 'system',
        content: `Answer based ONLY on the provided context. Cite sources as [1], [2], etc. If the context doesn't contain the answer, say "I don't have enough information."`,
      },
      {
        role: 'user',
        content: `Context:\n${context}\n\nQuestion: ${query}`,
      },
    ],
    temperature: 0.1,
  });

  return {
    answer: response.choices?.[0]?.message?.content ?? '',
    sources: results.map(r => r.text),
  };
}
```

## Output
- Text embeddings with `mistral-embed` (1024 dimensions)
- Semantic search with cosine similarity ranking
- Function calling with tool execution loop
- RAG pipeline combining retrieval and generation

## Error Handling
| Issue | Cause | Resolution |
|-------|-------|------------|
| Empty embeddings | Invalid input text | Validate non-empty strings before API call |
| Tool not found | Unknown function name | Check tool registry matches tool definitions |
| Infinite tool loop | Model keeps calling tools | Add max iteration count (e.g., 10) |
| RAG hallucination | Insufficient context | Add more documents, increase topK |
| `400 Bad Request` | Missing `toolCallId` | Each tool result must include the matching `toolCallId` |

## Resources
- [Embeddings API](https://docs.mistral.ai/capabilities/embeddings/)
- [Function Calling](https://docs.mistral.ai/capabilities/function_calling/)
- [RAG Guide](https://docs.mistral.ai/guides/rag/)
- [Code Embeddings](https://docs.mistral.ai/capabilities/embeddings/code_embeddings/)

## Next Steps
For SDK patterns, see `mistral-sdk-patterns`. For agents, see `mistral-webhooks-events`.
