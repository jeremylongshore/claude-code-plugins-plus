---
name: supabase-data-handling
description: |
  Implement Supabase PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for Supabase integrations.
  Trigger with phrases like "supabase data", "supabase PII",
  "supabase GDPR", "supabase data retention", "supabase privacy", "supabase CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Supabase Data Handling

## Overview
Handle sensitive data correctly when integrating with Supabase.

## Prerequisites
- Understanding of GDPR/CCPA requirements
- Supabase SDK with data export capabilities
- Database for audit logging
- Scheduled job infrastructure for cleanup

## Data Classification

| Category | Examples | Handling |
|----------|----------|----------|
| PII | Email, name, phone | Encrypt, minimize |
| Sensitive | API keys, tokens | Never log, rotate |
| Business | Usage metrics | Aggregate when possible |
| Public | Product names | Standard handling |

## PII Detection

Scan request and response payloads for PII patterns (emails, phone numbers, SSNs) before logging or storing data.

## Instructions

1. Assess the current state of the compliance configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [compliance implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with compliance |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply supabase data handling to a standard project setup with default configuration options.

**Advanced scenario**: Customize supabase data handling for production environments with multiple constraints and team-specific requirements.

## Resources

- Official compliance documentation
- Community best practices and patterns
- Related skills in this plugin pack
