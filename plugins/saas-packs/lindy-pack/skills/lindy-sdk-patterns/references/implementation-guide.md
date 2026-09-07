# Lindy Integration Patterns - Implementation Guide

## Support Boundary

The package name is retained for discovery by users searching for the historical
"SDK patterns" phrase. Do not install or import a Lindy SDK: current official Lindy
documentation documents UI-configured workflow primitives, not a public software
development kit, general API key, agent CRUD client, or streaming client.

Use this mapping:

| Need | Documented primitive |
|---|---|
| Application starts a workflow | Webhook Received trigger |
| Lindy calls an application/API | HTTP Request action |
| Workflow transforms/calculates data | Run Code action |
| Workflow responds asynchronously | Send POST Request to Callback |
| Operator verifies execution | Tasks / Test Panel |

## Inbound Contract Checklist

- Copy the generated URL from Webhook Received; do not construct another Lindy host.
- Generate and store the one-time webhook secret.
- Send it in the Authorization bearer header.
- Choose same-task/new-task/ignore follow-up behavior intentionally.
- Allow only the event names and fields required by this workflow.
- Bound strings, arrays, nesting, and total body size before transmission.
- Exclude user content, headers, credentials, and full source records when a stable
  reference is sufficient.
- Record an application operation ID, but do not assume Lindy offers a documented
  idempotency header.

## Outbound Contract Checklist

- Fix the URL to an application-owned HTTPS allowlist.
- Put only the target application's credential in HTTP Request headers.
- Use an exact body schema populated from named workflow outputs.
- Branch on status code and validate response shape before use.
- Keep requests read-only during initial tests where possible.
- Enable Ask for Confirmation or stage a draft for consequential side effects.
- Never forward Webhook Received headers/body wholesale to the outbound action.

## Run Code Checklist

- Name each input variable and remember that documented values arrive as strings.
- Convert and validate every input before use.
- Bound collection lengths, string lengths, numeric ranges, and output shape.
- Return the minimum structured value through `result`.
- Avoid printing sensitive content because stdout is exposed as `text`.
- Treat `stderr` as diagnostic output that also requires redaction.
- Consult the current Run Code page for available libraries and platform behavior;
  do not freeze library lists, runtime vendor, startup, or timeout claims here.

## Callback Checklist

- Include a fixed application-owned `callbackUrl` only for workflows that require it.
- Add Send POST Request to Callback as described in the Webhooks guide.
- Do not claim a Lindy HMAC/signature header; none is documented by that guide.
- Treat callback fields as untrusted until the receiver's own authentication and
  schema checks succeed.
- Stage sensitive/consequential results for approval rather than acting immediately.

## Test Matrix

| Case | Expected result |
|---|---|
| Exact URL + valid generated secret + valid minimal body | A task appears and follows the configured path |
| Missing/wrong secret | Request rejected; no trusted workflow result |
| Wrong host, redirect, or embedded URL credentials | Application wrapper refuses before sending |
| Extra/oversized body field | Schema validation refuses before sending |
| Target application returns 4xx/5xx | HTTP Request error branch runs |
| Run Code receives invalid JSON/type/range | Action fails without partial result |
| Callback content fails receiver checks | Result quarantined; no side effect |

Use the Test Panel with synthetic data and test integrations. Lindy documents that
Test Panel actions execute for real.

## Official References

- [Webhooks](https://docs.lindy.ai/skills/by-lindy/webhooks)
- [HTTP Request](https://docs.lindy.ai/skills/by-lindy/http-request)
- [Run Code](https://docs.lindy.ai/skills/by-lindy/run-code)
- [Test Panel](https://docs.lindy.ai/testing/test-panel)
- [Tasks](https://docs.lindy.ai/fundamentals/lindy-101/tasks)
