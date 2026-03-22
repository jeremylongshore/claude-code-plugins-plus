---
name: cohere-migration-deep-dive
description: |
  Migrate from OpenAI/Anthropic/other LLM providers to Cohere, or vice versa.
  Use when switching LLM providers, migrating embeddings between models,
  or re-platforming existing AI integrations to Cohere API v2.
  Trigger with phrases like "migrate to cohere", "switch from openai to cohere",
  "cohere migration", "replace openai with cohere", "cohere replatform".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Migration Deep Dive

## Overview
Comprehensive guide for migrating to Cohere from OpenAI, Anthropic, or other LLM providers, including embedding re-vectorization, prompt adaptation, and gradual traffic shifting.

## Prerequisites
- Current LLM integration documented
- Cohere API key and SDK installed
- Feature flag infrastructure
- Rollback strategy

## Migration Types

| From | Complexity | Duration | Key Challenge |
|------|-----------|----------|---------------|
| OpenAI → Cohere | Medium | 1-2 weeks | Prompt adaptation, embedding migration |
| Anthropic → Cohere | Medium | 1-2 weeks | Message format, tool definitions |
| Custom/OSS → Cohere | Low | Days | SDK integration |
| Embedding migration | High | 2-4 weeks | Re-vectorize entire corpus |

## Instructions

### Step 1: OpenAI to Cohere Chat Migration

```typescript
// --- OpenAI (before) ---
import OpenAI from 'openai';
const openai = new OpenAI();

const response = await openai.chat.completions.create({
  model: 'gpt-4o',
  messages: [
    { role: 'system', content: 'You are helpful.' },
    { role: 'user', content: 'Hello' },
  ],
  max_tokens: 500,
  temperature: 0.7,
});
const text = response.choices[0].message.content;

// --- Cohere (after) ---
import { CohereClientV2 } from 'cohere-ai';
const cohere = new CohereClientV2();

const response = await cohere.chat({
  model: 'command-a-03-2025',   // GPT-4o equivalent
  messages: [
    { role: 'system', content: 'You are helpful.' },  // Same format!
    { role: 'user', content: 'Hello' },
  ],
  maxTokens: 500,               // camelCase, not snake_case
  temperature: 0.7,
});
const text = response.message?.content?.[0]?.text;  // Different response shape
```

### Step 2: Embedding Migration

```typescript
// OpenAI embeddings: 3072 dims (text-embedding-3-large)
// Cohere embeddings: 1024 dims (embed-v4.0)
// IMPORTANT: You CANNOT mix embeddings from different models in the same vector DB

// Migration plan:
// 1. Create new vector collection with Cohere dimensions
// 2. Re-embed all documents with Cohere
// 3. Switch queries to new collection
// 4. Delete old collection

async function migrateEmbeddings(
  documents: Array<{ id: string; text: string }>,
  batchSize = 96
) {
  const cohere = new CohereClientV2();
  let processed = 0;

  for (let i = 0; i < documents.length; i += batchSize) {
    const batch = documents.slice(i, i + batchSize);

    const response = await cohere.embed({
      model: 'embed-v4.0',
      texts: batch.map(d => d.text),
      inputType: 'search_document',
      embeddingTypes: ['float'],
    });

    // Upsert to new vector collection
    for (let j = 0; j < batch.length; j++) {
      await vectorDB.upsert({
        collection: 'docs-cohere', // New collection
        id: batch[j].id,
        vector: response.embeddings.float[j],
        metadata: { text: batch[j].text },
      });
    }

    processed += batch.length;
    console.log(`Migrated ${processed}/${documents.length} embeddings`);
  }
}
```

### Step 3: Tool Use Migration

```typescript
// --- OpenAI tools ---
const openaiTools = [{
  type: 'function',
  function: {
    name: 'get_weather',
    description: 'Get weather',
    parameters: {
      type: 'object',
      properties: { city: { type: 'string' } },
      required: ['city'],
    },
  },
}];

// --- Cohere tools (same format in v2!) ---
const cohereTools = [{
  type: 'function',
  function: {
    name: 'get_weather',
    description: 'Get weather',
    parameters: {
      type: 'object',
      properties: { city: { type: 'string' } },
      required: ['city'],
    },
  },
}];
// Tool definitions are identical! The difference is in response handling.

// OpenAI: response.choices[0].message.tool_calls
// Cohere: response.message?.toolCalls
```

### Step 4: Streaming Migration

```typescript
// --- OpenAI streaming ---
const openaiStream = await openai.chat.completions.create({
  model: 'gpt-4o',
  messages: [...],
  stream: true,
});
for await (const chunk of openaiStream) {
  process.stdout.write(chunk.choices[0]?.delta?.content ?? '');
}

// --- Cohere streaming ---
const cohereStream = await cohere.chatStream({
  model: 'command-a-03-2025',
  messages: [...],
});
for await (const event of cohereStream) {
  if (event.type === 'content-delta') {
    process.stdout.write(event.delta?.message?.content?.text ?? '');
  }
}
```

### Step 5: Adapter Pattern for Gradual Migration

```typescript
interface LLMAdapter {
  chat(message: string, options?: { system?: string; maxTokens?: number }): Promise<string>;
  embed(texts: string[]): Promise<number[][]>;
  rerank(query: string, docs: string[], topN?: number): Promise<Array<{ index: number; score: number }>>;
}

class CohereAdapter implements LLMAdapter {
  private client = new CohereClientV2();

  async chat(message: string, options?: { system?: string; maxTokens?: number }): Promise<string> {
    const messages: any[] = [];
    if (options?.system) messages.push({ role: 'system', content: options.system });
    messages.push({ role: 'user', content: message });

    const response = await this.client.chat({
      model: 'command-a-03-2025',
      messages,
      maxTokens: options?.maxTokens,
    });
    return response.message?.content?.[0]?.text ?? '';
  }

  async embed(texts: string[]): Promise<number[][]> {
    const response = await this.client.embed({
      model: 'embed-v4.0',
      texts,
      inputType: 'search_document',
      embeddingTypes: ['float'],
    });
    return response.embeddings.float;
  }

  async rerank(query: string, docs: string[], topN = 5): Promise<Array<{ index: number; score: number }>> {
    const response = await this.client.rerank({
      model: 'rerank-v3.5',
      query,
      documents: docs,
      topN,
    });
    return response.results.map(r => ({ index: r.index, score: r.relevanceScore }));
  }
}

class OpenAIAdapter implements LLMAdapter {
  // ... OpenAI implementation
}

// Traffic splitting via feature flag
function getLLMAdapter(): LLMAdapter {
  const coherePercentage = getFeatureFlag('cohere_migration_pct'); // 0-100
  if (Math.random() * 100 < coherePercentage) {
    return new CohereAdapter();
  }
  return new OpenAIAdapter();
}
```

### Step 6: Validation and Comparison

```typescript
async function compareOutputs(message: string): Promise<{
  openai: string;
  cohere: string;
  latencyMs: { openai: number; cohere: number };
}> {
  const startOpenAI = Date.now();
  const openaiResult = await openaiAdapter.chat(message);
  const openaiLatency = Date.now() - startOpenAI;

  const startCohere = Date.now();
  const cohereResult = await cohereAdapter.chat(message);
  const cohereLatency = Date.now() - startCohere;

  return {
    openai: openaiResult,
    cohere: cohereResult,
    latencyMs: { openai: openaiLatency, cohere: cohereLatency },
  };
}

// Run comparison on sample queries during migration
const testQueries = ['Summarize this text', 'Translate to French', 'Extract key points'];
for (const q of testQueries) {
  const result = await compareOutputs(q);
  console.log(`Query: ${q}`);
  console.log(`OpenAI (${result.latencyMs.openai}ms): ${result.openai.slice(0, 100)}`);
  console.log(`Cohere (${result.latencyMs.cohere}ms): ${result.cohere.slice(0, 100)}`);
}
```

## Cohere-Unique Features (Not in OpenAI)

| Feature | Cohere | OpenAI |
|---------|--------|--------|
| Built-in Rerank | `cohere.rerank()` | Not available |
| RAG with citations | `documents` param + citations | Manual implementation |
| Connectors (data sources) | `connectors` param | Not available |
| Classify endpoint | `cohere.classify()` | Not available |
| Safety modes | `safetyMode` param | Moderation API (separate) |

## Rollback Plan

```bash
# Set feature flag to 0% Cohere traffic
curl -X POST https://flagservice/flags/cohere_migration_pct -d '{"value": 0}'

# Verify traffic is back on old provider
# Monitor error rates for 15 minutes
# If stable, migration is paused safely
```

## Output
- Adapter layer abstracting LLM provider
- Embedding migration with batch processing
- A/B comparison for output quality validation
- Feature-flag controlled traffic shifting
- Rollback via feature flag (instant, no deploy)

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Embedding dimension mismatch | Mixed providers in same DB | Separate collections per provider |
| Response shape different | Provider-specific format | Use adapter pattern |
| Higher latency on Cohere | Different model size | Try command-r7b for speed |
| Quality difference | Different model strengths | Tune system prompts per provider |

## Resources
- [Cohere OpenAI Compatibility](https://docs.cohere.com/docs/compatibility-api)
- [Cohere Models Overview](https://docs.cohere.com/docs/models)
- [API v2 Reference](https://docs.cohere.com/reference/about)

## Next Steps
For Cohere-specific architecture patterns, see `cohere-reference-architecture`.
