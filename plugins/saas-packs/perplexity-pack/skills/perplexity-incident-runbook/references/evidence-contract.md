# Incident Evidence Bundle Contract

The automated collector emits one allowlisted JSON summary and archives that exact file. It is not a general debug bundle and must never be expanded by copying arbitrary files into its temporary directory.

## Archive invariant

The tar archive contains exactly:

```text
summary.json
```

The summary contains exactly these top-level fields:

- `schema_version`
- `incident_id`
- `provider`
- `http_status`
- `latency_seconds`
- `model`
- `finish_reason`
- `citation_count`
- `usage`

`usage` contains only numeric `prompt_tokens`, `completion_tokens`, and `total_tokens`.

## Never collect automatically

- Raw API request or response bodies
- Prompts, generated answers, reasoning, search results, or citation URLs
- Authorization headers or any API-key metadata
- Raw application, Kubernetes, proxy, packet, or system logs
- Environment variables, deployment specifications, annotations, or secrets
- Customer, employee, tenant, or workload identifiers

Provider request IDs can be useful, but store them directly in the access-controlled incident record rather than broadening the bundle schema.

## Release checklist

1. List the archive and confirm it contains only `summary.json`.
2. Validate the JSON keys and numeric types against this contract.
3. Scan the archive for the organization's secret and personal-data patterns.
4. Record reviewer, destination, retention period, and deletion owner.
5. Restrict the archive to the incident team and remove the temporary local copy.

Any additional evidence requires a separately approved collector and an enforced redaction review before it enters an archive.

## Primary references

- [Perplexity SDK error handling](https://docs.perplexity.ai/docs/sdk/error-handling)
- [Sonar response structure](https://docs.perplexity.ai/docs/sonar/openai-compatibility)
