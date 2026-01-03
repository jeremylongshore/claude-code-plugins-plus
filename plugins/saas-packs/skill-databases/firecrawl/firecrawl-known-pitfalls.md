# firecrawl-known-pitfalls

## Skill Scaffold

```
firecrawl-known-pitfalls/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Identify and avoid 10 common anti-patterns including ignoring rate limits, poor error handling, inefficient crawl patterns, and content quality issues.
**Workflow:** Best practices skill - prevents common mistakes through pattern recognition and proactive guidance.
**Relates to:** Synthesizes lessons from all operational skills; foundational for code review

## Summary

This skill documents the most common FireCrawl anti-patterns and how to avoid them. It covers ignoring rate limits (causing API lockouts), missing error handling (silent failures), inefficient crawl patterns (over-fetching, redundant requests), poor caching (wasted API calls), ignoring content quality (accepting bad data), security anti-patterns (exposed keys, unvalidated input), and operational anti-patterns (missing monitoring, no alerting). Each anti-pattern includes detection methods, consequences, and fixes.
