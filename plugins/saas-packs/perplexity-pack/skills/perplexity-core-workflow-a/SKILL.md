---
name: perplexity-core-workflow-a
description: |
  Execute Perplexity primary workflow: single-query search with citations.
  Use when implementing AI search, building fact-checking tools,
  or integrating web-grounded answers into your application.
  Trigger with phrases like "perplexity search", "perplexity query",
  "search with citations", "perplexity main workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, workflow]

---
# Perplexity Core Workflow A: Search with Citations

## Overview
Primary money-path workflow: send a search query to Perplexity Sonar, receive a web-grounded answer with inline citations, parse and display the results. This is the single-query pattern used for search widgets, fact-checking, and real-time information retrieval.

## Prerequisites
- Completed `perplexity-install-auth` setup
- `openai` package installed
- `PERPLEXITY_API_KEY` set

## Instructions

### Step 1: Initialize Client and Send Query
```typescript
import OpenAI from "openai";

const perplexity = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY,
  baseURL: "https://api.perplexity.ai",
});

async function searchWithCitations(query: string) {
  const response = await perplexity.chat.completions.create({
    model: "sonar",
    messages: [
      {
        role: "system",
        content: "Provide accurate, well-sourced answers. Cite your sources inline.",
      },
      { role: "user", content: query },
    ],
    // Perplexity-specific parameters
    search_recency_filter: "week",  // hour | day | week | month
  } as any);

  return response;
}
```

### Step 2: Parse Response with Citations
```typescript
interface SearchResult {
  answer: string;
  citations: string[];
  searchResults: Array<{ title: string; url: string; snippet: string }>;
  tokensUsed: number;
}

function parseResponse(response: any): SearchResult {
  return {
    answer: response.choices[0].message.content,
    citations: response.citations || [],
    searchResults: response.search_results || [],
    tokensUsed: response.usage?.total_tokens || 0,
  };
}
```

### Step 3: Format Citations for Display
```typescript
function formatAnswer(result: SearchResult): string {
  let formatted = result.answer;

  // Replace [1], [2] markers with markdown links
  result.citations.forEach((url, i) => {
    formatted = formatted.replaceAll(`[${i + 1}]`, `[${i + 1}](${url})`);
  });

  // Append source list
  if (result.citations.length > 0) {
    formatted += "\n\n**Sources:**\n";
    result.citations.forEach((url, i) => {
      formatted += `${i + 1}. ${url}\n`;
    });
  }

  return formatted;
}
```

### Step 4: Complete Workflow
```typescript
async function main() {
  const query = "What are the latest advances in battery technology?";

  const response = await searchWithCitations(query);
  const result = parseResponse(response);
  const formatted = formatAnswer(result);

  console.log(formatted);
  console.log(`\n[${result.tokensUsed} tokens | ${result.citations.length} sources]`);
}

main().catch(console.error);
```

### Step 5: Domain-Filtered Search
```typescript
// Restrict search to trusted sources
async function domainFilteredSearch(query: string, domains: string[]) {
  const response = await perplexity.chat.completions.create({
    model: "sonar",
    messages: [{ role: "user", content: query }],
    search_domain_filter: domains,  // max 20 domains
  } as any);

  return parseResponse(response);
}

// Example: only search academic sources
const result = await domainFilteredSearch(
  "CRISPR gene editing latest trials",
  ["nature.com", "science.org", "nih.gov", "arxiv.org"]
);
```

### Step 6: Python Implementation
```python
from openai import OpenAI
import os, re

client = OpenAI(
    api_key=os.environ["PERPLEXITY_API_KEY"],
    base_url="https://api.perplexity.ai",
)

def search_with_citations(query: str, model: str = "sonar", recency: str = None) -> dict:
    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Provide accurate answers with cited sources."},
            {"role": "user", "content": query},
        ],
    }
    if recency:
        kwargs["search_recency_filter"] = recency

    response = client.chat.completions.create(**kwargs)
    raw = response.model_dump()

    return {
        "answer": response.choices[0].message.content,
        "citations": raw.get("citations", []),
        "tokens": response.usage.total_tokens,
    }

# Usage
result = search_with_citations(
    "What are the latest advances in battery technology?",
    recency="week"
)
print(result["answer"])
for i, url in enumerate(result["citations"], 1):
    print(f"  [{i}] {url}")
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Regenerate at perplexity.ai/settings/api |
| `429 Too Many Requests` | Rate limit exceeded | Implement exponential backoff |
| Empty citations | Query too vague | Make query more specific and factual |
| Stale information | No recency filter | Add `search_recency_filter: "day"` |
| Slow response (>10s) | Using sonar-pro | Switch to sonar for faster results |

## Output
- Web-grounded answer text with inline citation markers
- Parsed citation URLs for source verification
- Formatted markdown with linked sources
- Token usage for cost tracking

## Resources
- [Perplexity API Reference](https://docs.perplexity.ai/api-reference/chat-completions-post)
- [Search Parameters](https://docs.perplexity.ai/docs/sonar/quickstart)

## Next Steps
For multi-query research, see `perplexity-core-workflow-b`.
