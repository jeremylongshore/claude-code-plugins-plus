# firecrawl-reliability-patterns

## Skill Scaffold

```
firecrawl-reliability-patterns/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement circuit breakers, retry policies, fallback strategies, and dead letter queues for fault-tolerant scraping.
**Workflow:** Reliability engineering skill - ensures scraping pipelines gracefully handle failures.
**Relates to:** Extends firecrawl-sdk-patterns; critical for firecrawl-incident-runbook

## Summary

This skill implements reliability patterns for FireCrawl operations. It covers circuit breaker implementation (preventing cascade failures during API outages), intelligent retry policies (distinguishing transient from permanent failures), fallback strategies (cached content, alternative sources), dead letter queues for failed scrapes (guaranteed eventual processing), and graceful degradation patterns. These patterns ensure 99.9%+ uptime for scraping pipelines.
