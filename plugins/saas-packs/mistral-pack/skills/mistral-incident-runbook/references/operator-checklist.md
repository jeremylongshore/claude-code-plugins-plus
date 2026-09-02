# Mistral incident operator checklist

Use this checklist with the main runbook. Local severity definitions and evidence
retention policy remain authoritative.

## Declare and contain

- Name one incident commander, one communications owner, and one operations owner.
- State the user-visible impact, UTC start time, affected environment, and confidence.
- Freeze unrelated changes to the affected path.
- Select only a pre-approved, reversible fallback, rollback, or concurrency control.
- Set a next-update time even when the diagnosis is uncertain.

## Evidence allowlist

Retain request IDs, timestamps, error status/type/code, deployment generation, replica
counts, rollout status, aggregate latency/error metrics, and the exact mitigation
command after secret substitution. Do not retain authorization headers, API-key
values or prefixes, prompts, tool outputs, raw customer payloads, secret-bearing pod
specifications, or unredacted application logs.

Before sharing an archive, inspect every file, apply the organization's redaction
procedure, restrict access, and record the retention deadline. A filename or `grep`
filter is not evidence that secret-bearing material was removed.

## Recovery proof

1. The minimal Mistral probe succeeds without verbose credential output.
2. The real application path succeeds for a representative request.
3. Error rate and latency meet the local objective for the observation window.
4. Queue depth, retry volume, and fallback health show no hidden backlog.
5. The temporary mitigation has either been reverted or assigned an owner and expiry.
6. Communications state the remaining risk and the next follow-up.

## Official provider facts

- [Error glossary](https://docs.mistral.ai/resources/error-glossary) documents the
  current `4xx` and transient `5xx` classes and response fields.
- [Usage and limits](https://docs.mistral.ai/admin/billing-usage/usage-limits) documents
  where organization and model limits are inspected.
- [Known limitations](https://docs.mistral.ai/resources/known-limitations) records
  current context-window, rate-limit, batch, upload, and streaming constraints.
- [Status page](https://status.mistral.ai/) is supporting evidence only; it does not
  replace application telemetry or establish recovery by itself.
