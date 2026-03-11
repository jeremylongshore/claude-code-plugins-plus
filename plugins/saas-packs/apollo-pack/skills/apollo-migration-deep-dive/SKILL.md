---
name: apollo-migration-deep-dive
description: |
  Comprehensive Apollo.io migration strategies.
  Use when migrating from other CRMs to Apollo, consolidating data sources,
  or executing large-scale data migrations.
  Trigger with phrases like "apollo migration", "migrate to apollo",
  "apollo data import", "crm to apollo", "apollo migration strategy".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Apollo Migration Deep Dive

## Overview
Comprehensive guide for migrating to Apollo.io from other CRMs and data sources, including data mapping, validation, and rollback strategies.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-migration-deep-dive:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-migration-deep-dive/references/implementation-guide.md)`

## Output
- Pre-migration assessment framework
- Field mapping configurations
- Phased migration strategy
- Batch processing workers
- Validation and reconciliation
- Rollback procedures

## Error Handling
| Issue | Resolution |
|-------|------------|
| Field mapping error | Review and fix mapping |
| Batch failure | Retry with smaller batch |
| Validation mismatch | Investigate and re-migrate |
| Rollback needed | Execute phase rollback |

## Resources
- [Apollo Import Documentation](https://knowledge.apollo.io/hc/en-us/articles/4415154183053)
- [Salesforce Export Guide](https://help.salesforce.com/s/articleView?id=sf.exporting_data.htm)
- [HubSpot Export Guide](https://knowledge.hubspot.com/crm-setup/export-contacts-companies-deals-or-tickets)

## Next Steps

