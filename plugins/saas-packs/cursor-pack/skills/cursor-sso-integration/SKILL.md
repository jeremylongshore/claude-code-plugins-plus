---
name: cursor-sso-integration
description: |
  Configure SSO and enterprise authentication in Cursor. Triggers on "cursor sso",
  "cursor saml", "cursor oauth", "enterprise cursor auth", "cursor okta".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor SSO & Enterprise Authentication

## SSO Overview

### Availability
```
SSO is available on:
- Business plan: Basic SSO
- Enterprise plan: Full SSO with customization

Features:
- SAML 2.0 support
- OAuth 2.0/OIDC
- Auto-provisioning (SCIM)
- JIT provisioning
- Multiple IdP support
```

### Supported Identity Providers
```
Tested & Supported:
- Okta
- Azure AD (Entra ID)
- Google Workspace
- OneLogin
- Auth0
- Ping Identity
- JumpCloud

Generic SAML 2.0:
- Any SAML 2.0 compliant IdP
```

## Setting Up SSO

### Prerequisites
```
Before configuring:
[ ] Business or Enterprise plan active
[ ] Admin access to Cursor org
[ ] Admin access to Identity Provider
[ ] Domain verification completed
[ ] Team members informed of change
```

### Domain Verification
```
1. Go to Cursor Admin > Settings > Domains
2. Add your company domain (company.com)
3. Choose verification method:
   - DNS TXT record
   - HTML file upload
4. Complete verification
5. Domain shows as "Verified"
```

## SAML 2.0 Configuration

### Cursor SAML Details
```
For your IdP configuration:

ACS URL (Assertion Consumer Service):
https://cursor.com/api/auth/saml/callback

Entity ID (SP Entity ID):
https://cursor.com/saml/sp

Name ID Format:
urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress

Required Attributes:
- email (required)
- firstName (optional)
- lastName (optional)
```

### IdP Configuration

#### Okta
```
1. Admin Console > Applications > Create App Integration
2. Select SAML 2.0
3. Configure:
   - App name: Cursor
   - Single sign on URL: https://cursor.com/api/auth/saml/callback
   - Audience URI: https://cursor.com/saml/sp
   - Name ID format: Email
4. Attribute Statements:
   - email: user.email
   - firstName: user.firstName
   - lastName: user.lastName
5. Download IdP metadata XML
6. Upload to Cursor Admin
```

#### Azure AD (Entra ID)
```
1. Azure Portal > Enterprise Applications > New
2. Create your own application
3. Set up SSO > SAML
4. Configure:
   - Identifier: https://cursor.com/saml/sp
   - Reply URL: https://cursor.com/api/auth/saml/callback
   - Sign on URL: https://cursor.com
5. Attributes & Claims:
   - email: user.mail
   - firstName: user.givenname
   - lastName: user.surname
6. Download Federation Metadata XML
7. Upload to Cursor Admin
```

#### Google Workspace
```
1. Admin Console > Apps > Web and mobile apps
2. Add App > Search for or Add Custom SAML App
3. Configure:
   - ACS URL: https://cursor.com/api/auth/saml/callback
   - Entity ID: https://cursor.com/saml/sp
   - Name ID format: EMAIL
4. Attribute Mapping:
   - email: Primary Email
   - firstName: First Name
   - lastName: Last Name
5. Download IdP metadata
6. Upload to Cursor Admin
```

### Completing Setup in Cursor
```
1. Cursor Admin > Settings > SSO
2. Upload IdP metadata XML
   - Or enter details manually:
     - SSO URL
     - Certificate
     - Entity ID
3. Save configuration
4. Test SSO login
5. Enable for organization
```

## OAuth 2.0 / OIDC Configuration

### OAuth Setup
```json
// Cursor OAuth Configuration
{
  "provider": "custom",
  "authorization_endpoint": "https://idp.company.com/oauth2/authorize",
  "token_endpoint": "https://idp.company.com/oauth2/token",
  "userinfo_endpoint": "https://idp.company.com/oauth2/userinfo",
  "client_id": "cursor-app",
  "scopes": ["openid", "email", "profile"]
}
```

### OIDC Claims Mapping
```
Required claims:
- sub (subject identifier)
- email
- email_verified (optional)
- name (optional)
- given_name (optional)
- family_name (optional)
```

## User Provisioning

### Just-In-Time (JIT) Provisioning
```
How it works:
1. User attempts Cursor login
2. Redirects to IdP
3. User authenticates
4. IdP sends SAML assertion
5. Cursor creates account automatically
6. User has immediate access

Benefits:
- No manual user creation
- Always synchronized
- Reduced admin overhead
```

### SCIM Provisioning
```
For Enterprise plans:

SCIM Endpoint: https://cursor.com/scim/v2
Supported operations:
- Create users
- Update users
- Deactivate users
- Group management

Configure in IdP:
1. Add SCIM provisioning
2. Enter Cursor SCIM endpoint
3. Configure Bearer token
4. Map attributes
5. Enable sync
```

## Access Controls

### Role Assignment
```
Via IdP Groups:
1. Configure group claims in IdP
2. Map groups to Cursor roles:
   - cursor-admins → Admin
   - cursor-users → Member
3. Groups sync on login
```

### Conditional Access
```
Azure AD Conditional Access:
- Require MFA for Cursor
- Block legacy authentication
- Require compliant device
- Restrict by location

Okta Access Policies:
- MFA requirements
- Session length
- Network zones
- Device trust
```

## Testing SSO

### Pre-Launch Testing
```
1. Test with admin account first
2. Verify attribute mapping
3. Check role assignment
4. Test provisioning/deprovisioning
5. Verify logout behavior

Test checklist:
[ ] Login works
[ ] User attributes correct
[ ] Roles assigned properly
[ ] Logout clears session
[ ] Re-login works
```

### Troubleshooting

#### "SAML Response Invalid"
```
Check:
- Certificate hasn't expired
- Clock sync between IdP and SP
- Correct ACS URL
- Valid signature
```

#### "User Not Authorized"
```
Check:
- User assigned to app in IdP
- Email domain verified
- Proper group membership
- Attribute mapping correct
```

#### "Session Timeout Issues"
```
Check:
- IdP session length
- Cursor session settings
- Token refresh configuration
```

## Rollout Strategy

### Phased Rollout
```
Phase 1: Admin Testing
- Configure SSO
- Test with admin accounts
- Verify functionality

Phase 2: Pilot Group
- Enable for select team
- Gather feedback
- Address issues

Phase 3: Full Rollout
- Enable for organization
- Communicate changes
- Provide support

Phase 4: Enforcement
- Require SSO
- Disable password auth
- Monitor compliance
```

### Communication Template
```
Subject: Cursor SSO Update

Team,

We're enabling SSO for Cursor starting [date].

What's changing:
- Login via company SSO
- No separate Cursor password needed
- Existing sessions will work until [date]

Action needed:
- Bookmark: cursor.com/sso/company-name
- On next login, use SSO
- Contact IT if issues

Questions? Reach out to [support channel]
```

## Maintenance

### Regular Tasks
```
Monthly:
- Review user access
- Check sync status
- Verify certificate expiry

Annually:
- Certificate rotation
- Access review
- Policy update
- Penetration testing
```

### Certificate Rotation
```
Before expiry:
1. Generate new certificate in IdP
2. Update in Cursor Admin
3. Test with pilot user
4. Enable new certificate
5. Verify all users can login
6. Remove old certificate
```
