---
name: perplexity-reference-architecture
description: |
  Implement Perplexity reference architecture with best-practice project layout.
  Use when designing new Perplexity integrations, reviewing project structure,
  or establishing architecture standards for Perplexity applications.
  Trigger with phrases like "perplexity architecture", "perplexity best practices",
  "perplexity project structure", "how to organize perplexity", "perplexity layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Perplexity Reference Architecture

## Overview
Production architecture for AI-powered research and search with Perplexity Sonar API. Covers search pipeline design, citation management, model routing for cost/quality tradeoffs, and integration into RAG-based applications.

## Prerequisites
- Perplexity API key (Sonar access)
- OpenAI-compatible client library
- Understanding of search models (sonar, sonar-pro)
- Citation storage and display layer

## Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│              Application Layer                        │
│  Research Agent │ Fact Checker │ Content Writer       │
└──────────┬───────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────┐
│              Search Router                            │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ sonar    │  │ sonar-pro    │  │ sonar-         │  │
│  │ (fast)   │  │ (deep)       │  │ reasoning      │  │
│  └──────────┘  └──────────────┘  └────────────────┘  │
├──────────────────────────────────────────────────────┤
│              Citation Pipeline                        │
│  Extract URLs │ Validate │ Store │ Render            │
├──────────────────────────────────────────────────────┤
│              Cache Layer                              │
│  Query Hash → Result │ TTL by Freshness Need         │
└──────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Search Service with Model Routing
```typescript
import OpenAI from 'openai';

const perplexity = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY,
  baseURL: 'https://api.perplexity.ai',
});

type SearchDepth = 'quick' | 'standard' | 'deep' | 'reasoning';

const MODEL_FOR_DEPTH: Record<SearchDepth, string> = {
  quick: 'sonar',
  standard: 'sonar',
  deep: 'sonar-pro',
  reasoning: 'sonar-reasoning',
};

async function search(query: string, depth: SearchDepth = 'standard') {
  return perplexity.chat.completions.create({
    model: MODEL_FOR_DEPTH[depth],
    messages: [
      {
        role: 'system',
        content: 'Provide accurate, well-sourced answers. Include citations.',
      },
      { role: 'user', content: query },
    ],
    max_tokens: depth === 'quick' ? 512 : 2048,
  });
}
```

### Step 2: Citation Extraction Pipeline
```typescript
interface Citation {
  url: string;
  title?: string;
  snippet?: string;
  index: number;
}

function extractCitations(responseText: string): Citation[] {
  const citations: Citation[] = [];
  const urlRegex = /\[(\d+)\]\s*(https?:\/\/[^\s\]]+)/g;
  let match;

  while ((match = urlRegex.exec(responseText)) !== null) {
    citations.push({
      index: parseInt(match[1]),
      url: match[2],
      title: undefined,
      snippet: undefined,
    });
  }

  // Also extract inline URLs
  const inlineUrls = responseText.match(/https?:\/\/[^\s\])+/g) || [];
  for (const url of inlineUrls) {
    if (!citations.some(c => c.url === url)) {
      citations.push({ url, index: citations.length + 1 });
    }
  }

  return citations;
}

async function searchWithCitations(query: string, depth: SearchDepth = 'standard') {
  const result = await search(query, depth);
  const text = result.choices[0].message.content || '';

  return {
    answer: text,
    citations: extractCitations(text),
    model: MODEL_FOR_DEPTH[depth],
    usage: result.usage,
  };
}
```

### Step 3: Research Pipeline for Multi-Query Workflows
```typescript
async function deepResearch(topic: string) {
  // Phase 1: Broad overview with fast model
  const overview = await searchWithCitations(
    `What are the key aspects of ${topic}?`, 'quick'
  );

  // Phase 2: Deep dive into each subtopic
  const subtopics = await search(
    `List 3-5 specific subtopics worth researching about: ${topic}`,
    'quick'
  );

  // Phase 3: Detailed research per subtopic
  const details = await Promise.all(
    parseSubtopics(subtopics.choices[0].message.content || '').map(
      sub => searchWithCitations(sub, 'deep')
    )
  );

  return {
    overview,
    details,
    allCitations: deduplicateCitations([
      ...overview.citations,
      ...details.flatMap(d => d.citations),
    ]),
  };
}

function deduplicateCitations(citations: Citation[]): Citation[] {
  const seen = new Set<string>();
  return citations.filter(c => {
    if (seen.has(c.url)) return false;
    seen.add(c.url);
    return true;
  });
}
```

### Step 4: Conversational Search with Context
```typescript
class ResearchSession {
  private history: any[] = [];

  async ask(query: string, depth: SearchDepth = 'standard') {
    this.history.push({ role: 'user', content: query });

    const result = await perplexity.chat.completions.create({
      model: MODEL_FOR_DEPTH[depth],
      messages: [
        { role: 'system', content: 'You are a research assistant. Build on previous context.' },
        ...this.history,
      ],
    });

    const answer = result.choices[0].message.content || '';
    this.history.push({ role: 'assistant', content: answer });

    return { answer, citations: extractCitations(answer) };
  }

  reset() { this.history = []; }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No citations | Using basic sonar for complex query | Upgrade to sonar-pro |
| Stale information | Outdated sources | Add recency preference in prompt |
| High cost | Using sonar-pro for simple queries | Route simple queries to sonar |
| Rate limit | Too many concurrent searches | Add request queue with delays |

## Examples

### Fact-Check Service
```typescript
async function factCheck(claim: string) {
  const result = await searchWithCitations(
    `Is this claim accurate? Provide evidence: "${claim}"`,
    'deep'
  );
  return { claim, verdict: result.answer, sources: result.citations };
}
```

## Resources
- [Perplexity API Docs](https://docs.perplexity.ai/)
- [Perplexity Model Guide](https://docs.perplexity.ai/guides/model-cards)
