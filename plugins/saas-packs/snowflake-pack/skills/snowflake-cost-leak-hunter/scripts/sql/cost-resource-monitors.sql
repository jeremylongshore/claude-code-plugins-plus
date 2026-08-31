-- Current resource-monitor inventory is visibility-scoped to the active role. Names
-- and owners are hashed; configuration mutation is intentionally out of scope.
SHOW RESOURCE MONITORS
->> SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'resource_monitors',
  'name_sha256', SHA2(TO_VARCHAR("name"), 256),
  'owner_sha256', IFF("owner" IS NULL, NULL, SHA2(TO_VARCHAR("owner"), 256)),
  'level', "level",
  'frequency', "frequency",
  'credit_quota', "credit_quota",
  'used_credits', "used_credits",
  'remaining_credits', "remaining_credits"
) AS EVIDENCE
FROM $1
ORDER BY "name"
LIMIT 10000;
