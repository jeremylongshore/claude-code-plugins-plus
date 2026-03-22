---
name: cohere-upgrade-migration
description: |
  Migrate from Cohere API v1 to v2 and upgrade SDK versions.
  Use when upgrading cohere-ai SDK, migrating from CohereClient to CohereClientV2,
  or handling breaking changes between API versions.
  Trigger with phrases like "upgrade cohere", "cohere migration",
  "cohere v1 to v2", "update cohere SDK", "cohere breaking changes".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Upgrade & Migration

## Overview
Guide for migrating from Cohere API v1 to v2 and upgrading the `cohere-ai` TypeScript / `cohere` Python SDK. Covers every breaking change with before/after code.

## Prerequisites
- Current Cohere SDK installed
- Git for version control
- Test suite available

## Instructions

### Step 1: Check Current Version

```bash
# TypeScript
npm list cohere-ai

# Python
pip show cohere

# Latest versions
npm view cohere-ai version
pip index versions cohere
```

### Step 2: Create Upgrade Branch

```bash
git checkout -b upgrade/cohere-v2-migration
npm install cohere-ai@latest
# or: pip install cohere --upgrade
```

### Step 3: API v1 to v2 Breaking Changes

#### Client Import

```typescript
// v1
import { CohereClient } from 'cohere-ai';
const cohere = new CohereClient({ token: '...' });

// v2
import { CohereClientV2 } from 'cohere-ai';
const cohere = new CohereClientV2({ token: '...' });
```

#### Chat Endpoint — Messages Format

```typescript
// v1 — single message string
const response = await cohere.chat({
  message: 'Hello',
  preamble: 'You are helpful.',
  chatHistory: [
    { role: 'USER', message: 'Hi' },
    { role: 'CHATBOT', message: 'Hello!' },
  ],
});
console.log(response.text);

// v2 — OpenAI-compatible messages array, model required
const response = await cohere.chat({
  model: 'command-a-03-2025',  // REQUIRED in v2
  messages: [
    { role: 'system', content: 'You are helpful.' },
    { role: 'user', content: 'Hi' },
    { role: 'assistant', content: 'Hello!' },
    { role: 'user', content: 'Hello' },
  ],
});
console.log(response.message?.content?.[0]?.text);
```

#### Role Names

| v1 | v2 |
|----|----|
| `USER` | `user` |
| `CHATBOT` | `assistant` |
| `SYSTEM` | `system` |
| `TOOL` | `tool` |

#### Embed Endpoint — Required Fields

```typescript
// v1 — model optional, no embedding_types
const response = await cohere.embed({
  texts: ['hello'],
});

// v2 — model, inputType, embeddingTypes all REQUIRED
const response = await cohere.embed({
  model: 'embed-v4.0',          // Required
  texts: ['hello'],
  inputType: 'search_document', // Required for v3+ models
  embeddingTypes: ['float'],    // Required for v3+ models
});
```

#### Rerank Endpoint — Model Required

```typescript
// v1
const response = await cohere.rerank({
  query: 'best language',
  documents: ['Python', 'Rust'],
});

// v2
const response = await cohere.rerank({
  model: 'rerank-v3.5',  // Required
  query: 'best language',
  documents: ['Python', 'Rust'],
  topN: 2,
});
```

#### Classify Endpoint — Model Required

```typescript
// v1
const response = await cohere.classify({
  inputs: ['great product'],
  examples: [/*...*/],
});

// v2
const response = await cohere.classify({
  model: 'embed-english-v3.0',  // Required
  inputs: ['great product'],
  examples: [/*...*/],
});
```

#### Streaming Changes

```typescript
// v1
const stream = cohere.chatStream({ message: 'hello' });
for await (const event of stream) {
  if (event.eventType === 'text-generation') {
    process.stdout.write(event.text);
  }
}

// v2
const stream = await cohere.chatStream({
  model: 'command-a-03-2025',
  messages: [{ role: 'user', content: 'hello' }],
});
for await (const event of stream) {
  if (event.type === 'content-delta') {
    process.stdout.write(event.delta?.message?.content?.text ?? '');
  }
}
```

#### RAG / Documents

```typescript
// v1 — connectors or documents as strings
const response = await cohere.chat({
  message: 'question',
  documents: [{ title: 'Doc', snippet: 'content' }],
  connectors: [{ id: 'web-search' }],
});
// citations via response.citations

// v2 — documents as data objects
const response = await cohere.chat({
  model: 'command-a-03-2025',
  messages: [{ role: 'user', content: 'question' }],
  documents: [
    { id: 'doc1', data: { text: 'content' } },
  ],
});
// citations via response.message?.citations
```

#### Tool Use

```typescript
// v1 — Cohere-specific format
const tools = [{
  name: 'get_weather',
  description: 'Get weather',
  parameterDefinitions: {
    city: { type: 'str', required: true },
  },
}];

// v2 — OpenAI-compatible format
const tools = [{
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
```

### Step 4: Model Name Updates

| Old Name | Current Name | Status |
|----------|-------------|--------|
| `command` | `command-r7b-12-2024` | Use new ID |
| `command-r` | `command-r-08-2024` | Use new ID |
| `command-r-plus` | `command-r-plus-08-2024` | Use new ID |
| `command-nightly` | `command-a-03-2025` | Use Command A |
| `embed-english-v3.0` | `embed-v4.0` | Upgrade recommended |
| `rerank-english-v3.0` | `rerank-v3.5` | Upgrade recommended |

### Step 5: Python Migration

```python
# v1
import cohere
co = cohere.Client(api_key="...")
response = co.chat(message="hello")
print(response.text)

# v2
import cohere
co = cohere.ClientV2()  # reads CO_API_KEY
response = co.chat(
    model="command-a-03-2025",
    messages=[{"role": "user", "content": "hello"}],
)
print(response.message.content[0].text)
```

### Step 6: Run Tests and Verify

```bash
npm test
# Fix any type errors from changed response shapes
# Key changes: response.text → response.message?.content?.[0]?.text
#              response.citations → response.message?.citations

git add -A
git commit -m "chore: migrate to Cohere API v2"
```

## Migration Codemod (Find & Replace)

```bash
# Find all v1 imports
grep -rn "CohereClient\b" src/ --include="*.ts" | grep -v "CohereClientV2"

# Find v1 chat calls
grep -rn "\.chat({" src/ --include="*.ts" -A2 | grep "message:"

# Find v1 response access
grep -rn "response\.text\b" src/ --include="*.ts"

# Find v1 streaming events
grep -rn "eventType.*text-generation" src/ --include="*.ts"
```

## Output
- Updated SDK to latest version
- Migrated all endpoints from v1 to v2 format
- Updated model IDs to current names
- All tests passing against v2 API

## Error Handling
| Error After Migration | Cause | Fix |
|----------------------|-------|-----|
| `model is required` | Missed adding model param | Add model to every call |
| `response.text is undefined` | v1 response shape | Use `response.message?.content?.[0]?.text` |
| `embedding_types required` | v2 embed requirement | Add `embeddingTypes: ['float']` |
| `input_type required` | v2 embed requirement | Add `inputType: 'search_document'` |

## Resources
- [API v1 to v2 Migration Guide](https://docs.cohere.com/docs/migrating-v1-to-v2)
- [Cohere Deprecations](https://docs.cohere.com/docs/deprecations)
- [Cohere Models Overview](https://docs.cohere.com/docs/models)

## Next Steps
For CI integration during upgrades, see `cohere-ci-integration`.
