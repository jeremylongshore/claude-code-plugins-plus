---
name: guidewire-install-auth
description: |
  Install Guidewire Studio, configure Cloud API OAuth2 authentication,
  and register applications with Guidewire Hub.
  Trigger: "install guidewire", "guidewire auth", "guidewire OAuth2", "guidewire Cloud API setup".
allowed-tools: Read, Write, Edit, Bash(java:*), Bash(gradle:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Install & Auth

## Overview

Set up Guidewire InsuranceSuite development: install Guidewire Studio (IntelliJ-based), configure Cloud API OAuth2 authentication via Guidewire Hub, and obtain JWT tokens for PolicyCenter, ClaimCenter, and BillingCenter APIs.

## Prerequisites

- JDK 17 (Guidewire Cloud 202503+)
- Gradle 8.x
- Guidewire Cloud Console (GCC) access at `https://gcc.guidewire.com`

## Instructions

### Step 1: Register Application in Guidewire Hub

```
GCC > Identity & Access > Applications > Register Application

Service Application (backend): OAuth2 Client Credentials flow
Browser Application (Jutro): OAuth2 Authorization Code flow

Record: client_id and client_secret
```

### Step 2: Configure OAuth2 Environment

```bash
# .env (NEVER commit)
GW_AUTH_URL=https://guidewire-hub.guidewire.com/oauth/token
GW_CLIENT_ID=your_client_id
GW_CLIENT_SECRET=your_client_secret
GW_PC_URL=https://your-tenant.guidewire.com/pc/rest
GW_CC_URL=https://your-tenant.guidewire.com/cc/rest
GW_BC_URL=https://your-tenant.guidewire.com/bc/rest
```

### Step 3: Obtain Access Token

```typescript
async function getGuidewireToken(): Promise<string> {
  const res = await fetch(process.env.GW_AUTH_URL!, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: process.env.GW_CLIENT_ID!,
      client_secret: process.env.GW_CLIENT_SECRET!,
      scope: 'pc.service cc.service bc.service',
    }),
  });
  const { access_token } = await res.json();
  return access_token;
}
```

### Step 4: Verify Connection

```bash
TOKEN=$(curl -s -X POST "$GW_AUTH_URL" \
  -d "grant_type=client_credentials&client_id=$GW_CLIENT_ID&client_secret=$GW_CLIENT_SECRET" \
  | jq -r '.access_token')

curl -s -H "Authorization: Bearer $TOKEN" \
  "$GW_PC_URL/account/v1/accounts?pageSize=1" | jq '.count'
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `invalid_client` | Wrong credentials | Verify client_id/secret in GCC |
| `invalid_scope` | Unauthorized scope | Check API role assignments |
| `401 Unauthorized` | Expired token | Refresh (tokens are short-lived) |
| `403 Forbidden` | Missing API role | Assign roles in GCC > Identity & Access |
| `PKIX path building failed` | SSL cert issue | Import Guidewire CA certificates |

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Authentication](https://docs.guidewire.com/education/cloud-integration-basics/latest/docs/integration_cloud_basics/rest_api_client_overview/)
- [Cloud API Reference - PolicyCenter](https://docs.guidewire.com/cloud/pc/202503/apiref/)

## Next Steps

After auth, proceed to `guidewire-hello-world` for your first API calls.
