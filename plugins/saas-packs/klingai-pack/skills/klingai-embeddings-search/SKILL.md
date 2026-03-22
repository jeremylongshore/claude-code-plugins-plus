---
name: klingai-embeddings-search
description: |
  Execute Kling AI secondary workflow: Embeddings & Semantic Search.
  Use when building a RAG pipeline over documents,
  or semantic similarity search across content.
  Trigger with phrases like "klingai embeddings",
  "generate embeddings with klingai".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, klingai]
---

# Kling AI Embeddings & Semantic Search

## Overview
Generate vector embeddings for text and build semantic search over your data.
Essential for RAG pipelines, similarity matching, and knowledge retrieval.


## Prerequisites
- Completed `klingai-install-auth` setup
- Familiarity with `klingai-model-inference`
- Valid API credentials configured

## Instructions

### Step 1: Generate Embeddings
```typescript
const embedding = await client.embeddings.create({
  model: 'text-embedding-3-small',
  input: 'Your text to embed',
});
const vector = embedding.data[0].embedding; // float[] of 1536 dims

```

### Step 2: Store in Vector Database
```typescript
// Store embedding with metadata
await vectorDb.upsert({
  id: doc.id,
  values: vector,
  metadata: { source: doc.source, text: doc.text },
});

```

### Step 3: Query Similar Documents
```typescript
const queryEmbed = await client.embeddings.create({
  model: 'text-embedding-3-small',
  input: userQuery,
});
const results = await vectorDb.query({
  vector: queryEmbed.data[0].embedding,
  topK: 5,
});

```

## Output
- Completed Embeddings & Semantic Search execution

- Vector embeddings generated and stored
- Semantic search results ranked by similarity

- Success confirmation or error details

## Error Handling
| Aspect | Model Inference Pipeline | Embeddings & Semantic Search |
|--------|------------|------------|
| Use Case | sending chat completions with system prompts | building a RAG pipeline over documents |
| Complexity | Medium | Medium |
| Performance | Standard | Fast (50-200ms per embedding) |

## Examples

### Complete Workflow
```typescript
// Full RAG retrieval pipeline
async function retrieve(query: string, topK = 5) {
  const queryEmbed = await client.embeddings.create({
    model: 'text-embedding-3-small',
    input: query,
  });
  return vectorDb.query({ vector: queryEmbed.data[0].embedding, topK });
}

```

### Error Recovery
```typescript
try {
  const result = await client.embeddings.create({ model: 'text-embedding-3-small', input: text });
  return result.data[0].embedding;
} catch (err) {
  if (err.status === 429) {
    await new Promise(r => setTimeout(r, 1000));
    return retry(text); // exponential backoff
  }
  throw err;
}

```

## Resources
- [Kling AI Documentation](https://docs.klingai.com)
- [Kling AI API Reference](https://docs.klingai.com/api)

## Next Steps
For common errors, see `klingai-common-errors`.