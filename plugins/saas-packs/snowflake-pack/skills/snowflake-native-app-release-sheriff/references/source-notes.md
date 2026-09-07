# Primary-source semantics

Verified 2026-09-04 against current Snowflake documentation.

- [Manifest file reference](https://docs.snowflake.com/en/developer-guide/native-apps/manifest-reference): each version/patch has a manifest and setup script; package SQL metadata can override manifest version metadata. Manifest v2 enables automated privileges and App Specs.
- [Create a setup script](https://docs.snowflake.com/en/developer-guide/native-apps/creating-setup-script): setup is SQL-only, runs on install/upgrade, can be rerun after a failure, and forbids documented session-context and caller/import patterns. `CREATE OR REPLACE` can remove grants, so partial failure and replay are release hazards.
- [Automated privileges](https://docs.snowflake.com/en/developer-guide/native-apps/requesting-auto-privs): for manifest v2, changing `manifest_version` is permitted only in a major upgrade and the automated requested-privilege list cannot be modified in a patch. These constraints are not generalized to legacy references or App Specs.
- [References](https://docs.snowflake.com/en/developer-guide/native-apps/requesting-refs): references declare object type, privileges, and callback behavior; a declaration is not proof that a consumer bound it.
- [App Specs](https://docs.snowflake.com/en/developer-guide/native-apps/requesting-app-specs) and [settings requests](https://docs.snowflake.com/en/developer-guide/native-apps/requesting-app-specs-setting): consumers approve/decline requests; setting requests require manifest v2. Provider inventory cannot prove approval in every consumer.
- [`SHOW VERSIONS`](https://docs.snowflake.com/en/sql-reference/sql/show-versions): provider-visible version/patch rows expose state and `review_status`; piped output columns are referenced with lowercase quoted names.
- [Security scans](https://docs.snowflake.com/en/developer-guide/native-apps/security-run-scan): EXTERNAL ALPHA/DEFAULT release workflows invoke review; DEFAULT requires approval. QA versions do not initiate a scan. `NOT_REVIEWED`, `IN_PROGRESS`, and `REJECTED` are not approval.
- [`SHOW RELEASE DIRECTIVES`](https://docs.snowflake.com/en/sql-reference/sql/show-release-directives): current directives expose target, channel, version/patch, rollout state, maintenance-window setting, and deadline. Visibility requires OWNERSHIP or the documented package release/version management privilege.
- [Release channels and versions](https://docs.snowflake.com/en/developer-guide/native-apps/release-channels-versions) and [upgrade workflow](https://docs.snowflake.com/en/developer-guide/native-apps/release-channels-upgrade): test before changing a directive; changing a directive triggers upgrades and does not itself prove success.
- [`APPLICATION_STATE`](https://docs.snowflake.com/en/sql-reference/data-sharing-usage/application-state-view) and [Data Sharing Usage](https://docs.snowflake.com/en/sql-reference/data-sharing-usage): provider-side current installed-instance state can lag up to 10 minutes and removes an application after uninstall. It is not retained lifecycle history or an invoice-like complete ledger.

The collector omits package labels/comments, consumer names, account names,
regions, application hashes supplied by the provider view, failure reasons, SQL,
manifest/setup bodies, and App Spec definitions. Its absence and health claims
are bounded by role visibility, current-snapshot semantics, caps, and freshness.
