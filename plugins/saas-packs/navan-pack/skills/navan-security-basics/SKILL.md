---
name: navan-security-basics
description: 'Secure Navan API credentials with OAuth 2.0 best practices, SSO/SAML,
  and SCIM provisioning.

  Use when hardening a Navan integration, rotating credentials, or configuring identity
  provider SSO.

  Trigger with "navan security", "navan sso", "navan credentials", "navan scim".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Security Basics

## Overview
Navan holds SOC 1 Type II, SOC 2 Type II, ISO 27001, PCI DSS Level 1, GDPR, CSA, and VSA certifications. Infrastructure runs on AWS with TLS encryption in transit and AES encryption at rest via KMS. Annual penetration testing and OWASP compliance are standard. This skill covers the developer's responsibility: securing OAuth 2.0 credentials, configuring SSO through supported identity providers, setting up SCIM for automated user provisioning, and establishing rotation schedules.

## Prerequisites
- Navan admin account with API credential management permissions
- Access to Admin > Travel admin > Settings > Integrations for OAuth app creation
- Identity provider admin access (Okta, Azure AD, or Google Workspace) for SSO/SCIM setup
- Node.js 18+ or Python 3.8+ for credential management scripts

## Instructions

### Step 1: Secure OAuth 2.0 Credential Storage
```bash
# Create .env file — NEVER commit this
cat > .env << 'EOF'
NAVAN_CLIENT_ID=your-client-id
NAVAN_CLIENT_SECRET=your-client-secret
NAVAN_TOKEN_URL=https://api.navan.com/ta-auth/oauth/token
EOF

# Ensure .env is gitignored
echo '.env' >> .gitignore
echo '.env.*' >> .gitignore
```

```typescript
// Load credentials from environment only — never hardcode
import { config } from 'dotenv';
config();

async function getAccessToken(): Promise<string> {
  const { NAVAN_CLIENT_ID, NAVAN_CLIENT_SECRET, NAVAN_TOKEN_URL } = process.env;

  if (!NAVAN_CLIENT_ID || !NAVAN_CLIENT_SECRET) {
    throw new Error('Missing NAVAN_CLIENT_ID or NAVAN_CLIENT_SECRET in environment');
  }

  const response = await fetch(NAVAN_TOKEN_URL!, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: NAVAN_CLIENT_ID,
      client_secret: NAVAN_CLIENT_SECRET
    })
  });

  if (!response.ok) {
    throw new Error(`Token exchange failed: HTTP ${response.status}`);
  }

  const { access_token, expires_in } = await response.json();
  console.log(`Token acquired — expires in ${expires_in}s`);
  return access_token;
}
```

### Step 2: Implement Credential Rotation
```typescript
// Rotation script — run on a schedule (e.g., monthly cron)
async function rotateCredentials(adminToken: string): Promise<void> {
  // Step 1: Create new credentials
  const createRes = await fetch('https://api.navan.com/v1/api-credentials', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${adminToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ name: `rotation-${new Date().toISOString().slice(0, 10)}` })
  });
  const newCreds = await createRes.json();
  console.log('New credentials created:', newCreds.client_id);

  // Step 2: Update secret manager / environment
  // WARNING: client_secret is only shown once — store it immediately
  await updateSecretManager('NAVAN_CLIENT_ID', newCreds.client_id);
  await updateSecretManager('NAVAN_CLIENT_SECRET', newCreds.client_secret);

  // Step 3: Verify new credentials work
  const testToken = await getAccessToken();
  const verifyRes = await fetch('https://api.navan.com/v1/users?limit=1', {
    headers: { 'Authorization': `Bearer ${testToken}` }
  });

  if (!verifyRes.ok) {
    throw new Error('New credentials failed verification — do NOT revoke old credentials');
  }

  // Step 4: Revoke old credentials only after verification
  console.log('New credentials verified — revoke old credentials in Navan admin dashboard');
}
```

### Step 3: Configure SSO with Supported Identity Providers
Navan supports the following SSO providers:
- **Okta** — SAML 2.0, SCIM provisioning
- **Azure AD (Entra ID)** — SAML 2.0, SCIM provisioning
- **AD FS** — SAML 2.0
- **OneLogin** — SAML 2.0
- **Google Workspace** — OpenID Connect
- **Custom SAML 2.0** — Any SAML 2.0 compliant IdP

```bash
# Verify SSO configuration via API
curl -s -H "Authorization: Bearer $NAVAN_ACCESS_TOKEN" \
  https://api.navan.com/v1/company/sso-config | python3 -m json.tool
```

### Step 4: Set Up SCIM User Provisioning
```bash
# SCIM endpoint configuration for Okta or Entra ID
# Base URL: https://api.navan.com/scim/v2
# Authentication: Bearer token from Navan admin dashboard

# Test SCIM connectivity
curl -s -H "Authorization: Bearer $NAVAN_SCIM_TOKEN" \
  https://api.navan.com/scim/v2/Users?count=1 | python3 -m json.tool

# SCIM supports:
# - User creation (POST /Users)
# - User updates (PATCH /Users/{id})
# - User deactivation (PATCH /Users/{id} with active: false)
# - Group assignment (POST /Groups)
```

### Step 5: Security Audit Checklist
```markdown
## Pre-Production Security Review
- [ ] OAuth credentials stored in secret manager (not .env in production)
- [ ] .env and credential files in .gitignore
- [ ] Credential rotation schedule documented (recommend 90-day cycle)
- [ ] SSO enforced for all user accounts
- [ ] SCIM provisioning active for automated onboarding/offboarding
- [ ] API access scoped to minimum required permissions
- [ ] Webhook secrets rotated alongside API credentials
- [ ] Audit logs enabled in Navan admin dashboard
- [ ] TLS certificate pinning for API calls (optional, advanced)
```

## Output
A hardened Navan integration with environment-based credential storage, automated rotation capability, SSO/SAML configured through the organization's identity provider, and SCIM provisioning for automated user lifecycle management. The security audit checklist provides a pre-production gate for compliance reviews.

## Error Handling
| Error | Code | Solution |
|-------|------|----------|
| Invalid client credentials | 401 | Verify client_id/client_secret pair; credentials are shown only once at creation |
| Token expired | 401 | Refresh the access token; implement automatic token renewal before expiry |
| SSO configuration error | 400 | Verify SAML metadata XML and ACS URL match between IdP and Navan |
| SCIM authentication failed | 401 | Use the dedicated SCIM token from Navan admin, not the API OAuth token |
| Insufficient permissions | 403 | Ensure the OAuth app has required scopes for the requested operation |

## Examples

**Check if credentials are about to expire:**
```bash
# Decode JWT token to check expiry (if Navan uses JWT)
echo "$NAVAN_ACCESS_TOKEN" | cut -d'.' -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

**Scan codebase for leaked credentials:**
```bash
# Check for hardcoded Navan credentials
grep -rn 'NAVAN_CLIENT_SECRET\|navan.*secret' --include='*.ts' --include='*.js' --include='*.py' . \
  | grep -v 'node_modules\|.env.example\|process.env'
```

## Resources
- [Navan Security](https://navan.com/security) — Compliance certifications (SOC 2, ISO 27001, PCI DSS)
- [Navan Help Center](https://app.navan.com/app/helpcenter) — SSO and SCIM configuration guides
- [Navan Integrations](https://navan.com/integrations) — Supported identity provider integrations
- [OWASP API Security Top 10](https://owasp.org/API-Security/) — API security best practices

## Next Steps
After securing credentials, see `navan-enterprise-rbac` for role-based access control and travel policy configuration, or `navan-multi-env-setup` for separating dev/staging/prod credentials safely.
