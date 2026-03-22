---
name: perplexity-reference-architecture
description: |
  Implement Perplexity reference architecture with model routing, citation pipeline,
  and research automation. Use when designing new Perplexity integrations,
  reviewing project structure, or establishing architecture for search-augmented apps.
  Trigger with phrases like "perplexity architecture", "perplexity project structure",
  "how to organize perplexity", "perplexity design patterns".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, perplexity-reference]

---
# Perplexity Reference Architecture

## Overview
Production architecture for AI-powered search with Perplexity Sonar API. Three tiers: search service (model routing + caching), citation pipeline (extract, validate, store), and research orchestrator (multi-query synthesis).

## Architecture

```
┌─────────────────────────────────────────────┐
│              Application Layer              │
│  (Search Widget, Research Agent, Fact Check) │
└──────────────────────┬──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│            Search Service Layer             │
│  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │  Model   │ │  Query   │ │   Response   │ │
│  │  Router  │ │  Cache   │ │   Parser     │ │
│  └──────────┘ └──────────┘ └─────────────┘ │
└──────────────────────┬──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│          api.perplexity.ai/chat/completions │
│  sonar | sonar-pro | sonar-reasoning-pro    │
└─────────────────────────────────────────────┘
```

## Prerequisites
- Perplexity API key with Sonar access
- OpenAI-compatible client library (`openai` package)
- Redis for production caching (LRU for development)

## Instructions

### Step 1: Search Service with Model Routing
```typescript
// src/perplexity/search-service.ts
import OpenAI from "openai";
import { createHash } from "crypto";

type SearchDepth = "quick" | "standard" | "deep" | "reasoning";

const MODEL_MAP: Record<SearchDepth, { model: string; maxTokens: number; timeout: number }> = {
  quick:     { model: "sonar",               maxTokens: 256,  timeout: 10000 },
  standard:  { model: "sonar",               maxTokens: 1024, timeout: 15000 },
  deep:      { model: "sonar-pro",           maxTokens: 4096, timeout: 30000 },
  reasoning: { model: "sonar-reasoning-pro", maxTokens: 4096, timeout: 45000 },
};

export class SearchService {
  constructor(
    private client: OpenAI,
    private cache: Map<string, { result: any; expiry: number }> = new Map()
  ) {}

  async search(query: string, depth: SearchDepth = "standard", opts: {
    recencyFilter?: "hour" | "day" | "week" | "month";
    domainFilter?: string[];
    systemPrompt?: string;
  } = {}) {
    const config = MODEL_MAP[depth];
    const cacheKey = this.hashQuery(query, config.model, opts);

    // Check cache
    const cached = this.cache.get(cacheKey);
    if (cached && cached.expiry > Date.now()) {
      return { ...cached.result, cached: true };
    }

    const response = await this.client.chat.completions.create({
      model: config.model,
      messages: [
        ...(opts.systemPrompt ? [{ role: "system" as const, content: opts.systemPrompt }] : []),
        { role: "user" as const, content: query },
      ],
      max_tokens: config.maxTokens,
      ...(opts.recencyFilter && { search_recency_filter: opts.recencyFilter }),
      ...(opts.domainFilter && { search_domain_filter: opts.domainFilter }),
    } as any);

    const result = {
      answer: response.choices[0].message.content || "",
      citations: (response as any).citations || [],
      searchResults: (response as any).search_results || [],
      model: response.model,
      usage: response.usage,
    };

    // Cache with TTL based on query type
    const ttl = opts.recencyFilter === "hour" ? 900_000 : 3600_000;
    this.cache.set(cacheKey, { result, expiry: Date.now() + ttl });

    return { ...result, cached: false };
  }

  private hashQuery(query: string, model: string, opts: any): string {
    return createHash("sha256")
      .update(JSON.stringify({ query: query.toLowerCase().trim(), model, ...opts }))
      .digest("hex");
  }
}
```

### Step 2: Citation Pipeline
```typescript
// src/perplexity/citation-pipeline.ts
export interface Citation {
  url: string;
  domain: string;
  index: number;
}

export function extractCitations(answer: string, citationUrls: string[]): Citation[] {
  return citationUrls.map((url, i) => ({
    url,
    domain: new URL(url).hostname,
    index: i + 1,
  }));
}

export function renderCitationsAsMarkdown(answer: string, citations: Citation[]): string {
  let rendered = answer;
  for (const c of citations) {
    rendered = rendered.replaceAll(`[${c.index}]`, `[${c.index}](${c.url})`);
  }
  return rendered;
}

export function deduplicateCitations(citations: Citation[]): Citation[] {
  const seen = new Set<string>();
  return citations.filter((c) => {
    const normalized = c.url.split("?")[0].replace(/\/$/, "");
    if (seen.has(normalized)) return false;
    seen.add(normalized);
    return true;
  });
}
```

### Step 3: Research Orchestrator
```typescript
// src/perplexity/research-orchestrator.ts
export class ResearchOrchestrator {
  constructor(private searchService: SearchService) {}

  async research(topic: string): Promise<{
    sections: Array<{ question: string; answer: string; citations: string[] }>;
    bibliography: string[];
  }> {
    // Phase 1: Decompose topic (fast model)
    const overview = await this.searchService.search(
      `Break "${topic}" into 4-5 key research questions. List one per line.`,
      "quick"
    );
    const questions = overview.answer.split("\n").filter((q) => q.trim().length > 10);

    // Phase 2: Deep dive each question
    const sections = [];
    const allCitations = new Set<string>();

    for (const question of questions.slice(0, 5)) {
      const result = await this.searchService.search(question, "deep", {
        systemPrompt: `Research context: ${topic}. Provide detailed, well-cited answer.`,
      });
      sections.push({
        question: question.trim(),
        answer: result.answer,
        citations: result.citations,
      });
      result.citations.forEach((url: string) => allCitations.add(url));

      // Rate limit protection
      await new Promise((r) => setTimeout(r, 2000));
    }

    return { sections, bibliography: [...allCitations] };
  }
}
```

### Step 4: Fact-Check Service
```typescript
export async function factCheck(
  claim: string,
  searchService: SearchService
): Promise<{ verdict: string; confidence: string; sources: string[] }> {
  const result = await searchService.search(
    `Verify this claim with sources. State whether it is accurate, partially accurate, or inaccurate: "${claim}"`,
    "deep",
    { systemPrompt: "You are a fact-checker. Be precise and cite sources." }
  );

  return {
    verdict: result.answer,
    confidence: result.citations.length > 3 ? "high" : result.citations.length > 1 ? "medium" : "low",
    sources: result.citations,
  };
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No citations returned | Using sonar for complex query | Upgrade to sonar-pro |
| Stale information | No recency filter | Add `search_recency_filter` |
| High cost | sonar-pro for simple queries | Route by depth |
| Rate limit on research | Too many sequential queries | Add 2s delay between calls |

## Output
- Search service with model routing by query depth
- Citation extraction and rendering pipeline
- Multi-query research orchestrator
- Fact-checking service

## Resources
- [Perplexity API Docs](https://docs.perplexity.ai)
- [Model Guide](https://docs.perplexity.ai/getting-started/models)
