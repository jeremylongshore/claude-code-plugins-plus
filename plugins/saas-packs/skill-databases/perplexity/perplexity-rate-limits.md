# perplexity-rate-limits

> Handle Perplexity rate limits with proper backoff strategies

## Directory Structure

```
perplexity-rate-limits/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── rate_limiter.py         # Client-side rate limiting
    ├── backoff_strategy.py     # Exponential backoff implementation
    ├── queue_manager.py        # Request queue with rate limiting
    └── rate_limits.yaml        # Rate limit configuration
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with rate limit patterns |
| `rate_limiter.py` | Python | Client-side rate limiting implementation |
| `backoff_strategy.py` | Python | Exponential backoff with jitter |
| `queue_manager.py` | Python | Queue requests to respect limits |
| `rate_limits.yaml` | YAML | Rate limit configurations per tier |

## Summary

**Category:** operations
**Target Audience:** Developer building high-volume systems
**Trigger Phrases:** `perplexity rate limit`, `perplexity 429`, `perplexity throttle`, `perplexity backoff`

### What This Skill Does

This skill teaches rate limit handling for Perplexity:

- Understanding rate limit headers
- Client-side rate limiting
- Exponential backoff with jitter
- Request queuing strategies
- Tier-specific rate limits

### Technical Success Criteria

- Smooth request throughput without rate limit errors
- Exponential backoff properly implemented
- Request queue preventing bursts

### Business Success Criteria

- Reliable system operation under load
- No lost requests due to rate limiting
- Efficient use of API quota

## Related Skills

- `perplexity-common-errors` - Diagnosing 429 errors
- `perplexity-caching-strategy` - Reduce requests through caching
- `perplexity-load-testing` - Test rate limit handling
