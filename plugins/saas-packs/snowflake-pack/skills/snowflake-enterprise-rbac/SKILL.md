---
name: snowflake-enterprise-rbac
description: |
  Configure Snowflake enterprise RBAC with system roles, custom role hierarchies,
  SSO/SCIM integration, and least-privilege access patterns.
  Use when implementing role-based access control, configuring SSO with SAML/OIDC,
  or setting up organization-level governance in Snowflake.
  Trigger with phrases like "snowflake RBAC", "snowflake roles",
  "snowflake SSO", "snowflake SCIM", "snowflake permissions", "snowflake access control".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Enterprise RBAC

## Overview

Configure enterprise-grade access control using Snowflake's system-defined roles, custom role hierarchies, SSO via SAML/OIDC, and SCIM for automated user provisioning.

## Snowflake System Roles

| Role | Purpose | Use For |
|------|---------|---------|
| ACCOUNTADMIN | Top-level admin | Billing, resource monitors, replication |
| SECURITYADMIN | Security management | Users, roles, grants, network policies |
| SYSADMIN | Object management | Databases, warehouses, schemas, tables |
| USERADMIN | User management | Create users and roles |
| PUBLIC | Default for all users | Minimal access, applied automatically |

**Best Practice:** Never use ACCOUNTADMIN as a default role. Create custom roles and grant them to SYSADMIN.

## Instructions

### Step 1: Design Custom Role Hierarchy

```sql
-- Functional roles (what people do)
CREATE ROLE DATA_ENGINEER;
CREATE ROLE DATA_ANALYST;
CREATE ROLE DATA_SCIENTIST;
CREATE ROLE BI_VIEWER;
CREATE ROLE APP_SERVICE;         -- Service accounts

-- Access roles (what they can access)
CREATE ROLE RAW_DATA_READER;
CREATE ROLE CURATED_DATA_READER;
CREATE ROLE CURATED_DATA_WRITER;
CREATE ROLE GOLD_DATA_READER;

-- Role hierarchy (bottom-up)
--   BI_VIEWER → GOLD_DATA_READER
--   DATA_ANALYST → CURATED_DATA_READER + GOLD_DATA_READER
--   DATA_SCIENTIST → DATA_ANALYST + RAW_DATA_READER
--   DATA_ENGINEER → all access roles
--   All custom roles → SYSADMIN

GRANT ROLE GOLD_DATA_READER TO ROLE BI_VIEWER;
GRANT ROLE CURATED_DATA_READER TO ROLE DATA_ANALYST;
GRANT ROLE GOLD_DATA_READER TO ROLE DATA_ANALYST;
GRANT ROLE DATA_ANALYST TO ROLE DATA_SCIENTIST;
GRANT ROLE RAW_DATA_READER TO ROLE DATA_SCIENTIST;
GRANT ROLE RAW_DATA_READER TO ROLE DATA_ENGINEER;
GRANT ROLE CURATED_DATA_READER TO ROLE DATA_ENGINEER;
GRANT ROLE CURATED_DATA_WRITER TO ROLE DATA_ENGINEER;
GRANT ROLE GOLD_DATA_READER TO ROLE DATA_ENGINEER;

-- All custom roles under SYSADMIN
GRANT ROLE DATA_ENGINEER TO ROLE SYSADMIN;
GRANT ROLE DATA_ANALYST TO ROLE SYSADMIN;
GRANT ROLE DATA_SCIENTIST TO ROLE SYSADMIN;
GRANT ROLE BI_VIEWER TO ROLE SYSADMIN;
GRANT ROLE APP_SERVICE TO ROLE SYSADMIN;
```

### Step 2: Grant Object Privileges

```sql
-- Access role: RAW_DATA_READER
GRANT USAGE ON DATABASE PROD_DW TO ROLE RAW_DATA_READER;
GRANT USAGE ON SCHEMA PROD_DW.BRONZE TO ROLE RAW_DATA_READER;
GRANT SELECT ON ALL TABLES IN SCHEMA PROD_DW.BRONZE TO ROLE RAW_DATA_READER;
GRANT SELECT ON FUTURE TABLES IN SCHEMA PROD_DW.BRONZE TO ROLE RAW_DATA_READER;

-- Access role: CURATED_DATA_READER
GRANT USAGE ON DATABASE PROD_DW TO ROLE CURATED_DATA_READER;
GRANT USAGE ON SCHEMA PROD_DW.SILVER TO ROLE CURATED_DATA_READER;
GRANT SELECT ON ALL TABLES IN SCHEMA PROD_DW.SILVER TO ROLE CURATED_DATA_READER;
GRANT SELECT ON FUTURE TABLES IN SCHEMA PROD_DW.SILVER TO ROLE CURATED_DATA_READER;

-- Access role: CURATED_DATA_WRITER
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA PROD_DW.SILVER TO ROLE CURATED_DATA_WRITER;
GRANT INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA PROD_DW.SILVER TO ROLE CURATED_DATA_WRITER;

-- Access role: GOLD_DATA_READER
GRANT USAGE ON DATABASE PROD_DW TO ROLE GOLD_DATA_READER;
GRANT USAGE ON SCHEMA PROD_DW.GOLD TO ROLE GOLD_DATA_READER;
GRANT SELECT ON ALL TABLES IN SCHEMA PROD_DW.GOLD TO ROLE GOLD_DATA_READER;
GRANT SELECT ON FUTURE TABLES IN SCHEMA PROD_DW.GOLD TO ROLE GOLD_DATA_READER;

-- Warehouse grants (functional roles)
GRANT USAGE ON WAREHOUSE ETL_WH TO ROLE DATA_ENGINEER;
GRANT USAGE ON WAREHOUSE ANALYTICS_WH TO ROLE DATA_ANALYST;
GRANT USAGE ON WAREHOUSE ANALYTICS_WH TO ROLE DATA_SCIENTIST;
GRANT USAGE ON WAREHOUSE DASHBOARD_WH TO ROLE BI_VIEWER;
```

### Step 3: Configure SSO with SAML

```sql
-- Create SAML security integration
CREATE OR REPLACE SECURITY INTEGRATION saml_sso
  TYPE = SAML2
  ENABLED = TRUE
  SAML2_ISSUER = 'https://idp.company.com/saml/metadata'
  SAML2_SSO_URL = 'https://idp.company.com/saml/sso'
  SAML2_PROVIDER = 'OKTA'        -- Or 'ADFS', 'CUSTOM'
  SAML2_X509_CERT = '-----BEGIN CERTIFICATE-----
MIIBIj...
-----END CERTIFICATE-----'
  SAML2_SP_INITIATED_LOGIN_PAGE_LABEL = 'Company SSO'
  SAML2_ENABLE_SP_INITIATED = TRUE
  SAML2_SNOWFLAKE_ACS_URL = 'https://myorg-myaccount.snowflakecomputing.com/fed/login'
  SAML2_SNOWFLAKE_ISSUER_URL = 'https://myorg-myaccount.snowflakecomputing.com';

-- Map IdP groups to Snowflake roles (done in IdP, not SQL)
-- Okta: Group "Engineering" → Snowflake role "DATA_ENGINEER"
-- Okta: Group "Analytics" → Snowflake role "DATA_ANALYST"
```

### Step 4: Configure SCIM for Automated User Provisioning

```sql
-- Create SCIM integration (users/roles synced from IdP automatically)
CREATE OR REPLACE SECURITY INTEGRATION scim_provisioning
  TYPE = SCIM
  SCIM_CLIENT = 'OKTA'           -- Or 'AZURE', 'GENERIC'
  RUN_AS_ROLE = 'SECURITYADMIN';

-- Get SCIM endpoint and token for IdP configuration
SELECT SYSTEM$GENERATE_SCIM_ACCESS_TOKEN('scim_provisioning');

-- SCIM auto-creates users and assigns roles based on IdP groups
-- No manual user creation needed after SCIM is configured
```

### Step 5: Audit Role Grants

```sql
-- All current role grants
SELECT grantee_name, role,
       granted_by, created_on
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS
WHERE deleted_on IS NULL
ORDER BY grantee_name;

-- Users with ACCOUNTADMIN (should be minimal)
SELECT grantee_name, role, granted_by
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS
WHERE role = 'ACCOUNTADMIN' AND deleted_on IS NULL;

-- Unused privileges (granted but never used)
SELECT DISTINCT granted_on, name, privilege, grantee_name
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES gtr
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY ah
  ON gtr.name = ah.direct_objects_accessed[0]:objectName
WHERE ah.query_id IS NULL
  AND gtr.deleted_on IS NULL
  AND gtr.granted_on = 'TABLE';
```

## RBAC Checklist

- [ ] No human user has ACCOUNTADMIN as default role
- [ ] Custom roles follow functional + access role pattern
- [ ] All custom roles roll up to SYSADMIN
- [ ] `GRANT ... ON FUTURE` used for new objects
- [ ] SSO configured with IdP group-to-role mapping
- [ ] SCIM enabled for automated provisioning/deprovisioning
- [ ] Quarterly audit of role grants and unused privileges
- [ ] Service accounts use key pair auth with dedicated roles

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| SSO login fails | Wrong SAML config | Verify ACS URL and certificate |
| Role not inherited | Missing role grant | Check hierarchy with `SHOW GRANTS OF ROLE x` |
| SCIM sync fails | Token expired | Regenerate SCIM access token |
| Future grants not applying | Schema not included | Add `ON FUTURE` grants per schema |

## Resources

- [Access Control Overview](https://docs.snowflake.com/en/user-guide/security-access-control-overview)
- [Access Control Best Practices](https://docs.snowflake.com/en/user-guide/security-access-control-considerations)
- [SAML SSO](https://docs.snowflake.com/en/user-guide/admin-security-fed-auth-use)
- [SCIM Provisioning](https://docs.snowflake.com/en/user-guide/admin-security-fed-auth-use)

## Next Steps

For major platform migrations, see `snowflake-migration-deep-dive`.
