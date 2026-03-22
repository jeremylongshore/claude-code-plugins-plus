---
name: perplexity-known-pitfalls
description: |
  Identify and avoid Perplexity anti-patterns and common integration mistakes.
  Use when reviewing Perplexity code, onboarding new developers,
  or auditing existing integrations for best practices violations.
  Trigger with phrases like "perplexity mistakes", "perplexity anti-patterns",
  "perplexity pitfalls", "perplexity code review", "perplexity gotchas".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, audit]

---
# Perplexity Known Pitfalls

## Overview
Real gotchas when integrating Perplexity Sonar API. Perplexity uses an OpenAI-compatible chat endpoint but performs live web searches -- a fundamentally different paradigm from standard LLM completions. These pitfalls come from treating it like a regular chatbot.

## Prerequisites
- Perplexity API key configured
- Understanding of OpenAI-compatible chat API format

## Pitfalls

### 1. Using It as a Generic Chatbot
Perplexity searches the web per request. Using it for tasks that don't need web search wastes money.

```python
# BAD: general chatbot (wastes a search query)
response = call_perplexity("Write me a haiku about cats")
# Costs $0.005+ for something any LLM can do offline

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
    answer = answer.replace(f"[{i}]", f"[{i}]({url})")
```

### 3. Using Wrong SDK Import
There is no `@perplexity/sdk` or `perplexity` Python package. Use the standard OpenAI client.

```typescript
// BAD — this package doesn't exist
import { PerplexityClient } from "@perplexity/sdk";

// GOOD — use OpenAI client with Perplexity base URL
import OpenAI from "openai";
const client = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY,
  baseURL: "https://api.perplexity.ai",
});
```

### 4. Not Setting max_tokens
Without `max_tokens`, responses can be arbitrarily long, increasing costs unpredictably.

```typescript
// BAD: no token limit — output cost can spike
await client.chat.completions.create({
  model: "sonar-pro",  // $15/M output tokens!
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
`sonar-pro` costs 3-15x more than `sonar`. Using it for simple factual lookups wastes budget.

```typescript
// BAD: sonar-pro for a trivial question
await client.chat.completions.create({
  model: "sonar-pro",  // $3 input + $15 output per M tokens
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
app.get("/search", (req, res) => {
  const result = await client.chat.completions.create({ ... });
  res.json(result);
});

// GOOD: cache by query hash
const cache = new LRUCache({ max: 1000, ttl: 3600_000 });
app.get("/search", (req, res) => {
  const key = hash(req.query.q);
  if (cache.has(key)) return res.json(cache.get(key));
  const result = await client.chat.completions.create({ ... });
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
- [ ] Uses `openai` package, not fake `@perplexity/sdk`
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

## Output
- Identified anti-patterns in existing code
- Applied fixes for each pitfall
- Code review checklist for ongoing quality

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Perplexity Model Guide](https://docs.perplexity.ai/getting-started/models)
- [OpenAI Compatibility](https://docs.perplexity.ai/guides/chat-completions-guide)
