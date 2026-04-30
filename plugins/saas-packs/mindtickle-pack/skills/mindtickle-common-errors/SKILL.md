---
name: mindtickle-common-errors
description: 'Diagnose and fix MindTickle common errors.

  Trigger: "mindtickle error", "fix mindtickle", "debug mindtickle".

  '
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- mindtickle
- sales
compatibility: Designed for Claude Code
---
# MindTickle Common Errors

## Overview

MindTickle's API powers sales enablement workflows including course management, quiz administration, user provisioning via SCIM, and coaching analytics. Common integration errors include course access denied when user roles are misconfigured, quiz scoring discrepancies from version mismatches, and SCIM provisioning conflicts during bulk user imports from HR systems. The most frequent issue is 403 on course content access -- this almost always means the user is not enrolled, not that the API key lacks permissions. This reference covers authentication, content delivery, and user management errors that affect MindTickle platform integrations.

## Error Reference

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| `401` | `Invalid API key` | Key expired or revoked | Regenerate at MindTickle Admin > Integrations > API Keys |
| `403` | `Access denied` | API key lacks admin-level scope | Request admin API key from MindTickle account owner |
| `403` | `Course access denied` | User not enrolled or role insufficient | Enroll user in course via admin API before content access |
| `404` | `Module not found` | Invalid module/course/user/team ID | List available modules first; IDs change between environments |
| `409` | `SCIM user conflict` | Email already provisioned via different identity provider | Resolve duplicate in MindTickle Admin > Users > Merge |
| `422` | `Quiz scoring error` | Answer key version mismatch after quiz update | Re-publish quiz to sync answer keys; re-grade affected attempts |
| `429` | `Rate limited` | Exceeded 60 requests/minute | Implement exponential backoff; batch user operations |
| `500` | `Report generation failed` | Analytics query too broad or timeout | Narrow date range and team scope; retry after 30 seconds |

## Error Handler

```typescript
interface MindTickleError {
  code: number;
  message: string;
  category: "auth" | "rate_limit" | "validation" | "scim";
}

function classifyMindTickleError(status: number, body: string): MindTickleError {
  if (status === 401) {
    return { code: 401, message: body, category: "auth" };
  }
  if (status === 429) {
    return { code: 429, message: "Rate limited", category: "rate_limit" };
  }
  if (status === 409 && body.includes("SCIM")) {
    return { code: 409, message: body, category: "scim" };
  }
  return { code: status, message: body, category: "validation" };
}
```

## Debugging Guide

### Authentication Errors
MindTickle API keys are passed via `Authorization: Bearer` header. Keys are scoped to admin or read-only access levels. Most write operations require admin scope. Keys are automatically revoked when the issuing admin's account is deactivated -- re-issue from an active admin account.

### Rate Limit Errors
The API enforces 60 requests/minute per key. User provisioning operations (SCIM) share the same limit as content APIs. Batch user creation using SCIM bulk endpoints instead of individual POST calls. Use `Retry-After` header and implement exponential backoff starting at 2 seconds. Analytics report generation is throttled more aggressively at 10 requests/minute.

### Validation Errors
Course enrollment must precede content access -- a 403 on course content means the user is not enrolled, not that the API key is wrong. Quiz scoring errors occur when a quiz is updated after users have submitted attempts; re-publish the quiz and trigger re-grading. Module IDs differ between staging and production environments.

## Error Handling

| Scenario | Pattern | Recovery |
|----------|---------|----------|
| Course access denied for user | User not enrolled | Enroll via admin API, then retry content access |
| SCIM provisioning conflict | Duplicate email from different IdP | Merge user records in admin panel, then retry |
| Quiz score discrepancy | Answer key version mismatch | Re-publish quiz, trigger re-grade for affected users |
| Bulk user import partial failure | Some emails already exist | Parse error response, skip existing, retry new users |
| Report timeout | Query scope too broad | Add date range filter and limit to specific teams |

## Quick Diagnostic

```bash
# Verify API connectivity and key validity
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $MINDTICKLE_API_KEY" \
  https://api.mindtickle.com/v2/users/me
```

## Resources

- [MindTickle Integration Docs](https://www.mindtickle.com/platform/integrations/)
- [MindTickle SCIM API Reference](https://developers.mindtickle.com/scim)

## Next Steps

See `mindtickle-debug-bundle`.
