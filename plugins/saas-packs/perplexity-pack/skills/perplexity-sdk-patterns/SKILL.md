---
name: perplexity-sdk-patterns
description: |
  Apply production-ready Perplexity Sonar API patterns for TypeScript and Python.
  Use when implementing Perplexity integrations, refactoring SDK usage,
  or establishing team coding standards for search-augmented generation.
  Trigger with phrases like "perplexity SDK patterns", "perplexity best practices",
  "perplexity code patterns", "idiomatic perplexity", "perplexity wrapper".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, python, typescript]

---
# Perplexity SDK Patterns

## Overview
Production-ready patterns for Perplexity Sonar API. Since Perplexity uses the OpenAI wire format, you build wrappers around the `openai` client library with Perplexity-specific response handling (citations, search results, related questions).

## Prerequisites
- `openai` package installed (`npm install openai` or `pip install openai`)
- API key configured in `PERPLEXITY_API_KEY`
- Understanding of OpenAI chat completions format

## Instructions

### Step 1: Typed Client Singleton (TypeScript)
```typescript
// src/perplexity/client.ts
import OpenAI from "openai";

export interface PerplexityChatCompletion extends OpenAI.ChatCompletion {
  citations?: string[];
  search_results?: Array<{
    title: string;
    url: string;
    date?: string;
    snippet: string;
  }>;
  related_questions?: string[];
}

export interface PerplexityUsage extends OpenAI.CompletionUsage {
  citation_tokens?: number;
  num_search_queries?: number;
  reasoning_tokens?: number;
}

let instance: OpenAI | null = null;

export function getClient(): OpenAI {
  if (!instance) {
    if (!process.env.PERPLEXITY_API_KEY) {
      throw new Error("PERPLEXITY_API_KEY not set");
    }
    instance = new OpenAI({
      apiKey: process.env.PERPLEXITY_API_KEY,
      baseURL: "https://api.perplexity.ai",
    });
  }
  return instance;
}
```

### Step 2: Search with Full Response Parsing
```typescript
// src/perplexity/search.ts
import { getClient, PerplexityChatCompletion } from "./client";

export type SearchModel = "sonar" | "sonar-pro" | "sonar-reasoning-pro" | "sonar-deep-research";
export type RecencyFilter = "hour" | "day" | "week" | "month";

export interface SearchOptions {
  model?: SearchModel;
  systemPrompt?: string;
  maxTokens?: number;
  temperature?: number;
  searchRecencyFilter?: RecencyFilter;
  searchDomainFilter?: string[];   // max 20 domains
  returnRelatedQuestions?: boolean;
  returnImages?: boolean;
}

export interface SearchResult {
  answer: string;
  citations: string[];
  relatedQuestions: string[];
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
    citationTokens?: number;
    searchQueries?: number;
  };
  model: string;
}

export async function search(
  query: string,
  opts: SearchOptions = {}
): Promise<SearchResult> {
  const client = getClient();

  const response = (await client.chat.completions.create({
    model: opts.model || "sonar",
    messages: [
      ...(opts.systemPrompt
        ? [{ role: "system" as const, content: opts.systemPrompt }]
        : []),
      { role: "user" as const, content: query },
    ],
    max_tokens: opts.maxTokens,
    temperature: opts.temperature,
    ...(opts.searchRecencyFilter && { search_recency_filter: opts.searchRecencyFilter }),
    ...(opts.searchDomainFilter && { search_domain_filter: opts.searchDomainFilter }),
    ...(opts.returnRelatedQuestions && { return_related_questions: true }),
    ...(opts.returnImages && { return_images: true }),
  } as any)) as unknown as PerplexityChatCompletion;

  return {
    answer: response.choices[0].message.content || "",
    citations: response.citations || [],
    relatedQuestions: response.related_questions || [],
    usage: {
      promptTokens: response.usage?.prompt_tokens || 0,
      completionTokens: response.usage?.completion_tokens || 0,
      totalTokens: response.usage?.total_tokens || 0,
      citationTokens: (response.usage as any)?.citation_tokens,
      searchQueries: (response.usage as any)?.num_search_queries,
    },
    model: response.model,
  };
}
```

### Step 3: Retry with Exponential Backoff
```typescript
// src/perplexity/retry.ts
export async function withRetry<T>(
  operation: () => Promise<T>,
  opts = { maxRetries: 3, baseDelayMs: 1000, maxDelayMs: 30000 }
): Promise<T> {
  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err: any) {
      if (attempt === opts.maxRetries) throw err;

      const status = err.status || err.response?.status;
      // Only retry on rate limit (429), timeout (408), or server errors (5xx)
      if (status && status !== 429 && status !== 408 && status < 500) throw err;

      const delay = Math.min(
        opts.baseDelayMs * Math.pow(2, attempt) + Math.random() * 500,
        opts.maxDelayMs
      );
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}

// Usage
const result = await withRetry(() =>
  search("latest AI developments", { model: "sonar-pro" })
);
```

### Step 4: Python Patterns
```python
# perplexity_client.py
import os, hashlib, json
from openai import OpenAI
from functools import lru_cache

@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["PERPLEXITY_API_KEY"],
        base_url="https://api.perplexity.ai",
    )

def search(
    query: str,
    model: str = "sonar",
    system_prompt: str | None = None,
    max_tokens: int | None = None,
    search_recency_filter: str | None = None,
    search_domain_filter: list[str] | None = None,
) -> dict:
    client = get_client()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": query})

    kwargs = {"model": model, "messages": messages}
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    if search_recency_filter:
        kwargs["search_recency_filter"] = search_recency_filter
    if search_domain_filter:
        kwargs["search_domain_filter"] = search_domain_filter

    response = client.chat.completions.create(**kwargs)
    raw = response.model_dump()

    return {
        "answer": response.choices[0].message.content,
        "citations": raw.get("citations", []),
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        },
        "model": response.model,
    }
```

### Step 5: Citation Formatter
```typescript
// src/perplexity/citations.ts
export function formatCitationsAsMarkdown(
  answer: string,
  citations: string[]
): string {
  // Replace [1], [2], etc. with markdown links
  let formatted = answer;
  citations.forEach((url, i) => {
    const marker = `[${i + 1}]`;
    formatted = formatted.replaceAll(marker, `[${i + 1}](${url})`);
  });
  return formatted;
}

export function formatCitationsAsFootnotes(
  answer: string,
  citations: string[]
): string {
  const footnotes = citations
    .map((url, i) => `[${i + 1}]: ${url}`)
    .join("\n");
  return `${answer}\n\n---\n${footnotes}`;
}
```

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Typed response wrapper | All API calls | Access citations without `any` casts |
| Retry with backoff | Transient failures | Handles 429 rate limits gracefully |
| Citation formatter | User-facing output | Converts `[1]` markers to clickable links |
| Python `@lru_cache` | Client reuse | Single client instance across calls |

## Output
- Type-safe Perplexity client with full response typing
- Search function with all Perplexity-specific parameters
- Automatic retry with exponential backoff and jitter
- Citation formatting utilities

## Resources
- [Perplexity API Reference](https://docs.perplexity.ai/api-reference/chat-completions-post)
- [OpenAI Compatibility](https://docs.perplexity.ai/guides/chat-completions-guide)
- [Sonar Model Guide](https://docs.perplexity.ai/getting-started/models)

## Next Steps
Apply patterns in `perplexity-core-workflow-a` for real-world usage.
