---
name: perplexity-hello-world
description: |
  Create a minimal working Perplexity Sonar search example with citations.
  Use when starting a new Perplexity integration, testing your setup,
  or learning basic search-with-citations patterns.
  Trigger with phrases like "perplexity hello world", "perplexity example",
  "perplexity quick start", "simple perplexity search".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, api, testing]

---
# Perplexity Hello World

## Overview
Minimal working example demonstrating Perplexity's core value: web-grounded answers with citations. Unlike standard LLMs, Perplexity searches the web for every query and returns cited sources.

## Prerequisites
- Completed `perplexity-install-auth` setup
- `openai` package installed
- `PERPLEXITY_API_KEY` environment variable set

## Instructions

### Step 1: Basic Search with Citations (TypeScript)
```typescript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY,
  baseURL: "https://api.perplexity.ai",
});

async function main() {
  const response = await client.chat.completions.create({
    model: "sonar",
    messages: [
      {
        role: "system",
        content: "Be precise and cite your sources.",
      },
      {
        role: "user",
        content: "What are the latest features in Node.js 22?",
      },
    ],
  });

  const answer = response.choices[0].message.content;
  console.log("Answer:", answer);

  // Citations are returned as a top-level array on the response
  const citations = (response as any).citations || [];
  console.log("\nSources:");
  citations.forEach((url: string, i: number) => {
    console.log(`  [${i + 1}] ${url}`);
  });

  // Usage breakdown
  console.log("\nUsage:", {
    prompt_tokens: response.usage?.prompt_tokens,
    completion_tokens: response.usage?.completion_tokens,
    total_tokens: response.usage?.total_tokens,
  });
}

main().catch(console.error);
```

### Step 2: Basic Search with Citations (Python)
```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["PERPLEXITY_API_KEY"],
    base_url="https://api.perplexity.ai",
)

response = client.chat.completions.create(
    model="sonar",
    messages=[
        {"role": "system", "content": "Be precise and cite your sources."},
        {"role": "user", "content": "What are the latest features in Node.js 22?"},
    ],
)

answer = response.choices[0].message.content
print("Answer:", answer)

# Citations from the raw response
raw = response.model_dump()
citations = raw.get("citations", [])
print("\nSources:")
for i, url in enumerate(citations, 1):
    print(f"  [{i}] {url}")

print(f"\nTokens: {response.usage.total_tokens}")
```

### Step 3: Search with Domain Filter
```typescript
// Restrict search to specific domains
const response = await client.chat.completions.create({
  model: "sonar",
  messages: [
    { role: "user", content: "What is the latest Python release?" },
  ],
  // Perplexity-specific parameters (pass as extra body)
  search_domain_filter: ["python.org", "docs.python.org"],
  search_recency_filter: "month",
} as any);
```

### Step 4: Streaming Search
```typescript
const stream = await client.chat.completions.create({
  model: "sonar",
  messages: [
    { role: "user", content: "Explain quantum computing breakthroughs in 2025" },
  ],
  stream: true,
});

for await (const chunk of stream) {
  const text = chunk.choices[0]?.delta?.content || "";
  process.stdout.write(text);

  // Citations arrive in the final chunk
  if ((chunk as any).citations) {
    console.log("\n\nSources:", (chunk as any).citations);
  }
}
```

## Output
- Working search query returning a web-grounded answer
- Parsed citation URLs from the response
- Token usage stats confirming billing

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Verify key at perplexity.ai/settings/api |
| Empty citations array | Query too abstract | Ask a specific, factual question |
| `429 Too Many Requests` | Rate limit exceeded | Wait and retry with backoff |
| Timeout | Complex search query | Use `sonar` instead of `sonar-pro` |

## Resources
- [Perplexity API Reference](https://docs.perplexity.ai/api-reference/chat-completions-post)
- [Search Parameters](https://docs.perplexity.ai/docs/sonar/quickstart)
- [Model Cards](https://docs.perplexity.ai/getting-started/models)

## Next Steps
Proceed to `perplexity-local-dev-loop` for development workflow setup.
