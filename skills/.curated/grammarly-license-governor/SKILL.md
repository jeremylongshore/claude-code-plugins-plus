---
name: grammarly-license-governor
description: >-
  Produce a review-only plan from a sanitized Grammarly License Management snapshot,
  identifying non-admin users whose last activity is before an explicit cutoff. Use
  when governing unused seats without exposing identity data or mutating Grammarly.
  Trigger with "review Grammarly inactive licenses", "Grammarly seat audit", or
  "analyze a sanitized Grammarly license snapshot".
allowed-tools: Bash(python3:*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Agent Skills-compatible hosts; requires Python 3.10+
tags: [saas, grammarly, licenses, privacy, governance]
---

# Grammarly License Governor

This skill creates a human-review queue from a sanitized License Management API
snapshot. It never calls Grammarly, resolves identities, sends a mutation, or
deletes a user or invitee. A candidate is only a non-admin user whose recorded
`last_activity_at` is strictly earlier than the explicit `inactive_before` cutoff.

## Overview

Use this skill for a bounded seat-review decision from sanitized user activity
metadata, not for identity resolution or live account administration.

## Prerequisites

No credentials, network access, Grammarly account, names, email addresses, or raw
IDs are needed. Python 3.10+ is the only runtime requirement. If a separate live
integration is being designed, consult the official [OAuth 2.0 credentials documentation](https://developer.grammarly.com/oauth-credentials.html)
(accessed 2026-09-04) for scopes; live authentication and mutation are outside this
skill.

## Instructions

### Step 1: Run the analyzer

```bash
python3 scripts/analyze_license_snapshot.py snapshot.json
cat snapshot.json | python3 scripts/analyze_license_snapshot.py -
python3 scripts/analyze_license_snapshot.py --self-test
```

The input contract is intentionally narrow. It accepts one snapshot object with an
explicit snapshot timestamp and UTC cutoff, producer attestation for keyed
HMAC-SHA256 pseudonymization, and records containing only resource pseudonyms,
last-activity timestamps, and the admin flag. Names,
email addresses, raw numeric/string IDs, institution identifiers, secrets, tokens,
headers, and unknown
fields fail closed, including when nested.

### Step 2: Apply the review rules

- Require `snapshot_generated_at` and `inactive_before`; never use the current time or
  an implicit default, and reject a cutoff later than the snapshot.
- Compare timestamps in UTC and classify only `last_activity_at < inactive_before`.
  Equal timestamps are not inactive-before evidence.
- Exclude every record with `is_admin: true`. The official API says admin licenses
  cannot currently be removed; admins must not enter the candidate plan.
- Require the exact producer-attestation object and keep candidate identity to
  `resource_id_hmac_sha256`, generated outside this tool with an
  organization-controlled HMAC key. The analyzer validates attestation and digest
  shape but cannot cryptographically prove upstream generation. Do not reverse, join,
  enrich, or display identity attributes; a plain unsalted hash is not enough.
- Emit `HUMAN_REVIEW_ONLY` candidates. The output is not an execution manifest and
  contains no delete operation, endpoint call, or authorization instruction.
- Missing activity evidence, duplicate digests, malformed timestamps, and raw or
  identity-bearing fields are review blockers, not reasons to guess.

Invitees are outside this analyzer's inactivity rule because the documented invitee
shape has creation and invitation status, not `last_activity_at`. Keep them in a
separate human review if they need governance; do not silently treat an invitee's
creation date as inactivity.

### Step 3: Stop on the unresolved official path conflict

The official License Management API page gives two different paths for the institution
summary: its endpoint heading says `/ecosystem/api/v1/institutions-summary`, while its
example request omits `/v1` and uses `/ecosystem/api/institutions-summary`. This is
unresolved documentation evidence. Treat it as a fail-closed stop: verify the path
with Grammarly before any human-authorized integration work. This skill does not
automate that endpoint and the offline script never performs network access.

Read the focused references when needed:

- [`references/snapshot-schema.md`](references/snapshot-schema.md) — exact sanitized
  input and review-plan output schema.
- [`references/license-management-contract.md`](references/license-management-contract.md)
  — official user/admin/invitee facts and the preserved path conflict.

## Output

The script emits `plan_type: REVIEW_ONLY`, `mutation_performed: false`, snapshot time,
cutoff, the bounded producer-attestation claim, counts, and sorted candidates containing
only pseudonyms and the `HUMAN_REVIEW_ONLY` action. It never emits names, emails, raw
IDs, or a delete request.

## Error Handling

Invalid JSON, missing or implicit cutoff, non-UTC timestamps, malformed or duplicate
digests, admins with missing fields, forbidden identity/secret keys, and unknown
fields fail closed with a non-zero exit. No partial candidate plan is emitted.

## Examples

- A non-admin active before the cutoff becomes a review candidate.
- An admin with the same old activity is counted as excluded and never becomes a
  candidate.
- An invitee is not classified from `created_at`; its activity evidence is absent.
- Either institution-summary path variant stops live integration work for human
  verification; the offline analyzer does not select one.

## Resources

- [`references/snapshot-schema.md`](references/snapshot-schema.md) — exact input and
  review-plan output schemas.
- [`references/license-management-contract.md`](references/license-management-contract.md)
  — official facts and unresolved summary-path conflict.
- [Grammarly License Management API](https://developer.grammarly.com/license-management-api.html)
  (accessed 2026-09-04).

## Official source

[Grammarly License Management API](https://developer.grammarly.com/license-management-api.html)
(accessed 2026-09-04).
