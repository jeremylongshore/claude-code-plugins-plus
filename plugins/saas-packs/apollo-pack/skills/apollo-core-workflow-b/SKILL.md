---
name: apollo-core-workflow-b
description: |
  Implement Apollo.io email sequences and outreach workflow.
  Use when building automated email campaigns, creating sequences,
  or managing outreach through Apollo.
  Trigger with phrases like "apollo email sequence", "apollo outreach",
  "apollo campaign", "apollo sequences", "apollo automated emails".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Core Workflow B: Email Sequences & Outreach

## Overview
Implement Apollo.io's email sequencing and outreach automation capabilities for B2B sales campaigns.

## Prerequisites
- Completed `apollo-core-workflow-a` (lead search)
- Apollo account with Sequences feature enabled
- Connected email account in Apollo

## Instructions
Follow these high-level steps to implement apollo-core-workflow-b:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-core-workflow-b/references/implementation-guide.md)`

## Output
- List of available sequences with stats
- New sequence creation with steps
- Contacts added to sequences
- Campaign analytics and metrics

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Email Not Connected | No sending account | Connect email in Apollo UI |
| Contact Already in Sequence | Duplicate enrollment | Check before adding |
| Invalid Email Template | Missing variables | Validate template syntax |
| Sequence Limit Reached | Plan limits | Upgrade plan or archive sequences |

## Resources
- [Apollo Sequences API](https://apolloio.github.io/apollo-api-docs/#emailer-campaigns)
- [Apollo Email Templates](https://knowledge.apollo.io/hc/en-us/articles/4415154183053)
- [Sequence Best Practices](https://knowledge.apollo.io/hc/en-us/articles/4405955284621)

## Next Steps
Proceed to `apollo-common-errors` for error handling patterns.

## Examples

**Basic usage**: Apply apollo core workflow b to a standard project setup with default configuration options.

**Advanced scenario**: Customize apollo core workflow b for production environments with multiple constraints and team-specific requirements.