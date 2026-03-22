---
name: salesforce-enterprise-rbac
description: |
  Configure Salesforce Profiles, Permission Sets, and Sharing Rules for enterprise access control.
  Use when implementing role-based access, configuring SSO with Salesforce,
  or setting up organization-wide sharing defaults.
  Trigger with phrases like "salesforce permissions", "salesforce RBAC",
  "salesforce profiles", "salesforce SSO", "salesforce sharing rules", "salesforce OWD".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Enterprise RBAC

## Overview
Configure Salesforce's multi-layered security model: Profiles (baseline permissions), Permission Sets (additive permissions), Roles (record visibility), Organization-Wide Defaults (OWD), and Sharing Rules.

## Prerequisites
- Salesforce System Administrator access
- Understanding of your org's user hierarchy
- For SSO: Identity Provider (Okta, Azure AD, etc.) with SAML 2.0

## Instructions

### Step 1: Understand the Salesforce Security Model

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: Organization-Wide Defaults (OWD)                       │
│ Most restrictive baseline — controls default record access      │
│ Options: Private | Public Read Only | Public Read/Write         │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: Role Hierarchy                                         │
│ Users above in hierarchy see records of users below             │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: Sharing Rules                                          │
│ Grant access to groups of users based on criteria or ownership  │
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: Manual Sharing                                         │
│ Record owner shares individual records                          │
├─────────────────────────────────────────────────────────────────┤
│ Layer 5: Profile / Permission Set                               │
│ Controls CRUD + FLS (which objects and fields users can access) │
└─────────────────────────────────────────────────────────────────┘

Key principle: Salesforce OPENS access, never restricts beyond OWD.
OWD sets the floor. Everything else ADDS access on top.
```

### Step 2: Configure Profiles for Integration Users

```typescript
// Query existing profiles
const conn = await getConnection();
const profiles = await conn.query(`
  SELECT Id, Name, UserType, Description
  FROM Profile
  WHERE UserType = 'Standard'
  ORDER BY Name
`);

// Best practice: Create a custom profile for API integrations
// Setup > Profiles > Clone "Standard User" > Name: "API Integration Profile"
// Set object permissions:
const integrationPermissions = {
  Account:     { read: true, create: true, edit: true, delete: false },
  Contact:     { read: true, create: true, edit: true, delete: false },
  Opportunity: { read: true, create: false, edit: false, delete: false },
  Lead:        { read: true, create: true, edit: true, delete: false },
  Case:        { read: true, create: true, edit: true, delete: false },
};

// Check a user's effective permissions via API
const userPermissions = await conn.query(`
  SELECT Id, Name, Profile.Name,
    (SELECT PermissionSet.Name FROM PermissionSetAssignments)
  FROM User
  WHERE Username = 'integration@mycompany.com'
`);
```

### Step 3: Permission Sets (Additive Permissions)

```typescript
// Permission Sets add permissions ON TOP of Profile
// Use Permission Set Groups to bundle related sets

// Query permission set assignments
const psAssignments = await conn.query(`
  SELECT Assignee.Name, PermissionSet.Name, PermissionSet.IsCustom
  FROM PermissionSetAssignment
  WHERE Assignee.Username = 'integration@mycompany.com'
`);

// Create Permission Set via Metadata API (SFDX)
// force-app/main/default/permissionsets/Integration_API_Access.permissionset-meta.xml
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Integration API Access</label>
    <description>API access for integration user</description>
    <objectPermissions>
        <object>Account</object>
        <allowRead>true</allowRead>
        <allowCreate>true</allowCreate>
        <allowEdit>true</allowEdit>
        <allowDelete>false</allowDelete>
    </objectPermissions>
    <fieldPermissions>
        <field>Account.Industry</field>
        <readable>true</readable>
        <editable>true</editable>
    </fieldPermissions>
    <fieldPermissions>
        <field>Account.AnnualRevenue</field>
        <readable>true</readable>
        <editable>false</editable>
    </fieldPermissions>
</PermissionSet>
```

### Step 4: Organization-Wide Defaults (OWD)

```typescript
// Check current OWD settings via SOQL (metadata)
// Setup > Sharing Settings > Organization-Wide Defaults

// Recommended OWD for common objects:
const recommendedOWD = {
  Account:     'Private',            // Sales teams see only their accounts
  Contact:     'Controlled by Parent', // Follows Account access
  Opportunity: 'Private',            // Revenue data is sensitive
  Case:        'Private',            // Customer support data
  Lead:        'Public Read/Write',  // Sales team shares leads
};

// When OWD is Private, use Sharing Rules to open access:
// Setup > Sharing Settings > Sharing Rules > New
// Example: "Share all Accounts where Industry = 'Technology' with 'Engineering' Role"
```

### Step 5: SSO Integration

```
SAML 2.0 SSO with Salesforce:

Setup > Single Sign-On Settings > Enable SAML
Setup > Single Sign-On Settings > New

Configuration:
- Issuer: https://idp.yourcompany.com/saml/metadata
- Entity ID: https://login.salesforce.com
- Certificate: Upload IdP signing certificate
- SAML User ID Type: "Username"
- SAML User ID Location: "Subject" element

Identity Provider Configuration:
- ACS URL: https://login.salesforce.com?so=00Dxxxxxxxxxxxx
- Entity ID: https://saml.salesforce.com
- Name ID: user.email (must match Salesforce username)

Setup > My Domain > Authentication Configuration:
- Enable SAML as authentication option
- Optionally disable username/password login
```

### Step 6: Verify Access Programmatically

```typescript
// Check if current user can access a specific record
async function canAccessRecord(objectType: string, recordId: string): Promise<boolean> {
  try {
    await conn.sobject(objectType).retrieve(recordId);
    return true;
  } catch (error: any) {
    if (error.errorCode === 'INSUFFICIENT_ACCESS_OR_READONLY') {
      return false;
    }
    throw error;
  }
}

// Check object-level permissions
async function getObjectPermissions(objectType: string) {
  const describe = await conn.sobject(objectType).describe();
  return {
    queryable: describe.queryable,
    createable: describe.createable,
    updateable: describe.updateable,
    deletable: describe.deletable,
  };
}
```

## Output
- Profiles configured with least-privilege for integration users
- Permission Sets created for modular access control
- OWD set appropriately for each sObject
- SSO configured with SAML 2.0
- Programmatic access verification implemented

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `INSUFFICIENT_ACCESS_OR_READONLY` | Missing object/field permission | Check Profile + Permission Sets |
| `CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY` | Trigger/Flow denied by sharing | Check OWD and Sharing Rules |
| SSO loop | Wrong ACS URL | Verify My Domain + ACS URL match |
| User can't see records | OWD is Private, no sharing rule | Add appropriate Sharing Rule or Role Hierarchy |

## Resources
- [Salesforce Security Model](https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/)
- [Permission Sets](https://help.salesforce.com/s/articleView?id=sf.perm_sets_overview.htm)
- [Sharing Rules](https://help.salesforce.com/s/articleView?id=sf.security_sharing_rules.htm)
- [SAML SSO](https://help.salesforce.com/s/articleView?id=sf.sso_saml.htm)

## Next Steps
For major migrations, see `salesforce-migration-deep-dive`.
