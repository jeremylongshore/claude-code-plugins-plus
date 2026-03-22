---
name: perplexity-architecture-variants
description: |
  Choose and implement Perplexity architecture blueprints for different scales:
  direct search widget, cached research layer, and multi-query pipeline.
  Trigger with phrases like "perplexity architecture", "perplexity blueprint",
  "how to structure perplexity", "perplexity project layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, migration, scaling, microservices]

---
# Perplexity Architecture Variants

## Overview
Three validated architectures for Perplexity Sonar API at different scales. Each builds on the previous, adding caching and orchestration as volume grows.

## Decision Matrix

| Factor | Direct Widget | Cached Layer | Research Pipeline |
|--------|--------------|--------------|-------------------|
| Volume | <500/day | 500-5K/day | 5K+/day |
| Latency (p50) | 2-5s | 50ms (cached) / 2-5s (miss) | 10-30s |
| Model | `sonar` | `sonar` + cache | `sonar` + `sonar-pro` |
| Monthly Cost | <$150 | $50-$300 | $300+ |
| Complexity | Minimal | Moderate | High |

## Instructions

### Variant 1: Direct Search Widget (<500 queries/day)

Best for: Adding AI search to an existing app. No cache needed at this scale.

```typescript
// Simple endpoint — add to any Express/Next.js app
import OpenAI from "openai";

const perplexity = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY!,
  baseURL: "https://api.perplexity.ai",
});

app.post("/api/search", async (req, res) => {
  try {
    const response = await perplexity.chat.completions.create({
      model: "sonar",
      messages: [{ role: "user", content: req.body.query }],
      max_tokens: 1024,
    });

    res.json({
      answer: response.choices[0].message.content,
      citations: (response as any).citations || [],
    });
  } catch (err: any) {
    if (err.status === 429) {
      res.status(429).json({ error: "Rate limited. Try again shortly." });
    } else {
      res.status(500).json({ error: "Search unavailable" });
    }
  }
});
```

### Variant 2: Cached Research Layer (500-5K queries/day)

Best for: Repeated queries, knowledge base search, FAQ bots. Cache eliminates duplicate API calls.

```typescript
import { createHash } from "crypto";
import { LRUCache } from "lru-cache";

const cache = new LRUCache<string, any>({
  max: 5000,
  ttl: 4 * 3600_000,  // 4-hour TTL
});

class CachedSearchService {
  constructor(private client: OpenAI) {}

  async search(query: string, model = "sonar") {
    const key = this.cacheKey(query, model);
    const cached = cache.get(key);
    if (cached) return { ...cached, cached: true };

    const response = await this.client.chat.completions.create({
      model,
      messages: [{ role: "user", content: query }],
      max_tokens: 1024,
    });

    const result = {
      answer: response.choices[0].message.content || "",
      citations: (response as any).citations || [],
      model: response.model,
    };

    cache.set(key, result);
    return { ...result, cached: false };
  }

  private cacheKey(query: string, model: string): string {
    return createHash("sha256")
      .update(`${model}:${query.toLowerCase().trim()}`)
      .digest("hex");
  }

  get stats() {
    return { size: cache.size, max: 5000 };
  }
}
```

### Variant 3: Multi-Query Research Pipeline (5K+ queries/day)

Best for: Automated research, report generation, competitive intelligence. Uses job queue for rate limiting and sonar-pro for deep analysis.

```typescript
import PQueue from "p-queue";

class ResearchPipeline {
  private queue: PQueue;
  private cache: CachedSearchService;

  constructor(private client: OpenAI) {
    this.queue = new PQueue({
      concurrency: 3,
      interval: 60_000,
      intervalCap: 40,  // 40 RPM (safety margin)
    });
    this.cache = new CachedSearchService(client);
  }

  async researchTopic(topic: string): Promise<{
    overview: string;
    sections: Array<{ question: string; answer: string; citations: string[] }>;
    bibliography: string[];
  }> {
    // Phase 1: Decompose (sonar, fast)
    const decomposition = await this.cache.search(
      `Break "${topic}" into 4 focused research questions. One per line.`,
      "sonar"
    );
    const questions = decomposition.answer.split("\n").filter((q) => q.trim().length > 10);

    // Phase 2: Deep research each question (sonar-pro, queued)
    const sections = await Promise.all(
      questions.slice(0, 5).map((q) =>
        this.queue.add(async () => {
          const result = await this.cache.search(q.trim(), "sonar-pro");
          return { question: q.trim(), ...result };
        })
      )
    );

    // Phase 3: Compile
    const allCitations = new Set<string>();
    for (const s of sections) {
      if (s) s.citations.forEach((url: string) => allCitations.add(url));
    }

    return {
      overview: decomposition.answer,
      sections: sections.filter(Boolean).map((s) => ({
        question: s!.question,
        answer: s!.answer,
        citations: s!.citations,
      })),
      bibliography: [...allCitations],
    };
  }
}
```

### Python Variant (Direct Widget)
```python
from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)
client = OpenAI(api_key=os.environ["PERPLEXITY_API_KEY"], base_url="https://api.perplexity.ai")

@app.route("/api/search", methods=["POST"])
def search():
    query = request.json["query"]
    response = client.chat.completions.create(
        model="sonar",
        messages=[{"role": "user", "content": query}],
        max_tokens=1024,
    )
    raw = response.model_dump()
    return jsonify({
        "answer": response.choices[0].message.content,
        "citations": raw.get("citations", []),
    })
```

## Choosing the Right Variant

```
How many queries per day?
├─ <500 → Variant 1 (Direct Widget)
│   └─ Add retry with backoff
├─ 500-5K → Variant 2 (Cached Layer)
│   └─ Add LRU cache with 4-hour TTL
└─ 5K+ → Variant 3 (Research Pipeline)
    └─ Add job queue + sonar-pro for deep queries
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slow in UI | No caching | Add Variant 2 cache layer |
| High cost | sonar-pro for all queries | Route simple queries to sonar |
| Rate limited | Burst traffic | Add PQueue rate limiter |
| Stale answers | Long cache TTL | Reduce TTL for time-sensitive queries |

## Output
- Selected architecture variant matching your scale
- Implementation code for chosen variant
- Cache strategy if applicable
- Queue configuration if applicable

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Perplexity Model Pricing](https://docs.perplexity.ai/docs/getting-started/pricing)

## Next Steps
For common pitfalls, see `perplexity-known-pitfalls`.
