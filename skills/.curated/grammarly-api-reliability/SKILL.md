---
name: grammarly-api-reliability
description: >-
  Analyze a sanitized Grammarly asynchronous job receipt without sending requests,
  reading document content, or guessing provider SLAs. Use when a Writing Score or
  similar document job is PENDING, FAILED, or COMPLETED and a bounded retry decision
  is needed. Trigger with "analyze Grammarly job receipt", "Grammarly 429 retry", or
  "Grammarly job status".
allowed-tools: Bash(python3:*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Agent Skills-compatible hosts; requires Python 3.10+
tags: [saas, grammarly, reliability, retries, privacy]
---

# Grammarly API Reliability

This is a read-only, metadata-only decision aid for asynchronous Grammarly jobs. It
does not call Grammarly, upload text, inspect a response body, create a token, or
retry a request. It turns one strict JSON receipt into a bounded, evidence-labeled
classification.

## Overview

Use this skill to classify a sanitized asynchronous receipt without treating a
provider response as permission to retry blindly.

## Prerequisites

No credentials, network access, Grammarly account, document, or response body is
needed. Python 3.10+ is the only runtime requirement. If a separate live integration
is being designed, use the official [OAuth 2.0 credentials documentation](https://developer.grammarly.com/oauth-credentials.html)
(accessed 2026-09-04) to determine access; live authentication and requests are
outside this skill.

## Instructions

### Step 1: Run the deterministic analyzer

Run the bundled script against a receipt file or standard input:

```bash
python3 scripts/analyze_job_receipt.py receipt.json
cat receipt.json | python3 scripts/analyze_job_receipt.py -
python3 scripts/analyze_job_receipt.py --self-test
```

The analyzer accepts only the documented metadata schema in
[`references/receipt-schema.md`](references/receipt-schema.md). It recursively rejects
keys associated with document content, bodies, text, headers, or tokens, including
those hidden in an otherwise unknown nested object. Unknown keys, malformed values,
inconsistent 429 evidence, and attempts above the cap fail closed.

### Step 2: Apply the decision rules

- `COMPLETED` is terminal. Do not retry it.
- `PENDING` is not a failure. Report that the receipt is still pending; do not invent
  a polling interval, timeout, SLA, quota, or freshness guarantee.
- `FAILED` with `http_status: 429` is the only status-specific retry class in this
  skill. If a numeric `retry_after_seconds` value is supplied, the output preserves
  that evidence as the wait instruction. If it is absent, the output names
  Grammarly's documented 2-second-base exponential-backoff guidance for 429 only;
  it does not invent a maximum, jitter rule, quota, or service promise.
- Any failure without 429 evidence is `MANUAL_REVIEW`: the receipt alone does not
  establish that retrying is safe.
- A failed receipt at `attempts == max_attempts` is `ATTEMPT_CAP_REACHED` and must
  not receive retry guidance. An input with `attempts > max_attempts` is invalid.

The cap is caller-supplied policy, not a Grammarly limit. The analyzer never changes
the cap or performs the next attempt. A human or caller-owned controller must decide
whether a retry is appropriate after reviewing the emitted classification.

### Step 3: Enforce the safety boundaries

Use synthetic receipts for evaluation. Never paste document text, raw request or
response bodies, HTTP headers, access tokens, authorization values, or secrets. The
script is standard-library-only and has no network, filesystem-write, subprocess,
or deletion behavior. It reports validation errors rather than trying to sanitize
unsafe input.

Read the focused references only when needed:

- [`references/receipt-schema.md`](references/receipt-schema.md) — exact accepted
  fields, recursive rejection rules, and output classes.
- [`references/official-contract.md`](references/official-contract.md) — the
  primary Grammarly Writing Score contract and the narrow 429 guidance boundary.

## Output

The JSON result names the accepted status, attempts, cap, classification, and a
short evidence-bounded guidance string. It never echoes submitted metadata beyond
those safe scalar fields and never fabricates an SLA, timeout, quota, result body,
or document diagnosis.

## Error Handling

Invalid JSON, forbidden recursive keys, unknown fields, unsupported statuses,
contradictory 429 evidence, and cap violations are errors. The script exits non-zero
and emits no classification. A valid non-429 failure is `MANUAL_REVIEW`, not a retry
recommendation.

## Examples

- A completed receipt returns `COMPLETED_TERMINAL` and no retry instruction.
- A failed 429 with `retry_after_seconds: 17` returns `RETRY_AFTER_EVIDENCE` and
  preserves 17 seconds.
- A nested `diagnostics.response_body` or `credentials.access_token` field is
  rejected before classification.

## Resources

- [`references/receipt-schema.md`](references/receipt-schema.md) — accepted fields,
  recursive rejection, and classifications.
- [`references/official-contract.md`](references/official-contract.md) — primary
  Grammarly contract and narrow 429 guidance.
- [Grammarly Writing Score API](https://developer.grammarly.com/writing-score-api.html)
  (accessed 2026-09-04).

## Official source

[Grammarly Writing Score API](https://developer.grammarly.com/writing-score-api.html)
(accessed 2026-09-04).
