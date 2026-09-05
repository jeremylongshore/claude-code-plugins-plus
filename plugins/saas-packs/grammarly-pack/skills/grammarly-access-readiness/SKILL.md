---
name: grammarly-access-readiness
description: |
  Audit a Grammarly API OAuth configuration offline for recognized organization
  access, least-privilege scopes, and documented API coverage. Use when reviewing
  Grammarly Enterprise or institution-wide Grammarly for Education API readiness,
  OAuth scope changes, or an AI/plagiarism access discrepancy. Trigger with
  "Grammarly OAuth readiness", "Grammarly API scopes", or "Grammarly
  institution-wide access". Do not use for
  obtaining credentials, making API calls, or submitting documents.
allowed-tools: Bash(python3:*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Agent Skills-compatible hosts; requires Python 3.10+
tags: [saas, grammarly, oauth, security, enterprise]
---

# Grammarly Access Readiness

Audit an operator-supplied OAuth metadata document without contacting Grammarly
and without handling a credential. The audit is a readiness gate, not an OAuth
client or an authorization oracle.

## Overview

The skill separates documented API scope requirements from account eligibility and
reports a deterministic `READY` or `BLOCKED` result. It is deliberately useful in
an offline review or CI check where live credentials and network access are
forbidden.

## When to use

Use this skill for a planned integration, scope review, or access review involving
the Grammarly Writing Score API, Analytics API, License Management API, AI Detection
API (Beta), or Plagiarism Detection API (Beta). Do not trigger for generic OAuth
questions, unrelated Grammarly application use, or a request to retrieve or rotate
secrets.

## Prerequisites

- A synthetic metadata-only JSON object matching
  [references/oauth-scope-contract.md](references/oauth-scope-contract.md).
- An out-of-band administrator confirmation of the Enterprise or institution-wide
  Education license; do not put that confirmation's identifier in the JSON.
- Python 3.10 or newer. No Grammarly credential, network access, or writable output
  directory is required.

## Instructions

1. Ask for the metadata-only JSON shape in
   [references/oauth-scope-contract.md](references/oauth-scope-contract.md). Never
   ask for a client secret, access token, refresh token, authorization header, or
   pasted API response.
2. Run the deterministic guard with stdin:

   ```bash
   python3 scripts/audit_oauth_config.py < oauth-config.json
   ```

3. Treat `BLOCKED` as a stop. Resolve the named metadata issue and rerun; do not
   broaden scopes merely to make the result pass.
4. Treat `READY` as an offline configuration result only. An administrator still
   has to create the OAuth credential and approve the production change through the
   organization's normal process.

The script uses its own closed-world operation map and exact scope strings; callers
cannot redefine the official catalog. It recognizes only `enterprise` or
`education-institution-wide` access, requires an approved configuration-source class,
and recursively rejects secret-bearing keys and values. AI Detection and Plagiarism
always carry the official catalog discrepancy flag and require an explicit authorized
exception decision; that decision does not prove beta provisioning.

## Output

Return the script's JSON decision, the missing or excessive scope names, the
required scopes, and any official-catalog flag. Do not repeat input values
other than non-sensitive operation and scope names. Never print a credential or
claim that the OAuth configuration was tested live.

## Error Handling

`BLOCKED` is expected for unsupported operations, missing or excess scopes,
unrecognized account access, secret-bearing input, or the documented beta-scope
catalog discrepancy. Do not retry with broader scopes, substitute an invented
endpoint, or paste a token to diagnose the result. Invalid JSON and duplicate keys
also block with a non-zero exit status.

## Examples

- Enterprise + `writing-score` with exactly `scores-api:read` and
  `scores-api:write`: `READY` when the catalog is structurally valid.
- Institution-wide Education + `ai-detection`: `BLOCKED` until an authorized reviewer
  acknowledges the pinned official scope-catalog inconsistency.
- A nested `client_secret` or an operation named `grammar_check`: `BLOCKED` without
  echoing the sensitive value.

## Resources

- Read [references/oauth-scope-contract.md](references/oauth-scope-contract.md) for
  the accepted JSON schema, exact operations, and official-source boundary.
- Read [references/access-review.md](references/access-review.md) when explaining
  enterprise/education eligibility, least privilege, or the AI/plagiarism catalog
  discrepancy.
- The script is deliberately offline and has no write capability.
