# Sanitized job-receipt schema

The analyzer accepts one JSON object and rejects everything else. Its accepted
top-level fields are:

| Field | Required | Type and rule |
| --- | --- | --- |
| `status` | yes | Exactly `PENDING`, `FAILED`, or `COMPLETED`. |
| `attempts` | yes | Integer `>= 0`; booleans are not integers here. |
| `max_attempts` | yes | Integer `>= 1`; this is caller-supplied policy. |
| `http_status` | no | Integer from 100 through 599. |
| `retry_after_seconds` | no | Integer `>= 0`; allowed only with `FAILED` and `http_status: 429`. |

No arrays, nested objects, job payloads, provider response bodies, or extra fields
are accepted. In particular, `retry_after_seconds` is an already-sanitized numeric
observation; the analyzer does not parse an HTTP header or accept a date string.

The recursive key guard rejects a key, at any depth and regardless of case, when
its spelling contains `content`, `body`, `text`, `header`, or `token`. This catches
variants such as `document_text`, `response_body`, `request_headers`, and
`access_token` before normal schema validation. Unknown keys are rejected as well.

## Classification table

| Valid receipt | Classification | Guidance boundary |
| --- | --- | --- |
| `COMPLETED` | `COMPLETED_TERMINAL` | No retry. |
| `PENDING`, `attempts < max_attempts` | `PENDING_OBSERVATION` | No inferred poll interval, timeout, SLA, or quota. |
| `PENDING` or `FAILED`, `attempts >= max_attempts` | `ATTEMPT_CAP_REACHED` | Stop; the cap is caller policy. |
| `FAILED`, 429, supplied wait | `RETRY_AFTER_EVIDENCE` | Preserve the supplied non-negative seconds. |
| `FAILED`, 429, no wait | `RETRY_429_EXPONENTIAL_2S_BASE` | Mention Grammarly's documented 2-second base guidance only. |
| Other `FAILED` | `MANUAL_REVIEW` | No automatic retry conclusion from this receipt. |

The analyzer does not calculate a service-level deadline or a retry count beyond
the supplied cap. `attempts > max_attempts`, an invalid status, contradictory 429
evidence, or any forbidden field is a schema error and exits non-zero.
