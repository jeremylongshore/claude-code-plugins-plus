# posthog-data-warehouse-sync

> Configure PostHog data export to data warehouse for advanced analytics and long-term storage

## Directory Structure

```
posthog-data-warehouse-sync/
├── SKILL.md
└── examples/
    ├── bigquery_sync.py
    ├── snowflake_config.md
    ├── schema_mapping.json
    └── data_validation.sql
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for PostHog to data warehouse sync |
| bigquery_sync.py | Python | Script for syncing PostHog data to BigQuery |
| snowflake_config.md | Markdown | Configuration guide for Snowflake integration |
| schema_mapping.json | JSON | PostHog to warehouse schema mappings |
| data_validation.sql | SQL | Queries to validate data sync completeness |

## Summary

**Category:** Advanced
**Target Audience:** Data engineers integrating PostHog with enterprise data warehouses
**Trigger Phrases:** "posthog data warehouse", "export posthog data", "posthog bigquery", "posthog snowflake", "sync posthog warehouse", "posthog data export"

---

**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**License:** MIT
**Version:** 1.0.0
