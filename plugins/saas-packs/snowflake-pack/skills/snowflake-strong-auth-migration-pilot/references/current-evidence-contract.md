# Current and Historical Evidence Contract

Use this contract when collecting or validating strong-auth migration evidence.
It defines a bounded, read-only evidence lane. It does not grant permission to
change users, credentials, integrations, authentication policies, or sessions.

## Evidence classes

The analyzer requires three independent live collector receipts:

| Collection key | Surface | Source | Dataset | What it supports |
|---|---|---|---|---|
| `current` | `auth-current` | `SHOW USERS` | `current_users` | Near-current configuration posture, subject to active-role visibility |
| `historical` | `auth` | `SNOWFLAKE.ACCOUNT_USAGE.USERS` | `historical_users` | Delayed configuration corroboration |
| `login_history` | `auth-login-history` | `SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY` | `login_history` | Settled seven-day authentication observations |

Each receipt also contains exactly one same-statement `execution_context` row.
The account, collector user, primary role, and secondary-role representation are
SHA-256 pseudonyms. The analyzer requires equivalent authorization context across
all three invocations but does not claim they used one physical session.

The reviewed LOGIN_HISTORY SQL deliberately excludes the newest two hours. Both
Account Usage sources can lag by up to 120 minutes. A present event is an
observation. An absent event does not prove that authentication never occurred.

## Privacy boundary

Permitted identity correlation is `user_name_sha256`, computed inside Snowflake
from the exact username representation returned by each source. SHA-256 is
pseudonymization, not anonymity; common names remain guessable.

Receipt rows must not contain raw usernames, login/display/profile names, email,
client IP, connection or private-link identifiers, raw event or factor IDs,
client version, login details, free-form error messages, credential comments,
PAT names, WIF issuer/subject/audience data, public-key fingerprints, secrets,
tokens, passwords, or private keys. Unknown fields fail closed rather than being
silently copied into the report.

## Bundle envelope

Combine the three unchanged collector receipts with an operator-owned workload
inventory. `metadata.coverage.user_name_sha256` is the explicit denominator and
must match the current receipt and the operator user mapping exactly.

```json
{
  "schema_version": "2.0",
  "metadata": {
    "evaluated_at": "2026-09-03T12:05:00Z",
    "max_age_seconds": 3600,
    "connection_profile": "auth-readonly",
    "login_history_latency_seconds": 7200,
    "coverage": {
      "user_name_sha256": ["<64-lowercase-hex>"]
    }
  },
  "collections": {
    "current": {"receipt": {}},
    "historical": {"receipt": {}},
    "login_history": {"receipt": {}}
  },
  "users": [
    {
      "name": "ETL_SVC",
      "user_name_sha256": "<same-64-lowercase-hex>",
      "type": "SERVICE",
      "auth_methods": ["PASSWORD"],
      "owner": "data-platform"
    }
  ],
  "workloads": [
    {
      "name": "ETL_PROD",
      "identity": "ETL_SVC",
      "identity_sha256": "<same-64-lowercase-hex>",
      "owner": "data-platform",
      "current_auth": "PASSWORD",
      "supported_auth": ["WIF", "KEY_PAIR"],
      "roles": ["ETL_ROLE"]
    }
  ],
  "integrations": [],
  "enforcement_windows": [
    {
      "name": "etl-pilot",
      "workload": "ETL_PROD",
      "identity_sha256": "<same-64-lowercase-hex>",
      "target_auth": "WIF",
      "start": "2026-09-03T08:00:00Z",
      "end": "2026-09-03T09:00:00Z",
      "owner": "data-platform",
      "approved_by": "security-approver",
      "change_id": "CHG-1001"
    }
  ]
}
```

Use stable internal workload and change references; do not put ticket prose or
secrets in receipt rows. Raw names in the separate owner inventory are local
operator inputs and are never inferred from pseudonyms or emitted as collector evidence.

## Trust and freshness

The collector's `receipt_sha256` detects accidental receipt changes but can be
recomputed by anyone who can edit the file. Before analysis, compute the canonical
whole-bundle digest with `--print-input-sha256` and retain it outside the bundle at
a controlled local boundary. Supply that value through `--trusted-input-sha256`.

Only `DIGEST_MATCHED_OPERATOR_ASSERTED` permits receipt datasets into scoped
reconciliation. This status means byte identity with the separately recorded
bundle; it is not a signature, origin attestation, or statement about who collected it.

Every receipt must be live, recent, internally ordered, below its reviewed cap,
and bound to the exact bundled SQL and expected source/dataset fields. Offline,
stale, future-dated, errored, capped, privilege-filtered, or context-mismatched
receipts are quarantined.

## Reconciliation and claims

The current and historical rows join only on `user_name_sha256`. The analyzer
compares `disabled`, `type`, and the password, RSA, MFA, PAT, and workload-identity
posture flags. `NULL` means unknown, never false. Current-only, historical-only,
duplicate, malformed, or field-drift rows require review; delayed history never
overrides the current SHOW observation.

`evidence_scope_complete` is limited to the declared pseudonymous denominator.
It is not account-wide proof. `LOGIN_HISTORY` cannot set canary, recovery, or
cutover readiness by itself. Positive target login/action, negative old-path and
scope outcomes, and a separately tested recovery path remain human approval gates.

## Least-privilege and source limitations

Use an established read-only profile. `SNOWFLAKE.SECURITY_VIEWER` is the documented
database role for the Account Usage security views, but it is broader than these
two queries. `SHOW USERS` exposes detailed columns only when the active role has
the documented visibility; this workflow reports the gap and does not grant
`MANAGE GRANTS` or any other privilege.

Snowflake references:

- [SHOW USERS](https://docs.snowflake.com/en/sql-reference/sql/show-users)
- [USERS Account Usage view](https://docs.snowflake.com/en/sql-reference/account-usage/users)
- [LOGIN_HISTORY Account Usage view](https://docs.snowflake.com/en/sql-reference/account-usage/login_history)
- [Authentication policies](https://docs.snowflake.com/en/user-guide/authentication-policies)
- [Strong-authentication rollout](https://docs.snowflake.com/en/user-guide/security-mfa-rollout)
