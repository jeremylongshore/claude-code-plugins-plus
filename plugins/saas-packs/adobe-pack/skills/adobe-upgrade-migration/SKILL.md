---
name: adobe-upgrade-migration
description: |
  Analyze, plan, and execute Adobe SDK upgrades — including the critical
  JWT-to-OAuth migration, PDF Services SDK v3-to-v4, and Photoshop API
  endpoint changes (cutout v1 to remove-background v2).
  Trigger with phrases like "upgrade adobe", "adobe migration",
  "adobe breaking changes", "update adobe SDK", "jwt to oauth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Upgrade & Migration

## Overview

Guide for the most critical Adobe migrations: JWT to OAuth Server-to-Server, PDF Services SDK v3 to v4, Photoshop API v1 to v2 endpoints, and general SDK version upgrades.

## Prerequisites

- Current Adobe SDK installed
- Git for version control
- Test suite covering Adobe integration points
- Staging environment for validation

## Instructions

### Migration 1: JWT to OAuth Server-to-Server (CRITICAL)

**Deadline passed:** JWT (Service Account) credentials reached EOL June 2025. If you are still using JWT, migrate immediately.

```typescript
// BEFORE (JWT — no longer works)
import jwt from 'jsonwebtoken';
const jwtToken = jwt.sign({
  exp: Math.round(Date.now() / 1000) + 60 * 60 * 24,
  iss: orgId,
  sub: technicalAccountId,
  aud: `https://ims-na1.adobelogin.com/c/${clientId}`,
  'https://ims-na1.adobelogin.com/s/ent_firefly_sdk': true,
}, privateKey, { algorithm: 'RS256' });

// AFTER (OAuth Server-to-Server — current standard)
const tokenResponse = await fetch('https://ims-na1.adobelogin.com/ims/token/v3', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    client_id: process.env.ADOBE_CLIENT_ID!,
    client_secret: process.env.ADOBE_CLIENT_SECRET!,
    grant_type: 'client_credentials',
    scope: process.env.ADOBE_SCOPES!,
  }),
});
```

**Migration steps:**
1. In Developer Console, open your project
2. Click **Add credential** > **OAuth Server-to-Server**
3. Assign same product profiles as your JWT credential
4. Update application code to use `client_credentials` grant
5. Remove `jsonwebtoken` dependency and private key files
6. Test in staging
7. Deploy to production
8. Delete the old JWT credential in Developer Console

### Migration 2: PDF Services SDK v3 to v4

```bash
# Check current version
npm list @adobe/pdfservices-node-sdk

# Upgrade
npm install @adobe/pdfservices-node-sdk@latest
```

**Key breaking changes v3 -> v4:**

```typescript
// BEFORE (v3)
import PDFServicesSdk from '@adobe/pdfservices-node-sdk';
const credentials = PDFServicesSdk.Credentials
  .serviceAccountCredentialsBuilder()
  .fromFile('pdfservices-api-credentials.json')
  .build();
const executionContext = PDFServicesSdk.ExecutionContext.create(credentials);
const extractPDFOperation = PDFServicesSdk.ExtractPDF.Operation.createNew();

// AFTER (v4)
import {
  ServicePrincipalCredentials,
  PDFServices,
  ExtractPDFJob,
  ExtractPDFParams,
  ExtractElementType,
} from '@adobe/pdfservices-node-sdk';
const credentials = new ServicePrincipalCredentials({
  clientId: process.env.ADOBE_CLIENT_ID!,
  clientSecret: process.env.ADOBE_CLIENT_SECRET!,
});
const pdfServices = new PDFServices({ credentials });
// Job-based API: submit job, poll for result
const job = new ExtractPDFJob({ inputAsset, params });
const pollingURL = await pdfServices.submit({ job });
```

### Migration 3: Photoshop Remove Background v1 to v2

```typescript
// BEFORE (v1 — deprecated)
const response = await fetch('https://image.adobe.io/sensei/cutout', {
  method: 'POST',
  // ...
});

// AFTER (v2 — current)
const response = await fetch('https://image.adobe.io/v2/remove-background', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'x-api-key': process.env.ADOBE_CLIENT_ID!,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    input: { href: inputUrl, storage: 'external' },
    output: { href: outputUrl, storage: 'external', type: 'image/png' },
  }),
});
```

### Step 4: General SDK Upgrade Process

```bash
# 1. Create upgrade branch
git checkout -b upgrade/adobe-sdk

# 2. Check for outdated packages
npm outdated | grep @adobe

# 3. Upgrade all Adobe packages
npm install @adobe/pdfservices-node-sdk@latest \
  @adobe/firefly-apis@latest \
  @adobe/photoshop-apis@latest \
  @adobe/lightroom-apis@latest

# 4. Run tests
npm test

# 5. Fix any breaking changes (check changelogs)
# Firefly: https://developer.adobe.com/firefly-services/docs/firefly-api/guides/changelog/
# PDF Services: https://developer.adobe.com/document-services/docs/overview/pdf-services-api/releasenotes

# 6. Commit and test in staging
git add package.json package-lock.json
git commit -m "chore: upgrade Adobe SDKs to latest"
```

## Output

- Migrated from JWT to OAuth Server-to-Server
- Upgraded PDF Services SDK to v4 job-based API
- Updated Photoshop endpoints to v2
- All tests passing with new SDK versions

## Error Handling

| Error After Upgrade | Cause | Solution |
|---------------------|-------|----------|
| `invalid_client` | Still using JWT credentials | Complete OAuth migration |
| `ExecutionContext is not a constructor` | v3 API in v4 SDK | Use new Job-based API |
| `404 /sensei/cutout` | Old Photoshop endpoint | Update to `/v2/remove-background` |
| `Cannot find module` | Import paths changed | Check SDK changelog for new imports |

## Resources

- [JWT to OAuth Migration Guide](https://developer.adobe.com/developer-console/docs/guides/authentication/ServerToServerAuthentication/migration)
- [PDF Services Release Notes](https://developer.adobe.com/document-services/docs/overview/pdf-services-api/releasenotes)
- [Firefly API Changelog](https://developer.adobe.com/firefly-services/docs/firefly-api/guides/changelog/)
- [Photoshop API Migration](https://developer.adobe.com/firefly-services/docs/photoshop/guides/remove_background/)

## Next Steps

For CI integration during upgrades, see `adobe-ci-integration`.
