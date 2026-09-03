---
name: perplexity-known-pitfalls
description: 'Identify and avoid Perplexity anti-patterns and common integration mistakes.

  Use when reviewing Perplexity code, onboarding new developers,

  or auditing existing integrations for best practices violations.

  Trigger with phrases like "perplexity mistakes", "perplexity anti-patterns",

  "perplexity pitfalls", "perplexity code review", "perplexity gotchas".

  '
allowed-tools: Read, Grep
version: 1.13.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- perplexity
- audit
compatibility: Designed for Claude Code
---
# Perplexity Known Pitfalls

## Overview

Real gotchas when integrating Perplexity Sonar API. Perplexity uses an OpenAI-compatible chat endpoint but performs live web searches -- a fundamentally different paradigm from standard LLM completions. These pitfalls come from treating it like a regular chatbot.

## Prerequisites

- Perplexity API key configured
- Familiarity with either the official Perplexity SDK or its documented OpenAI compatibility mode
- A data-classification and citation-display policy for the calling application

## Instructions

1. Use `Read` to identify the exact Perplexity surface in use and `Grep` to locate its call sites: official SDK, Sonar through OpenAI compatibility, Search API, or Agent API. Do not mix endpoint or response assumptions across surfaces.
2. Trace one request from validated input through model selection, timeout/retry policy, citation handling, cache scope, and output rendering.
3. Compare each stage with the pitfalls and code-review checklist below. Treat credentials, customer prompts, citation URLs, and cached answers as untrusted or sensitive inputs.
4. Fix one class at a time and verify it with a synthetic request plus negative tests for invalid input, throttling, timeout, and unsafe citation URLs.
5. Record the chosen SDK/API, model policy, cache scope, and failure behavior so future upgrades can detect drift.

## Pitfalls

### 1. Using It as a Generic Chatbot

Sonar is designed for web-grounded answers. Using it for work that does not need retrieval adds avoidable latency and spend.

```python
# BAD: general chatbot (wastes a search query)
response = call_perplexity("Write me a haiku about cats")
# Adds retrieval work without adding value for this task

# GOOD: leverage web search capability
response = call_perplexity(
    "What are the latest Next.js 15 features released this month?",
    search_recency_filter="month"
)
```

### 2. Ignoring Citations

Perplexity returns `[1]`, `[2]` markers in text with a separate `citations` array. Ignoring them loses the key value prop.

```python
data = response.model_dump()  # or response.json() for raw HTTP
answer = data["choices"][0]["message"]["content"]
citations = data.get("citations", [])  # NOT in choices — top-level field

# BAD: displaying raw markers
print(answer)  # "According to [1], Node.js 22 adds..."

# GOOD: replace markers with links
import re
for i, url in enumerate(citations, 1):
    answer = answer.replace(f"[{i}]", f"{i}")
```

### 3. Assuming There Is No Official SDK

Perplexity provides official Python and TypeScript SDKs. OpenAI-compatible clients remain supported for Sonar, but new integrations should choose deliberately instead of inventing package names or assuming compatibility is the only path.

```typescript
// BAD — invented package name
import { PerplexityClient } from "@perplexity/sdk";

// GOOD — official SDK; reads PERPLEXITY_API_KEY from the environment
import Perplexity from "@perplexity-ai/perplexity_ai";
const client = new Perplexity();
```

### 4. Not Setting max_tokens

Without `max_tokens`, responses can be arbitrarily long, increasing costs unpredictably.

```typescript
// BAD: no token limit — output cost can spike
await client.chat.completions.create({
  model: "sonar-pro",
  messages: [{ role: "user", content: "Tell me about AI" }],
});

// GOOD: always set max_tokens
await client.chat.completions.create({
  model: "sonar-pro",
  messages: [{ role: "user", content: "Tell me about AI" }],
  max_tokens: 1024,
});
```

### 5. No Recency Filter for Time-Sensitive Queries

Without `search_recency_filter`, Perplexity may cite outdated articles.

```python
# BAD: may return articles from any time period
response = call_perplexity("current Bitcoin price")

# GOOD: constrain to recent results
response = call_perplexity(
    "current Bitcoin price",
    search_recency_filter="day"  # hour | day | week | month
)
```

### 6. Sending Full Conversation History

Each message in the conversation may trigger new search queries. Sending 20 turns of history is expensive and slow.

```python
# BAD: 20 turns of history = many search queries
messages = long_history + [{"role": "user", "content": "summarize"}]

# GOOD: summarize context, send focused query
messages = [
    {"role": "system", "content": "Answer based on web search."},
    {"role": "user", "content": f"Context: {summary}\nQuestion: {question}"}
]
```

### 7. Using sonar-pro for Simple Queries

Using a higher-cost model for a simple factual lookup can waste budget. Resolve prices from the current provider catalog rather than embedding them in application logic.

```typescript
// BAD: sonar-pro for a trivial question
await client.chat.completions.create({
  model: "sonar-pro",
  messages: [{ role: "user", content: "What is the capital of France?" }],
});

// GOOD: match model to complexity
const model = isComplexQuery(query) ? "sonar-pro" : "sonar";
```

### 8. Mixing Allowlist and Denylist in Domain Filter

`search_domain_filter` supports either allowlist (include) or denylist (exclude with `-` prefix), but not both in the same request.

```typescript
// BAD: mixing modes
search_domain_filter: ["python.org", "-reddit.com"]  // ERROR

// GOOD: pick one mode
search_domain_filter: ["python.org", "docs.python.org"]  // Allowlist
// OR
search_domain_filter: ["-reddit.com", "-quora.com"]  // Denylist
```

### 9. Not Caching Search Results

Every uncached call performs a web search. At scale, duplicate queries burn budget.

```typescript
// BAD: same query hits API every time
app.get("/search", async (req, res) => {
  const result = await client.chat.completions.create({ ... });
  res.json(result);
});

// GOOD: cache by query hash
const cache = new LRUCache({ max: 1000, ttl: 3600_000 });
app.get("/search", async (req, res) => {
  const tenantId = requireTenant(req);
  const key = hash(`${tenantId}:${normalizeQuery(req.query.q)}`);
  if (cache.has(key)) return res.json(cache.get(key));
  const result = await client.chat.completions.create({ /* bounded request */ });
  cache.set(key, result);
  res.json(result);
});
```

### 10. Wrong Base URL

The API is at `api.perplexity.ai`, not `api.perplexity.com`.

```typescript
// BAD
baseURL: "https://api.perplexity.com"  // Wrong domain

// GOOD
baseURL: "https://api.perplexity.ai"   // Correct
```

## Code Review Checklist

- [ ] Uses the official Perplexity SDK or the documented OpenAI compatibility path; no invented client package
- [ ] Base URL is `https://api.perplexity.ai`
- [ ] `max_tokens` set on every request
- [ ] Citations parsed from `response.citations` array
- [ ] `search_recency_filter` used for time-sensitive queries
- [ ] Caching implemented for repeated queries
- [ ] Model routing: sonar for simple, sonar-pro for complex
- [ ] Conversation history trimmed before sending
- [ ] PII sanitized from queries
- [ ] Domain filter uses only allowlist OR denylist, not both

## Error Handling

| Pitfall | Impact | Detection |
|---------|--------|-----------|
| No caching | 3-5x cost overrun | Check cache hit rate metric |
| Wrong model | Budget waste | Grep for `sonar-pro` in simple query paths |
| No max_tokens | Unpredictable costs | Grep for `create()` calls without `max_tokens` |
| PII in queries | Privacy violation | Run sanitization check in CI |

## Examples

### Review an existing search route

Start with one route and document its API surface, tenant boundary, request model, maximum output tokens, timeout, bounded retry budget, and citation-rendering path. Add negative fixtures for an absent credential, a 429 response, a timeout, a `javascript:` citation, a localhost citation, and a cache lookup from another tenant. The review is complete only when each failure is explicit and no prompt, answer, key metadata, or raw provider body is logged.

### Choose an SDK intentionally

For a new integration, prefer the official Perplexity SDK when its typed APIs cover the required surface. If an existing system already standardizes on the OpenAI client, use the documented Sonar compatibility base URL and add Perplexity-specific types for `citations` and `search_results`. Pin the package version and retain a contract test before upgrading either path.

## Output

- Identified anti-patterns in existing code
- Applied fixes for each pitfall
- Code review checklist for ongoing quality

## Resources

- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Official Perplexity SDK](https://docs.perplexity.ai/docs/sdk/overview)
- [Perplexity Quickstart](https://docs.perplexity.ai/docs/getting-started/quickstart)
- [OpenAI Compatibility](https://docs.perplexity.ai/docs/sonar/openai-compatibility)
- [API-surface review matrix](references/api-surface-review.md)
