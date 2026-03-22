---
name: salesforce-security-basics
description: |
  Apply Salesforce security best practices for Connected Apps, OAuth, and field-level security.
  Use when securing API credentials, implementing least privilege access,
  or auditing Salesforce security configuration.
  Trigger with phrases like "salesforce security", "salesforce secrets",
  "secure salesforce", "salesforce connected app security", "salesforce FLS".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Security Basics

## Overview
Security best practices for Salesforce integrations: Connected App configuration, OAuth scope management, field-level security, and credential rotation.

## Prerequisites
- Salesforce org with System Administrator access
- Connected App created in Setup > App Manager
- Understanding of Salesforce security model (Profile, Permission Set, OWD)

## Instructions

### Step 1: Secure Connected App Configuration
```
Setup > App Manager > New Connected App:

1. Enable OAuth Settings
2. Callback URL: https://yourapp.com/oauth/callback (NOT localhost in prod)
3. Selected OAuth Scopes — USE MINIMUM REQUIRED:
   - "Manage user data via APIs (api)" — for REST/SOQL access
   - "Perform requests at any time (refresh_token, offline_access)" — for refresh tokens
   - DO NOT add "Full access (full)" unless absolutely necessary

4. Require Proof Key for Code Exchange (PKCE): Enable for public clients
5. Require Secret for Web Server Flow: Enable
6. IP Relaxation: "Enforce IP restrictions" (not "Relax IP restrictions")
```

### Step 2: Credential Storage

```bash
# .env (NEVER commit to git)
SF_LOGIN_URL=https://login.salesforce.com
SF_USERNAME=integration-user@yourcompany.com
SF_PASSWORD=<from-vault>
SF_SECURITY_TOKEN=<from-vault>
SF_CLIENT_ID=<connected-app-consumer-key>
SF_CLIENT_SECRET=<connected-app-consumer-secret>

# .gitignore — ALWAYS include
.env
.env.local
.env.*.local
server.key    # JWT private key
*.pem
*.key
```

### Step 3: Use a Dedicated Integration User
```
Create a dedicated Salesforce user for API access:

1. Profile: Create "API Integration" profile (clone from Standard User)
   - Login Hours: restrict to expected operating hours
   - Login IP Ranges: restrict to your server IPs
   - Object permissions: ONLY objects your integration needs

2. Permission Set: "Integration API Access"
   - Object: Account — Read, Create, Edit (no Delete)
   - Object: Contact — Read, Create, Edit (no Delete)
   - Field-Level Security: only expose fields the integration reads/writes

3. NEVER use a System Administrator user for integrations
```

### Step 4: Field-Level Security (FLS) Enforcement

```typescript
// Always check FLS before operations — especially for managed packages
const conn = await getConnection();
const meta = await conn.sobject('Account').describe();

// Check if field is accessible (readable)
const industryField = meta.fields.find(f => f.name === 'Industry');
if (!industryField?.accessible) {
  throw new Error('Industry field is not accessible — check FLS');
}

// Check if field is updateable (writable)
if (!industryField?.updateable) {
  console.warn('Industry field is read-only for this user');
}

// Check which fields the current user can actually see
const accessibleFields = meta.fields
  .filter(f => f.accessible)
  .map(f => f.name);
console.log('Accessible fields:', accessibleFields.length);
```

### Step 5: Security Token Rotation

```bash
# Salesforce security tokens auto-reset when password changes
# Rotation procedure:
# 1. Setup > My Personal Information > Reset My Security Token
# 2. New token is emailed to the user
# 3. Update SF_SECURITY_TOKEN in your vault/env
# 4. Verify connection works with new token
# 5. For JWT: rotate the certificate in the Connected App

# Automate rotation check
sf org display --target-org integration-user --json | jq '.result.accessToken'
```

### Step 6: Audit Logging

```typescript
// Query Setup Audit Trail for security events
const auditTrail = await conn.query(`
  SELECT CreatedDate, CreatedBy.Username, Action, Section, Display
  FROM SetupAuditTrail
  WHERE CreatedDate >= LAST_N_DAYS:7
    AND (Section = 'Connected Apps' OR Section = 'Users' OR Section = 'Profiles')
  ORDER BY CreatedDate DESC
  LIMIT 50
`);

for (const entry of auditTrail.records) {
  console.log(`${entry.CreatedDate} | ${entry.CreatedBy?.Username} | ${entry.Action} | ${entry.Display}`);
}
```

### Security Checklist
- [ ] Connected App uses minimum OAuth scopes (not `full`)
- [ ] Dedicated integration user (not admin)
- [ ] IP restrictions on Connected App and user profile
- [ ] Credentials in vault/env vars, never in code
- [ ] `.env` and `*.key` files in `.gitignore`
- [ ] Field-Level Security restricts sensitive fields
- [ ] Security token rotated regularly
- [ ] Setup Audit Trail monitored
- [ ] PKCE enabled for public clients

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Exposed credentials in git | `git log -p --all -S 'SF_PASSWORD'` | Rotate immediately, use git-secrets |
| Overprivileged user | Check profile permissions | Create restricted integration profile |
| Missing FLS | Describe call shows `accessible: false` | Update Permission Set |
| IP not whitelisted | `LOGIN_MUST_USE_SECURITY_TOKEN` | Add IP to login IP ranges |

## Resources
- [Salesforce Security Guide](https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/)
- [Connected Apps](https://help.salesforce.com/s/articleView?id=sf.connected_app_overview.htm)
- [Field-Level Security](https://help.salesforce.com/s/articleView?id=sf.admin_fls.htm)
- [Setup Audit Trail](https://help.salesforce.com/s/articleView?id=sf.admin_monitorsetup.htm)

## Next Steps
For production deployment, see `salesforce-prod-checklist`.
