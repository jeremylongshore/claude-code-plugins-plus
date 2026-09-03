# Failure-Classification Reference

Classify an observed failure before changing code or retry policy. Status alone is not always enough: retain the provider request ID and typed SDK error class, but suppress raw bodies from ordinary logs and support bundles.

| Class | Typical signal | Retry | Operator action |
|---|---|---:|---|
| Validation | SDK validation error or HTTP 400/422 | No | Correct request shape against current API docs |
| Authentication | Typed authentication error or HTTP 401 | No | Verify secret reference; rotate through approved procedure |
| Authorization | HTTP 403 | No | Correct project, key, or policy scope |
| Billing | HTTP 402 | No | Resolve project billing or credit state |
| Not found | HTTP 404 for endpoint/model/resource | No | Verify the selected API surface and current catalog |
| Conflict | HTTP 409 | Conditional | Resolve resource state before retrying |
| Throttling | Typed rate-limit error or HTTP 429 | Bounded | Honor valid `Retry-After`, add jitter, enforce attempt ceiling |
| Timeout | Client deadline or HTTP 408/504 | Bounded | Retry only idempotent work within the operation budget |
| Provider | HTTP 500-599 | Bounded | Back off, then use an approved compatible fallback |
| Schema | HTTP 200 with missing required response fields | No | Fail closed and retain metadata-only evidence |

## Retry invariants

- Count the initial call as part of the attempt budget.
- Cap both per-delay and total elapsed time.
- Do not retry authentication, billing, authorization, validation, or policy failures.
- Do not switch models when the request itself is invalid.
- Preserve idempotency and cancellation through every attempt.
- Log status class, attempt, elapsed time, model, and request ID only.

## Verification receipt

Record the failing class, the bounded corrective action, and a same-input synthetic verification. A 200 response is accepted only when required typed fields parse successfully. Never use a shell success code that masks a failed JSON parser.

## Primary references

- [Perplexity SDK error handling](https://docs.perplexity.ai/docs/sdk/error-handling)
- [Perplexity SDK configuration](https://docs.perplexity.ai/docs/sdk/configuration)
- [Sonar OpenAI compatibility](https://docs.perplexity.ai/docs/sonar/openai-compatibility)
