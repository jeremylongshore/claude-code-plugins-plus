---
name: exa-known-pitfalls
description: |
  Identify and avoid Exa anti-patterns and common integration mistakes.
  Use when reviewing Exa code, onboarding new developers,
  or auditing existing Exa integrations for correctness.
  Trigger with phrases like "exa mistakes", "exa anti-patterns",
  "exa pitfalls", "exa what not to do", "exa code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, audit, best-practices]

---
# Exa Known Pitfalls

## Overview
Real gotchas when integrating Exa's neural search API. Exa uses embeddings-based search rather than keyword matching, which creates a different class of failure modes than traditional search APIs. This skill covers the top pitfalls with wrong/right examples.

## Pitfall 1: Keyword-Style Queries

Exa's neural search interprets natural language semantically. Boolean operators and keyword syntax degrade results.

```typescript
import Exa from "exa-js";
const exa = new Exa(process.env.EXA_API_KEY);

// BAD: keyword/boolean style — Exa ignores AND/OR
const bad = await exa.search(
  "python AND machine learning OR deep learning 2024"
);

// GOOD: natural language statement
const good = await exa.search(
  "recent tutorials on building ML models with Python",
  { type: "neural", numResults: 10 }
);
```

## Pitfall 2: Wrong Search Type

Using neural search for exact lookups (URLs, names) or keyword search for conceptual queries silently degrades quality.

```typescript
// BAD: neural search for a specific URL/identifier
const bad = await exa.search("arxiv.org/abs/2301.00001", { type: "neural" });

// GOOD: keyword for exact terms, neural for concepts
const exactMatch = await exa.search("arxiv.org/abs/2301.00001", {
  type: "keyword",
});
const conceptual = await exa.search(
  "transformer architecture improvements for long context",
  { type: "neural" }
);
```

## Pitfall 3: Expecting Content from search()

`search()` returns metadata only (URL, title, score). Content requires `searchAndContents()` or `getContents()`.

```typescript
// BAD: accessing .text from search() — it's undefined
const results = await exa.search("AI safety research");
const text = results.results[0].text;  // undefined!

// GOOD: use searchAndContents for text/highlights
const withContent = await exa.searchAndContents("AI safety research", {
  numResults: 5,
  text: { maxCharacters: 2000 },
  highlights: { maxCharacters: 500 },
});
console.log(withContent.results[0].text);       // actual content
console.log(withContent.results[0].highlights);  // key excerpts
```

## Pitfall 4: Narrow Date Filters Return Empty

Date filters silently exclude results. A single-day window often returns nothing without error.

```typescript
// BAD: too narrow, likely returns empty array
const bad = await exa.search("AI news", {
  startPublishedDate: "2025-03-15T00:00:00.000Z",
  endPublishedDate: "2025-03-15T23:59:59.000Z",
});

// GOOD: reasonable window with fallback
let results = await exa.search("AI news", {
  startPublishedDate: "2025-03-01T00:00:00.000Z",
  endPublishedDate: "2025-03-31T23:59:59.000Z",
  numResults: 10,
});
// Fallback if no results
if (results.results.length === 0) {
  results = await exa.search("AI news", { numResults: 10 });
}
```

## Pitfall 5: findSimilar Takes a URL, Not a Query

`findSimilar` expects a URL as its first argument. Passing a query string gives meaningless results.

```typescript
// BAD: passing a query string to findSimilar
const bad = await exa.findSimilar("machine learning research papers");

// GOOD: pass a URL — findSimilar finds pages semantically similar to it
const good = await exa.findSimilar("https://arxiv.org/abs/2301.00001", {
  numResults: 10,
  excludeSourceDomain: true,
});
```

## Pitfall 6: Date Filters with company/people Categories

The `company` and `people` categories do NOT support date filters. Using them returns a 400 error.

```typescript
// BAD: date filter with company category → 400 error
const bad = await exa.search("AI startups", {
  category: "company",
  startPublishedDate: "2024-01-01T00:00:00.000Z",  // not supported!
});

// GOOD: company search without date filters
const good = await exa.search("AI startups", {
  category: "company",
  numResults: 10,
});
```

## Pitfall 7: Not Limiting Content Size

Requesting full text without `maxCharacters` can return massive payloads, increasing latency and cost.

```typescript
// BAD: unlimited text retrieval
const bad = await exa.searchAndContents("topic", {
  numResults: 20,
  text: true,  // could return megabytes of content
});

// GOOD: limit content size
const good = await exa.searchAndContents("topic", {
  numResults: 10,
  text: { maxCharacters: 2000 },  // cap at 2000 chars per result
  highlights: { maxCharacters: 500 },
});
```

## Pitfall 8: Creating New Client Per Request

Each `new Exa()` call creates a new HTTP client. Reuse a singleton for connection pooling.

```typescript
// BAD: new client every request (in a route handler)
app.get("/search", async (req, res) => {
  const exa = new Exa(process.env.EXA_API_KEY);  // wasteful!
  const results = await exa.search(req.query.q);
  res.json(results);
});

// GOOD: singleton client
const exa = new Exa(process.env.EXA_API_KEY);
app.get("/search", async (req, res) => {
  const results = await exa.search(req.query.q);
  res.json(results);
});
```

## Pitfall 9: Ignoring the requestId in Errors

Exa error responses include `requestId` for support debugging. Always log it.

```typescript
// BAD: generic error handling
try {
  await exa.search("query");
} catch (err) {
  console.error("Search failed");  // loses diagnostic info
}

// GOOD: capture requestId
try {
  await exa.search("query");
} catch (err: any) {
  console.error("Search failed:", {
    status: err.status,
    message: err.message,
    requestId: err.requestId,  // include when contacting support
    tag: err.error_tag,
  });
}
```

## Quick Review Checklist
- [ ] Queries are natural language, not keyword/boolean syntax
- [ ] Search type matches the query intent (neural vs keyword)
- [ ] Using `searchAndContents` when page content is needed
- [ ] Date filter windows are wide enough (7+ days)
- [ ] `findSimilar` receives URLs, not query strings
- [ ] No date filters on `company` or `people` categories
- [ ] `maxCharacters` set on text and highlights
- [ ] Exa client is a singleton, not created per request
- [ ] Error handling captures `requestId`

## Resources
- [Exa Search Reference](https://docs.exa.ai/reference/search)
- [Exa Error Codes](https://docs.exa.ai/reference/error-codes)
- [Exa Contents Retrieval](https://docs.exa.ai/reference/contents-retrieval)

## Next Steps
For SDK patterns, see `exa-sdk-patterns`. For common errors, see `exa-common-errors`.
