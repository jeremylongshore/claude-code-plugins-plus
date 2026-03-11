---
name: guidewire-common-errors
description: |
  Diagnose and resolve common Guidewire InsuranceSuite errors.
  Use when encountering API errors, Gosu exceptions, validation failures,
  or integration issues in PolicyCenter, ClaimCenter, or BillingCenter.
  Trigger with phrases like "guidewire error", "policycenter error",
  "claimcenter error", "gosu exception", "api error 422".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Guidewire Common Errors

## Overview

Diagnose and resolve the most common errors encountered in Guidewire InsuranceSuite Cloud API, Gosu development, and integrations.

## Prerequisites

- Access to Guidewire Cloud Console logs
- Understanding of HTTP status codes
- Familiarity with Gosu exception handling

## HTTP Status Code Reference

| Code | Meaning | Common Cause | Resolution |
|------|---------|--------------|------------|
| 400 | Bad Request | Malformed JSON, invalid field | Check request body structure |
| 401 | Unauthorized | Invalid/expired token | Refresh OAuth token |
| 403 | Forbidden | Missing API role | Check role assignments in GCC |
| 404 | Not Found | Invalid endpoint or ID | Verify URL and resource ID |
| 409 | Conflict | Concurrent modification | Retry with updated checksum |
| 422 | Unprocessable | Business rule violation | Fix validation errors |
| 429 | Too Many Requests | Rate limit exceeded | Implement backoff |
| 500 | Server Error | Internal error | Check server logs |
| 503 | Service Unavailable | Maintenance/overload | Retry with backoff |

## Common Validation Error Codes

| Code | Description | Example |
|------|-------------|---------|
| `required` | Missing required field | `accountHolder is required` |
| `invalid_format` | Wrong data format | `dateOfBirth must be ISO date` |
| `invalid_value` | Value not in allowed set | `state.code 'XX' not valid` |
| `range_exceeded` | Value outside range | `premium exceeds policy limit` |
| `duplicate` | Duplicate entity | `Account number already exists` |
| `reference_not_found` | Invalid foreign key | `producerCode.id not found` |

## Instructions

### Step 1: Identify the Error Category

Check HTTP status code and error response body to determine if the issue is authentication (401/403), validation (422), concurrency (409), or rate limiting (429).

### Step 2: Apply the Correct Fix Pattern

- **401**: Implement automatic token refresh with 60-second pre-expiry buffer
- **403**: Add required API role in GCC Identity & Access, wait 5 minutes for propagation
- **409**: Implement retry with GET-then-PATCH loop using checksums
- **422**: Parse validation details by field and code, fix each violation

### Step 3: Handle Gosu-Specific Exceptions

Key patterns: use null-safe operators (`?.`, `?:`), add entities to bundles before modifying, handle `AtMostOneRow` for multi-result queries, and catch `ValidationException` during commits.

### Step 4: Handle Integration Errors

Use circuit breakers for external services, retry message queue deliveries with exponential backoff (max 3 retries), and implement deadlock detection for database operations.

For detailed code implementations (TypeScript, Gosu, error wrappers), load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output

- Error identified and categorized
- Appropriate fix pattern applied
- Error handling code implemented

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Token refresh loop | Invalid credentials | Verify client ID/secret in GCC |
| Checksum mismatch | Stale data | Re-fetch before update |
| Validation cascade | Dependent fields | Fix root field first |
| Deadlock timeout | Lock contention | Add retry with backoff |

## Resources

- [Cloud API Error Reference](https://docs.guidewire.com/cloud/pc/202503/cloudapica/)
- [Gosu Exception Handling](https://gosu-lang.github.io/)
- [Integration Troubleshooting](https://docs.guidewire.com/education/)

## Next Steps

For debugging techniques, see `guidewire-debug-bundle`.

## Examples

**Basic usage**: Apply guidewire common errors to a standard project setup with default configuration options.

**Advanced scenario**: Customize guidewire common errors for production environments with multiple constraints and team-specific requirements.