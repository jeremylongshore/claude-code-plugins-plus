---
name: maintainx-data-handling
description: |
  Data synchronization, ETL patterns, and data management for MaintainX.
  Use when syncing data between MaintainX and other systems,
  building ETL pipelines, or managing data consistency.
  Trigger with phrases like "maintainx data sync", "maintainx etl",
  "maintainx export", "maintainx data migration", "maintainx data pipeline".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# MaintainX Data Handling

## Overview
Patterns and best practices for synchronizing, transforming, and managing data between MaintainX and external systems.

## Prerequisites
- MaintainX API access
- Database for local storage
- Understanding of data pipeline concepts

## Instructions
Follow these high-level steps to implement maintainx-data-handling:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-data-handling/references/implementation-guide.md)`

## Output
- ETL pipeline implemented
- Incremental sync running
- Data reconciliation tools
- Export capabilities (CSV, BigQuery)

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [MaintainX API Documentation](https://maintainx.dev/)
- [Apache Airflow](https://airflow.apache.org/) - Workflow orchestration
- [dbt](https://www.getdbt.com/) - Data transformation

## Next Steps
For enterprise access control, see `maintainx-enterprise-rbac`.
