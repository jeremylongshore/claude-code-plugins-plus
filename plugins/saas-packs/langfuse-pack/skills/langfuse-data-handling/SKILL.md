---
name: langfuse-data-handling
description: |
  Manage Langfuse data export, retention, and compliance requirements.
  Use when exporting trace data, configuring retention policies,
  or implementing data compliance for LLM observability.
  Trigger with phrases like "langfuse data export", "langfuse retention",
  "langfuse GDPR", "langfuse compliance", "export langfuse traces".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Langfuse Data Handling

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Manage the Langfuse data lifecycle including export (JSON/CSV), retention policies, GDPR compliance, anonymization, and audit trails.

## Prerequisites
- Langfuse account with data access
- Understanding of data retention requirements
- Compliance framework knowledge (GDPR, SOC2, etc.)

## Instructions

### Step 1: Export Trace Data
Paginate through traces with date range filters. Export as JSON or CSV with optional input/output inclusion.

### Step 2: Implement Retention Policy
Define retention periods per data type (traces: 90d, generations: 30d, scores: 1y). Auto-identify expired data.

### Step 3: Handle GDPR Requests
Implement data access (export user traces) and data deletion (mark for removal) endpoints for data subject requests.

### Step 4: Anonymize Data for Analytics
Hash user IDs, redact inputs/outputs, and strip PII metadata fields before sharing data externally.

### Step 5: Create Audit Trail
Log all data access and export events with tamper-evident hashing. Support time-range and actor-based queries.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Data export functionality (JSON/CSV)
- Retention policy enforcement
- GDPR compliance handlers
- Data anonymization pipeline
- Audit trail logging

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Export timeout | Too much data | Use pagination with smaller pages |
| Missing user data | Wrong userId format | Verify identifier format |
| Deletion failed | No DB access | Contact Langfuse support (cloud) |
| Audit gaps | Async logging | Use sync logging for critical events |

## Examples

### Data Categories
| Category | Retention | Sensitivity |
|----------|-----------|-------------|
| Traces | 90 days | Medium |
| Generations | 30-90 days | High |
| Scores | 1 year | Low |
| Sessions | 90 days | High |

## Resources
- [Langfuse Privacy Policy](https://langfuse.com/privacy)
- [GDPR Guidelines](https://gdpr.eu/)
- [Langfuse Data Protection](https://langfuse.com/docs/security)