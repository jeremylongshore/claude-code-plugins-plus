---
name: clay-data-handling
description: |
  Implement Clay PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for Clay integrations.
  Trigger with phrases like "clay data", "clay PII",
  "clay GDPR", "clay data retention", "clay privacy", "clay CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clay Data Handling

## Overview

Manage lead data through Clay enrichment pipelines safely. Covers data import validation, deduplication, enrichment data retention, GDPR-compliant management, and secure CRM export.

## Prerequisites

- Clay account with API access
- Understanding of data enrichment sources
- CRM integration for lead export
- Knowledge of GDPR/CCPA lead data requirements

## Instructions

### Step 1: Validate and Clean Import Data

Use Zod schemas to validate email format, company domain, and optional fields. Reject invalid records with error details. Track valid rate percentage.

### Step 2: Deduplicate Before Enrichment

Key on email (primary) or `domain:first_name:last_name` (fallback). Remove duplicates before sending to Clay to avoid wasting enrichment credits.

### Step 3: Add Retention Metadata

Tag each enriched record with `enriched_at`, `retention_expires` (default 365 days), and `enrichment_source`. Run weekly cleanup to remove expired records.

### Step 4: GDPR-Compliant Export

Strip PII for analytics exports (hash company names, remove emails). Add `consent_basis: legitimate_interest` for CRM exports. Include enrichment timestamp for audit trails.

For complete TypeScript implementations of validation, dedup, retention, and export, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| High duplicate rate | Same list imported twice | Run dedup before enrichment |
| Invalid emails | Bad source data | Validate with Zod before import |
| Expired data in CRM | No retention cleanup | Schedule weekly expiration check |
| Missing consent | No legal basis tracked | Add consent_basis to all exports |

## Resources

- [Clay API Documentation](https://docs.clay.com/api)
- [GDPR Lead Data Requirements](https://gdpr.eu/what-is-gdpr/)
