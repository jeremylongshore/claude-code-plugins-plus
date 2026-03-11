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

```typescript