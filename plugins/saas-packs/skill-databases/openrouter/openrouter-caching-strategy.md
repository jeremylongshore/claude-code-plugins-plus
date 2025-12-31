# openrouter-caching-strategy

> Implement intelligent caching for OpenRouter responses

## Directory Structure

```
openrouter-caching-strategy/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 semantic_cache.py       # Semantic similarity caching
    ├── 🐍 redis_cache.py          # Redis-based response caching
    └── ⚙️ cache_config.yaml       # Cache TTL and invalidation rules
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with caching patterns |
| `semantic_cache.py` | 🐍 Python | Semantic similarity-based cache lookup |
| `redis_cache.py` | 🐍 Python | Redis integration for distributed caching |
| `cache_config.yaml` | ⚙️ YAML | TTL, invalidation, and sizing configuration |

## Summary

**Category:** operations
**Target Audience:** Developer optimizing costs
**Trigger Phrases:** `openrouter caching`, `cache openrouter`, `openrouter performance`, `reduce openrouter costs`

### What This Skill Does

This skill teaches intelligent caching strategies for OpenRouter responses:

- Exact match caching for identical prompts
- Semantic caching for similar queries
- Redis and in-memory cache implementations
- Cache TTL and invalidation strategies
- Cost savings measurement and reporting

### Technical Success Criteria

- Cache hit rate >60% for eligible requests
- Latency reduced by 80% for cached responses
- Proper cache invalidation preventing stale data

### Business Success Criteria

- 30-50% reduction in API costs
- Improved user experience with faster responses
- Reduced load on OpenRouter API

## Related Skills

- `openrouter-performance-tuning` - Overall performance optimization
- `openrouter-cost-controls` - Budget management
- `openrouter-rate-limits` - Rate limit optimization
