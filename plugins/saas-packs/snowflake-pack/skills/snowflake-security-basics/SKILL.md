---
name: snowflake-security-basics
description: |
  Apply Snowflake security best practices: network policies, key rotation,
  MFA, encryption, and least-privilege access.
  Use when securing Snowflake access, implementing network policies,
  or auditing security configuration.
  Trigger with phrases like "snowflake security", "snowflake network policy",
  "secure snowflake", "snowflake MFA", "snowflake encryption".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Security Basics

## Overview

Security best practices for Snowflake: network policies, key pair rotation, MFA, secret management, and least-privilege roles.

## Prerequisites

- SECURITYADMIN or ACCOUNTADMIN role access
- Understanding of network CIDR notation
- Secret management solution (Vault, AWS Secrets Manager, etc.)

## Instructions

### Step 1: Create Network Policies

```sql
-- Restrict access to known IP ranges
CREATE OR REPLACE NETWORK POLICY corporate_policy
  ALLOWED_IP_LIST = (
    '203.0.113.0/24',        -- Corporate office
    '198.51.100.0/24',       -- VPN range
    '10.0.0.0/8'             -- Internal network
  )
  BLOCKED_IP_LIST = (
    '203.0.113.99'           -- Block specific IP
  );

-- Apply to entire account
ALTER ACCOUNT SET NETWORK_POLICY = corporate_policy;

-- Or apply to specific user (service account)
ALTER USER svc_etl SET NETWORK_POLICY = corporate_policy;

-- Verify current policy
SELECT * FROM TABLE(INFORMATION_SCHEMA.POLICY_REFERENCES(POLICY_NAME => 'corporate_policy'));
```

### Step 2: Configure Key Pair Rotation

```bash
#!/bin/bash
# rotate-snowflake-keys.sh

# Generate new key pair
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key_new.p8 -nocrypt
openssl rsa -in rsa_key_new.p8 -pubout -out rsa_key_new.pub

# Extract public key (remove headers and newlines)
PUB_KEY=$(grep -v "BEGIN\|END" rsa_key_new.pub | tr -d '\n')

echo "Run in Snowflake:"
echo "ALTER USER svc_etl SET RSA_PUBLIC_KEY_2 = '${PUB_KEY}';"
echo ""
echo "After verifying new key works:"
echo "ALTER USER svc_etl UNSET RSA_PUBLIC_KEY;"
echo "ALTER USER svc_etl SET RSA_PUBLIC_KEY = '${PUB_KEY}';"
echo "ALTER USER svc_etl UNSET RSA_PUBLIC_KEY_2;"
```

```sql
-- Snowflake supports two active public keys for zero-downtime rotation
-- Step 1: Set new key as RSA_PUBLIC_KEY_2
ALTER USER svc_etl SET RSA_PUBLIC_KEY_2 = 'MIIBIj...new_key...';

-- Step 2: Update application to use new private key
-- Step 3: After verification, promote and clean up
ALTER USER svc_etl SET RSA_PUBLIC_KEY = 'MIIBIj...new_key...';
ALTER USER svc_etl UNSET RSA_PUBLIC_KEY_2;
```

### Step 3: Enable MFA

```sql
-- Enforce MFA via authentication policy
CREATE OR REPLACE AUTHENTICATION POLICY require_mfa
  MFA_AUTHENTICATION_METHODS = ('TOTP')
  CLIENT_TYPES = ('SNOWFLAKE_UI', 'SNOWSQL')
  SECURITY_INTEGRATIONS = ();

-- Apply to human users (not service accounts)
ALTER USER analyst_user SET AUTHENTICATION POLICY = require_mfa;

-- Check MFA enrollment status
SELECT name, has_mfa, login_name, disabled
FROM SNOWFLAKE.ACCOUNT_USAGE.USERS
WHERE has_mfa = 'false' AND disabled = 'false';
```

### Step 4: Secret Management for Applications

```typescript
// src/snowflake/secrets.ts

// AWS Secrets Manager
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

async function getSnowflakeCredentials(): Promise<{
  account: string;
  username: string;
  privateKey: string;
}> {
  const client = new SecretsManagerClient({ region: 'us-east-1' });
  const response = await client.send(
    new GetSecretValueCommand({ SecretId: 'snowflake/production/credentials' })
  );
  return JSON.parse(response.SecretString!);
}

// GCP Secret Manager
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

async function getSnowflakeKey(): Promise<string> {
  const client = new SecretManagerServiceClient();
  const [version] = await client.accessSecretVersion({
    name: 'projects/my-project/secrets/snowflake-private-key/versions/latest',
  });
  return version.payload!.data!.toString();
}
```

### Step 5: Audit Access

```sql
-- Recent login activity
SELECT user_name, client_ip, reported_client_type,
       first_authentication_factor, second_authentication_factor,
       is_success, error_message, event_timestamp
FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY
WHERE event_timestamp >= DATEADD(days, -7, CURRENT_TIMESTAMP())
ORDER BY event_timestamp DESC;

-- Privilege grants audit
SELECT created_on, privilege, granted_on, name, granted_to, grantee_name, granted_by
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
WHERE deleted_on IS NULL
  AND granted_on = 'TABLE'
  AND privilege = 'OWNERSHIP'
ORDER BY created_on DESC;

-- Detect unused roles (no logins in 30 days)
SELECT r.name AS role_name
FROM SNOWFLAKE.ACCOUNT_USAGE.ROLES r
LEFT JOIN (
  SELECT DISTINCT role_name
  FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY
  WHERE event_timestamp >= DATEADD(days, -30, CURRENT_TIMESTAMP())
) l ON r.name = l.role_name
WHERE l.role_name IS NULL AND r.deleted_on IS NULL;
```

## Security Checklist

- [ ] Network policy restricts access to known IPs
- [ ] Service accounts use key pair auth (not passwords)
- [ ] Key rotation automated (90-day cycle minimum)
- [ ] MFA enabled for all human users
- [ ] Credentials stored in secret manager (not env files in prod)
- [ ] `.env`, `rsa_key.p8` in `.gitignore`
- [ ] Audit LOGIN_HISTORY weekly for anomalies
- [ ] Unused roles/users disabled

## Error Handling

| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Failed logins spike | `LOGIN_HISTORY WHERE is_success = 'NO'` | Check for brute force, lock user |
| Key not rotated | `DESC USER; check RSA_PUBLIC_KEY` | Run rotation script |
| No network policy | `SHOW PARAMETERS LIKE 'NETWORK_POLICY'` | Create and apply policy |
| Excessive privileges | `GRANTS_TO_ROLES` audit | Revoke unnecessary grants |

## Resources

- [Network Policies](https://docs.snowflake.com/en/user-guide/network-policies)
- [Key Pair Auth & Rotation](https://docs.snowflake.com/en/user-guide/key-pair-auth)
- [MFA](https://docs.snowflake.com/en/user-guide/security-mfa)
- [Authentication Policies](https://docs.snowflake.com/en/user-guide/authentication-policies)

## Next Steps

For production deployment, see `snowflake-prod-checklist`.
