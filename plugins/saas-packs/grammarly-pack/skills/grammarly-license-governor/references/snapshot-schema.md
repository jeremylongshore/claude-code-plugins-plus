# Sanitized license snapshot schema

The offline analyzer accepts exactly one object:

```json
{
  "snapshot_version": 1,
  "snapshot_generated_at": "2026-09-04T00:00:00Z",
  "inactive_before": "2026-09-01T00:00:00Z",
  "pseudonymization_attestation": {
    "scheme": "HMAC-SHA256",
    "key_reference": "org-license-audit",
    "key_version": "v1",
    "producer_attested": true
  },
  "users": [
    {
      "resource_id_hmac_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "last_activity_at": "2026-08-01T00:00:00Z",
      "is_admin": false
    }
  ]
}
```

`snapshot_version` must be integer `1`. `snapshot_generated_at`, `inactive_before`, and each
`last_activity_at` must be an ISO-8601 UTC timestamp ending in `Z`; offsets and
date-only values are rejected so comparisons remain deterministic. The comparison
is strictly earlier than the cutoff. A timestamp equal to the cutoff is recent for
this purpose, and the cutoff cannot be later than the snapshot timestamp.

`resource_id_hmac_sha256` must be exactly 64 hexadecimal characters produced by
HMAC-SHA256 under an organization-controlled key outside this tool. It is the only
identifier accepted. A plain unsalted hash of a predictable raw ID is not sufficient
because it can be enumerated. The pseudonym is carried through but never resolved or
joined. Duplicate pseudonyms fail closed because the plan would be ambiguous.

The root attestation is mandatory and closed-schema. `scheme` must be
`HMAC-SHA256`; `key_reference` and `key_version` are bounded non-secret references;
and `producer_attested` must be `true`. This is provenance evidence, not cryptographic
verification: the analyzer never receives the key or raw identifier and cannot
distinguish a dishonest producer's plain digest from a real HMAC.

Each user record must contain exactly the three fields shown. The root must contain
exactly `snapshot_version`, `snapshot_generated_at`, `inactive_before`,
`pseudonymization_attestation`, and `users`; an empty users list is valid. Names,
emails, numeric IDs, institution IDs, invitee IDs, raw IDs, tokens,
secrets, headers, and unknown nested objects are not accepted. The recursive guard
also rejects key spellings containing identity or credential terms before the exact
schema check.

## Review output

The result includes `snapshot_generated_at`, `inactive_before`, `candidate_count`, `excluded_admin_count`,
and sorted `candidates`. Each candidate contains only:

```json
{
  "resource_id_hmac_sha256": "…",
  "reason": "last_activity_before_cutoff",
  "recommended_review_action": "HUMAN_REVIEW_ONLY"
}
```

The result also sets `plan_type` to `REVIEW_ONLY` and `mutation_performed` to
`false`. It is not a delete list, API request body, or authorization artifact.
