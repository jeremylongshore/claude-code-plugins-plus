---
name: serpapi-hello-world
description: |
  Run your first SerpApi search -- Google, Bing, or YouTube results as JSON.
  Use when starting with SerpApi, testing search queries,
  or learning the structured result format.
  Trigger: "serpapi hello world", "serpapi example", "serpapi first search".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(python3:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Hello World

## Overview

Run a Google search via SerpApi and parse the structured JSON response. SerpApi returns organic results, knowledge graph, answer boxes, ads, local results, and more -- all as structured data. Key parameter: `engine` (google, bing, youtube, etc.).

## Prerequisites

- `serpapi` package installed (see `serpapi-install-auth`)
- `SERPAPI_API_KEY` environment variable set

## Instructions

### Step 1: Basic Google Search (Python)

```python
import serpapi
import os

client = serpapi.Client(api_key=os.environ["SERPAPI_API_KEY"])

result = client.search(
    engine="google",
    q="best programming languages 2025",
    location="Austin, Texas",
    hl="en",
    gl="us",
    num=5,  # Number of results
)

# Organic results
for r in result["organic_results"]:
    print(f"{r['position']}. {r['title']}")
    print(f"   {r['link']}")
    print(f"   {r.get('snippet', 'No snippet')}\n")

# Answer box (if present)
if "answer_box" in result:
    print(f"Answer Box: {result['answer_box'].get('answer', result['answer_box'].get('snippet'))}")
```

### Step 2: Google Search (Node.js)

```typescript
import { getJson } from 'serpapi';

const result = await getJson({
  engine: 'google',
  q: 'best programming languages 2025',
  location: 'Austin, Texas',
  hl: 'en',
  gl: 'us',
  num: 5,
  api_key: process.env.SERPAPI_API_KEY,
});

result.organic_results.forEach((r: any) => {
  console.log(`${r.position}. ${r.title}`);
  console.log(`   ${r.link}`);
});

// Knowledge graph
if (result.knowledge_graph) {
  console.log(`\nKnowledge Graph: ${result.knowledge_graph.title}`);
}
```

### Step 3: Try Different Engines

```python
# Bing search
bing = client.search(engine="bing", q="Claude AI", count=5)
for r in bing["organic_results"]:
    print(f"Bing: {r['title']}")

# YouTube search
youtube = client.search(engine="youtube", search_query="python tutorial")
for v in youtube["video_results"]:
    print(f"YouTube: {v['title']} ({v['length']})")

# Google News
news = client.search(engine="google_news", q="artificial intelligence")
for n in news["news_results"]:
    print(f"News: {n['title']} - {n['source']['name']}")
```

## Output

```
1. Python - Best programming language for beginners
   https://example.com/python
   Python remains the top choice...

2. JavaScript - Most versatile language
   https://example.com/js
   JavaScript dominates web development...

Knowledge Graph: Programming languages
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid API key` | Wrong key | Check serpapi.com/manage-api-key |
| `No organic_results key` | Different result structure | Check `search_metadata.status` first |
| `Your searches for the month have run out` | Plan limit reached | Upgrade at serpapi.com/pricing |
| Empty results | Unusual query or location | Try without `location` parameter |

## Resources

- [Google Search API](https://serpapi.com/search-api)
- [Result Structure](https://serpapi.com/organic-results)
- [Supported Engines](https://serpapi.com/)

## Next Steps

Proceed to `serpapi-local-dev-loop` for development workflow setup.
