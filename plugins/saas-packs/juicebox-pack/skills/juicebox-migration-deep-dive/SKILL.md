---
name: juicebox-migration-deep-dive
description: |
  Advanced Juicebox data migration strategies.
  Use when migrating from other recruiting platforms, performing bulk data imports,
  or implementing complex data transformation pipelines.
  Trigger with phrases like "juicebox data migration", "migrate to juicebox",
  "juicebox import", "juicebox bulk migration".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Migration Deep Dive

## Overview
Advanced strategies for migrating data to Juicebox from other recruiting and people search platforms.

## Prerequisites
- Source data access and export capabilities
- Juicebox Enterprise plan (for bulk imports)
- Data mapping documentation
- Testing environment

## Instructions
1. Step 1: Data Assessment
2. Step 2: Schema Mapping
3. Step 3: Data Transformation Pipeline
4. Step 4: Bulk Import with Rate Limiting
5. Step 5: Validation and Reconciliation
6. Step 6: Rollback Strategy

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Data assessment tools
- Schema mapping configuration
- Transformation pipeline
- Bulk import with rate limiting
- Validation and reconciliation

## Resources
- [Bulk Import Guide](https://juicebox.ai/docs/migration)
- [Data Format Specifications](https://juicebox.ai/docs/data-formats)

## Next Steps
This skill pack completes the enterprise-grade Juicebox integration toolkit.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with CI/CD |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply juicebox migration deep dive to a standard project setup with default configuration options.

**Advanced scenario**: Customize juicebox migration deep dive for production environments with multiple constraints and team-specific requirements.