# Snowflake primary-source notes

- [`POLICY_REFERENCES`](https://docs.snowflake.com/en/sql-reference/functions/policy_references)
  returns policy associations and provider statuses but is privilege-dependent.
- [`TAG_REFERENCES_ALL_COLUMNS`](https://docs.snowflake.com/en/sql-reference/functions/tag_references_all_columns)
  includes inherited column tags and accepts the documented `TABLE` domain.
- [`POLICY_CONTEXT`](https://docs.snowflake.com/en/sql-reference/functions/policy_context)
  simulates masking, row access, aggregation, projection, and join policy behavior
  under supplied role/context and requires its own privileges.
- [`DATA_CLASSIFICATION_LATEST`](https://docs.snowflake.com/en/sql-reference/account-usage/data_classification_latest)
  is Enterprise Edition or higher, reports latest success and attempt/error state,
  and has documented latency up to three hours.
- [Classification results](https://docs.snowflake.com/en/user-guide/classify-results)
  distinguish automatic and manual classification observations.
- [Classification troubleshooting](https://docs.snowflake.com/en/user-guide/classify-troubleshooting)
  documents failure and privilege cases.
- [`CREATE CLASSIFICATION_PROFILE`](https://docs.snowflake.com/en/sql-reference/classes/classification_profile/commands/create-classification-profile)
  warns that `CREATE OR REPLACE` can detach the profile and disable automatic
  classification.
- [Tag-based masking](https://docs.snowflake.com/en/user-guide/tag-based-masking-policies)
  documents direct-over-tag precedence.
- [Tag-based policy preview](https://docs.snowflake.com/en/release-notes/2026/other/2026-07-21-tag-based-policies-preview)
  covers tag-based aggregation, row access, projection, and join policies.
- [Row access policies](https://docs.snowflake.com/en/user-guide/security-row-intro)
  are evaluated before masking policies.
- [Projection policies](https://docs.snowflake.com/en/user-guide/projection-policies)
  constrain final projection, not inner-query or predicate use.
- [Privacy policy limitations](https://docs.snowflake.com/en/user-guide/diff-privacy/differential-privacy-admin)
  document interactions with aggregation, masking, and projection policies.

Provider documentation and edition/preview status can change. Reconfirm these
primary sources for each governed rollout; an unknown or unverified state remains
inconclusive.
