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
---
# Databricks Security Basics

## Overview
Security best practices for Databricks tokens, secrets, and access control.

## Prerequisites
- Databricks CLI installed
- Workspace admin access (for secrets management)
- Understanding of Unity Catalog

## Instructions

### Step 1: Configure Secret Scopes
```bash
# Create a secret scope (Databricks-backed)
databricks secrets create-scope my-app-secrets

# Create a secret scope (Azure Key Vault-backed)
databricks secrets create-scope azure-secrets \
  --scope-backend-type AZURE_KEYVAULT \
  --resource-id "/subscriptions/.../vaults/my-vault" \
  --dns-name "https://my-vault.vault.azure.net/"

# List scopes
databricks secrets list-scopes
```

### Step 2: Store Secrets
```bash
# Store a secret
databricks secrets put-secret my-app-secrets db-password

# Store from file (for multi-line secrets)
databricks secrets put-secret my-app-secrets api-key --string-value "sk_live_..."

# List secrets in scope (values are hidden)
databricks secrets list-secrets my-app-secrets
```

### Step 3: Access Secrets in Code
```python
# In notebooks and jobs
db_password = dbutils.secrets.get(scope="my-app-secrets", key="db-password")
api_key = dbutils.secrets.get(scope="my-app-secrets", key="api-key")

# Secrets are redacted in logs
print(f"Password: {db_password}")  # Shows [REDACTED]

# Use in connection strings
jdbc_url = f"jdbc:postgresql://host:5432/db?user=app&password={db_password}"  # 5432: PostgreSQL port
```

### Step 4: Secret Scope ACLs
```bash
# Grant read access to a user
databricks secrets put-acl my-app-secrets user@company.com READ

# Grant manage access to a group
databricks secrets put-acl my-app-secrets data-engineers MANAGE

# List ACLs
databricks secrets list-acls my-app-secrets
```

### Step 5: Token Management
```python
# src/databricks/tokens.py
from databricks.sdk import WorkspaceClient
from datetime import datetime, timedelta

def audit_tokens(w: WorkspaceClient) -> list[dict]:
    """Audit all tokens in workspace for security review."""
    tokens = list(w.tokens.list())

    token_audit = []
    for token in tokens:
        created = datetime.fromtimestamp(token.creation_time / 1000)  # 1000: 1 second in ms
        expiry = datetime.fromtimestamp(token.expiry_time / 1000) if token.expiry_time else None  # 1 second in ms

        token_audit.append({
            "token_id": token.token_id,
            "comment": token.comment,
            "created": created,
            "expires": expiry,
            "days_until_expiry": (expiry - datetime.now()).days if expiry else None,
            "is_expired": expiry < datetime.now() if expiry else False,
            "needs_rotation": expiry and (expiry - datetime.now()).days < 30 if expiry else True,
        })

    return token_audit

def rotate_token(w: WorkspaceClient, old_token_id: str, lifetime_days: int = 90) -> str:
    """Rotate a token by creating new and deleting old."""
    # Create new token
    new_token = w.tokens.create(
        comment=f"Rotated token - {datetime.now().isoformat()}",
        lifetime_seconds=lifetime_days * 24 * 60 * 60,
    )

    # Delete old token
    w.tokens.delete(token_id=old_token_id)

    return new_token.token_value
```

### Step 6: Implement Least Privilege
```python
# Environment-specific permissions
permission_matrix = {
    "development": {
        "cluster_access": "CAN_ATTACH_TO",
        "job_access": "CAN_MANAGE_RUN",
        "notebook_access": "CAN_EDIT",
    },
    "staging": {
        "cluster_access": "CAN_RESTART",
        "job_access": "CAN_MANAGE_RUN",
        "notebook_access": "CAN_READ",
    },
    "production": {
        "cluster_access": "CAN_ATTACH_TO",  # Read-only
        "job_access": "CAN_VIEW",
        "notebook_access": "CAN_READ",
    },
}

def apply_environment_permissions(
    w: WorkspaceClient,
    environment: str,
    user_email: str,
    resource_type: str,
    resource_id: str,
) -> None:
    """Apply environment-appropriate permissions."""
    perms = permission_matrix[environment]

    if resource_type == "cluster":
        w.permissions.update(
            object_type="clusters",
            object_id=resource_id,
            access_control_list=[{
                "user_name": user_email,
                "permission_level": perms["cluster_access"],
            }]
        )
```

## Output
- Secret scopes configured
- Secrets stored securely
- Token rotation procedures
- Least privilege access

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Exposed token | Audit logs | Immediate rotation |
| Excessive scopes | Permission audit | Reduce to minimum |
| No token expiry | Token audit | Set 90-day max lifetime |
| Shared credentials | Usage patterns | Individual service principals |

## Examples

### Security Audit Script
```python
from databricks.sdk import WorkspaceClient

def security_audit(w: WorkspaceClient) -> dict:
    """Run comprehensive security audit."""
    audit_results = {
        "tokens": [],
        "secrets": [],
        "permissions": [],
        "findings": [],
    }

    # Audit tokens
    for token in w.tokens.list():
        if not token.expiry_time:
            audit_results["findings"].append({
                "severity": "HIGH",
                "type": "token_no_expiry",
                "detail": f"Token {token.comment} has no expiration",
            })

    # Audit secret scopes
    for scope in w.secrets.list_scopes():
        acls = list(w.secrets.list_acls(scope=scope.name))
        if not acls:
            audit_results["findings"].append({
                "severity": "MEDIUM",
                "type": "scope_no_acl",
                "detail": f"Scope {scope.name} has no ACLs",
            })

    return audit_results
```

### Service Principal Setup (Azure)
```bash
# Create service principal in Azure AD
az ad sp create-for-rbac --name databricks-cicd

# Add to Databricks workspace (Admin Console or SCIM API)
databricks service-principals create \
  --json '{
    "display_name": "CI/CD Pipeline",
    "application_id": "your-azure-app-id"
  }'

# Grant permissions
databricks permissions update jobs --job-id 123 --json '{
  "access_control_list": [{
    "service_principal_name": "your-azure-app-id",
    "permission_level": "CAN_MANAGE"
  }]
}'
```

### Unity Catalog Security
```sql
-- Create secure group
CREATE GROUP IF NOT EXISTS `data-scientists`;

-- Grant schema access (not table-level for simplicity)
GRANT USAGE ON CATALOG main TO `data-scientists`;
GRANT USAGE ON SCHEMA main.analytics TO `data-scientists`;
GRANT SELECT ON SCHEMA main.analytics TO `data-scientists`;

-- Audit grants
SHOW GRANTS ON SCHEMA main.analytics;

-- Row-level security
ALTER TABLE main.analytics.customers
SET ROW FILTER customer_region_filter ON (region);
```

### Security Checklist
- [ ] Personal access tokens have expiration dates
- [ ] Secrets stored in Databricks Secret Scopes
- [ ] No hardcoded credentials in notebooks
- [ ] Service principals for automation
- [ ] Unity Catalog for data governance
- [ ] Audit logging enabled
- [ ] Network security (IP access lists)
- [ ] Cluster policies enforced

## Resources
- [Databricks Security Guide](https://docs.databricks.com/security/index.html)
- [Secret Management](https://docs.databricks.com/security/secrets/index.html)
- [Unity Catalog Security](https://docs.databricks.com/data-governance/unity-catalog/index.html)
- [Token Management](https://docs.databricks.com/dev-tools/auth.html)

## Next Steps
For production deployment, see `databricks-prod-checklist`.