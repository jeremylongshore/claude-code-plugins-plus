---
name: clay-known-pitfalls
description: |
  Identify and avoid Clay anti-patterns and common integration mistakes.
  Use when reviewing Clay code for issues, onboarding new developers,
  or auditing existing Clay integrations for best practices violations.
  Trigger with phrases like "clay mistakes", "clay anti-patterns",
  "clay pitfalls", "clay what not to do", "clay code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clay Known Pitfalls

## Overview

Real gotchas when using Clay's data enrichment platform. Clay's credit-based waterfall enrichment model, table-based workflow, and multi-provider data sourcing create specific failure modes.

## Prerequisites

- Clay account with API access
- Understanding of waterfall enrichment logic
- Familiarity with Clay's credit billing model

## Instructions

### Step 1: Prevent Credit Burn from Waterfall Misconfiguration

Enable "Stop on first result" on each waterfall step. Without this, all providers run even after finding data, burning 3x credits per lookup.

### Step 2: Filter Blank/Invalid Rows Before Enrichment

Clay charges credits per row processed, even if input data is blank. Validate emails contain `@`, filter empty fields, and deduplicate before sending rows.

### Step 3: Normalize CSV Headers Before Import

Clay auto-maps CSV columns by name. "Company Name" vs "company_name" causes silent mismatches. Normalize: `strip().lower().replace(" ", "_")`.

### Step 4: Rate Limit API Calls

Batch rows (50 per request) with 2-second delays between batches. Handle 429 responses by reading the `Retry-After` header.

### Step 5: Don't Read Immediately After Write

Enrichments run asynchronously. Poll with exponential backoff (up to 30s) or use webhooks instead of reading immediately after row creation.

For detailed code examples (Python and TypeScript) of each pitfall and fix, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Credits burning fast | Waterfall not stopping on match | Enable "stop on first result" |
| Blank enrichment results | Input rows have invalid data | Pre-validate before sending |
| Column mapping errors | CSV header mismatch | Normalize headers before import |
| 429 rate limit errors | Too many API calls/minute | Batch requests with delays |
| Empty enrichment fields | Reading before enrichment completes | Poll with backoff or use webhooks |

## Resources

- [Clay API Docs](https://docs.clay.com/api)
- [Clay Waterfall Guide](https://docs.clay.com/enrichment/waterfall)
