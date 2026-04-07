---
name: appfolio-common-errors
description: |
  Diagnose and fix common AppFolio API integration errors.
  Trigger: "appfolio error".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# AppFolio Common Errors

## Overview

AppFolio's Stack API powers property management integrations for tenant screening, work orders, lease management, and accounting. Each portfolio operates under its own subdomain (`{company}.appfolio.com`), meaning a single integration may need to handle multiple base URLs. Errors commonly stem from authentication misconfiguration, incorrect base URLs per portfolio, and business logic violations like duplicate tenant records or conflicting lease dates. Tenant lookup failures (404) are the most frequent issue, typically caused by targeting the wrong portfolio subdomain. This reference covers HTTP-level failures, property-management-specific validation errors, and recovery patterns for the most frequently encountered issues.

## Error Reference

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| `401` | `Unauthorized` | Invalid or rotated client_id/secret pair | Regenerate credentials in AppFolio Stack partner portal |
| `403` | `Forbidden` | Account not approved as Stack partner | Complete partner application at appfolio.com/stack |
| `404` | `Tenant not found` | Wrong portfolio base URL or deleted tenant | Verify base URL is `{company}.appfolio.com/api/v1` |
| `409` | `Lease conflict` | Overlapping lease dates for same unit | Check existing leases on unit before creating new one |
| `422` | `Validation failed` | Missing required fields on work order or tenant | Include all required fields: `unit_id`, `description`, `priority` |
| `429` | `Too Many Requests` | Exceeded 120 requests/minute limit | Implement exponential backoff starting at 1s delay |
| `500` | `Internal Server Error` | AppFolio platform issue | Retry after 30s; check status.appfolio.com |
| `503` | `Service Unavailable` | Maintenance window (typically weekends) | Retry with backoff; subscribe to maintenance calendar |

## Error Handler

```typescript
interface AppFolioError {
  code: number;
  message: string;
  category: "auth" | "rate_limit" | "validation" | "server";
}

function classifyAppFolioError(status: number, body: string): AppFolioError {
  if (status === 401 || status === 403) {
    return { code: status, message: body, category: "auth" };
  }
  if (status === 429) {
    return { code: 429, message: "Rate limit exceeded", category: "rate_limit" };
  }
  if (status === 404 || status === 409 || status === 422) {
    return { code: status, message: body, category: "validation" };
  }
  return { code: status, message: body, category: "server" };
}
```

## Debugging Guide

### Authentication Errors
AppFolio uses HTTP Basic Auth with `client_id:client_secret`. Verify credentials are not URL-encoded. Each portfolio has its own base URL -- confirm you are targeting the correct `{company}.appfolio.com` subdomain. Credentials rotate on partner approval changes.

### Rate Limit Errors
The Stack API enforces 120 requests/minute per API key. Batch tenant lookups instead of individual calls. Use `Retry-After` header value when present. Bulk endpoints (e.g., `/properties?page=1&per_page=100`) reduce call count significantly. Rate limits are per-key, not per-portfolio, so multi-portfolio integrations share the same budget.

### Validation Errors
Work order creation requires `unit_id`, `description`, and `priority`. Tenant creation requires `first_name`, `last_name`, and `email`. Lease creation fails with 409 if dates overlap an existing active lease on the same unit -- query current leases first. Move-in and move-out dates must be valid ISO 8601 format. Unit IDs are portfolio-specific and cannot be reused across subdomains.

## Error Handling

| Scenario | Pattern | Recovery |
|----------|---------|----------|
| Tenant lookup returns 404 | Search by email before creating | Use `/tenants?email=` endpoint |
| Work order 422 | Missing priority field | Default to `normal` if unspecified |
| Lease date conflict | Overlapping active lease | End existing lease before creating new |
| Bulk import partial failure | Some records rejected | Parse error array, retry failed records only |
| Auth token expired mid-batch | 401 on subsequent calls | Re-authenticate and resume from last offset |

## Quick Diagnostic

```bash
# Verify API connectivity and auth
curl -s -o /dev/null -w "%{http_code}" \
  -u "${APPFOLIO_CLIENT_ID}:${APPFOLIO_CLIENT_SECRET}" \
  "${APPFOLIO_BASE_URL}/api/v1/properties"
```

## Resources

- [AppFolio Stack API Docs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Status Page](https://status.appfolio.com)

## Next Steps

See `appfolio-debug-bundle`.
