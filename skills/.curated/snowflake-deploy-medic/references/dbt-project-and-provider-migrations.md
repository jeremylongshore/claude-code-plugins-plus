# dbt Project and provider migration preflight

## Provider segments

Treat an upgrade as the ordered set of official migration-guide segments between
the locked source and target versions. For each segment record:

- source and target semantic versions;
- official migration-guide or release-note URL;
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

Snowflake's pending 2026_06 behavior change migrates dbt Project objects from
immutable numbered deployments to one mutable live version. Do not assume the old
version-selection or rollback semantics still apply. Record the object denominator,
current/target model, deployed and staged artifact hashes, supported runtime,
behavior-change disposition, and exact rollback artifact.

Primary sources:

- [Live-version behavior change](https://docs.snowflake.com/en/release-notes/bcr-bundles/2026_06/bcr-2362)
- [Deploy dbt project objects](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake-deploy)
- [Supported dbt versions](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake-dbt-core-versions)

The analyzer never deploys a project. It blocks when the denominator, supported
version, BCR disposition, code hashes, or rollback artifact cannot be proven.
