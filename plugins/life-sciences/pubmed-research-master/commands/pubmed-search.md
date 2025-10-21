---
name: pubmed-search
description: Interactive PubMed search with advanced filters
model: sonnet
---

# PubMed Advanced Search

Search PubMed for scientific articles using the complete E-utilities API with filters.

## What This Does

Performs an advanced PubMed search with:
- Custom search query
- Date range filtering
- Maximum results limit
- Article type filtering
- Rate limit compliance (3 req/s without API key, 10 req/s with key)

## Usage

Simply invoke this command and provide your search parameters when prompted.

## Examples

### Basic Search
```
Query: CRISPR gene editing
Max results: 50
```

### Advanced Search with Date Filter
```
Query: mRNA vaccines COVID-19
Max results: 100
Date from: 2020/01/01
Date to: 2025/12/31
```

### Search with Article Type
```
Query: Alzheimer's disease treatment
Max results: 75
Article type: Clinical Trial
```

## What You'll Get

- Total article count
- List of PMIDs (first 20 shown)
- Can then use PMIDs with other tools:
  - `get_article_details` for full metadata
  - `export_citations` for BibTeX/RIS/EndNote
  - `get_related_articles` to expand search
  - `compare_studies` to analyze multiple papers

## Tips

1. **Use specific terms** - "BRCA1 mutation breast cancer" vs just "cancer"
2. **Try MeSH terms** - Use `/mesh-search` for controlled vocabulary
3. **Filter by date** - Focus on recent research
4. **Start broad, then narrow** - Refine based on initial results
5. **Get an API key** - Free from NCBI, increases rate limit to 10 req/s

## API Key Setup

Get a free NCBI API key: https://www.ncbi.nlm.nih.gov/account/settings/

Add to environment:
```bash
export PUBMED_API_KEY="your-key-here"
export EMAIL="your@email.com"
```

## Rate Limits

- Without API key: 3 requests/second
- With API key: 10 requests/second
- This plugin automatically enforces these limits
