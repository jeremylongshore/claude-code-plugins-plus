# Official Grammarly contract boundary

Source: [Writing Score API](https://developer.grammarly.com/writing-score-api.html)
(accessed 2026-09-04).

The documented status values for a score request are `PENDING`, `FAILED`, and
`COMPLETED`. A score request is created, a document is uploaded, and the status and
result are retrieved through the documented API flow. This skill analyzes only a
sanitized status receipt; it does not reproduce that flow or accept the document.

The official constraints section says to consider exponential backoff for HTTP 429
and reports an ideal base factor of 2 seconds from load-test results. That statement
is deliberately narrow: this skill uses it only for a failed 429 when no
`retry_after_seconds` evidence was supplied. It does not turn the documentation into
an SLA, timeout, quota, universal maximum retry count, or guarantee.

When `retry_after_seconds` is supplied by the caller as sanitized evidence, preserve
that value in the review output. Do not replace it with the 2-second base, average it,
cap it, or claim that it is provider-authenticated.

The source also documents content and upload constraints. Those facts are not inputs
to this analyzer: receipt processing must remain metadata-only, and a content or
body field is rejected rather than inspected.
