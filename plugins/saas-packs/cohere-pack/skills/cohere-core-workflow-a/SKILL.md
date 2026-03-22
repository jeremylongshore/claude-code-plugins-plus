---
name: cohere-core-workflow-a
description: |
  Build a complete RAG pipeline with Cohere Chat, Embed, and Rerank.
  Use when implementing retrieval-augmented generation, building
  grounded Q&A systems, or combining search with LLM generation.
  Trigger with phrases like "cohere RAG", "cohere retrieval",
  "cohere grounded generation", "cohere search and answer".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere RAG Pipeline (Core Workflow A)

## Overview
End-to-end Retrieval-Augmented Generation using Cohere's three core endpoints: Embed (vectorize), Rerank (sort by relevance), Chat (generate grounded answer with citations).

## Prerequisites
- Completed `cohere-install-auth` setup
- `cohere-ai` package installed
- Understanding of vector similarity search

## Instructions

### Step 1: Embed Your Documents

```typescript
import { CohereClientV2 } from 'cohere-ai';

const cohere = new CohereClientV2();

// Your knowledge base
const documents = [
  { id: 'doc1', text: 'Cohere Command A has 256K context and supports tool use.' },
  { id: 'doc2', text: 'Embed v4 generates 1024-dim vectors with 128K token context.' },
  { id: 'doc3', text: 'Rerank v3.5 scores relevance from 0 to 1 across 100+ languages.' },
  { id: 'doc4', text: 'The Chat API v2 requires model as a mandatory parameter.' },
  { id: 'doc5', text: 'Cohere supports structured JSON output via response_format.' },
];

// Embed documents for storage
const docEmbeddings = await cohere.embed({
  model: 'embed-v4.0',
  texts: documents.map(d => d.text),
  inputType: 'search_document',
  embeddingTypes: ['float'],
});

// Store vectors alongside document text in your vector DB
const vectors = docEmbeddings.embeddings.float;
console.log(`Embedded ${vectors.length} docs, ${vectors[0].length} dimensions each`);
```

### Step 2: Search — Embed the Query

```typescript
async function searchDocuments(query: string, topK = 10) {
  // Embed the query (note: inputType is 'search_query', not 'search_document')
  const queryEmbedding = await cohere.embed({
    model: 'embed-v4.0',
    texts: [query],
    inputType: 'search_query',
    embeddingTypes: ['float'],
  });

  const queryVector = queryEmbedding.embeddings.float[0];

  // Cosine similarity search (replace with your vector DB query)
  const scores = vectors.map((vec, i) => ({
    index: i,
    score: cosineSimilarity(queryVector, vec),
  }));

  return scores
    .sort((a, b) => b.score - a.score)
    .slice(0, topK)
    .map(s => documents[s.index]);
}

function cosineSimilarity(a: number[], b: number[]): number {
  let dot = 0, magA = 0, magB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    magA += a[i] * a[i];
    magB += b[i] * b[i];
  }
  return dot / (Math.sqrt(magA) * Math.sqrt(magB));
}
```

### Step 3: Rerank Retrieved Documents

```typescript
async function rerankResults(query: string, candidates: typeof documents) {
  const response = await cohere.rerank({
    model: 'rerank-v3.5',
    query,
    documents: candidates.map(d => d.text),
    topN: 3,
  });

  return response.results.map(r => ({
    ...candidates[r.index],
    relevanceScore: r.relevanceScore,
  }));
}
```

### Step 4: Generate Grounded Answer with Citations

```typescript
async function ragAnswer(query: string) {
  // 1. Retrieve
  const candidates = await searchDocuments(query);

  // 2. Rerank
  const topDocs = await rerankResults(query, candidates);

  // 3. Generate with inline citations
  const response = await cohere.chat({
    model: 'command-a-03-2025',
    messages: [{ role: 'user', content: query }],
    documents: topDocs.map(d => ({
      id: d.id,
      data: { text: d.text },
    })),
  });

  const answer = response.message?.content?.[0]?.text ?? '';
  const citations = response.message?.citations ?? [];

  return { answer, citations, sources: topDocs };
}

// Usage
const result = await ragAnswer('What context length does Command A support?');
console.log('Answer:', result.answer);
console.log('Citations:', result.citations.length);
```

## Complete Pipeline (Copy-Paste Ready)

```typescript
import { CohereClientV2 } from 'cohere-ai';

const cohere = new CohereClientV2();

async function rag(query: string, knowledgeBase: string[]) {
  // 1. Rerank the knowledge base directly (skip embed for small corpora)
  const ranked = await cohere.rerank({
    model: 'rerank-v3.5',
    query,
    documents: knowledgeBase,
    topN: 5,
  });

  // 2. Feed top docs to Chat for grounded answer
  const docs = ranked.results.map((r, i) => ({
    id: `doc-${i}`,
    data: { text: knowledgeBase[r.index] },
  }));

  const response = await cohere.chat({
    model: 'command-a-03-2025',
    messages: [{ role: 'user', content: query }],
    documents: docs,
  });

  return response.message?.content?.[0]?.text ?? '';
}
```

## Output
- Embedded document vectors (float, int8, or binary)
- Reranked candidates with relevance scores (0.0-1.0)
- Grounded answer with fine-grained citations pointing to source documents

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `input_type is required` | Missing embed inputType | Use `search_document` or `search_query` |
| `embedding_types required` | Missing for v3+ models | Add `embeddingTypes: ['float']` |
| Empty citations | Docs too short/irrelevant | Improve document quality or chunking |
| `too many documents` | >1000 rerank docs | Batch into groups of 1000 |

## Resources
- [RAG Complete Example](https://docs.cohere.com/docs/rag-complete-example)
- [RAG Citations](https://docs.cohere.com/docs/rag-citations)
- [Embed API](https://docs.cohere.com/reference/embed)
- [Rerank Best Practices](https://docs.cohere.com/docs/reranking-best-practices)

## Next Steps
For tool-use and agents workflow, see `cohere-core-workflow-b`.
