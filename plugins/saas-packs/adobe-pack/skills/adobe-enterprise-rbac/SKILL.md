---
name: adobe-enterprise-rbac
description: |
  Configure Adobe enterprise identity with Admin Console SCIM provisioning,
  User Management API, product profile-based RBAC, and Federated ID
  with Azure AD or Google Workspace.
  Trigger with phrases like "adobe SSO", "adobe RBAC",
  "adobe enterprise", "adobe roles", "adobe SCIM", "adobe user management".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Enterprise RBAC

## Overview

Configure enterprise-grade access control for Adobe integrations using Admin Console product profiles, User Management API (UMAPI) for programmatic user provisioning, and SCIM-based identity sync with Azure AD or Google Workspace.

## Prerequisites

- Adobe Enterprise or Teams subscription
- Adobe Admin Console system administrator access
- Identity Provider (Azure AD, Google Workspace, or Okta) for SSO
- Understanding of SCIM 2.0 protocol

## Instructions

### Step 1: Set Up Federated Identity in Admin Console

1. Go to https://adminconsole.adobe.com > Settings > Identity
2. Create a Federated ID directory
3. Configure SSO:
   - **Azure AD**: Admin Console > Add Azure Sync > Follow SCIM setup
   - **Google Workspace**: Admin Console > Add Google Sync > SCIM provisioning
   - **Generic SAML**: Upload IdP metadata XML

```yaml
# SAML Configuration Values (for your IdP)
Adobe SP Entity ID: https://federatedid-na1.services.adobe.com/federated/saml/metadata
ACS URL: https://federatedid-na1.services.adobe.com/federated/saml/SSO
Name ID Format: urn:oasis:names:tc:SAML:2.0:nameid-format:emailAddress
```

### Step 2: Define Product Profiles (Adobe's RBAC Mechanism)

Product Profiles in Admin Console are Adobe's native RBAC system. Create profiles that map to your application roles:

| Profile Name | Adobe APIs Granted | Application Role |
|-------------|-------------------|------------------|
| `API-Developers` | Firefly, PDF Services, Photoshop | Full API access |
| `API-Viewers` | PDF Services (read-only) | Report viewers |
| `API-Automation` | PDF Services, Document Generation | CI/CD service accounts |
| `API-Admin` | All APIs + Admin Console | Platform administrators |

### Step 3: Programmatic User Management via UMAPI

```typescript
// src/adobe/user-management.ts
// Adobe User Management API (UMAPI) — manage users and product profile assignments

const UMAPI_BASE = 'https://usermanagement.adobe.io/v2/usermanagement';

interface UmapiUser {
  email: string;
  firstname: string;
  lastname: string;
  country: string;
}

export async function addUserToProductProfile(
  user: UmapiUser,
  productProfile: string
): Promise<void> {
  const token = await getAccessToken();

  const response = await fetch(`${UMAPI_BASE}/action/${process.env.ADOBE_IMS_ORG_ID}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'x-api-key': process.env.ADOBE_CLIENT_ID!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify([{
      user: user.email,
      requestID: `req-${Date.now()}`,
      do: [
        {
          addAdobeID: {
            email: user.email,
            firstname: user.firstname,
            lastname: user.lastname,
            country: user.country,
          },
        },
        {
          add: {
            product: [productProfile],
          },
        },
      ],
    }]),
  });

  if (!response.ok) throw new Error(`UMAPI error: ${await response.text()}`);
  const result = await response.json();
  console.log(`User ${user.email} added to profile ${productProfile}:`, result);
}

export async function removeUserFromProductProfile(
  email: string,
  productProfile: string
): Promise<void> {
  const token = await getAccessToken();

  const response = await fetch(`${UMAPI_BASE}/action/${process.env.ADOBE_IMS_ORG_ID}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'x-api-key': process.env.ADOBE_CLIENT_ID!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify([{
      user: email,
      requestID: `req-${Date.now()}`,
      do: [{
        remove: {
          product: [productProfile],
        },
      }],
    }]),
  });

  if (!response.ok) throw new Error(`UMAPI error: ${await response.text()}`);
}
```

### Step 4: Map IdP Groups to Adobe Product Profiles

```typescript
// src/adobe/group-sync.ts
// Sync IdP group membership to Adobe Product Profiles

const GROUP_TO_PROFILE: Record<string, string[]> = {
  'Engineering':        ['API-Developers'],
  'Data-Science':       ['API-Developers', 'API-Viewers'],
  'Platform-Admins':    ['API-Admin'],
  'CI-CD-Services':     ['API-Automation'],
  'Business-Analysts':  ['API-Viewers'],
};

export async function syncGroupMembership(
  userEmail: string,
  idpGroups: string[]
): Promise<void> {
  // Determine which Adobe profiles this user should have
  const targetProfiles = new Set<string>();
  for (const group of idpGroups) {
    const profiles = GROUP_TO_PROFILE[group];
    if (profiles) profiles.forEach(p => targetProfiles.add(p));
  }

  // Get current Adobe profile assignments
  const currentProfiles = await getUserProfiles(userEmail);

  // Add missing profiles
  for (const profile of targetProfiles) {
    if (!currentProfiles.includes(profile)) {
      await addUserToProductProfile(
        { email: userEmail, firstname: '', lastname: '', country: 'US' },
        profile
      );
    }
  }

  // Remove stale profiles
  for (const profile of currentProfiles) {
    if (!targetProfiles.has(profile)) {
      await removeUserFromProductProfile(userEmail, profile);
    }
  }
}
```

### Step 5: Application-Level Permission Check

```typescript
// src/middleware/adobe-auth.ts
// Check that the current user's Adobe profile grants the required permission

interface AdobeUserContext {
  email: string;
  profiles: string[];  // Product profiles from SSO token claims
}

const PROFILE_PERMISSIONS: Record<string, string[]> = {
  'API-Developers': ['read', 'write', 'generate', 'extract'],
  'API-Viewers':    ['read', 'extract'],
  'API-Automation': ['read', 'write', 'extract', 'generate'],
  'API-Admin':      ['read', 'write', 'generate', 'extract', 'delete', 'admin'],
};

function checkAdobePermission(user: AdobeUserContext, requiredPerm: string): boolean {
  return user.profiles.some(profile => {
    const perms = PROFILE_PERMISSIONS[profile];
    return perms?.includes(requiredPerm);
  });
}

// Express middleware
function requireAdobePermission(permission: string) {
  return (req: any, res: any, next: any) => {
    if (!checkAdobePermission(req.user, permission)) {
      return res.status(403).json({
        error: 'Forbidden',
        message: `Missing Adobe permission: ${permission}`,
        requiredProfile: Object.entries(PROFILE_PERMISSIONS)
          .filter(([_, perms]) => perms.includes(permission))
          .map(([profile]) => profile),
      });
    }
    next();
  };
}

// Usage
app.post('/api/generate-image', requireAdobePermission('generate'), generateHandler);
app.delete('/api/assets/:id', requireAdobePermission('delete'), deleteHandler);
```

## Output

- Federated Identity with SSO (SAML/OIDC) configured
- Product Profiles created for each application role
- Programmatic user provisioning via UMAPI
- IdP group-to-profile sync automation
- Application middleware enforcing Adobe permissions

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| SSO login redirect loop | Wrong ACS URL | Verify SAML config in Admin Console |
| UMAPI 403 | Missing admin permission | Use system admin credentials for UMAPI |
| Profile not applied | SCIM sync delay | Wait 5-10min for Azure/Google sync |
| User can't access API | Missing product profile | Assign profile in Admin Console or via UMAPI |

## Resources

- [Adobe Admin Console](https://adminconsole.adobe.com)
- [User Management API](https://adobe.io/apis/experienceplatform/umapi-new.html)
- [Adobe Admin Console Roles](https://helpx.adobe.com/enterprise/using/roles.html)
- [Azure AD Sync Setup](https://helpx.adobe.com/enterprise/using/add-azure-sync.html)
- [Google Workspace Sync](https://helpx.adobe.com/enterprise/using/add-google-sync.html)

## Next Steps

For major migrations, see `adobe-migration-deep-dive`.
