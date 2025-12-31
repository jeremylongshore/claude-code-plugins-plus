# perplexity-hello-world

> Create first search query with a simple example

## Directory Structure

```
perplexity-hello-world/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── basic_search.py         # Simple search query example
    ├── basic_search.ts         # TypeScript search example
    └── curl_example.sh         # cURL command for testing
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with first search query patterns |
| `basic_search.py` | Python | Simple search query with response parsing |
| `basic_search.ts` | TypeScript | TypeScript implementation of basic search |
| `curl_example.sh` | Shell | cURL command for quick API testing |

## Summary

**Category:** onboarding
**Target Audience:** Developer new to Perplexity
**Trigger Phrases:** `perplexity first query`, `perplexity hello world`, `perplexity example`, `try perplexity`

### What This Skill Does

This skill helps developers make their first successful Perplexity search request:

- Understanding the Perplexity API request format
- Sending a basic search query
- Parsing the response with citations
- Understanding response structure and fields
- Handling the citations array

### Technical Success Criteria

- Successfully make first API call and receive response
- Response parsed correctly with content and citations
- Understanding of response JSON structure

### Business Success Criteria

- Quick validation of API integration readiness
- Developer confidence in using the API
- Foundation for building more complex queries

## Related Skills

- `perplexity-install-auth` - Required authentication setup
- `perplexity-citation-handling` - Processing citations from responses
- `perplexity-model-selection` - Choosing optimal model for queries
