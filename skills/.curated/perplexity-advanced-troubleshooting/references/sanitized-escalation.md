# Sanitized Escalation and Evidence Contract

Use this reference after the main workflow has isolated a reproducible provider-facing problem. The goal is to preserve diagnostic value without exporting prompts, answers, credentials, or customer data.

## Allowed evidence

- Incident identifier and severity
- First and last observed timestamps in UTC
- Provider request IDs
- API surface and model identifier
- HTTP status counts by five-minute window
- Latency p50, p95, and timeout count
- Finish-reason counts
- Citation counts and opaque URL fingerprints
- Retry and fallback counts
- Synthetic reproduction steps and expected result

## Prohibited evidence

- Authorization or request headers
- API-key value, prefix, suffix, length, hash, or secret-manager path
- Customer or employee prompts and generated answers
- Full response and error bodies
- Citation URLs or page contents unless separately approved
- Raw application, proxy, container, or network logs
- Environment dumps, deployment manifests, or screenshots containing identifiers

## Escalation sequence

1. Confirm the reproduction uses a synthetic prompt and the fixed Perplexity API origin.
2. Remove fields outside the allowed list above.
3. Review the package as the same principal that will submit it.
4. Record who approved release, when, and the retention period.
5. Transfer it only through the approved support channel.
6. Delete the local working copy after the retained record is confirmed.

## Interpretation boundaries

Citation rotation across repeated web-grounded requests is not by itself an outage. Escalate when the contract breaks: required citations are missing, an approved domain filter is violated, the response schema is malformed, latency exceeds the product budget, or retryable failures exceed the bounded retry and fallback policy.

## Primary references

- [Perplexity SDK error handling](https://docs.perplexity.ai/docs/sdk/error-handling)
- [Sonar OpenAI compatibility and response fields](https://docs.perplexity.ai/docs/sonar/openai-compatibility)
- [Search filters](https://docs.perplexity.ai/docs/sonar/filters)
