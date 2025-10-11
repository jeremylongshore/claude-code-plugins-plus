---
description: Add rate limiting to API endpoints
shortcut: ratelimit
---

# Add Rate Limiting

Implement rate limiting with token bucket, sliding window, or fixed window algorithms using Redis.

## Strategies

1. **Token Bucket** - Smooth rate limiting with burst allowance
2. **Sliding Window** - More accurate than fixed window
3. **Fixed Window** - Simple counter per time window
4. **Leaky Bucket** - Constant rate output

## Implementation

- Per-user/IP rate limits
- Tiered limits (free/premium/enterprise)
- Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining)
- 429 Too Many Requests response
- Retry-After header

Generate production-ready rate limiting with Redis.
