---
name: databricks-enterprise-rbac
description: |
  Configure Databricks enterprise SSO, Unity Catalog RBAC, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls with Unity Catalog.
  Trigger with phrases like "databricks SSO", "databricks RBAC",
  "databricks enterprise", "unity catalog permissions", "databricks SCIM".
allowed-tools: Read, Write, Edit, Bash(databricks:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Databricks Enterprise RBAC

## Overview
Implement access control across Databricks using Unity Catalog privileges, workspace-level entitlements, and SCIM-provisioned groups. Unity Catalog enforces a three-level namespace (catalog.schema.table) with privilege inheritance, so granting `USAGE` on a catalog cascades to its schemas. Combine this with cluster policies and SQL warehouse permissions for full coverage.

## Prerequisites
- Databricks Premium or Enterprise tier with Unity Catalog enabled
- Account-level admin access for SCIM and group management
- Identity Provider supporting SAML 2.0 and SCIM 2.0

## Instructions

### Step 1: Create Account-Level Groups via SCIM
```bash
# Provision groups that map to IdP teams
databricks account groups create --json '{
  "displayName": "data-engineers",
  "entitlements": [{"value": "workspace-access"}, {"value": "databricks-sql-access"}]
}'

databricks account groups create --json '{
  "displayName": "data-analysts",
  "entitlements": [{"value": "workspace-access"}, {"value": "databricks-sql-access"}]
}'
```

### Step 2: Grant Unity Catalog Privileges
```sql
-- Data Engineers: full ETL access to bronze/silver, read gold
GRANT USAGE ON CATALOG analytics TO `data-engineers`;
GRANT CREATE, MODIFY, SELECT ON SCHEMA analytics.bronze TO `data-engineers`;
GRANT CREATE, MODIFY, SELECT ON SCHEMA analytics.silver TO `data-engineers`;
GRANT SELECT ON SCHEMA analytics.gold TO `data-engineers`;

-- Analysts: read-only on curated gold tables
GRANT USAGE ON CATALOG analytics TO `data-analysts`;
GRANT SELECT ON SCHEMA analytics.gold TO `data-analysts`;
```

### Step 3: Apply Cluster Policies
```json
{
  "name": "analyst-serverless-only",
  "definition": {
    "cluster_type": { "type": "fixed", "value": "sql" },
    "autotermination_minutes": { "type": "range", "maxValue": 30 },
    "num_workers": { "type": "range", "maxValue": 4 }
  }
}
```
Assign the policy to `data-analysts` so they cannot spin up expensive GPU clusters.

### Step 4: Configure SQL Warehouse Permissions
```bash
databricks permissions update sql/warehouses WAREHOUSE_ID --json '[
  {"group_name": "data-analysts", "permission_level": "CAN_USE"},
  {"group_name": "data-engineers", "permission_level": "CAN_MANAGE"}
]'
```

### Step 5: Audit with System Tables
```sql
SELECT event_time, user_identity.email, action_name, request_params
FROM system.access.audit
WHERE action_name LIKE '%Grant%' OR action_name LIKE '%Revoke%'
  AND event_date > current_date() - INTERVAL 30 DAYS
ORDER BY event_time DESC;
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `PERMISSION_DENIED` on table | Missing `USAGE` on parent catalog/schema | Grant `USAGE` at each namespace level |
| SCIM sync fails | Expired bearer token | Regenerate account-level PAT |
| Cluster start blocked | No matching cluster policy | Assign a permissive policy to the group |
| Cannot see SQL warehouse | Missing `CAN_USE` grant | Add warehouse permission for the group |

## Examples
```sql
-- Check effective permissions for a specific principal
SELECT * FROM system.information_schema.object_privileges
WHERE grantee = 'data-engineers'
ORDER BY object_type, object_name;
```

```bash
# Quickly grant a new team read access to gold tables
databricks unity-catalog permissions update schema analytics.gold \
  --json '[{"principal": "new-team", "privileges": ["USAGE", "SELECT"]}]'
```
