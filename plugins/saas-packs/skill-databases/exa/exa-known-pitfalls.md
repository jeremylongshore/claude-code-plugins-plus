# exa-known-pitfalls

## Skill Scaffold

```
exa-known-pitfalls/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Identify and avoid 10 common Exa anti-patterns including over-fetching, ignoring search modes, and missing caching.
**Workflow:** Code review skill - prevents common mistakes before they reach production.
**Relates to:** Follows all onboarding skills; used in code review processes

## Summary

This skill documents 10 common Exa anti-patterns: 1) Over-fetching results (requesting 100 when 10 needed), 2) Always using neural mode (keyword better for exact terms), 3) No caching (repeated identical queries), 4) Ignoring rate limits (no retry/backoff), 5) Full content extraction when highlights suffice, 6) Not using domain filters for trusted sources, 7) Exposing API keys in client-side code, 8) No fallback for Exa failures, 9) Synchronous blocking in async contexts, 10) Missing error handling for empty results. Each includes detection, impact, and fix.
