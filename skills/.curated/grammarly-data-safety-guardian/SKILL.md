---
name: grammarly-data-safety-guardian
description: |
  Audit and gate a Grammarly document-submission manifest offline before an authorized
  integration upload. Use when checking supported extensions, file-size and
  text-length metadata, approval, consent, retention, and approved destination.
  This skill never accepts or submits document content and is not a replacement for
  legal, privacy, or security approval. Trigger with "Grammarly submission
  preflight", "Grammarly document safety", or "Grammarly retention check".
allowed-tools: Bash(python3:*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Agent Skills-compatible hosts; requires Python 3.10+
tags: [saas, grammarly, data-safety, privacy, governance]
---

# Grammarly Data Safety Guardian

Run a deterministic preflight over a metadata-only submission manifest. The guard
answers whether a planned document upload satisfies this skill's hard safety gates;
it does not read a document, contact Grammarly, create an upload URL, or retain a
copy of the manifest.

## Overview

The guard is a closed-world policy check for a planned document submission. It
combines Grammarly's documented format and size constraints with local governance
decisions while keeping the document itself outside the workflow.

## When to use

Use for a Writing Score, AI Detection (Beta), or Plagiarism Detection (Beta)
document submission before and after the evaluator inspects the provider-issued upload
origin. The preliminary decision gates OAuth metadata disclosure; the final decision
gates document bytes. Do not trigger for writing or editing content, document previews,
credential troubleshooting, or a request to upload a real document.

## Prerequisites

- A synthetic or production-approved metadata-only manifest matching
  [references/submission-contract.md](references/submission-contract.md).
- Independent data-owner approval, consent evidence, transfer approval, content
  classification, and acknowledgment of provider retention boundaries.
- Python 3.10 or newer. No document path, document content, credential, network, or
  writable output directory is required.

## Instructions

1. Collect only the manifest described in
   [references/submission-contract.md](references/submission-contract.md). The
   manifest may contain extension, byte count, optional derived text counts, and
   governance decisions, the pinned API control-plane origin, and the exact sanitized
   presigned upload origin; it must not contain text, content, previews, credentials,
   paths, filenames, full upload URLs, or raw API responses.
2. Run the guard with stdin:

   ```bash
   python3 scripts/audit_submission_manifest.py < submission-manifest.json
   ```

3. Treat `BLOCKED` as a hard stop. Fix the named metadata or governance decision;
   never truncate or transform a document silently to pass the guard.
4. Treat `INSPECTION_READY` as permission only to create a normalized-filename job and
   inspect its sanitized upload origin. Treat `READY` as permission to continue to the separately authorized upload
   workflow, not as proof that a document is lawful, accurate, or safe for a new
   destination.

The script accepts strict JSON, rejects duplicate keys and non-standard constants,
recursively rejects raw text, location, response, and credential fields, and performs
no network or filesystem writes. It enforces the documented extensions, 4,194,304-byte
maximum, UTF-8 text counts, a non-restricted classification, all approval gates, the
exact `https://api.grammarly.com` control-plane origin, and an explicitly approved
public HTTPS S3 presigned-upload origin on the default TLS port.

## Output

Return the deterministic JSON decision and failed check names. Do not echo a
filename, path, text, preview, credential, identifier, or raw document metadata
beyond the safe numeric and enum fields in the script's output.

## Error Handling

`BLOCKED` is a hard stop for an unsupported extension, zero or oversized bytes,
supplied character/word limits, failed approval/consent/retention/destination
checks, unknown fields, duplicate keys, or unsafe content/credential fields. Do not
truncate, split, preview, log, or upload a document to investigate. Invalid input
returns a non-zero exit status and a JSON decision without the rejected value.

## Examples

- A `.docx` manifest at 4,194,304 bytes with approved classification, authority,
  consent, transfer, retention, exact API origin, and exact inspected upload origin:
  `READY`.
- The same content-bound manifest with `presigned_upload_origin: null` and
  `presigned_upload_origin_approved: false`: `INSPECTION_READY`, which permits only
  destination discovery and no document upload.
- A `.txt` manifest missing derived counts or with `word_count: 29`: `BLOCKED`.
- A `restricted` manifest, lookalike API origin, private upload origin, or unapproved
  inspected upload origin: `BLOCKED`.
- A manifest containing `preview`, `raw_text`, or `client_token`: `BLOCKED` before
  any size or governance decision is used.

## Resources

- Read [references/submission-contract.md](references/submission-contract.md) for
  the closed-world input schema and API-derived limits.
- Read [references/governance-gate.md](references/governance-gate.md) when deciding
  what approval, consent, retention, and destination evidence is sufficient.
- The script is intentionally offline and has no write capability.
