# Mistral error triage playbook

Use this reference after the main skill identifies the HTTP status and error body.
It is grounded in Mistral's current public error contract; confirm the linked pages
before treating model names, context windows, or limits as fixed.

## Evidence boundary

Collect only the UTC timestamp, environment, endpoint, model, HTTP status, response
`type`, response `code`, request ID, retry headers, and an already-redacted payload
shape. Exclude authorization headers, API keys, prompts, tool results, customer data,
and raw request or response bodies unless the incident's approved evidence procedure
explicitly allows them.

## Decision matrix

| Status | Initial classification | Safe first action | Escalate when |
|---|---|---|---|
| `400` | Invalid request or context-window overflow | Validate the named `param`; compare token demand with the selected model card | The same known-good request fails |
| `401` | Missing, revoked, or invalid credential | Verify secret injection without printing it; rotate through the secret manager if the probe also fails | A newly issued key fails from a known-good network |
| `403` | Authorization or policy denial | Check workspace, role, and endpoint entitlement | The documented entitlement is present |
| `404` | Wrong endpoint or missing resource | Re-read the configured base URL and resource identifier | The resource is visible in the same workspace |
| `422` | Semantically invalid payload | Validate message, tool, and structured-output shapes | A minimal documented request fails |
| `429` | Organization or model limit exceeded | Reduce concurrency and retry with jitter; inspect server limit headers | Sustained legitimate demand exceeds the approved limit |
| `500`, `502`, `503`, `504` | Transient provider or gateway failure | Use bounded retries and a circuit breaker; check provider status | Errors persist beyond the incident threshold |

The official SDKs include retry behavior. Prefer their supported configuration over
maintaining a second unbounded retry loop. Retries must be capped, jittered, and
limited to transient classes; do not retry authentication or validation failures.

## Verification rules

1. Re-run one redacted minimal probe against the same environment.
2. Verify the affected application path, not only `/v1/models`.
3. Confirm error rate and latency return to the service objective for the observation
   window.
4. Record the reversible mitigation and the condition for undoing it.
5. Escalate with request IDs and sanitized evidence, never credentials or raw customer
   content.

## Official sources

- [Error glossary](https://docs.mistral.ai/resources/error-glossary) — supported HTTP
  statuses, response fields, and retry classes.
- [First API request](https://docs.mistral.ai/getting-started/quickstarts/developer/first-api-request)
  — current authentication and basic request pattern.
- [Usage and limits](https://docs.mistral.ai/admin/billing-usage/usage-limits) — where
  organization and model limits are exposed.
- [Known limitations](https://docs.mistral.ai/resources/known-limitations) — current
  context-window, rate-limit, upload, batch, and streaming boundaries.
- [Function calling](https://docs.mistral.ai/studio/conversations/function-calling) —
  required assistant/tool-result ordering and tool call identifiers.
