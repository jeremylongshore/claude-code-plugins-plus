-- Current budget inventory only. SHOW does not prove spend coverage or notification
-- configuration; class method CALLs remain outside the read-only collector contract.
SHOW SNOWFLAKE.CORE.BUDGET INSTANCES IN ACCOUNT
->> SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'budgets',
  'name_sha256', SHA2(TO_VARCHAR("name"), 256),
  'database_name_sha256', IFF("database_name" IS NULL, NULL, SHA2(TO_VARCHAR("database_name"), 256)),
  'schema_name_sha256', IFF("schema_name" IS NULL, NULL, SHA2(TO_VARCHAR("schema_name"), 256)),
  'current_version', "current_version",
  'owner_sha256', IFF("owner" IS NULL, NULL, SHA2(TO_VARCHAR("owner"), 256)),
  'owner_role_type', "owner_role_type"
) AS EVIDENCE
FROM $1
ORDER BY "database_name", "schema_name", "name"
LIMIT 10000;
