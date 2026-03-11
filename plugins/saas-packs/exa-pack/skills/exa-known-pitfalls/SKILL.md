---
name: exa-known-pitfalls
description: |
  Identify and avoid Exa anti-patterns and common integration mistakes.
  Use when reviewing Exa code for issues, onboarding new developers,
  or auditing existing Exa integrations for best practices violations.
  Trigger with phrases like "exa mistakes", "exa anti-patterns",
  "exa pitfalls", "exa what not to do", "exa code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Exa Known Pitfalls

## Overview
Real gotchas when integrating Exa's neural search API. Exa uses embeddings-based search rather than keyword matching, which creates a different class of failure modes than traditional search APIs.

## Prerequisites
- Exa API key configured
- Understanding of neural vs keyword search differences
- Familiarity with search result relevance scoring

## Instructions

### Step 1: Avoid Keyword-Style Queries

Exa's neural search interprets natural language, not keywords. Boolean operators and exact-match syntax degrade results.

```python
from exa_py import Exa
exa = Exa(api_key=os.environ["EXA_API_KEY"])

# BAD: keyword-style query returns poor results
results = exa.search("python AND machine learning OR deep learning 2024")  # 2024 year

# GOOD: natural language query
results = exa.search(
    "recent tutorials on building ML models with Python",
    num_results=10,
    use_autoprompt=True  # let Exa optimize the query
)
```

### Step 2: Don't Ignore Search Type Selection

Exa offers `neural` and `keyword` search. Using the wrong type silently degrades quality.

```python
# BAD: using neural search for a specific URL or exact title
results = exa.search("arxiv.org/abs/2301.00001", type="neural")

# GOOD: use keyword search for exact matches, neural for concepts
results = exa.search("arxiv.org/abs/2301.00001", type="keyword")
results_concept = exa.search(
    "transformer architecture improvements for long context",
    type="neural"
)
```

### Step 3: Handle Content Retrieval Separately

A common mistake is assuming `search()` returns full page content. It returns metadata only unless you request contents.

```python
# BAD: accessing content that wasn't fetched
results = exa.search("AI safety research papers")
text = results.results[0].text  # None! Content not requested

# GOOD: use search_and_contents or get_contents
results = exa.search_and_contents(
    "AI safety research papers",
    text={"max_characters": 3000},  # 3000: 3 seconds in ms
    highlights=True
)
print(results.results[0].text)       # full text
print(results.results[0].highlights) # key excerpts
```

### Step 4: Watch Date Filtering Edge Cases

Date filters silently exclude results. Overly narrow windows return empty results without error.

```python
# BAD: too narrow, may return nothing
results = exa.search(
    "breaking news in AI",
    start_published_date="2024-03-10",  # 2024 year
    end_published_date="2024-03-10"  # single day = few results
)

# GOOD: reasonable date window with fallback
results = exa.search(
    "breaking news in AI",
    start_published_date="2024-03-01",
    end_published_date="2024-03-15"
)
if not results.results:
    results = exa.search("breaking news in AI", num_results=5)
```

### Step 5: Autoprompt Cost Awareness

`use_autoprompt=True` makes an extra LLM call per request, adding latency and cost.

```python
# BAD: autoprompt on every request in a high-volume loop
for query in thousands_of_queries:
    exa.search(query, use_autoprompt=True)  # 2x cost, extra latency

# GOOD: use autoprompt selectively
results = exa.search(
    well_formed_query,
    use_autoprompt=False  # skip when query is already well-structured
)
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Empty results, no error | Date filter too narrow | Widen date range or remove filter |
| Low relevance scores | Keyword-style query | Rewrite as natural language |
| Missing `.text` field | Content not requested | Use `search_and_contents()` |
| Slow responses | Autoprompt on every call | Disable for pre-optimized queries |
| 429 rate limit | Burst requests | Add exponential backoff with jitter |

## Examples

### Similarity Search Pitfall
```python
# find_similar requires a URL, not a query string
# BAD:
results = exa.find_similar("machine learning papers")

# GOOD:
results = exa.find_similar(
    "https://arxiv.org/abs/2301.00001",
    num_results=10
)
```

## Resources
- [Exa API Docs](https://docs.exa.ai)
- [Search Types Guide](https://docs.exa.ai/reference/search)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale