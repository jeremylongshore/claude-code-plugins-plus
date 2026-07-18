# Intercom Debug Bundle — Examples and Redaction Rules

Focused snippets for the recurring gotchas that show up in support tickets:
verifying auth before collecting anything, reading rate-limit headers, and
knowing exactly what is safe to attach to a bundle.

## Verify Auth Before Collecting

Most failed bundles are just a bad token. Confirm `/me` returns `200` first —
if it does not, fix auth before running the full collector.

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me
# 200 = OK, 401 = regenerate token in the Developer Hub
```

## Read Rate-Limit Headers

Intercom returns rate-limit state in response headers, not the body. Dump them
with `curl -D -` and grep the `x-ratelimit` family:

```bash
curl -s -D - -o /dev/null \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me | grep -i "x-ratelimit"
# x-ratelimit-limit: 10000
# x-ratelimit-remaining: 9998
# x-ratelimit-reset: 1700000000
```

## Capture the request_id From an Error

When an API call fails, the `request_id` in the error body is the single most
useful thing to hand Intercom support — it lets them trace your exact request.

```bash
curl -s -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/contacts/does-not-exist \
  | jq '{type, request_id, errors}'
```

## Sensitive Data Policy

**ALWAYS redact before sharing:**

- Access tokens and OAuth secrets
- Webhook signing secrets
- Email addresses and PII
- Customer conversation content

**Safe to include:**

- HTTP status codes and error codes
- `request_id` from error responses (Intercom support needs these)
- Rate limit header values
- SDK and runtime versions
- Endpoint latency measurements
