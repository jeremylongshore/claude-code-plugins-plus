---
name: juicebox-common-errors
description: 'Diagnose and fix Juicebox API errors.

  Trigger: "juicebox error", "fix juicebox", "debug juicebox".

  '
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- recruiting
- juicebox
compatibility: Designed for Claude Code
---
# Juicebox Common Errors

## Overview

Juicebox provides AI-powered people search and analysis for recruiting and research workflows. API integrations cover search queries, profile enrichment, dataset operations, and quota management. Common errors include dataset format mismatches when uploading CSVs, analysis timeouts on large candidate pools, and quota exhaustion on free or starter plans. The quota system counts individual profile enrichments separately from search queries, which often surprises new integrators. This reference covers HTTP errors, business logic failures, and recovery strategies for reliable Juicebox integrations.

## Error Reference

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| `400` | `Invalid query format` | Malformed search query or empty filters | Ensure query is non-empty; validate filter field names |
| `401` | `invalid_api_key` | API key missing or revoked | Verify key at app.juicebox.ai > Settings > API |
| `403` | `quota_exceeded` | Plan search limit reached | Check quota in dashboard; upgrade plan or wait for reset |
| `404` | `Profile not found` | Candidate removed or profile unavailable | Re-run search to find updated profile data |
| `408` | `Analysis timeout` | Complex query exceeded 60s limit | Reduce dataset size or narrow search filters |
| `413` | `Dataset too large` | Upload exceeds 50MB or 100K row limit | Split dataset into smaller chunks before upload |
| `422` | `Invalid dataset format` | CSV headers don't match expected schema | Use template from Juicebox docs; required: `name`, `title`, `company` |
| `429` | `Rate limited` | Exceeded 30 requests/minute | Check `Retry-After` header; implement exponential backoff |

## Error Handler

```typescript
interface JuiceboxError {
  code: number;
  message: string;
  category: "auth" | "rate_limit" | "validation" | "timeout";
}

function classifyJuiceboxError(status: number, body: string): JuiceboxError {
  if (status === 401 || status === 403) {
    return { code: status, message: body, category: "auth" };
  }
  if (status === 429) {
    return { code: 429, message: "Rate limited", category: "rate_limit" };
  }
  if (status === 408) {
    return { code: 408, message: body, category: "timeout" };
  }
  return { code: status, message: body, category: "validation" };
}
```

## Debugging Guide

### Authentication Errors
Juicebox API keys are passed via `Authorization: Bearer` header. Keys are scoped per workspace. If you receive 401, verify the key has not been rotated at app.juicebox.ai > Settings. A 403 indicates quota exhaustion, not a permissions issue -- check your plan's remaining searches.

### Rate Limit Errors
The API enforces 30 requests/minute per key. Batch profile enrichment calls where possible. Use the `Retry-After` response header to determine wait time. For bulk operations, use the dataset upload endpoint instead of individual search queries.

### Validation Errors
Dataset uploads require CSV format with headers matching the Juicebox schema: `name`, `title`, `company` are required columns. Optional enrichment columns include `email`, `linkedin_url`, and `location`. Files over 50MB or 100K rows are rejected -- split into chunks. Analysis queries that exceed 60 seconds timeout with 408; narrow filters by adding location, title, or company constraints to reduce result set size.

## Error Handling

| Scenario | Pattern | Recovery |
|----------|---------|----------|
| Quota exceeded mid-batch | 403 after N successful calls | Track remaining quota via response headers; pause and resume |
| Dataset upload rejected | Invalid CSV format | Download template, reformat, and retry |
| Analysis timeout | Large candidate pool | Add location/title/company filters to narrow scope |
| Profile data stale | 404 on enrichment | Re-run search query to get current profile URLs |
| Rate limit during bulk search | 429 on sequential calls | Switch to dataset upload for bulk operations |

## Quick Diagnostic

```bash
# Verify API connectivity and key validity
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $JUICEBOX_API_KEY" \
  https://api.juicebox.ai/v1/health
```

## Resources

- [Juicebox Documentation](https://docs.juicebox.work)
- [Juicebox API Reference](https://api.juicebox.ai/docs)

## Next Steps

See `juicebox-debug-bundle`.
