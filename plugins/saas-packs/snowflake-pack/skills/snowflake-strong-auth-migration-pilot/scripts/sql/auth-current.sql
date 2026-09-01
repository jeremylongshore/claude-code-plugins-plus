-- Current user posture visible to the executing read-only role. Account Usage
-- USERS remains the historical reconciliation source in auth.sql. The pipe
-- projection deliberately excludes login/display/first/last names, email,
-- comments, namespaces, warehouses, roles, and every other raw SHOW field.
SHOW USERS
->> SELECT OBJECT_CONSTRUCT_KEEP_NULL(
  '_dataset', 'current_users',
  'user_name_sha256', SHA2(TO_VARCHAR("name"), 256),
  'disabled', "disabled",
  'type', "type",
  'has_password', "has_password"
) AS EVIDENCE
FROM $1
ORDER BY SHA2(TO_VARCHAR("name"), 256)
LIMIT 10000;
