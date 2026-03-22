---
name: serpapi-core-workflow-b
description: |
  Search Bing, YouTube, Google Shopping, Google News, and Google Maps with SerpApi.
  Use when scraping non-Google engines, building multi-engine search,
  or extracting video/news/shopping/maps data.
  Trigger: "serpapi youtube", "serpapi bing", "serpapi news", "serpapi shopping".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Core Workflow B: Multi-Engine Search

## Overview

SerpApi supports 15+ search engines beyond Google. Each engine has its own parameters and result structure. Key engines: YouTube (`search_query`), Bing (`q`), Google News, Google Shopping, Google Maps, Walmart, eBay, Apple App Store.

## Instructions

### Step 1: YouTube Search

```python
import serpapi, os
client = serpapi.Client(api_key=os.environ["SERPAPI_API_KEY"])

# YouTube uses search_query (not q)
yt = client.search(engine="youtube", search_query="python asyncio tutorial")

for video in yt.get("video_results", []):
    print(f"{video['title']}")
    print(f"  Channel: {video.get('channel', {}).get('name')}")
    print(f"  Views: {video.get('views')}, Length: {video.get('length')}")
    print(f"  Link: {video['link']}")
    print(f"  Published: {video.get('published_date')}")
```

### Step 2: Bing Search

```python
bing = client.search(engine="bing", q="machine learning frameworks", count=10)

for r in bing.get("organic_results", []):
    print(f"{r['position']}. {r['title']}")
    print(f"   {r['link']}")
    # Bing has different snippet structure
    print(f"   {r.get('snippet', 'N/A')}")
```

### Step 3: Google News

```python
news = client.search(engine="google_news", q="artificial intelligence", gl="us", hl="en")

for article in news.get("news_results", []):
    print(f"{article['title']}")
    print(f"  Source: {article['source']['name']}")
    print(f"  Date: {article.get('date')}")
    print(f"  Link: {article['link']}")
    # News often has thumbnail
    if "thumbnail" in article:
        print(f"  Image: {article['thumbnail']}")
```

### Step 4: Google Shopping

```python
shopping = client.search(
    engine="google_shopping",
    q="mechanical keyboard",
    gl="us",
    hl="en",
)

for product in shopping.get("shopping_results", []):
    print(f"{product['title']}")
    print(f"  Price: {product.get('price')}")
    print(f"  Source: {product.get('source')}")
    print(f"  Rating: {product.get('rating')} ({product.get('reviews', 0)} reviews)")
    print(f"  Link: {product['link']}")
```

### Step 5: Google Maps / Local

```python
maps = client.search(
    engine="google_maps",
    q="pizza restaurants",
    ll="@30.2672,-97.7431,14z",  # Austin, TX coordinates + zoom
)

for place in maps.get("local_results", []):
    print(f"{place['title']} - {place.get('rating', 'N/A')} stars ({place.get('reviews', 0)} reviews)")
    print(f"  Address: {place.get('address')}")
    print(f"  Phone: {place.get('phone')}")
    print(f"  Type: {place.get('type')}")
    print(f"  Hours: {place.get('operating_hours', {}).get('monday')}")
```

### Step 6: Cross-Engine Comparison

```python
def multi_search(query: str) -> dict:
    """Search across multiple engines for the same query."""
    engines = [
        {"engine": "google", "q": query},
        {"engine": "bing", "q": query},
        {"engine": "youtube", "search_query": query},
        {"engine": "google_news", "q": query},
    ]
    results = {}
    for params in engines:
        result = client.search(**params)
        engine = params["engine"]
        key = "organic_results" if engine != "youtube" else "video_results"
        if engine == "google_news":
            key = "news_results"
        results[engine] = result.get(key, [])[:3]
    return results  # 4 API credits total
```

## Error Handling

| Error | Engine | Solution |
|-------|--------|----------|
| `search_query` required | YouTube | Use `search_query` not `q` |
| No `shopping_results` | Google Shopping | Query must be product-related |
| Empty `local_results` | Google Maps | Add `ll` parameter with coordinates |
| `count` vs `num` | Bing | Bing uses `count`, Google uses `num` |

## Resources

- [YouTube Search API](https://serpapi.com/youtube-search-api)
- [Bing Search API](https://serpapi.com/bing-search-api)
- [Google News API](https://serpapi.com/google-news-api)
- [Google Shopping API](https://serpapi.com/google-shopping-api)
- [Google Maps API](https://serpapi.com/google-maps-api)

## Next Steps

For common errors, see `serpapi-common-errors`.
