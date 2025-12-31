# firecrawl-rate-limits

## Skill Scaffold

```
firecrawl-rate-limits/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement rate limiting, exponential backoff with jitter, and request queuing to handle FireCrawl API rate limits gracefully.
**Workflow:** Production hardening skill - ensures reliable operation under rate limit constraints.
**Relates to:** Builds on firecrawl-sdk-patterns; foundational for firecrawl-batch-processing

## Summary

This skill implements robust rate limit handling for FireCrawl API operations. It covers reading and respecting rate limit headers, implementing exponential backoff with jitter to avoid thundering herd problems, request queuing to smooth out burst traffic, and proper 429 response handling. The patterns ensure scraping operations continue reliably even when approaching or hitting rate limits, maximizing throughput while staying within API constraints.
