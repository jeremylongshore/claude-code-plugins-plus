---
name: serpapi-core-workflow-a
description: |
  Google Search scraping with SerpApi -- organic results, knowledge graph, answer boxes.
  Use when building search-powered features, SEO monitoring,
  or extracting structured data from Google results.
  Trigger: "serpapi google search", "scrape google", "serpapi organic results".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Core Workflow A: Google Search

## Overview

Extract structured data from Google Search: organic results, answer boxes, knowledge graph, related questions (PAA), local pack, ads, and shopping results. Each search costs 1 API credit.

## Instructions

### Step 1: Full Google Search with All Components

```python
import serpapi, os

client = serpapi.Client(api_key=os.environ["SERPAPI_API_KEY"])

result = client.search(
    engine="google",
    q="best project management tools",
    location="New York, New York",
    hl="en", gl="us",
    num=10,
)

# 1. Organic Results
for r in result.get("organic_results", []):
    print(f"{r['position']}. {r['title']}")
    print(f"   URL: {r['link']}")
    print(f"   Snippet: {r.get('snippet', 'N/A')}")
    # Rich snippets: sitelinks, rating, date
    if "rich_snippet" in r:
        print(f"   Rating: {r['rich_snippet'].get('top', {}).get('rating')}")

# 2. Answer Box
if ab := result.get("answer_box"):
    print(f"\nAnswer Box ({ab.get('type', 'unknown')}):")
    print(f"  {ab.get('answer') or ab.get('snippet') or ab.get('title')}")

# 3. Knowledge Graph
if kg := result.get("knowledge_graph"):
    print(f"\nKnowledge Graph: {kg['title']}")
    print(f"  Type: {kg.get('type')}")
    print(f"  Description: {kg.get('description', 'N/A')[:100]}")

# 4. People Also Ask
for paa in result.get("related_questions", []):
    print(f"\nPAA: {paa['question']}")
    print(f"  Answer: {paa.get('snippet', 'N/A')[:100]}")

# 5. Related Searches
for rs in result.get("related_searches", []):
    print(f"Related: {rs['query']}")
```

### Step 2: Paginate Through Results

```python
def paginate_google(query: str, pages: int = 3, num: int = 10):
    """Get multiple pages of results (each page = 1 credit)."""
    all_results = []
    for page in range(pages):
        result = client.search(
            engine="google", q=query, num=num,
            start=page * num,  # Offset parameter
        )
        organic = result.get("organic_results", [])
        if not organic:
            break
        all_results.extend(organic)
    return all_results

results = paginate_google("python web frameworks", pages=3)
print(f"Total results: {len(results)}")
```

### Step 3: Google with Filters

```python
# Time-based filtering
recent = client.search(engine="google", q="AI news", tbs="qdr:w")  # Past week
# tbs options: qdr:h (hour), qdr:d (day), qdr:w (week), qdr:m (month), qdr:y (year)

# Device-specific results
mobile = client.search(engine="google", q="restaurants near me", device="mobile")

# Safe search
safe = client.search(engine="google", q="query", safe="active")
```

### Step 4: Extract Local Pack Results

```python
result = client.search(engine="google", q="coffee shops austin tx")

for place in result.get("local_results", {}).get("places", []):
    print(f"{place['title']} - {place.get('rating', 'N/A')} stars")
    print(f"  Address: {place.get('address')}")
    print(f"  Hours: {place.get('hours')}")
    print(f"  GPS: {place.get('gps_coordinates', {})}")
```

## Output

```
1. Monday.com - Best Project Management Software
   URL: https://monday.com
   Snippet: Rated #1 project management tool...

Answer Box (organic_result):
  Compare the best project management tools...

Knowledge Graph: Project management
  Type: Topic
  Description: Project management is the application of...
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| No `organic_results` | CAPTCHA or unusual query | Check `search_metadata.status` |
| Empty `local_results` | Query not location-specific | Add `location` parameter |
| `search_metadata.status: Error` | Invalid parameters | Check `search_metadata.error` message |

## Resources

- [Google Search API](https://serpapi.com/search-api)
- [Google Search Parameters](https://serpapi.com/search-api#api-parameters)
- [Organic Results](https://serpapi.com/organic-results)

## Next Steps

For Bing, YouTube, and other engines, see `serpapi-core-workflow-b`.
