# vercel-migration-deep-dive

## Skill Scaffold

```
vercel-migration-deep-dive/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Execute major re-architecture using strangler fig pattern with data migration and gradual traffic shifting.
**Workflow:** Used for major platform migrations - typically a multi-week project with careful planning.
**Relates to:** Follows vercel-enterprise-rbac; flagship+ leads to vercel-advanced-troubleshooting

## Summary

This skill provides a comprehensive guide for major Vercel migrations. It covers migration type assessment (fresh install, competitor, major version, full replatform), pre-migration analysis scripts, the strangler fig pattern for gradual migration, adapter layer implementation for abstraction, batch data migration with error handling, feature flag-controlled traffic shifting, rollback procedures, and post-migration validation. The goal is complete migration with minimal cumulative downtime.
