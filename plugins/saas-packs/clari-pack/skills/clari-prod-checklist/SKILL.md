---
name: clari-prod-checklist
description: |
  Production readiness checklist for Clari API integrations.
  Use when launching a Clari data pipeline, validating export automation,
  or preparing for production forecast sync.
  Trigger with phrases like "clari production", "clari go-live",
  "clari checklist", "clari launch".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, revenue-intelligence, forecasting, clari]
compatible-with: claude-code
---

# Clari Production Checklist

## Checklist

### Authentication
- [ ] API token stored in secrets manager
- [ ] Token tested against production endpoint
- [ ] Token rotation procedure documented

### Data Pipeline
- [ ] Export pipeline tested with real forecast data
- [ ] All required `typesToExport` configured (forecast, quota, crm_closed, etc.)
- [ ] Time period coverage verified (current + historical)
- [ ] Deduplication logic handles re-exports
- [ ] Error handling for empty exports, job failures, timeouts

### Data Warehouse
- [ ] Target table schema created
- [ ] MERGE/UPSERT prevents duplicate records
- [ ] Data retention policy defined
- [ ] PII access restricted by role

### Scheduling
- [ ] Export scheduled (daily or weekly via cron/Airflow)
- [ ] Job completion monitoring with alerts
- [ ] Retry logic for transient failures

### Monitoring
- [ ] Alert on export failures
- [ ] Alert on empty results (data quality)
- [ ] Track forecast amounts for anomaly detection
- [ ] Dashboard for pipeline health

### Rollback
- [ ] Can re-run exports for any past period
- [ ] Data warehouse supports point-in-time recovery
- [ ] Pipeline can run manually for ad-hoc exports

## Resources

- [Clari API Reference](https://developer.clari.com/documentation/external_spec)

## Next Steps

For version upgrades, see `clari-upgrade-migration`.
