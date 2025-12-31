# exa-migration-strategies

## Skill Scaffold

```
exa-migration-strategies/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Execute migration from other search providers (Elasticsearch, Algolia, Google Search) to Exa with parallel running and quality comparison.
**Workflow:** Migration skill - enables transition from other search solutions.
**Relates to:** Follows exa-reference-architecture; uses exa-search-quality for comparison

## Summary

This skill manages migration to Exa: migration assessment and compatibility analysis, adapter layer for gradual transition, parallel search (old provider + Exa) during migration, quality comparison metrics and A/B testing, query translation patterns from other systems, data migration for cached/indexed content, traffic shifting strategies (10%/50%/100%), rollback procedures, and success criteria validation. Target: Complete migration with <1 hour cumulative downtime and equal or better relevance.
