---
name: perplexity-known-pitfalls
description: |
  Identify and avoid Perplexity anti-patterns and common integration mistakes.
  Use when reviewing Perplexity code for issues, onboarding new developers,
  or auditing existing Perplexity integrations for best practices violations.
  Trigger with phrases like "perplexity mistakes", "perplexity anti-patterns",
  "perplexity pitfalls", "perplexity what not to do", "perplexity code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Perplexity Known Pitfalls

## Overview
Real gotchas when integrating Perplexity's AI search API (Sonar). Perplexity uses an OpenAI-compatible chat endpoint but returns grounded, cited answers from web sources -- a fundamentally different paradigm from standard LLM completions.

## Prerequisites
- Perplexity API key configured
- Understanding of OpenAI-compatible chat API format
- Familiarity with citation-based response handling

## Instructions

### Step 1: Don't Treat It Like a Standard LLM

Perplexity Sonar searches the web per request. System prompts that assume a static knowledge model produce poor results.

```python
import requests

# BAD: using it as a generic chatbot
response = requests.post("https://api.perplexity.ai/chat/completions", json={
    "model": "sonar",
    "messages": [{"role": "user", "content": "Tell me a joke"}]
}, headers={"Authorization": f"Bearer {api_key}"})
# Works but wastes a search query on non-search tasks

# GOOD: leverage its search capability
response = requests.post("https://api.perplexity.ai/chat/completions", json={
    "model": "sonar",
    "messages": [{"role": "user", "content": "What are the latest Next.js 15 features released this month?"}],
    "search_recency_filter": "week"
}, headers={"Authorization": f"Bearer {api_key}"})
```

### Step 2: Parse Citations Correctly

Perplexity returns inline citation markers `[1]`, `[2]` with a separate `citations` array. Ignoring them loses the key value prop.

```python
data = response.json()
answer = data["choices"][0]["message"]["content"]
citations = data.get("citations", [])

# BAD: displaying raw answer with [1] [2] markers
print(answer)  # "According to [1], Next.js 15 adds..."

# GOOD: replace markers with actual URLs
import re
for i, url in enumerate(citations, 1):
    answer = answer.replace(f"[{i}]", f"[{i}]({url})")
print(answer)
```

### Step 3: Choose the Right Model Tier

Using `sonar-pro` for simple factual queries wastes budget. Using `sonar` for complex research gives shallow answers.

```python
# BAD: sonar-pro for a simple lookup
response = call_perplexity("What is the capital of France?", model="sonar-pro")
# Costs 5x more for a trivial question

# GOOD: match model to task complexity
def smart_search(query: str, complexity: str = "simple"):
    model = "sonar-pro" if complexity == "deep" else "sonar"
    return call_perplexity(query, model=model)
```

### Step 4: Handle Search Recency Properly

Not setting `search_recency_filter` returns results from any time period, which may include outdated information for fast-moving topics.

```python
# BAD: no recency filter for current events
response = call_perplexity("current Bitcoin price")  # may cite old articles

# GOOD: set recency for time-sensitive queries
response = call_perplexity(
    "current Bitcoin price",
    search_recency_filter="day"  # options: day, week, month, year
)
```

### Step 5: Avoid Excessive Context in Messages

Perplexity performs a web search per turn. Sending full conversation history triggers redundant searches.

```python
# BAD: sending 20 turns of history
messages = long_conversation_history + [{"role": "user", "content": "summarize"}]
# Each message may trigger new searches

# GOOD: summarize history, send focused query
messages = [
    {"role": "system", "content": "Answer based on web search results."},
    {"role": "user", "content": f"Given context: {summary}\nQuestion: {question}"}
]
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Stale information | No recency filter | Set `search_recency_filter` |
| High costs | Using sonar-pro everywhere | Route simple queries to sonar |
| Missing citations | Not parsing response | Extract `citations` array from JSON |
| Slow responses | Large conversation context | Trim history before sending |
| Empty search results | Overly niche query | Broaden the question scope |

## Examples

### Streaming with Citation Handling
```python
response = requests.post(url, json={
    "model": "sonar",
    "messages": messages,
    "stream": True
}, headers=headers, stream=True)

for line in response.iter_lines():
    if line.startswith(b"data: "):
        chunk = json.loads(line[6:])
        # Citations arrive in the final chunk
        if chunk.get("citations"):
            handle_citations(chunk["citations"])
```

## Resources
- [Perplexity API Docs](https://docs.perplexity.ai)
- [Sonar Model Guide](https://docs.perplexity.ai/guides/model-cards)
