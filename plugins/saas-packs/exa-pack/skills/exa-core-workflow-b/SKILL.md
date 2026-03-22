---
name: exa-core-workflow-b
description: |
  Execute Exa findSimilar, getContents, answer, and streaming answer workflows.
  Use when finding pages similar to a URL, retrieving content for known URLs,
  or getting AI-generated answers with citations.
  Trigger with phrases like "exa find similar", "exa get contents",
  "exa answer", "exa similarity search", "findSimilarAndContents".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, workflow, similarity-search, answer]

---
# Exa Core Workflow B — Similarity, Contents & Answer

## Overview
Secondary Exa workflow covering three endpoints beyond search: `findSimilar` (discover pages semantically related to a URL), `getContents` (retrieve text/highlights for known URLs), and `answer` (get AI-generated answers with web citations). These complement the primary search workflow in `exa-core-workflow-a`.

## Prerequisites
- `exa-js` installed and `EXA_API_KEY` configured
- Familiarity with `exa-core-workflow-a` search patterns

## Instructions

### Step 1: Find Similar Pages
```typescript
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);

// findSimilar takes a URL (not a query string) and returns
// pages with semantically similar content
const similar = await exa.findSimilar(
  "https://openai.com/research/gpt-4",
  {
    numResults: 10,
    excludeSourceDomain: true, // exclude openai.com from results
    startPublishedDate: "2024-01-01T00:00:00.000Z",
    excludeDomains: ["reddit.com", "twitter.com"],
  }
);

for (const r of similar.results) {
  console.log(`${r.title} — ${r.url}`);
}
```

### Step 2: Find Similar with Contents
```typescript
// findSimilarAndContents combines similarity search + content extraction
const results = await exa.findSimilarAndContents(
  "https://huggingface.co/blog/llama3",
  {
    numResults: 5,
    text: { maxCharacters: 2000 },
    highlights: { maxCharacters: 500, query: "open source LLM" },
    excludeSourceDomain: true,
  }
);

for (const r of results.results) {
  console.log(`## ${r.title}`);
  console.log(`URL: ${r.url}`);
  console.log(`Highlights: ${r.highlights?.join(" | ")}`);
  console.log(`Text preview: ${r.text?.substring(0, 300)}...\n`);
}
```

### Step 3: Get Contents for Known URLs
```typescript
// getContents retrieves page content for a list of URLs you already have
// Useful when you have URLs from a previous search or external source
const contents = await exa.getContents(
  [
    "https://arxiv.org/abs/2401.00001",
    "https://arxiv.org/abs/2401.00002",
    "https://blog.example.com/article",
  ],
  {
    text: { maxCharacters: 3000 },
    highlights: { maxCharacters: 500 },
    summary: { query: "key findings and methodology" },
    livecrawl: "preferred",     // try fresh, fall back to cache
    livecrawlTimeout: 15000,    // 15s timeout
    // Subpage crawling: retrieve linked pages from each URL
    subpages: 3,                // crawl up to 3 subpages per URL
    subpageTarget: "documentation",  // find subpages matching this term
  }
);

for (const r of contents.results) {
  console.log(`${r.title}: ${r.text?.length || 0} chars`);
  if (r.summary) console.log(`Summary: ${r.summary}`);
}
```

### Step 4: AI-Powered Answer with Citations
```typescript
// answer() searches the web and returns an AI-generated answer with sources
const answer = await exa.answer(
  "What are the key differences between RAG and fine-tuning for LLMs?",
  {
    text: true,
    // The answer response includes citations linking to source results
  }
);

console.log("Answer:", answer.answer);
console.log("\nSources:");
for (const r of answer.results) {
  console.log(`  - ${r.title}: ${r.url}`);
}
```

### Step 5: Streaming Answer
```typescript
// streamAnswer returns chunks as they're generated
for await (const chunk of exa.streamAnswer(
  "What is the current state of quantum computing in 2025?"
)) {
  if (chunk.content) {
    process.stdout.write(chunk.content);
  }
  if (chunk.citations) {
    console.log("\n\nCitations:", JSON.stringify(chunk.citations, null, 2));
  }
}
```

## Output
- Similar pages discovered from a seed URL
- Page content (text, highlights, summary) for known URLs
- AI-generated answers with web source citations
- Streaming answer chunks for real-time display

## Error Handling
| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| `INVALID_URLS` | 400 | Malformed URLs in getContents | Validate URLs have protocol |
| `CRAWL_NOT_FOUND` | 404 | Content unavailable at URL | Verify URL is accessible |
| `CRAWL_TIMEOUT` | 504 | Live crawl exceeded timeout | Increase `livecrawlTimeout` |
| `SOURCE_NOT_AVAILABLE` | 403 | Paywalled or blocked content | Try without `livecrawl: "always"` |
| `UNABLE_TO_GENERATE_RESPONSE` | 501 | Insufficient data for answer | Rephrase query or add context |
| Empty `similar.results` | 200 | Seed URL not indexed | Try a more popular seed URL |

## Examples

### Competitive Intelligence Pipeline
```typescript
async function findCompetitors(companyUrl: string) {
  // Find companies similar to a given company
  const similar = await exa.findSimilarAndContents(companyUrl, {
    numResults: 10,
    excludeSourceDomain: true,
    text: { maxCharacters: 500 },
    category: "company",
  });

  return similar.results.map(r => ({
    name: r.title,
    url: r.url,
    description: r.text?.substring(0, 200),
  }));
}
```

### Batch URL Content Retrieval
```typescript
async function enrichUrls(urls: string[]) {
  // Process URLs in batches to stay within rate limits
  const batchSize = 10;
  const allContents = [];

  for (let i = 0; i < urls.length; i += batchSize) {
    const batch = urls.slice(i, i + batchSize);
    const contents = await exa.getContents(batch, {
      text: { maxCharacters: 1500 },
      summary: { query: "main topic and key points" },
    });
    allContents.push(...contents.results);
  }

  return allContents;
}
```

## Resources
- [Exa Find Similar](https://docs.exa.ai/reference/find-similar-links)
- [Exa Get Contents](https://docs.exa.ai/reference/get-contents)
- [Exa Contents Retrieval](https://docs.exa.ai/reference/contents-retrieval)

## Next Steps
For common errors, see `exa-common-errors`. For SDK patterns, see `exa-sdk-patterns`.
