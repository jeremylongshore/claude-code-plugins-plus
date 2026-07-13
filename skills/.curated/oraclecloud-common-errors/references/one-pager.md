# oraclecloud-common-errors — One-Pager

Diagnose and fix OCI API errors with real error codes, root causes, and proven fixes.

## The Problem

OCI errors are cryptic. "NotAuthenticated" (401) covers six different config file problems and gives no hint which field is wrong. "NotAuthorizedOrNotFound" (404) could be a missing IAM policy OR a typo in an OCID — OCI intentionally hides the distinction. "CERTIFICATE_VERIFY_FAILED" has different fixes depending on your SDK language, operating system, and whether you sit behind a corporate proxy. Rate limit errors (429) lack a Retry-After header. Timeout errors surface as ServiceError with status -1, which looks like a bug rather than a network issue.

## The Solution

This is the diagnostic decoder ring. It maps every common OCI error to its real root cause and fix, with runnable diagnostic scripts. The 401 diagnostic checks all six failure modes automatically (missing config, wrong key path, public vs. private key confusion, permission bits, fingerprint mismatch, wrong OCID). The 404 section provides IAM policy statements to copy-paste. SSL errors have per-environment fixes. Every error includes the exact Python exception class and CLI diagnostic command.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Any developer hitting OCI API errors — from first-time users to production operators |
| **What** | Error-to-fix mapping with diagnostic scripts, IAM policies, SSL fixes, and retry patterns |
| **When** | Encountering 401, 404, 429, 500, timeout, or SSL errors from OCI SDK or CLI |

## Key Features

1. **401 diagnostic script** — Automated Python checker for all six NotAuthenticated root causes
2. **404 IAM decoder** — OCID validation and ready-to-use IAM policy statements
3. **SSL fix matrix** — Per-environment solutions for CERTIFICATE_VERIFY_FAILED (Linux, macOS, Docker, proxy)
4. **Complete error table** — Every OCI error code with status, exception class, cause, and fix

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
