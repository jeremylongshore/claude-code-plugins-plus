---
name: grammarly-document-evaluator
description: |
  Validate, plan, and explicitly execute Grammarly Writing Score, AI Detection,
  or Plagiarism Detection document jobs using the documented create, presigned
  upload, and poll lifecycle. Use when an operator needs to score a document,
  detect AI-generated content, check originality, diagnose a malformed document
  submission, or verify API result fields. Do not use for browser-editor grammar
  suggestions, live text rewriting, license deletion, or undocumented webhooks.
  Trigger with "score this document", "run Grammarly AI detection", "check this
  document for plagiarism", or "diagnose this Grammarly document job".
allowed-tools: Bash(python3:*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Agent Skills-compatible hosts; requires Python 3.10+
tags: [saas, grammarly, document-analysis, security, operator-workflow]
---

# Grammarly Document Evaluator

## Overview

Run Grammarly's three documented document APIs without inventing a direct-text
endpoint. The helper is dry-run by default. Before upload, it can create a metadata-only
request that reveals only the sanitized presigned origin for approval. Inspection
requires an `INSPECTION_READY` manifest before OAuth. Live execution requires an exact digest and a READY closed-schema safety manifest bound to the
operation, bytes, and both destinations. It reads OAuth credentials only from the
process environment, bounds polling locally, and emits no token, full upload URL, raw
request identifier, or document text.

## Prerequisites

- Grammarly Enterprise or an institution-wide Grammarly for Education license with API access.
- Python 3.10 or newer.
- One supported regular, non-symlink file: `.doc`, `.docx`, `.odt`, `.txt`, or `.rtf`.
- For live execution only, `GRAMMARLY_CLIENT_ID` and `GRAMMARLY_CLIENT_SECRET` in the environment.
- The exact read/write scopes for the selected operation; see [API contract](references/api-contract.md).

## Instructions

1. Classify the operation as `writing-score`, `ai-detection`, or `plagiarism`.
2. Run the helper without `--execute` from this skill directory:

   ```bash
   python3 scripts/run_document_evaluation.py \
     --operation writing-score \
     --file /approved/input/document.txt
   ```

3. Review the endpoint, scopes, beta marker, local constraints, retention boundary,
   and `content_sha256`. A dry run does not contact Grammarly.
4. Create a preliminary manifest with `presigned_upload_origin: null` and
   `presigned_upload_origin_approved: false`. Continue only when the safety guardian
   returns `INSPECTION_READY`, then inspect the actual byte destination. This creates
   a provider request but performs no upload and emits no signed URL:

   ```bash
   python3 scripts/run_document_evaluation.py \
     --operation writing-score \
     --file /approved/input/document.txt \
     --inspect-upload-origin \
     --confirm-content-sha256 sha256:REVIEWED_DIGEST \
     --approval-manifest /approved/metadata/grammarly-inspection.json
   ```

5. Put that exact sanitized origin and the dry-run metadata into the closed manifest
   for `grammarly-data-safety-guardian`. Continue only when it returns `READY`.
6. If live transfer is authorized, execute with both bindings:

   ```bash
   python3 scripts/run_document_evaluation.py \
     --operation writing-score \
     --file /approved/input/document.txt \
     --execute \
     --confirm-content-sha256 sha256:REVIEWED_DIGEST \
     --approval-manifest /approved/metadata/grammarly-transfer.json
   ```

7. Treat `COMPLETED` and `FAILED` as terminal. A local polling-budget exhaustion means
   only that this helper stopped; Grammarly documents no processing-time SLA.
8. Interpret all score fields on the documented `0..1` scale. Never convert them into
   unsupported pass/fail policy unless the operator supplies that policy separately.

## Output

- Dry run: a JSON transfer plan with content digest, byte size, extension, endpoint,
  scopes, beta status, and documented retention boundaries.
- Upload-origin inspection: sanitized public HTTPS origin, hashed request identifier,
  hashed full URL, and `document_uploaded: false`; the signed path/query remains secret.
- Execute: the same plan plus approved origin, hashed request identifier, terminal
  status, and exact API-specific score fields when completed.
- No raw content, OAuth token, client secret, presigned URL, or raw provider body.

## Error Handling

| Failure | Meaning | Safe response |
|---|---|---|
| Unsupported, empty, oversized, symlinked, or changing file | Local safety check failed | Stop and prepare a new approved regular file. |
| Fewer than 30 words or more than 100,000 UTF-8 characters in `.txt` | Documented text constraint failed | Correct the source; do not split and recombine scores. |
| Digest confirmation mismatch | Reviewed bytes differ from execution bytes | Stop and repeat dry run and approval. |
| Missing, blocked, or mismatched approval manifest | Governance decision does not bind this operation, content, phase, or origin | Stop before OAuth or before upload. |
| Newly issued upload origin differs from the approved inspected origin | Provider byte destination changed | Stop before PUT; inspect and approve again. |
| OAuth or API HTTP failure | Provider boundary rejected the operation | Report only phase and status code; never dump bodies or credentials. |
| Unknown status or result field | Response differs from the pinned contract | Fail closed and verify current official documentation. |
| Polling budget exhausted | Local cap reached; provider limit is undocumented | Return deferred/unknown, never fabricate a score. |

## Examples

**AI detection request:** choose `ai-detection`, disclose that it is Beta, require
`ai-detection-api:read,write`, and return only `average_confidence` and
`ai_generated_percentage` on a `0..1` scale.

**“Send this paragraph directly to `/v1/check`”:** refuse that contract. Grammarly's
document APIs require a filename-only creation body, a presigned file upload, and
status polling.

**Provider outage:** return an explicit unavailable or deferred result. Never substitute
an invented score.

## Resources

- [Pinned API contract](references/api-contract.md)
- [Security and retention boundaries](references/security-boundaries.md)
- [Deterministic evaluator](scripts/run_document_evaluation.py)
- [Grammarly developer documentation](https://developer.grammarly.com/)
