---
name: intercom-common-errors
description: 'Diagnose and fix Intercom API errors by HTTP status code and error type.

  Use when encountering Intercom errors, debugging failed API requests,

  or troubleshooting integration issues.

  Trigger with phrases like "intercom error", "fix intercom",

  "intercom not working", "debug intercom", "intercom 401", "intercom 429".

  '
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Common Errors

## Overview

Quick reference for diagnosing and fixing Intercom REST API errors by HTTP
status code. Every Intercom error returns the same envelope, so triage is
fast: read the `errors[].code`, match it to the table below, apply the fix.

All Intercom errors share this shape:

```json
{
  "type": "error.list",
  "request_id": "req_abc123",
  "errors": [{ "code": "unauthorized", "message": "Access Token Invalid" }]
}
```

The full per-code catalog (causes + copy-paste fixes) lives in
[references/error-reference.md](references/error-reference.md).

## Prerequisites

- An Intercom access token in `INTERCOM_ACCESS_TOKEN` (Developer Hub > Your App > Authentication).
- `curl` and `jq` for the diagnostic commands.
- For the TypeScript fixes: the `intercom-client` SDK (`npm install intercom-client`).

## Instructions

1. **Capture the error.** Grab the HTTP status and the JSON body. Use **Read** on your app logs, or **Grep** the codebase for the failing call site to see how the request is built.
2. **Match the code.** Find the `errors[].code` in the Error Handling table below.
3. **Confirm the token/limits first.** Run the diagnostic script in [references/diagnostics.md](references/diagnostics.md) to rule out auth and rate-limit issues in one shot.
4. **Apply the fix.** Open [references/error-reference.md](references/error-reference.md), jump to your status code, and use the causes + fix snippet there.
5. **Retry only retryable errors.** 429 and 5xx are retryable with backoff; 4xx client errors are not — fix the request instead.

Fast auth check:

```bash
curl -s https://api.intercom.io/me \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  -H "Accept: application/json" | jq '.type'
# Returns "admin" when the token is valid
```

## Output

You resolve the request into one of three outcomes:

- **Fixed request** — a corrected token, added OAuth scope, valid payload, or existence check that makes the call succeed.
- **Backoff-and-retry** — for 429 / 5xx, a retry wrapper that respects `X-RateLimit-Reset` and exponential backoff.
- **Escalation** — for persistent 5xx, the `request_id` to hand to Intercom support along with the status-page state.

## Error Handling

| Error Code | HTTP | Retryable | Action |
|------------|------|-----------|--------|
| `unauthorized` | 401 | No | Regenerate token |
| `forbidden` | 403 | No | Add OAuth scope |
| `not_found` | 404 | No | Verify resource ID |
| `conflict` | 409 | No | Search before create |
| `parameter_invalid` | 422 | No | Fix input data |
| `rate_limit_exceeded` | 429 | Yes | Backoff and retry |
| `server_error` | 500+ | Yes | Retry, check status page |

**Limits:** 10,000 req/min per app, 25,000 req/min per workspace. On 429,
read `X-RateLimit-Reset` and wait until that epoch before retrying.

## Examples

**401 — invalid token.** The auth check returns nothing instead of `"admin"`. Regenerate the token in Developer Hub and update the app's env. Full walkthrough: [references/error-reference.md](references/error-reference.md).

**409 — duplicate contact.** `create` fails because the `email`/`external_id` already exists. Search first, then create:

```typescript
const existing = await client.contacts.search({
  query: { field: "email", operator: "=", value: email },
});
return existing.data.length > 0
  ? existing.data[0]
  : client.contacts.create({ role: "user", email, externalId });
```

**429 — rate limited.** Wrap the call in exponential backoff that honors
`X-RateLimit-Reset`. Full retry helper: [references/error-reference.md](references/error-reference.md).

For a full triage sweep (auth + rate limit + Intercom status in one command),
run the script in [references/diagnostics.md](references/diagnostics.md).

## Resources

- [Error Codes](https://developers.intercom.com/docs/references/rest-api/errors/error-codes)
- [HTTP Responses](https://developers.intercom.com/docs/references/rest-api/errors/http-responses)
- [Rate Limiting](https://developers.intercom.com/docs/references/rest-api/errors/rate-limiting)
- [Intercom Status](https://status.intercom.com)
- [Full error reference](references/error-reference.md) — per-code causes and fixes
- [Diagnostics](references/diagnostics.md) — one-shot health-check script

## Next Steps

For deeper, end-to-end debugging of an Intercom integration — capturing request/response pairs, replaying failing calls, and correlating `request_id`s across a session — see the `intercom-debug-bundle` skill in this pack.
