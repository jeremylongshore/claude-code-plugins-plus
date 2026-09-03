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
| `login_history` | `auth-login-history` | `SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY` | `login_history` | Settled portion of the trailing seven-day authentication horizon |

Each receipt also contains exactly one same-statement `execution_context` row.
The organization-plus-account identifier, collector user, primary role, and
secondary-role representation are SHA-256 pseudonyms. The analyzer requires equivalent authorization context across
all three invocations but does not claim they used one physical session.
The account pseudonym hashes `CURRENT_ORGANIZATION_NAME()` plus
`CURRENT_ACCOUNT_NAME()`; the reusable legacy locator is not the binding key.
`primary_role_type` accepts only Snowflake's documented `ROLE` and
`APPLICATION_INSTANCE` values.

The reviewed `LOGIN_HISTORY` SQL deliberately excludes the newest two hours, so
its effective settled interval is the older portion of the trailing seven-day
horizon rather than seven full settled days. Both
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

`REPORTED_CLIENT_TYPE` is excluded entirely because Snowflake documents it as
unauthenticated telemetry. Snowflake-managed `SNOWFLAKE_SERVICE` principals are
retained in both raw user datasets so a 10,000-row cap cannot be hidden, marked
`SNOWFLAKE_MANAGED_EXCLUDED`, and then excluded from the operator denominator.
Operator-owned `SERVICE_AGENT` principals remain in scope and are treated as
service identities. A source `TYPE=NULL` is normalized to Snowflake's documented
`PERSON` meaning.

For operator-owned `SERVICE` and `SERVICE_AGENT` principals, Snowflake may expose
the same non-applicable password or MFA field as `FALSE` in `SHOW USERS` and
`NULL` in Account Usage. Reconciliation normalizes both to the same negative
observation; neither form is treated as positive posture evidence.

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
    "authorization_context": {
      "account_identifier_sha256": "<64-lowercase-hex>",
      "collector_user_sha256": "<64-lowercase-hex>",
      "primary_role_sha256": "<64-lowercase-hex>",
      "primary_role_type": "ROLE",
      "secondary_roles_sha256": "<64-lowercase-hex>"
    },
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
      "type": "LEGACY_SERVICE",
      "auth_methods": ["PASSWORD", "WIF"],
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
Operator `type`, `auth_methods`, and workload `current_auth` values must reconcile
to current receipted posture. Methods that user posture cannot prove, such as
OAuth or SAML, do not support scoped completeness in this bundle.
MFA is a separate factor posture flag, not a primary `auth_methods` value.
Workload names are unique; duplicates cannot collapse the enforcement-window
denominator.
The top-level bundle, metadata object, receipt wrapper, receipt, datasets, and
projected rows are exact schemas: unknown fields fail closed. A connection profile
is only a local profile name containing letters, digits, dot, underscore, or
hyphen; it is never a connection string or credential field.

Canary and break-glass evidence is deliberately not part of this schema. Keep
those operational receipts in the separately controlled approval workflow;
embedding either object is rejected so arbitrary telemetry cannot be echoed or
mistaken for independently verified proof.

## Trust and freshness

The collector's `receipt_sha256` detects accidental receipt changes but can be
recomputed by anyone who can edit the file. Before analysis, compute the canonical
whole-bundle digest with `--print-input-sha256` and retain it outside the bundle at
a controlled local boundary. Supply that value through `--trusted-input-sha256`.

Only `DIGEST_MATCHED_OPERATOR_ASSERTED` permits receipt datasets into scoped
reconciliation. This status means byte identity with the separately recorded
bundle; it is not a signature, origin attestation, or statement about who collected it.

`metadata.evaluated_at` must be within five minutes of the analyzer's actual UTC
clock, and `metadata.max_age_seconds` cannot exceed 3600. This prevents a caller
from moving the entire evidence timeline backward or declaring arbitrarily old
receipts fresh. Every receipt must be live, recent, internally ordered, below its reviewed cap,
and bound to the exact bundled SQL, canonical nonclaims, expected authorization
context, and expected source/dataset fields. Offline,
stale, future-dated, errored, capped, privilege-filtered, or context-mismatched
receipts are quarantined. Freshness is measured from each same-statement
`execution_context.observed_at`, not from later CLI completion, and the entire
collection interval must fit inside the declared maximum age.

## Reconciliation and claims

The current and historical rows join only on `user_name_sha256`. The analyzer
also compares normalized `created_on` to detect same-name principal recreation,
then compares `disabled`, `type`, and the password, RSA, MFA, PAT, and workload-identity
posture flags. `SERVICE` and `SERVICE_AGENT` password/MFA fields may be `NULL`
only where Snowflake defines them as non-applicable; other unknown posture blocks
completeness. A login observation older than the reconciled `created_on` is not
attributed to the current principal. Current-only, historical-only,
duplicate, malformed, or field-drift rows require review; delayed history never
overrides the current SHOW observation.

`evidence_scope_complete` is limited to the declared pseudonymous denominator.
It is not account-wide proof. `LOGIN_HISTORY` cannot set canary, recovery, or
cutover readiness by itself. Positive target login/action, negative old-path and
scope outcomes, and a separately tested recovery path remain human approval gates.
Likewise, `supported_auth` is an operator declaration, not independent proof that
the runtime, driver, connector, or Snowflake integration supports the selected
target. Current posture flags describe current configuration only.

The analyzer performs no Snowflake operation, and the reviewed collector SQL is
read-only. Neither component attests to actions taken elsewhere in the surrounding
session or workflow.

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
- [Account identifiers](https://docs.snowflake.com/en/user-guide/admin-account-identifier)
- [CURRENT_ROLE_TYPE](https://docs.snowflake.com/en/sql-reference/functions/current_role_type)
- [Authentication policies](https://docs.snowflake.com/en/user-guide/authentication-policies)
- [Strong-authentication rollout](https://docs.snowflake.com/en/user-guide/security-mfa-rollout)
