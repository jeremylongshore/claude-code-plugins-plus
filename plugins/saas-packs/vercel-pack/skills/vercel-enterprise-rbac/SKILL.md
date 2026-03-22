---
name: vercel-enterprise-rbac
description: |
  Configure Vercel enterprise RBAC, access groups, SSO integration, and audit logging.
  Use when implementing team access control, configuring SAML SSO,
  or setting up role-based permissions for Vercel projects.
  Trigger with phrases like "vercel SSO", "vercel RBAC",
  "vercel enterprise", "vercel roles", "vercel permissions", "vercel access groups".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, rbac, enterprise, sso]

---
# Vercel Enterprise RBAC

## Overview
Configure Vercel's role-based access control (RBAC) with team roles, project-level access groups, SSO/SAML integration, and audit logging. Covers the two access control planes: team-level (who can deploy) and application-level (who can access deployed content).

## Prerequisites
- Vercel Pro or Enterprise plan
- Identity Provider (IdP) with SAML 2.0 support (for SSO)
- Understanding of your organization's access requirements

## Instructions

### Step 1: Understand Vercel's Role Model

**Team-Level Roles:**

| Role | Deploy Prod | Manage Projects | Manage Billing | Manage Members |
|------|-------------|-----------------|----------------|----------------|
| Owner | Yes | Yes | Yes | Yes |
| Member | Yes | Yes | No | No |
| Developer | Preview only | Limited | No | No |
| Viewer | No | Read-only | No | No |
| Security (Enterprise) | No | Security settings | No | No |

**Extended Permissions (Enterprise):**
Layer on top of base roles for granular control:
- Deploy to production
- Manage environment variables
- Manage domains
- Access runtime logs
- Manage integrations

### Step 2: Configure Team Members via API
```bash
# Invite a team member
curl -X POST "https://api.vercel.com/v1/teams/team_xxx/members" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "developer@company.com",
    "role": "DEVELOPER"
  }'

# List team members
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v2/teams/team_xxx/members" \
  | jq '.members[] | {name: .name, email: .email, role: .role}'

# Update a member's role
curl -X PATCH "https://api.vercel.com/v1/teams/team_xxx/members/user_xxx" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "MEMBER"}'

# Remove a team member
curl -X DELETE "https://api.vercel.com/v1/teams/team_xxx/members/user_xxx" \
  -H "Authorization: Bearer $VERCEL_TOKEN"
```

### Step 3: Access Groups (Project-Level Permissions)
Access Groups assign teams of people to specific projects with specific roles:

1. Go to **Team Settings > Access Groups**
2. Create a group (e.g., "Frontend Team", "Backend Team")
3. Add members to the group
4. Assign the group to specific projects with a role

```
Example Access Group Setup:
├── Frontend Team → [project-web, project-docs] → Member role
├── Backend Team → [project-api, project-worker] → Member role
├── DevOps Team → [all projects] → Member role
└── QA Team → [all projects] → Viewer role
```

### Step 4: SSO / SAML Configuration
In the Vercel dashboard: **Team Settings > Authentication > SAML Single Sign-On**

1. Enable SAML SSO
2. Configure your IdP (Okta, Azure AD, Google Workspace):
   - ACS URL: `https://vercel.com/api/auth/saml/acs`
   - Entity ID: `https://vercel.com`
   - Name ID format: `emailAddress`
3. Enter IdP metadata URL or upload certificate
4. Map SAML attributes to Vercel fields

```
SAML Attribute Mapping:
├── email → user email (required)
├── firstName → display name
├── lastName → display name
└── groups → Vercel team roles (optional)
```

**Enforce SSO for all team members:**
Once enabled, toggle "Require SAML for login" — all members must authenticate through SSO.

### Step 5: Application-Level Auth with Middleware
```typescript
// middleware.ts — enforce auth on deployed application routes
import { NextRequest, NextResponse } from 'next/server';
import { verifyJWT } from '@/lib/auth';

const ROLE_ROUTES: Record<string, string[]> = {
  '/admin': ['admin'],
  '/dashboard': ['admin', 'member'],
  '/api/admin': ['admin'],
};

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if route requires auth
  const requiredRoles = Object.entries(ROLE_ROUTES)
    .find(([prefix]) => pathname.startsWith(prefix));

  if (!requiredRoles) return NextResponse.next();

  const token = request.cookies.get('session')?.value;
  if (!token) {
    return pathname.startsWith('/api')
      ? NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
      : NextResponse.redirect(new URL('/login', request.url));
  }

  const payload = await verifyJWT(token);
  if (!payload || !requiredRoles[1].includes(payload.role)) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
  }

  // Pass user info to API routes via headers
  const response = NextResponse.next();
  response.headers.set('x-user-id', payload.sub);
  response.headers.set('x-user-role', payload.role);
  return response;
}

export const config = {
  matcher: ['/admin/:path*', '/dashboard/:path*', '/api/admin/:path*'],
};
```

### Step 6: Audit Logging
Vercel Enterprise includes audit logs in **Team Settings > Audit Log**.

Events tracked:
- Team member added/removed/role changed
- Project created/deleted
- Deployment to production
- Environment variable created/updated/deleted
- Domain added/removed
- Integration installed/uninstalled
- SSO configuration changes

```bash
# Export audit logs via API (Enterprise)
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v1/teams/team_xxx/audit-log?limit=100" \
  | jq '.events[] | {action: .action, user: .user.email, createdAt: .createdAt, resource: .resource}'
```

## RBAC Checklist

| Check | Status |
|-------|--------|
| Team roles assigned per least privilege | Required |
| Production deploy restricted to Member+ | Required |
| Access Groups configured per project | Recommended |
| SSO/SAML enforced for all members | Enterprise |
| Audit logging exported to SIEM | Enterprise |
| Application-level auth in middleware | Required |
| Off-boarding removes Vercel access via IdP | Required |

## Output
- Team roles configured with least-privilege access
- Access Groups scoping members to specific projects
- SSO/SAML enforced for all team authentication
- Application-level RBAC in Edge Middleware
- Audit logs exported for compliance

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Member can't deploy to prod | Developer role (preview only) | Change to Member or Owner role |
| SSO login fails | IdP metadata URL expired | Update SAML configuration |
| Access Group not applied | Member not in group | Add member to the Access Group |
| Audit log missing events | Free/Pro plan limitation | Upgrade to Enterprise for audit logs |
| Off-boarded user still has access | SSO not enforced | Enable "Require SAML for login" |

## Resources
- [Vercel RBAC](https://vercel.com/docs/rbac)
- [Access Roles](https://vercel.com/docs/rbac/access-roles)
- [Access Groups](https://vercel.com/docs/rbac/access-groups)
- [Extended Permissions](https://vercel.com/docs/rbac/access-roles/extended-permissions)
- [Managing Team Members](https://vercel.com/docs/rbac/managing-team-members)

## Next Steps
For migration strategies, see `vercel-migration-deep-dive`.
