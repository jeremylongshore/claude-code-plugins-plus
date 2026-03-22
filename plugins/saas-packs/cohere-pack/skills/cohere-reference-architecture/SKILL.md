---
name: cohere-reference-architecture
description: |
  Implement Cohere reference architecture with layered project layout for RAG and agents.
  Use when designing new Cohere integrations, reviewing project structure,
  or establishing architecture standards for Cohere API v2 applications.
  Trigger with phrases like "cohere architecture", "cohere project structure",
  "cohere layout", "organize cohere app", "cohere design pattern".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Reference Architecture

## Overview
Production-ready architecture for Cohere API v2 applications covering RAG pipelines, tool-use agents, and multi-model orchestration.

## Prerequisites
- Understanding of layered architecture
- `cohere-ai` SDK v7+
- TypeScript project with vitest

## Project Structure

```
my-cohere-app/
├── src/
│   ├── cohere/
│   │   ├── client.ts           # CohereClientV2 singleton
│   │   ├── models.ts           # Model selection logic
│   │   ├── types.ts            # Cohere-specific types
│   │   └── errors.ts           # Error classification
│   ├── services/
│   │   ├── chat.ts             # Chat completions + streaming
│   │   ├── rag.ts              # RAG pipeline (embed → rerank → chat)
│   │   ├── agents.ts           # Tool-use agent loops
│   │   ├── embed.ts            # Batch embedding + caching
│   │   ├── rerank.ts           # Document reranking
│   │   └── classify.ts         # Few-shot classification
│   ├── tools/                  # Tool definitions for agents
│   │   ├── registry.ts         # Tool name → executor mapping
│   │   ├── search.ts
│   │   └── calculator.ts
│   ├── api/
│   │   ├── chat.ts             # POST /api/chat (streaming)
│   │   ├── embed.ts            # POST /api/embed
│   │   └── health.ts           # GET /api/health
│   └── cache/
│       └── embeddings.ts       # LRU cache for embeddings
├── tests/
│   ├── unit/
│   │   ├── chat.test.ts
│   │   ├── rag.test.ts
│   │   └── fixtures/           # Mocked API responses
│   └── integration/
│       └── cohere.test.ts      # Real API tests (gated)
├── config/
│   ├── models.json             # Model selection per environment
│   └── tools.json              # Tool definitions
└── package.json
```

## Layer Architecture

```
┌─────────────────────────────────────────┐
│             API Layer                    │
│   (Express/Next.js routes, SSE stream)  │
├─────────────────────────────────────────┤
│           Service Layer                  │
│  (RAG pipeline, agent loop, classify)   │
├─────────────────────────────────────────┤
│          Cohere Layer                    │
│   (CohereClientV2, retry, model select) │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Embed cache, tool registry, queue)   │
└─────────────────────────────────────────┘
```

## Core Components

### Client Layer

```typescript
// src/cohere/client.ts
import { CohereClientV2, CohereError, CohereTimeoutError } from 'cohere-ai';

let instance: CohereClientV2 | null = null;

export function getCohere(): CohereClientV2 {
  if (!instance) {
    instance = new CohereClientV2({
      token: process.env.CO_API_KEY,
    });
  }
  return instance;
}

// src/cohere/models.ts
export const MODELS = {
  chat: {
    premium: 'command-a-03-2025',
    standard: 'command-r-08-2024',
    fast: 'command-r7b-12-2024',
  },
  embed: {
    latest: 'embed-v4.0',
    english: 'embed-english-v3.0',
    multilingual: 'embed-multilingual-v3.0',
  },
  rerank: {
    latest: 'rerank-v3.5',
  },
} as const;
```

### RAG Service

```typescript
// src/services/rag.ts
import { getCohere } from '../cohere/client';
import { MODELS } from '../cohere/models';

interface RAGResult {
  answer: string;
  citations: Array<{ start: number; end: number; text: string; sources: string[] }>;
  model: string;
}

export async function ragQuery(
  query: string,
  documents: Array<{ id: string; text: string }>,
  options?: { model?: string; topN?: number }
): Promise<RAGResult> {
  const cohere = getCohere();
  const model = options?.model ?? MODELS.chat.standard;

  // Step 1: Rerank documents
  const reranked = await cohere.rerank({
    model: MODELS.rerank.latest,
    query,
    documents: documents.map(d => d.text),
    topN: options?.topN ?? 5,
  });

  // Step 2: Chat with top documents
  const topDocs = reranked.results.map(r => ({
    id: documents[r.index].id,
    data: { text: documents[r.index].text },
  }));

  const response = await cohere.chat({
    model,
    messages: [{ role: 'user', content: query }],
    documents: topDocs,
  });

  return {
    answer: response.message?.content?.[0]?.text ?? '',
    citations: (response.message?.citations ?? []).map(c => ({
      start: c.start,
      end: c.end,
      text: c.text,
      sources: c.sources?.map((s: any) => s.id) ?? [],
    })),
    model,
  };
}
```

### Agent Service

```typescript
// src/services/agents.ts
import { getCohere } from '../cohere/client';
import { MODELS } from '../cohere/models';
import { toolRegistry } from '../tools/registry';

export async function runAgent(
  userMessage: string,
  maxSteps = 5
): Promise<string> {
  const cohere = getCohere();
  const messages: any[] = [{ role: 'user', content: userMessage }];
  const tools = toolRegistry.getToolDefinitions();

  for (let step = 0; step < maxSteps; step++) {
    const response = await cohere.chat({
      model: MODELS.chat.premium,
      messages,
      tools,
    });

    if (response.finishReason !== 'TOOL_CALL') {
      return response.message?.content?.[0]?.text ?? '';
    }

    const toolCalls = response.message?.toolCalls ?? [];
    messages.push({ role: 'assistant', toolCalls });

    for (const tc of toolCalls) {
      const result = await toolRegistry.execute(
        tc.function.name,
        JSON.parse(tc.function.arguments)
      );
      messages.push({ role: 'tool', toolCallId: tc.id, content: result });
    }
  }

  return 'Agent reached max steps.';
}
```

### Tool Registry

```typescript
// src/tools/registry.ts
interface ToolDefinition {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: Record<string, unknown>;
  };
}

class ToolRegistry {
  private tools: Map<string, {
    definition: ToolDefinition;
    executor: (args: any) => Promise<string>;
  }> = new Map();

  register(
    name: string,
    description: string,
    parameters: Record<string, unknown>,
    executor: (args: any) => Promise<string>
  ) {
    this.tools.set(name, {
      definition: {
        type: 'function',
        function: { name, description, parameters },
      },
      executor,
    });
  }

  getToolDefinitions(): ToolDefinition[] {
    return Array.from(this.tools.values()).map(t => t.definition);
  }

  async execute(name: string, args: any): Promise<string> {
    const tool = this.tools.get(name);
    if (!tool) return JSON.stringify({ error: `Unknown tool: ${name}` });
    try {
      return await tool.executor(args);
    } catch (err) {
      return JSON.stringify({ error: String(err) });
    }
  }
}

export const toolRegistry = new ToolRegistry();
```

### Error Classification

```typescript
// src/cohere/errors.ts
import { CohereError, CohereTimeoutError } from 'cohere-ai';

export type ErrorCategory = 'auth' | 'rate_limit' | 'bad_request' | 'server' | 'timeout' | 'unknown';

export function classifyError(err: unknown): {
  category: ErrorCategory;
  retryable: boolean;
  message: string;
} {
  if (err instanceof CohereTimeoutError) {
    return { category: 'timeout', retryable: true, message: 'Request timed out' };
  }
  if (err instanceof CohereError) {
    switch (err.statusCode) {
      case 401: return { category: 'auth', retryable: false, message: 'Invalid API key' };
      case 429: return { category: 'rate_limit', retryable: true, message: 'Rate limited' };
      case 400: return { category: 'bad_request', retryable: false, message: err.message };
      default:
        if (err.statusCode && err.statusCode >= 500) {
          return { category: 'server', retryable: true, message: err.message };
        }
    }
  }
  return { category: 'unknown', retryable: false, message: String(err) };
}
```

## Data Flow

```
User Query
     │
     ▼
┌─────────────┐
│   API Route  │  POST /api/chat
└──────┬──────┘
       │
       ▼
┌─────────────┐    ┌─────────────┐
│  RAG Service │───▶│  Rerank     │  rerank-v3.5
│  or Agent   │    │  Service    │
└──────┬──────┘    └─────────────┘
       │
       ▼
┌─────────────┐    ┌─────────────┐
│ Chat/Stream  │───▶│  Embed      │  embed-v4.0
│  Service    │    │  Cache      │  (cached)
└──────┬──────┘    └─────────────┘
       │
       ▼
┌─────────────┐
│ CohereClient │  command-a-03-2025
│     V2      │
└─────────────┘
```

## Output
- Layered architecture separating API, service, and client concerns
- RAG pipeline with rerank pre-filtering and grounded citations
- Agent loop with pluggable tool registry
- Error classification for retry/alert decisions
- Model selection per environment and use case

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Circular imports | Wrong layering | Services depend on client, not vice versa |
| Tool not found | Missing registration | Register tools at startup |
| Model mismatch | Env config wrong | Validate model IDs at startup |
| Cache miss storm | TTL expired | Stale-while-revalidate pattern |

## Resources
- [Cohere API Reference](https://docs.cohere.com/reference/about)
- [RAG Guide](https://docs.cohere.com/docs/retrieval-augmented-generation-rag)
- [Tool Use Guide](https://docs.cohere.com/docs/tools)

## Next Steps
For multi-environment setup, see `cohere-multi-env-setup`.
