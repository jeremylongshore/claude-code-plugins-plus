---
name: mistral-core-workflow-b
description: |
  Execute Mistral AI secondary workflows: Embeddings and Function Calling.
  Use when implementing semantic search, RAG applications,
  or tool-augmented LLM interactions.
  Trigger with phrases like "mistral embeddings", "mistral function calling",
  "mistral tools", "mistral RAG", "mistral semantic search".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Mistral AI Core Workflow B: Embeddings & Function Calling

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Secondary workflows for Mistral AI: text embeddings for semantic search/RAG and function calling for tool-augmented interactions. Uses `mistral-embed` (1024 dimensions) for embeddings and `mistral-large-latest` for function calling.

## Prerequisites
- Completed `mistral-install-auth` setup
- Familiarity with `mistral-core-workflow-a`
- Valid API credentials configured

## Instructions

### Step 1: Generate Text Embeddings
Use `client.embeddings.create()` with model `mistral-embed` and `inputs` array. Returns 1024-dimensional vectors per input text.

### Step 2: Batch Embeddings
Pass multiple texts in the `inputs` array for efficient batch processing. Map response `data` array to extract embedding vectors.

### Step 3: Build Semantic Search
Implement `SemanticSearch` class with `indexDocuments()` (embeds all docs) and `search()` (embeds query, ranks by cosine similarity, returns top-K results). Use cosine similarity: dot product divided by product of norms.

### Step 4: Define Function Tools
Create tool definitions with JSON Schema parameters. Each tool has type `function`, name, description, and parameter schema with required fields.

### Step 5: Implement Function Calling Loop
Send messages with `tools` and `toolChoice: 'auto'` to `client.chat.complete()`. Check for `toolCalls` in response. Execute matching tool function, add result as `role: 'tool'` message, and loop until model returns final text response.

### Step 6: Build RAG Pipeline
Combine semantic search with chat completion. Retrieve relevant documents for user query, inject as context in system prompt, generate response with `mistral-small-latest`. Instruct model to answer from context only.

## Output
- Text embeddings with `mistral-embed` (1024 dimensions)
- Semantic search with cosine similarity ranking
- Function calling with tool execution loop
- RAG chat combining retrieval and generation

## Error Handling
| Issue | Cause | Resolution |
|-------|-------|------------|
| Empty embeddings | Invalid input text | Validate non-empty strings before API call |
| Tool not found | Unknown function name | Check tool registry matches definitions |
| RAG hallucination | Insufficient context | Add more documents, tune retrieval top-K |
| High latency | Large batch size | Split into smaller batches, add concurrency |

## Examples

### Embeddings
```typescript
const response = await client.embeddings.create({
  model: 'mistral-embed',
  inputs: ['Machine learning is fascinating.'],
});
console.log(`Dimensions: ${response.data[0].embedding.length}`); // 1024
```

### Function Calling
```typescript
const response = await client.chat.complete({
  model: 'mistral-large-latest',
  messages: [{ role: 'user', content: 'Weather in Paris?' }],
  tools, toolChoice: 'auto',
});
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [Mistral AI Embeddings](https://docs.mistral.ai/capabilities/embeddings/)
- [Mistral AI Function Calling](https://docs.mistral.ai/capabilities/function_calling/)
- [Mistral AI Agents](https://docs.mistral.ai/capabilities/agents/)
