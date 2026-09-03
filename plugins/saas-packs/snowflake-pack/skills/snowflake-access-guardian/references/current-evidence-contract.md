# Current access evidence and receipt contract

Use this reference to collect and assemble schema `2.0` access evidence. It was
verified against Snowflake primary documentation on 2026-09-03. This workflow
collects security-sensitive metadata, not credentials or query/customer data.

## Why two evidence layers are required

The historical `access` surface queries these Account Usage views:

- `SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES`;
- `SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS`; and
- `SNOWFLAKE.ACCOUNT_USAGE.ROLES`.

They provide an account-wide baseline to a role holding the narrow
`SNOWFLAKE.SECURITY_VIEWER` database role, but changes can take up to 120 minutes
to appear. The views also omit some shared/imported database-role cases and some
object classes. Current `SHOW` statements are a separate cross-check, scoped by
the executing primary role.

Snowflake documents no way to combine immediate, complete, account-wide grant
visibility with a strictly read-only privilege. Full `SHOW` visibility requires
`MANAGE GRANTS`, which can grant and revoke privileges. Never add it, switch to
`ACCOUNTADMIN`, or activate secondary roles automatically. If an approved audit
session already has that privilege, record it as a high-authority visibility
boundary rather than calling the role read-only.

## Collector surfaces

| Surface | Selector | Purpose |
|---|---|---|
| `access` | none | Delayed Account Usage grants, user-role assignments, and role inventory |
| `access-session` | none | Current user, primary role, directly activated secondary roles, and session ID |
| `access-role-current` | `--role ROLE` | Privileges and roles granted to one account role |
| `access-role-parents` | `--role ROLE` | Roles/users receiving that account role |
| `access-user-current` | `--user USER` | Current account roles granted to one user |
| `access-database-role-current` | `--database-role DB.ROLE` | Grants to one local database role; capability-test because Snowflake reference pages currently differ |
| `access-future-database` | `--database DB` | Future grants at the database scope |
| `access-future-schema` | `--schema DB.SCHEMA` | Future grants at the schema scope |

Every scoped `SHOW` pipe emits one allowlisted `rows` dataset plus exactly one
`execution_context` row from the same Snowflake statement. Each context records
server observation time, session ID, account, current user, primary role/type,
and Snowflake's documented `roles`/`value` secondary-role object. Independent
invocations may have different session IDs, but their authorization contexts
must match exactly. This proves context equivalence, not one physical session.

Every account role declared in `metadata.coverage.roles` needs both role
surfaces, except `PUBLIC`, whose universal implicit inheritance makes a parent
census both redundant and potentially unbounded. `PUBLIC` always needs its
current grants-to receipt because every user receives it; omitting that receipt
can hide a high-risk path. Every declared user/database role needs its matching
receipt. Each future database needs at least one relevant schema receipt so
schema precedence cannot be hidden.
Quoted or multipart identifiers are intentionally unsupported by this bounded
lane; use a separately reviewed connector/bind path for them.

`CURRENT_SECONDARY_ROLES()` reports directly activated secondary roles, not all
lower roles inherited through their hierarchies. `CURRENT_AVAILABLE_ROLES()` is
not activation evidence and omits database, application, and instance roles.
Privileges granted directly to a user are active only when Snowflake user-based
access control is enabled for the statement with `USE SECONDARY ROLES ALL`;
`NONE` or an explicit role list must not turn them into an effective path.
The collector never executes `USE ROLE` or `USE SECONDARY ROLES`. Current access
surfaces are live-only: normalizing previously saved JSON can preserve bytes but
cannot establish a fresh server observation.

## Schema `2.0` bundle

Each collection wrapper binds the selector outside the receipt to the receipt's
template/rendered hashes and selector fingerprint. The raw selector is absent
from receipt metadata but remains in this locally controlled bundle because the
analyzer needs it to reconstruct the exact reviewed SQL.

```json
{
  "schema_version": "2.0",
  "metadata": {
    "account": "ORG-ACCOUNT",
    "collector_role": "ACCESS_AUDITOR",
    "connection_profile": "access-auditor",
    "evaluated_at": "2026-09-03T12:00:00Z",
    "window_start": "2026-09-03T11:45:00Z",
    "window_end": "2026-09-03T11:59:00Z",
    "max_age_seconds": 7200,
    "coverage": {
      "roles": ["ANALYST", "DATA_READER"],
      "users": ["ALICE"],
      "database_roles": ["ANALYTICS.READER"],
      "future_databases": ["ANALYTICS"],
      "future_schemas": ["ANALYTICS.CURATED"]
    },
    "external_boundaries": {
      "object_policies": "REVIEWED",
      "shares": "REVIEWED",
      "inherited_grants_capability": "REVIEWED"
    }
  },
  "collections": {
    "historical": {"selector": {}, "receipt": {}},
    "session": {"selector": {}, "receipt": {}},
    "role_current": [{"selector": {"role": "DATA_READER"}, "receipt": {}}],
    "role_parents": [{"selector": {"role": "DATA_READER"}, "receipt": {}}],
    "user_current": [{"selector": {"user": "ALICE"}, "receipt": {}}],
    "database_role_current": [
      {"selector": {"database_role": "ANALYTICS.READER"}, "receipt": {}}
    ],
    "future_database": [{"selector": {"database": "ANALYTICS"}, "receipt": {}}],
    "future_schema": [
      {"selector": {"schema": "ANALYTICS.CURATED"}, "receipt": {}}
    ]
  },
  "request": {
    "principal": "ALICE",
    "object": "ANALYTICS.CURATED.ORDERS",
    "privilege": "SELECT"
  },
  "managed_access_schemas": ["ANALYTICS.CURATED"],
  "verification": {"positive": [], "negative": []}
}
```

Copy complete collector receipts into the wrappers; do not recreate selected
receipt fields manually. `external_boundaries` records separate reviews—it is
not a switch that makes absent evidence true. If policy, share, or inherited-
grant capability review is absent, the full authorization claim stays blocked.

`SHOW GRANTS` can also return Snowflake-provided or imported database-role
links with an unqualified role name, such as `ALERT_VIEWER`. Account Usage can
omit those relationships, and an unqualified name cannot satisfy the local
`DATABASE.ROLE` selector contract. The analyzer reports each such link under
`unresolved_imported_database_role_edges`, excludes it from current-vs-history
reconciliation and the local coverage denominator, and never uses it to prove
an access path. Fully qualified local database-role links remain mandatory.

## Trust and failure semantics

The analyzer validates for every receipt:

- schema/surface identity and an error-free collection status;
- exact canonical template and rendered-selector SHA-256 values;
- exact source list, template name, and selector-presence metadata;
- selector fingerprint recomputed from the declared scope;
- self-checksum, dataset names, row counts, reviewed cap, and truncation state;
- local collection interval plus same-statement Snowflake observation time
  against the declared evaluation time and freshness bound;
- equivalent authorization context across independent live invocations; and
- one-to-one wrapper coverage plus the mandatory denominator derived from the
  request principal/object, active roles, and every traversed role edge.

The receipt checksum detects accidental edits but is forgeable. Grant-graph
scope completeness additionally requires a matching digest recorded when the
final bundle crossed a controlled local boundary. Status
`DIGEST_MATCHED_OPERATOR_ASSERTED` means byte identity matched that assertion;
it is not a signature and does not authenticate the collector. A mismatch,
malformed digest, or digest computed only after untrusted transport blocks every
graph claim. Invalid, stale, or untrusted datasets are quarantined rather than
fed to the graph.

Current-only and historical-only rows are reported as drift requiring review;
they are not flattened into an exact-match claim. Missing permissions, errors,
cap hits, selector gaps, stale receipts, database-only future evidence, or
unsupported database-role syntax are explicit blockers, never empty success.
`absence_claim_blocked` is always true in v3 because scoped `SHOW` visibility,
policies, shares, and operational denial are not a complete authorization proof.

## Privacy boundary

The minimum data still contains sensitive account, user, role, object, grantor,
and privilege topology. Protect it with access control, encryption, retention,
and export review. Do not collect user login/display names, email, comments,
authentication identifiers, MFA state, query text/tags, client IPs, object
definitions, or free-form error content. Snowflake warns that metadata can be
processed outside the account region and must not contain regulated data.

## Primary sources

- [Account Usage latency and scope](https://docs.snowflake.com/en/sql-reference/account-usage)
- [`GRANTS_TO_ROLES`](https://docs.snowflake.com/en/sql-reference/account-usage/grants_to_roles)
- [`GRANTS_TO_USERS`](https://docs.snowflake.com/en/sql-reference/account-usage/grants_to_users)
- [`ROLES`](https://docs.snowflake.com/en/sql-reference/account-usage/roles)
- [`SHOW GRANTS`](https://docs.snowflake.com/en/sql-reference/sql/show-grants)
- [Database-sharing guide showing `SHOW GRANTS TO DATABASE ROLE`](https://docs.snowflake.com/en/user-guide/data-sharing-gs)
- [`CURRENT_SECONDARY_ROLES`](https://docs.snowflake.com/en/sql-reference/functions/current_secondary_roles)
- [`CURRENT_SESSION`](https://docs.snowflake.com/en/sql-reference/functions/current_session)
- [`GRANT ... TO USER` user-based access semantics](https://docs.snowflake.com/en/sql-reference/sql/grant-privilege-user)
- [`CURRENT_AVAILABLE_ROLES`](https://docs.snowflake.com/en/sql-reference/functions/current_available_roles)
- [Snowflake database roles](https://docs.snowflake.com/en/sql-reference/snowflake-db-roles)
- [Metadata privacy guidance](https://docs.snowflake.com/en/sql-reference/metadata)
- [Inherited grants preview](https://docs.snowflake.com/en/user-guide/inherited-grants-using)
