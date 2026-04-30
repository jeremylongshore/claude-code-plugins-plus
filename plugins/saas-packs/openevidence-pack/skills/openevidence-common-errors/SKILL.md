---
name: openevidence-common-errors
description: 'Diagnose and fix OpenEvidence common errors.

  Trigger: "openevidence error", "fix openevidence", "debug openevidence".

  '
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openevidence
- healthcare
compatibility: Designed for Claude Code
---
# OpenEvidence Common Errors

## Overview

OpenEvidence provides AI-powered clinical decision support through evidence-based query answering with citation tracking. API integrations involve submitting clinical questions, retrieving evidence summaries, and managing citation references. Common errors include overly broad queries that exceed processing limits, citation-not-found errors when referenced studies are retracted, and timeouts on complex multi-condition queries that trigger deep literature analysis. The DeepConsult mode provides more thorough analysis but consumes 5x the rate limit quota and has a 90-second timeout. This reference covers authentication, query validation, and clinical-specific error patterns.

## Error Reference

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| `401` | `Authentication failed` | Invalid or expired API key | Regenerate at OpenEvidence developer portal |
| `403` | `Organization access denied` | API key not authorized for org | Verify org ID matches the key's assigned organization |
| `404` | `Citation not found` | Referenced study retracted or removed | Query for updated evidence; citation database refreshes weekly |
| `408` | `Query timeout` | Complex multi-condition query exceeded 90s limit | Simplify query to single clinical question; avoid compound conditions |
| `422` | `Query too broad` | Question not specific enough for clinical analysis | Add condition, population, or intervention to narrow scope |
| `422` | `Non-medical query` | Question not recognized as clinical | Rephrase using medical terminology and clinical context |
| `429` | `Rate limited` | Exceeded API request quota | Implement backoff; check `Retry-After` header |
| `503` | `Service unavailable` | DeepConsult queue at capacity | Retry after 60s; consider standard query mode instead |

## Error Handler

```typescript
interface OpenEvidenceError {
  code: number;
  message: string;
  category: "auth" | "rate_limit" | "query" | "availability";
}

function classifyOpenEvidenceError(status: number, body: string): OpenEvidenceError {
  if (status === 401 || status === 403) {
    return { code: status, message: body, category: "auth" };
  }
  if (status === 429) {
    return { code: 429, message: "Rate limited", category: "rate_limit" };
  }
  if (status === 503) {
    return { code: 503, message: body, category: "availability" };
  }
  return { code: status, message: body, category: "query" };
}
```

## Debugging Guide

### Authentication Errors
OpenEvidence API keys are scoped per organization. A 401 means the key itself is invalid; a 403 means the key is valid but not authorized for the specified org ID. Verify both the `OPENEVIDENCE_API_KEY` and the `org_id` parameter match. Keys are rotated quarterly for compliance -- check expiration date.

### Rate Limit Errors
Rate limits vary by plan tier. Standard plans allow 100 queries/hour; enterprise plans have higher limits. DeepConsult queries (longer analysis) consume 5x the rate limit quota of standard queries. Use `Retry-After` header and implement exponential backoff.

### Validation Errors
Queries must be clinically relevant and specific. "What causes headaches?" is too broad -- narrow to "What is the first-line treatment for migraine with aura in adults?" Add population, intervention, or comparison to improve query specificity. Non-medical queries are rejected with 422. Citation references use DOI-based identifiers; retracted studies return 404 and should be re-queried for updated evidence.

## Error Handling

| Scenario | Pattern | Recovery |
|----------|---------|----------|
| Query too broad | 422 with specificity warning | Add condition + population + intervention details |
| Citation not found | 404 on citation lookup | Re-query for updated evidence; citations refresh weekly |
| DeepConsult queue full | 503 on complex queries | Fall back to standard query mode; retry deep after delay |
| Timeout on compound query | 408 after 90s | Split into individual clinical questions |
| Org access mismatch | 403 despite valid key | Verify org_id parameter matches key's assigned organization |

## Quick Diagnostic

```bash
# Verify API connectivity and key validity
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $OPENEVIDENCE_API_KEY" \
  https://api.openevidence.com/v1/health
```

## Resources

- [OpenEvidence Platform](https://www.openevidence.com)
- [OpenEvidence API Documentation](https://docs.openevidence.com)

## Next Steps

See `openevidence-debug-bundle`.
