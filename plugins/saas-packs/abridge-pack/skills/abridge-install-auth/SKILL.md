---
name: abridge-install-auth
description: |
  Set up Abridge clinical AI platform authentication and EHR integration credentials.
  Use when onboarding a healthcare org to Abridge, configuring Epic/Athena integration,
  or setting up developer sandbox access for ambient AI documentation.
  Trigger: "install abridge", "setup abridge", "abridge auth", "configure abridge credentials".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, clinical-documentation]
compatible-with: claude-code
---

# Abridge Install & Auth

## Overview

Configure Abridge ambient AI platform credentials and EHR integration tokens. Abridge is an enterprise clinical documentation platform — it does not have a public npm/pip SDK. Integration happens through EHR-embedded workflows (Epic Pal, Athena, eClinicalWorks) and partner API access.

## Prerequisites

- Healthcare organization with Abridge contract
- EHR system access (Epic, Athena, eClinicalWorks, Cerner, or AllScripts)
- Abridge Partner Portal credentials from your sales engineer
- HIPAA-compliant infrastructure (required for PHI handling)

## Instructions

### Step 1: Obtain Abridge Partner Credentials

```bash
# Abridge uses partner-issued credentials, not self-service API keys
# Contact your Abridge sales engineer for:
# 1. Partner API client_id and client_secret
# 2. Organization ID (org_id)
# 3. Sandbox environment URL

# Store credentials securely (never in source control)
cat > .env.local << 'EOF'
ABRIDGE_CLIENT_ID=partner_xxxxxxxxxxxx
ABRIDGE_CLIENT_SECRET=secret_xxxxxxxxxxxx
ABRIDGE_ORG_ID=org_xxxxxxxxxxxx
ABRIDGE_BASE_URL=https://api.abridge.com/v1
ABRIDGE_SANDBOX_URL=https://sandbox.api.abridge.com/v1
EOF

chmod 600 .env.local
echo ".env.local" >> .gitignore
```

### Step 2: Configure Epic EHR Integration (Most Common Path)

```typescript
// src/config/abridge-ehr.ts
// Abridge is Epic's first "Pal" — integration uses Epic's FHIR R4 APIs

interface AbridgeEpicConfig {
  epicClientId: string;           // From Epic App Orchard registration
  epicFhirBaseUrl: string;        // e.g., https://fhir.epic.com/interconnect-fhir-oauth
  abridgeOrgId: string;           // From Abridge partner portal
  abridgeApiBaseUrl: string;      // Partner API endpoint
  smartLaunchUrl: string;         // SMART on FHIR launch URL
}

const config: AbridgeEpicConfig = {
  epicClientId: process.env.EPIC_CLIENT_ID!,
  epicFhirBaseUrl: process.env.EPIC_FHIR_BASE_URL!,
  abridgeOrgId: process.env.ABRIDGE_ORG_ID!,
  abridgeApiBaseUrl: process.env.ABRIDGE_BASE_URL!,
  smartLaunchUrl: `${process.env.EPIC_FHIR_BASE_URL}/oauth2/authorize`,
};

export default config;
```

### Step 3: Authenticate via OAuth 2.0 (SMART on FHIR)

```typescript
// src/auth/smart-fhir-auth.ts
import axios from 'axios';

interface SmartTokenResponse {
  access_token: string;
  token_type: 'Bearer';
  expires_in: number;
  scope: string;
  patient?: string;         // Patient context from EHR launch
  encounter?: string;       // Encounter context from EHR launch
}

async function getAbridgeToken(
  authCode: string,
  redirectUri: string
): Promise<SmartTokenResponse> {
  const tokenUrl = `${process.env.EPIC_FHIR_BASE_URL}/oauth2/token`;

  const response = await axios.post(tokenUrl, new URLSearchParams({
    grant_type: 'authorization_code',
    code: authCode,
    redirect_uri: redirectUri,
    client_id: process.env.EPIC_CLIENT_ID!,
    client_secret: process.env.EPIC_CLIENT_SECRET!,
  }), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });

  return response.data;
}

export { getAbridgeToken, SmartTokenResponse };
```

### Step 4: Verify Connection

```typescript
// src/auth/verify-connection.ts
import axios from 'axios';

async function verifyAbridgeConnection(): Promise<boolean> {
  try {
    // Verify partner API access
    const response = await axios.get(
      `${process.env.ABRIDGE_BASE_URL}/health`,
      {
        headers: {
          'Authorization': `Bearer ${process.env.ABRIDGE_CLIENT_SECRET}`,
          'X-Org-Id': process.env.ABRIDGE_ORG_ID!,
        },
        timeout: 5000,
      }
    );

    console.log('Abridge connection verified:', response.data.status);
    return response.status === 200;
  } catch (error) {
    console.error('Abridge connection failed:', error);
    return false;
  }
}
```

## Output

- `.env.local` with partner credentials (chmod 600, gitignored)
- EHR integration config pointing to correct FHIR endpoints
- SMART on FHIR OAuth flow for clinician authentication
- Verified connectivity to Abridge partner API

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid partner credentials | Contact Abridge sales engineer for new credentials |
| `403 Forbidden` | Org not provisioned | Verify org_id matches your Abridge contract |
| SMART launch failure | Epic App Orchard not configured | Register app in Epic App Orchard first |
| CORS errors | Wrong redirect URI | Update allowed redirect URIs in Epic portal |
| Certificate error | Self-signed cert in sandbox | Use Abridge-provided sandbox CA certificate |

## Security Checklist

- [ ] Credentials stored in environment variables, never in code
- [ ] `.env.local` is gitignored and chmod 600
- [ ] OAuth tokens stored in encrypted session store
- [ ] PHI data encrypted at rest and in transit (HIPAA requirement)
- [ ] Audit logging enabled for all Abridge API calls
- [ ] BAA (Business Associate Agreement) signed with Abridge

## Resources

- [Abridge Platform Overview](https://www.abridge.com/product)
- [Epic App Orchard Registration](https://appmarket.epic.com/)
- [SMART on FHIR Authorization](https://hl7.org/fhir/smart-app-launch/)
- [Abridge Partner Portal](https://partners.abridge.com)

## Next Steps

After authentication is configured, proceed to `abridge-hello-world` for your first ambient session test.
