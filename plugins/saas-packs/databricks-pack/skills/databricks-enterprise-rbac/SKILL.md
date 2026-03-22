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
tags: [saas, databricks, rbac]

---
# Databricks Enterprise RBAC

## Overview
Implement enterprise access control using Unity Catalog privileges, SCIM-provisioned groups, workspace entitlements, cluster policies, and audit logging. Unity Catalog uses a three-level namespace (`catalog.schema.object`) with privilege inheritance: granting `USAGE` on a catalog cascades to schemas. Account-level SCIM syncs groups from your IdP (Okta, Azure AD, Google Workspace).

## Prerequisites
- Databricks Premium or Enterprise with Unity Catalog enabled
- Account admin access for SCIM and group management
- Identity Provider supporting SAML 2.0 and SCIM 2.0

## Instructions

### Step 1: Provision Groups via SCIM API
Sync groups from your IdP at the account level. Max 10,000 users + service principals and 5,000 groups per account.

```bash
# Create account-level groups that map to IdP teams
databricks account groups create --json '{
  "displayName": "data-engineers",
  "entitlements": [
    {"value": "workspace-access"},
    {"value": "databricks-sql-access"}
  ]
}'

databricks account groups create --json '{
  "displayName": "data-analysts",
  "entitlements": [
    {"value": "workspace-access"},
    {"value": "databricks-sql-access"}
  ]
}'

databricks account groups create --json '{
  "displayName": "ml-engineers",
  "entitlements": [
    {"value": "workspace-access"},
    {"value": "databricks-sql-access"},
    {"value": "allow-cluster-create"}
  ]
}'
```

```python
# Assign groups to workspaces
from databricks.sdk import AccountClient

acct = AccountClient()

# Get workspace ID
workspaces = list(acct.workspaces.list())
prod_ws = next(ws for ws in workspaces if ws.workspace_name == "production")

# Assign group to workspace with permissions
acct.workspace_assignment.update(
    workspace_id=prod_ws.workspace_id,
    principal_id=group_id,
    permissions=["USER"],
)
```

### Step 2: Unity Catalog Privilege Hierarchy
```sql
-- Privilege model: CATALOG > SCHEMA > TABLE/VIEW/FUNCTION
-- USAGE grants must cascade from catalog to schema

-- Data Engineers: full ETL access
GRANT USAGE ON CATALOG analytics TO `data-engineers`;
GRANT CREATE SCHEMA ON CATALOG analytics TO `data-engineers`;
GRANT CREATE, MODIFY, SELECT ON SCHEMA analytics.bronze TO `data-engineers`;
GRANT CREATE, MODIFY, SELECT ON SCHEMA analytics.silver TO `data-engineers`;
GRANT SELECT ON SCHEMA analytics.gold TO `data-engineers`;

-- Data Analysts: read-only curated data
GRANT USAGE ON CATALOG analytics TO `data-analysts`;
GRANT SELECT ON SCHEMA analytics.gold TO `data-analysts`;

-- ML Engineers: full ML lifecycle
GRANT USAGE ON CATALOG analytics TO `ml-engineers`;
GRANT SELECT ON SCHEMA analytics.gold TO `ml-engineers`;
GRANT ALL PRIVILEGES ON SCHEMA analytics.ml_features TO `ml-engineers`;
GRANT ALL PRIVILEGES ON SCHEMA analytics.ml_models TO `ml-engineers`;

-- Service Principal: CI/CD automation
GRANT USAGE ON CATALOG analytics TO `cicd-service-principal`;
GRANT ALL PRIVILEGES ON CATALOG analytics TO `cicd-service-principal`;
```

### Step 3: Cluster Policies by Role
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Analyst policy: restrict to SQL warehouses and small clusters
analyst_policy = w.cluster_policies.create(
    name="analyst-compute-policy",
    definition="""{
        "cluster_type": {
            "type": "allowlist",
            "values": ["all-purpose"],
            "hidden": false
        },
        "autotermination_minutes": {
            "type": "range",
            "minValue": 10,
            "maxValue": 30,
            "defaultValue": 15
        },
        "num_workers": {
            "type": "range",
            "minValue": 0,
            "maxValue": 4
        },
        "node_type_id": {
            "type": "allowlist",
            "values": ["m5.xlarge", "m5.2xlarge"]
        },
        "spark_conf.spark.databricks.cluster.profile": {
            "type": "fixed",
            "value": "singleNode"
        }
    }""",
)

# Assign to analysts group
w.cluster_policies.set_permissions(
    cluster_policy_id=analyst_policy.policy_id,
    access_control_list=[{
        "group_name": "data-analysts",
        "all_permissions": [{"permission_level": "CAN_USE"}],
    }],
)
```

### Step 4: SQL Warehouse Permissions
```bash
# Grant warehouse access by group
databricks permissions update sql/warehouses/$WAREHOUSE_ID --json '[
  {"group_name": "data-analysts", "permission_level": "CAN_USE"},
  {"group_name": "data-engineers", "permission_level": "CAN_MANAGE"},
  {"group_name": "ml-engineers", "permission_level": "CAN_USE"}
]'
```

### Step 5: Row-Level Security and Column Masking
```sql
-- Row filter: analysts only see their department's data
CREATE OR REPLACE FUNCTION analytics.gold.dept_filter(dept STRING)
  RETURN IF(IS_ACCOUNT_GROUP_MEMBER('data-admins'), true,
            dept = current_user_department());

ALTER TABLE analytics.gold.sales
  SET ROW FILTER analytics.gold.dept_filter ON (department);

-- Column mask: hide email from non-engineers
CREATE OR REPLACE FUNCTION analytics.gold.mask_email(email STRING)
  RETURN IF(IS_ACCOUNT_GROUP_MEMBER('data-engineers'), email,
            REGEXP_REPLACE(email, '(.).*@', '$1***@'));

ALTER TABLE analytics.gold.customers
  ALTER COLUMN email SET MASK analytics.gold.mask_email;
```

### Step 6: Service Principal for Automation
```python
from databricks.sdk import AccountClient

acct = AccountClient()

# Create service principal
sp = acct.service_principals.create(
    display_name="cicd-pipeline",
    active=True,
)

# Generate OAuth secret
secret = acct.service_principal_secrets.create(
    service_principal_id=sp.id,
)
print(f"Client ID: {sp.application_id}")
print(f"Secret: {secret.secret}")  # Store securely — shown only once
```

### Step 7: Audit Access Patterns
```sql
-- Who accessed what in the last 7 days
SELECT event_time, user_identity.email AS actor,
       action_name, request_params
FROM system.access.audit
WHERE action_name LIKE '%Grant%' OR action_name LIKE '%Revoke%'
  AND event_date > current_date() - INTERVAL 7 DAYS
ORDER BY event_time DESC;

-- Excessive privilege detection
SELECT user_identity.email, action_name, COUNT(*) AS access_count
FROM system.access.audit
WHERE event_date > current_date() - INTERVAL 30 DAYS
  AND service_name = 'unityCatalog'
GROUP BY user_identity.email, action_name
HAVING COUNT(*) > 100
ORDER BY access_count DESC;
```

## Output
- Account-level groups provisioned via SCIM matching IdP teams
- Unity Catalog grants enforcing least-privilege across medallion layers
- Cluster policies restricting compute by role (analysts vs engineers)
- SQL warehouse permissions assigned per group
- Row-level security and column masking for PII protection
- Service principal for CI/CD with OAuth M2M
- Audit queries for ongoing compliance monitoring

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `PERMISSION_DENIED` on table | Missing `USAGE` on parent catalog/schema | Grant `USAGE` at each namespace level |
| SCIM sync fails | Expired bearer token | Regenerate account-level PAT or use OAuth |
| Can't create cluster | No matching cluster policy | Assign a policy to the user's group |
| Can't see SQL warehouse | Missing `CAN_USE` grant | Add warehouse permission for the group |
| Row filter too slow | Complex subquery in filter function | Materialize permissions in a small lookup table |

## Examples

### Verify Current Permissions
```sql
SHOW GRANTS ON CATALOG analytics;
SHOW GRANTS `data-analysts` ON SCHEMA analytics.gold;
SHOW GRANTS ON TABLE analytics.gold.sales;
```

### Permission Matrix Reference
| Role | Bronze | Silver | Gold | ML | Clusters | Warehouses |
|------|--------|--------|------|----|----------|------------|
| Data Engineer | Read/Write | Read/Write | Read | - | Create (policy) | Use/Manage |
| Data Analyst | - | - | Read | - | Single-node (policy) | Use |
| ML Engineer | - | Read | Read | Read/Write | Create (policy) | Use |
| Admin | Full | Full | Full | Full | Unrestricted | Manage |
| CI/CD SP | Full | Full | Full | Full | Manage | - |

## Resources
- [Unity Catalog Privileges](https://docs.databricks.com/aws/en/data-governance/unity-catalog/manage-privileges/)
- [SCIM Provisioning](https://docs.databricks.com/aws/en/admin/users-groups/scim/)
- [Cluster Policies](https://docs.databricks.com/aws/en/admin/clusters/policy-definition)
- [Row and Column Filters](https://docs.databricks.com/aws/en/data-governance/unity-catalog/row-and-column-filters)
