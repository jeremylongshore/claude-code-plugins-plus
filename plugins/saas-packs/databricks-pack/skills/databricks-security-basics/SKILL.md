---
name: databricks-security-basics
description: |
  Apply Databricks security best practices for secrets and access control.
  Use when securing API tokens, implementing least privilege access,
  or auditing Databricks security configuration.
  Trigger with phrases like "databricks security", "databricks secrets",
  "secure databricks", "databricks token security", "databricks scopes".
allowed-tools: Read, Write, Grep, Bash(databricks:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, databricks, api, security, audit]

---
# Databricks Security Basics

## Overview
Implement Databricks security: secret scopes for credential storage, token rotation, least-privilege access via Unity Catalog grants, and security auditing via system tables. Secrets API uses `PUT /api/2.0/secrets/put` and values are automatically redacted in notebook output.

## Prerequisites
- Databricks CLI configured
- Workspace admin access (for secret scope creation)
- Unity Catalog enabled

## Instructions

### Step 1: Create and Manage Secret Scopes
```bash
# Create a Databricks-backed secret scope
databricks secrets create-scope my-app-secrets

# Create Azure Key Vault-backed scope (Azure only)
databricks secrets create-scope azure-kv \
  --scope-backend-type AZURE_KEYVAULT \
  --resource-id "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/<vault>" \
  --dns-name "https://<vault>.vault.azure.net/"

# List all scopes
databricks secrets list-scopes
```

### Step 2: Store and Access Secrets
```bash
# Store a secret (prompts for value interactively)
databricks secrets put-secret my-app-secrets db-password

# Store from CLI argument
databricks secrets put-secret my-app-secrets api-key --string-value "sk_live_abc123"

# List secrets (values always hidden)
databricks secrets list-secrets my-app-secrets
```

```python
# Access secrets in notebooks and jobs — values auto-redacted in output
db_password = dbutils.secrets.get(scope="my-app-secrets", key="db-password")
api_key = dbutils.secrets.get(scope="my-app-secrets", key="api-key")

# Printing shows [REDACTED] — Databricks prevents accidental exposure
print(f"Password: {db_password}")  # Output: Password: [REDACTED]

# Use in JDBC connections
jdbc_url = f"jdbc:postgresql://host:5432/db?user=app&password={db_password}"
df = spark.read.format("jdbc").option("url", jdbc_url).load()
```

### Step 3: Secret Scope Access Control
```bash
# Grant READ to a user
databricks secrets put-acl my-app-secrets user@company.com READ

# Grant MANAGE to a group (full control)
databricks secrets put-acl my-app-secrets data-engineers MANAGE

# List ACLs for a scope
databricks secrets list-acls my-app-secrets
```

### Step 4: Token Audit and Rotation
```python
from databricks.sdk import WorkspaceClient
from datetime import datetime

w = WorkspaceClient()

def audit_tokens() -> list[dict]:
    """Audit all PATs for expiration and rotation needs."""
    findings = []
    for token in w.tokens.list():
        created = datetime.fromtimestamp(token.creation_time / 1000)
        expiry = datetime.fromtimestamp(token.expiry_time / 1000) if token.expiry_time else None

        finding = {
            "token_id": token.token_id,
            "comment": token.comment,
            "created": created.isoformat(),
            "expires": expiry.isoformat() if expiry else "NEVER",
            "days_until_expiry": (expiry - datetime.now()).days if expiry else None,
        }

        if not expiry:
            finding["risk"] = "HIGH — no expiration set"
        elif (expiry - datetime.now()).days < 30:
            finding["risk"] = "MEDIUM — expires within 30 days"
        else:
            finding["risk"] = "LOW"

        findings.append(finding)
    return findings

def rotate_token(old_token_id: str, lifetime_days: int = 90) -> str:
    """Create new token and delete old one."""
    new = w.tokens.create(
        comment=f"Rotated {datetime.now().isoformat()}",
        lifetime_seconds=lifetime_days * 86400,
    )
    w.tokens.delete(token_id=old_token_id)
    return new.token_value  # Store this immediately — shown only once

for finding in audit_tokens():
    print(f"{finding['comment']}: {finding['risk']} (expires {finding['expires']})")
```

### Step 5: Unity Catalog Least Privilege
```sql
-- Grant minimal access per role
-- Engineers: read/write bronze+silver, read gold
GRANT USAGE ON CATALOG analytics TO `data-engineers`;
GRANT CREATE, MODIFY, SELECT ON SCHEMA analytics.bronze TO `data-engineers`;
GRANT CREATE, MODIFY, SELECT ON SCHEMA analytics.silver TO `data-engineers`;
GRANT SELECT ON SCHEMA analytics.gold TO `data-engineers`;

-- Analysts: read-only on curated gold tables
GRANT USAGE ON CATALOG analytics TO `data-analysts`;
GRANT SELECT ON SCHEMA analytics.gold TO `data-analysts`;

-- Audit current grants
SHOW GRANTS ON SCHEMA analytics.gold;
SHOW GRANTS `data-analysts` ON CATALOG analytics;
```

### Step 6: Column-Level Masking and Row-Level Security
```sql
-- Mask email for non-privileged users
CREATE OR REPLACE FUNCTION analytics.gold.mask_email(email STRING)
  RETURN IF(IS_ACCOUNT_GROUP_MEMBER('data-engineers'), email,
            REGEXP_REPLACE(email, '(.).*@', '$1***@'));

ALTER TABLE analytics.gold.customers ALTER COLUMN email
  SET MASK analytics.gold.mask_email;

-- Row-level security: restrict by department
CREATE OR REPLACE FUNCTION analytics.gold.dept_filter(dept STRING)
  RETURN IF(IS_ACCOUNT_GROUP_MEMBER('data-admins'), true,
            dept = session_user_department());

ALTER TABLE analytics.gold.sales
  SET ROW FILTER analytics.gold.dept_filter ON (department);
```

### Step 7: Security Audit via System Tables
```sql
-- Recent permission changes (last 7 days)
SELECT event_time, user_identity.email AS actor,
       action_name, request_params
FROM system.access.audit
WHERE action_name IN ('grantPermission', 'revokePermission',
                       'changeJobPermissions', 'changeClusterPermissions')
  AND event_date >= current_date() - 7
ORDER BY event_time DESC;

-- Failed authentication attempts
SELECT event_time, user_identity.email, source_ip_address,
       response.error_message
FROM system.access.audit
WHERE action_name = 'tokenLogin' AND response.status_code != 200
  AND event_date >= current_date() - 7
ORDER BY event_time DESC;
```

## Output
- Secret scopes with ACL-based access control
- Token audit report identifying expiring/non-expiring tokens
- Unity Catalog grants enforcing least privilege by role
- Column masking and row-level security on sensitive tables
- Audit queries for ongoing security monitoring

## Error Handling
| Security Issue | Detection | Mitigation |
|---------------|-----------|------------|
| Token without expiry | `audit_tokens()` shows `NEVER` | Set 90-day max lifetime via rotation |
| Hardcoded credentials | Code review / secret scanning | Move to Databricks Secret Scopes |
| Over-privileged service principal | `SHOW GRANTS` audit | Reduce to minimum required privileges |
| Shared PATs across users | Audit log `tokenLogin` events | Individual service principals per app |

## Examples

### Security Checklist
- [ ] All PATs have expiration dates (max 90 days)
- [ ] Secrets stored in Databricks Secret Scopes, not env vars
- [ ] No hardcoded credentials in notebooks or repos
- [ ] Service principals for all automated workflows
- [ ] Unity Catalog enforcing least privilege
- [ ] Column masking on PII fields
- [ ] IP access lists configured (Admin Console > Workspace Settings)
- [ ] Cluster policies restrict instance types and auto-termination
- [ ] Audit log queries scheduled for weekly review

## Resources
- [Secret Management](https://docs.databricks.com/aws/en/security/secrets/)
- [Unity Catalog Security](https://docs.databricks.com/aws/en/data-governance/unity-catalog/)
- [Row and Column Filters](https://docs.databricks.com/aws/en/data-governance/unity-catalog/row-and-column-filters)
- [Audit Logs](https://docs.databricks.com/aws/en/admin/system-tables/audit-logs)

## Next Steps
For production deployment, see `databricks-prod-checklist`.
