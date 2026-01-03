# klingai-rate-limits

> Handle Kling AI rate limits with proper backoff strategies

## Directory Structure

```
klingai-rate-limits/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 rate_limiter.py         # Client-side rate limiting
    ├── 🐍 backoff_strategies.py   # Exponential backoff implementation
    └── 🐍 token_bucket.py         # Token bucket algorithm
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with rate limit handling strategies |
| `rate_limiter.py` | 🐍 Python | Client-side rate limiting decorator |
| `backoff_strategies.py` | 🐍 Python | Various backoff strategies |
| `token_bucket.py` | 🐍 Python | Token bucket rate limiting |

## Summary

**Category:** operations
**Target Audience:** Developer building high-throughput systems
**Trigger Phrases:** `klingai rate limit`, `kling ai 429`, `klingai throttle`, `klingai backoff`

### What This Skill Does

This skill teaches proper rate limit handling for Kling AI API. It covers:

- Understanding rate limit headers (X-RateLimit-*, Retry-After)
- Client-side rate limiting with decorators
- Exponential backoff with jitter
- Token bucket algorithm implementation
- Queue-based request management
- Graceful degradation strategies

### Technical Success Criteria

- Smooth request throughput without rate limit errors
- Proper backoff implemented with Retry-After header
- Client-side rate limiting preventing 429s

### Business Success Criteria

- Reliable system operation under load
- No dropped requests due to rate limits
- Predictable throughput capacity

## Related Skills

- `klingai-batch-processing` - Batch requests with rate awareness
- `klingai-common-errors` - 429 error handling
- `klingai-performance-tuning` - Throughput optimization
