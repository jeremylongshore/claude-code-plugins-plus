# clay-enrichment-patterns

## File Scaffold

```
clay-enrichment-patterns/
|-- SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Apply production-ready Clay enrichment patterns for person and company data. Covers batching strategies, error handling, retry logic, and type-safe implementations.
**Workflow:** Pattern reference skill for building robust Clay integrations. Use when moving from prototype to production-ready code.
**Relates to:** Builds on clay-hello-world; foundational patterns used by clay-table-from-requirements and clay-crm-sync-core.

## Summary

This skill provides production-ready patterns for Clay enrichment operations. It covers singleton API client initialization, robust error handling with structured logging, batch processing for multiple records, automatic retry with exponential backoff for rate limits, and type-safe TypeScript or Python implementations. These patterns form the foundation for all production Clay integrations.
