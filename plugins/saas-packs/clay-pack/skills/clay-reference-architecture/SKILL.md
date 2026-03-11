---
name: clay-reference-architecture
description: |
  Implement Clay reference architecture with best-practice project layout.
  Use when designing new Clay integrations, reviewing project structure,
  or establishing architecture standards for Clay applications.
  Trigger with phrases like "clay architecture", "clay best practices",
  "clay project structure", "how to organize clay", "clay layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clay Reference Architecture

## Overview

Production architecture for Clay-based lead enrichment and data operations. Covers table design, enrichment pipeline patterns, webhook integration, and CRM synchronization flows.

## Prerequisites

- Clay account with API access
- Understanding of Clay tables and enrichment columns
- CRM integration configured (HubSpot, Salesforce)
- Webhook endpoint for automation triggers

## Instructions

### Step 1: Design Table Schema

Define input columns (company name, domain, contact, LinkedIn URL), enrichment columns (company size, industry, email, phone, technologies), formula columns (ICP score, lead tier), and AI columns (personalized intro, pain points).

### Step 2: Configure Enrichment Waterfall

Order providers by cost: Apollo (1 credit) -> Hunter (1) -> Dropcontact (2) -> Findymail (3). Enable "stop on first result" to minimize credit usage.

### Step 3: Set Up Webhook Integration

On enrichment completion, check ICP score. Push high-value leads (score >= 80 with valid email) to CRM immediately. Add tier-A leads to outreach sequences.

### Step 4: Implement ICP Scoring Formula

Weight company size (up to 50 pts), target industry match (30 pts), and technology stack matches (10 pts each, max 100 total).

For architecture diagrams, TypeScript implementations, and ICP scoring code, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Enrichment credits exhausted | Too many lookups | Use waterfall pattern, set daily limits |
| Duplicate records | Re-importing same list | Deduplicate on domain + contact name |
| Webhook timeout | Processing too slow | Acknowledge immediately, process async |
| Low email find rate | Bad input data | Validate domains before enrichment |

## Resources

- [Clay API Documentation](https://docs.clay.com/api)
- [Clay Enrichment Providers](https://docs.clay.com/enrichments)
- [Clay Formulas Guide](https://docs.clay.com/formulas)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [design implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Examples

**Basic usage**: Apply clay reference architecture to a standard project setup with default configuration options.

**Advanced scenario**: Customize clay reference architecture for production environments with multiple constraints and team-specific requirements.