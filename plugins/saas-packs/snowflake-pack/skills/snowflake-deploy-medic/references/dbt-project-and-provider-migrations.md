# dbt Project and provider migration preflight

## Provider segments

Treat an upgrade as the ordered set of official migration-guide segments between
the locked source and target versions. For each segment record:

- source and target semantic versions;
- immutable commit-pinned migration-guide URL and source snapshot SHA-256;
- current observation timestamp inside the evidence window;
- affected Terraform addresses and resource schemas;
- state move/import/replace boundary;
- isolated-state test result and disposition;
- canonical receipt SHA-256.

Snowflake's provider documentation says preview resources can change without a
major-version bump and the maintained roadmap identifies migration assistance,
grant patterns, and dependency handling as ongoing operator concerns. A green plan
does not erase a skipped segment.

Primary sources:

- [Provider repository and preview contract](https://github.com/snowflakedb/terraform-provider-snowflake)
- [Migration guide](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/MIGRATION_GUIDE.md)
- [Provider roadmap](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/ROADMAP.md)

## dbt Project objects

Snowflake's 2026_06 BCR-2362 changes dbt Project objects from immutable numbered
deployments to one mutable live version. Query the target account's current bundle
status at execution time; do not encode a timeless pending/released claim. Record
the exact object denominator, current/target model, deployed and staged artifact
hashes, supported runtime, behavior-change disposition, exact rollback artifact,
profile/dependency/compile/build/test results, ownership, and any FORCE replacement.
An explicit VERSIONED-to-LIVE transition requires an enabled bundle or a current,
hash-bound account-specific early-opt-in receipt. An early-opted-in object can use
demigration before full enablement. Once the change is released, both current and
target state must be LIVE and demigration is no longer a valid rollback claim.
Bind BCR-2362's affected refs, disposition, and any early-opt-in proof to each dbt
Project receipt; a generic bundle observation is not project-level impact proof.

The immutable 2026_06 bundle page currently contains 19 item IDs (including
BCR-2362). The analyzer pins that exact ID set and its normalized digest; a caller-
declared count or a generic Snowflake documentation URL cannot establish bundle
completeness. Update the pinned set only from the canonical bundle page and with
new adversarial fixtures.

Primary sources:

- [Canonical 2026_06 bundle](https://docs.snowflake.com/en/release-notes/bcr-bundles/2026_06_bundle)
- [Live-version behavior change](https://docs.snowflake.com/en/release-notes/bcr-bundles/2026_06/bcr-2362)
- [Deploy dbt project objects](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake-deploy)
- [Supported dbt versions](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake-dbt-core-versions)

The analyzer never deploys a project. It blocks when the denominator, supported
version, BCR disposition, code hashes, or rollback artifact cannot be proven.

## Evidence trust contract

The JSON packet is a sanitized projection, not a raw Terraform plan or Snowflake
query log. Hash account, role, backend, workspace, object, operator, and owner
identities before projection. Each nested receipt binds its exact finite fields,
but a caller can recompute those receipts; therefore, the complete canonical
packet digest must arrive through an independent trusted CI/artifact channel.

The analyzer also requires an explicit evaluation timestamp. `PASS_AS_OF` means
only that the supplied zero-change evidence reconciled at that instant. It does
not remain valid into the future and never authorizes Terraform, schemachange, or
Snowflake mutation.
