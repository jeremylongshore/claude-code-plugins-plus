---
name: exa-reliability-patterns
description: |
  Implement Exa reliability patterns: query fallback chains, circuit breakers, and graceful degradation.
  Use when building fault-tolerant Exa integrations, implementing fallback strategies,
  or adding resilience to production search services.
  Trigger with phrases like "exa reliability", "exa circuit breaker",
  "exa fallback", "exa resilience", "exa graceful degradation".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, reliability, resilience]

---
# Exa Reliability Patterns

## Overview
Production reliability patterns for Exa neural search. Exa-specific failure modes include: empty result sets (query too narrow), content retrieval failures (sites block crawling), variable latency by search type, and 429 rate limits at 10 QPS default.

## Instructions

### Step 1: Query Fallback Chain
```typescript
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);

// If neural search returns too few results, fall back through search types
async function resilientSearch(
  query: string,
  minResults = 3,
  opts: any = {}
) {
  // Try 1: Neural search (best quality)
  let results = await exa.searchAndContents(query, {
    type: "neural",
    numResults: 10,
    ...opts,
  });
  if (results.results.length >= minResults) return results;

  // Try 2: Auto search (Exa picks best approach)
  results = await exa.searchAndContents(query, {
    type: "auto",
    numResults: 10,
    ...opts,
  });
  if (results.results.length >= minResults) return results;

  // Try 3: Keyword search (different index)
  results = await exa.searchAndContents(query, {
    type: "keyword",
    numResults: 10,
    ...opts,
  });
  if (results.results.length >= minResults) return results;

  // Try 4: Remove filters and broaden
  const broadOpts = { ...opts };
  delete broadOpts.startPublishedDate;
  delete broadOpts.endPublishedDate;
  delete broadOpts.includeDomains;
  delete broadOpts.includeText;

  return exa.searchAndContents(query, {
    type: "auto",
    numResults: 10,
    ...broadOpts,
  });
}
```

### Step 2: Retry with Exponential Backoff
```typescript
async function searchWithRetry(
  query: string,
  opts: any,
  maxRetries = 3
) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await exa.searchAndContents(query, opts);
    } catch (err: any) {
      const status = err.status || 0;

      // Only retry on rate limits (429) and server errors (5xx)
      if (status !== 429 && (status < 500 || status >= 600)) throw err;
      if (attempt === maxRetries) throw err;

      const delay = 1000 * Math.pow(2, attempt) + Math.random() * 500;
      console.log(`[Exa] ${status} retry ${attempt + 1}/${maxRetries} in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}
```

### Step 3: Circuit Breaker
```typescript
class ExaCircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: "closed" | "open" | "half-open" = "closed";
  private readonly threshold = 5;       // failures before opening
  private readonly resetTimeMs = 30000; // 30s before half-open

  async execute<T>(fn: () => Promise<T>, fallback?: () => T): Promise<T> {
    // Check if circuit should reset
    if (this.state === "open") {
      if (Date.now() - this.lastFailure > this.resetTimeMs) {
        this.state = "half-open";
      } else if (fallback) {
        return fallback();
      } else {
        throw new Error("Exa circuit breaker is open");
      }
    }

    try {
      const result = await fn();
      if (this.state === "half-open") {
        this.state = "closed";
        this.failures = 0;
      }
      return result;
    } catch (err: any) {
      this.failures++;
      this.lastFailure = Date.now();

      if (this.failures >= this.threshold) {
        this.state = "open";
        console.warn(`[Exa] Circuit breaker OPEN after ${this.failures} failures`);
      }

      if (fallback && this.state === "open") return fallback();
      throw err;
    }
  }

  getState() {
    return { state: this.state, failures: this.failures };
  }
}

const circuitBreaker = new ExaCircuitBreaker();

// Usage with fallback to cached results
const result = await circuitBreaker.execute(
  () => exa.searchAndContents("query", { numResults: 5, text: true }),
  () => getCachedResults("query") // fallback when circuit is open
);
```

### Step 4: Graceful Degradation
```typescript
interface SearchResultWithMeta {
  results: any[];
  degraded: boolean;
  source: "live" | "cache" | "fallback";
  searchType: string;
}

async function degradableSearch(
  query: string,
  opts: any = {}
): Promise<SearchResultWithMeta> {
  // Level 1: Full search with contents
  try {
    const results = await searchWithRetry(query, {
      type: "neural",
      numResults: 10,
      text: { maxCharacters: 2000 },
      highlights: { maxCharacters: 500 },
      ...opts,
    }, 2);
    return { results: results.results, degraded: false, source: "live", searchType: "neural" };
  } catch {}

  // Level 2: Fast search without content (less expensive)
  try {
    const results = await exa.search(query, {
      type: "fast",
      numResults: 5,
    });
    return { results: results.results, degraded: true, source: "live", searchType: "fast" };
  } catch {}

  // Level 3: Return cached results
  const cached = getCachedResults(query);
  if (cached) {
    return { results: cached, degraded: true, source: "cache", searchType: "cached" };
  }

  // Level 4: Return empty with degradation flag
  return { results: [], degraded: true, source: "fallback", searchType: "none" };
}
```

### Step 5: Result Quality Monitoring
```typescript
class SearchQualityMonitor {
  private stats = { total: 0, empty: 0, lowScore: 0 };

  record(results: any[]) {
    this.stats.total++;
    if (results.length === 0) this.stats.empty++;
    if (results[0]?.score < 0.5) this.stats.lowScore++;
  }

  isHealthy(): boolean {
    if (this.stats.total < 10) return true; // not enough data
    const emptyRate = this.stats.empty / this.stats.total;
    const lowScoreRate = this.stats.lowScore / this.stats.total;
    return emptyRate < 0.2 && lowScoreRate < 0.3;
  }

  getReport() {
    return {
      ...this.stats,
      emptyRate: `${((this.stats.empty / this.stats.total) * 100).toFixed(1)}%`,
      lowScoreRate: `${((this.stats.lowScore / this.stats.total) * 100).toFixed(1)}%`,
      healthy: this.isHealthy(),
    };
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Empty results | Query too specific | Use fallback chain with broader query |
| Slow responses | Neural on complex query | Degrade to `fast` type |
| 429 rate limit | Burst traffic | Circuit breaker + backoff |
| Content retrieval fails | Site blocks crawling | Fall back to highlights or summary |
| Quality degradation | Query drift | Monitor empty/low-score rates |

## Resources
- [Exa API Reference](https://docs.exa.ai/reference/search)
- [Exa Error Codes](https://docs.exa.ai/reference/error-codes)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)

## Next Steps
For policy guardrails, see `exa-policy-guardrails`. For architecture variants, see `exa-architecture-variants`.
