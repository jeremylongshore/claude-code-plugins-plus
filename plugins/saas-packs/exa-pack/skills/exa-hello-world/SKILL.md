---
name: exa-hello-world
description: |
  Create a minimal working Exa search example with real results.
  Use when starting a new Exa integration, testing your setup,
  or learning basic search, searchAndContents, and findSimilar patterns.
  Trigger with phrases like "exa hello world", "exa example",
  "exa quick start", "simple exa search", "first exa query".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, api, quickstart, neural-search]

---
# Exa Hello World

## Overview
Minimal working examples demonstrating all core Exa search operations: basic search, search with contents, find similar, and get contents. Each example is runnable standalone.

## Prerequisites
- `exa-js` SDK installed (`npm install exa-js`)
- `EXA_API_KEY` environment variable set
- Node.js 18+ with ES module support

## Instructions

### Step 1: Basic Search (Metadata Only)
```typescript
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);

// Basic search returns URLs, titles, and scores — no page content
const results = await exa.search("best practices for building RAG pipelines", {
  type: "auto",       // auto | neural | keyword | fast | instant
  numResults: 5,
});

for (const r of results.results) {
  console.log(`[${r.score.toFixed(2)}] ${r.title}`);
  console.log(`  ${r.url}`);
}
```

### Step 2: Search with Contents
```typescript
// searchAndContents returns text, highlights, and/or summary with each result
const results = await exa.searchAndContents(
  "how transformers work in large language models",
  {
    type: "neural",
    numResults: 3,
    text: { maxCharacters: 1000 },
    highlights: { maxCharacters: 500, query: "attention mechanism" },
    summary: { query: "explain transformers simply" },
  }
);

for (const r of results.results) {
  console.log(`## ${r.title}`);
  console.log(`URL: ${r.url}`);
  console.log(`Summary: ${r.summary}`);
  console.log(`Text preview: ${r.text?.substring(0, 200)}...`);
  console.log(`Highlights: ${r.highlights?.join(" | ")}`);
  console.log();
}
```

### Step 3: Find Similar Pages
```typescript
// findSimilar takes a URL and returns semantically similar pages
const similar = await exa.findSimilarAndContents(
  "https://arxiv.org/abs/2301.00234",
  {
    numResults: 5,
    text: { maxCharacters: 500 },
    excludeSourceDomain: true,
  }
);

console.log("Pages similar to the seed URL:");
for (const r of similar.results) {
  console.log(`  ${r.title} — ${r.url}`);
}
```

### Step 4: Get Contents for Known URLs
```typescript
// getContents retrieves page content for specific URLs
const contents = await exa.getContents(
  ["https://example.com/article-1", "https://example.com/article-2"],
  {
    text: { maxCharacters: 2000 },
    highlights: { maxCharacters: 500 },
    livecrawl: "preferred",
    livecrawlTimeout: 10000,
  }
);

for (const r of contents.results) {
  console.log(`${r.title}: ${r.text?.length} chars retrieved`);
}
```

## Output
- Working TypeScript file with Exa client initialization
- Search results printed to console with titles, URLs, and scores
- Content extraction (text, highlights, summary) demonstrated
- Similarity search results from a seed URL

## Error Handling
| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| `INVALID_API_KEY` | 401 | API key missing or invalid | Check `EXA_API_KEY` env var |
| `INVALID_REQUEST_BODY` | 400 | Malformed parameters | Verify parameter types match SDK docs |
| `NO_MORE_CREDITS` | 402 | Account credits depleted | Top up at dashboard.exa.ai |
| `429 Too Many Requests` | 429 | Rate limit exceeded | Wait and retry; default is 10 QPS |
| Empty `results` array | 200 | Query too narrow or filters too strict | Broaden query or relax date/domain filters |

## Examples

### Complete Runnable Script
```typescript
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);

async function main() {
  // 1. Search
  const search = await exa.search("AI safety research", { numResults: 3 });
  console.log(`Found ${search.results.length} results\n`);

  // 2. Search with contents
  const detailed = await exa.searchAndContents("AI safety research", {
    numResults: 2,
    text: true,
    highlights: { maxCharacters: 300 },
  });
  console.log("First result text length:", detailed.results[0]?.text?.length);

  // 3. Find similar
  if (search.results[0]) {
    const similar = await exa.findSimilar(search.results[0].url, {
      numResults: 3,
    });
    console.log("\nSimilar pages:", similar.results.map(r => r.title));
  }
}

main().catch(console.error);
```

## Resources
- [Exa Quickstart](https://docs.exa.ai/reference/quickstart)
- [Exa Search Reference](https://docs.exa.ai/reference/search)
- [Exa Cheat Sheet](https://docs.exa.ai/sdks/cheat-sheet)

## Next Steps
Proceed to `exa-core-workflow-a` for neural search patterns or `exa-sdk-patterns` for production-ready code.
