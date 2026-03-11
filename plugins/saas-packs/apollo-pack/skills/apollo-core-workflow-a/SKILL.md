---
name: apollo-core-workflow-a
description: |
  Implement Apollo.io lead search and enrichment workflow.
  Use when building lead generation features, searching for contacts,
  or enriching prospect data from Apollo.
  Trigger with phrases like "apollo lead search", "search apollo contacts",
  "find leads in apollo", "apollo people search", "enrich contacts apollo".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Core Workflow A: Lead Search & Enrichment

## Overview
Implement the primary Apollo.io workflow for searching leads and enriching contact/company data. This is the core use case for B2B sales intelligence.

## Prerequisites
- Completed `apollo-sdk-patterns` setup
- Valid Apollo API credentials
- Understanding of your target market criteria

## Instructions
Follow these high-level steps to implement apollo-core-workflow-a:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-core-workflow-a/references/implementation-guide.md)`

## Output
- Paginated people search results
- Enriched company firmographic data
- Enriched contact data with emails
- Combined lead pipeline with scoring

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Empty Results | Too narrow criteria | Broaden search parameters |
| Missing Emails | Contact not in database | Try LinkedIn enrichment |
| Rate Limited | Too many enrichment calls | Implement batching |
| Invalid Domain | Domain doesn't exist | Validate domains first |

## Resources
- [Apollo People Search Docs](https://apolloio.github.io/apollo-api-docs/#search-for-people)
- [Apollo Organization Enrichment](https://apolloio.github.io/apollo-api-docs/#enrich-organization)
- [Apollo Person Enrichment](https://apolloio.github.io/apollo-api-docs/#enrich-person)

## Next Steps
Proceed to `apollo-core-workflow-b` for email sequences and outreach.

## Examples

**Basic usage**: Apply apollo core workflow a to a standard project setup with default configuration options.

**Advanced scenario**: Customize apollo core workflow a for production environments with multiple constraints and team-specific requirements.