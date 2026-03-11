---
name: databricks-data-handling
description: |
  Implement Delta Lake data management patterns including GDPR, PII handling, and data lifecycle.
  Use when implementing data retention, handling GDPR requests,
  or managing data lifecycle in Delta Lake.
  Trigger with phrases like "databricks GDPR", "databricks PII",
  "databricks data retention", "databricks data lifecycle", "delete user data".
allowed-tools: Read, Write, Edit, Bash(databricks:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks Data Handling

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement data management patterns for GDPR compliance, PII masking, data retention, and row-level security in Delta Lake with Unity Catalog.

## Prerequisites
- Unity Catalog configured
- Understanding of Delta Lake features
- Compliance requirements documented
- Data classification in place

## Instructions

### Step 1: Classify and Tag Data
Tag tables with `data_classification` (PII/CONFIDENTIAL/INTERNAL) and `retention_days`. Tag columns with `pii` type (email, phone, etc.) using Unity Catalog tags.

### Step 2: Implement GDPR Deletion
Build GDPRHandler that finds all PII-tagged tables, locates user records by ID, and deletes with audit logging. Support dry-run mode for impact assessment.

### Step 3: Enforce Retention Policies
DataRetentionManager reads `retention_days` tags, finds appropriate date columns, and deletes expired data. Schedule daily with VACUUM to clean up old Delta files.

### Step 4: Configure PII Masking
Create masked views with email masking (`j***@***.com`), phone masking (`***-****`), name hashing, and full redaction. Use for analytics and testing environments.

### Step 5: Enable Row-Level Security
Create filter functions that check group membership. Apply row filters and column masks to restrict data access by user role.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for SQL tagging, GDPRHandler class, DataRetentionManager, PIIMasker, row-level security functions, and SAR report generation.

## Output
- Data classification tags applied across catalog
- GDPR deletion process with audit trail
- Retention policies enforced automatically
- PII masking for non-production access
- Row-level security on sensitive tables

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Vacuum fails | Retention too short | Ensure > 7 days (168 hours) retention |
| Delete timeout | Large table | Partition deletes, run over multiple days |
| Missing user column | Non-standard schema | Map user columns manually per table |
| Mask function error | Invalid regex | Test masking functions on sample data |

## Examples

### Quick GDPR Dry Run
```python
gdpr = GDPRHandler(spark, "prod_catalog")
report = gdpr.process_deletion_request("user-12345", "GDPR-2024-001", dry_run=True)  # 2024: port 12345 - example/test
print(f"Would delete {report['total_rows_deleted']} rows from {len(report['tables_processed'])} tables")
```

## Resources
- [Delta Lake Privacy](https://docs.databricks.com/delta/privacy.html)
- [Unity Catalog Security](https://docs.databricks.com/data-governance/unity-catalog/row-level-security.html)
- [GDPR Compliance](https://docs.databricks.com/security/privacy/gdpr.html)

## Next Steps
For enterprise RBAC, see `databricks-enterprise-rbac`.