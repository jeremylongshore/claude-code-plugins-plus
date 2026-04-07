---
name: guidewire-enterprise-rbac
description: |
  Implement Guidewire RBAC: API roles, user permissions, and security policies.
  Trigger: "guidewire enterprise rbac", "enterprise-rbac".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Enterprise RBAC

## Overview

Guidewire InsuranceSuite (PolicyCenter, ClaimCenter, BillingCenter) enforces role-based access at both the UI and Cloud API layers. Claims adjusters see only claims in their assigned regions. Underwriters access policy data scoped to their authority level. Admins manage user provisioning through Guidewire Cloud Console (GCC). Insurance regulations (NAIC, state DOI) require strict data classification tiers and audit trails on every policy and claim access. SAML assertions map AD groups to Guidewire roles for SSO.

## Role Hierarchy

| Role | Permissions | Scope |
|------|------------|-------|
| System Admin | User provisioning, role config, API token management via GCC | All modules |
| Underwriter | Create/bind policies, view risk data, approve endorsements | Authority-level tier |
| Claims Adjuster | View/update claims, upload documents, set reserves | Assigned region/LOB |
| Agent/Broker | Submit applications, view own policy status, limited billing | Own book of business |
| Auditor | Read-only access to all records, export compliance reports | Organization-wide |

## Permission Check

```typescript
async function checkGuidewireAccess(userId: string, resource: string, action: 'read' | 'write'): Promise<boolean> {
  const response = await fetch(`${GW_CLOUD_API}/admin/v1/users/${userId}/permissions`, {
    headers: { Authorization: `Bearer ${GW_API_TOKEN}`, 'Content-Type': 'application/json' },
  });
  const perms = await response.json();
  const grant = perms.data.find((p: any) => p.resource === resource);
  if (!grant) return false;
  return action === 'read' ? grant.canRead : grant.canWrite;
}
```

## Role Assignment

```typescript
async function assignGuidewireRole(userId: string, role: string, region?: string): Promise<void> {
  await fetch(`${GW_CLOUD_API}/admin/v1/users/${userId}/roles`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${GW_API_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ roleCode: role, regionFilter: region ?? 'ALL', effectiveDate: new Date().toISOString() }),
  });
}

async function revokeRole(userId: string, role: string): Promise<void> {
  await fetch(`${GW_CLOUD_API}/admin/v1/users/${userId}/roles/${role}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${GW_API_TOKEN}` },
  });
}
```

## Audit Logging

```typescript
interface GuidewireAuditEntry {
  timestamp: string; userId: string; role: string;
  action: 'policy_view' | 'claim_update' | 'reserve_set' | 'document_upload' | 'role_change';
  resource: string; region: string; policyNumber?: string; result: 'allowed' | 'denied';
}

function logAccess(entry: GuidewireAuditEntry): void {
  console.log(JSON.stringify({ ...entry, environment: process.env.GW_ENVIRONMENT }));
}
```

## RBAC Checklist

- [ ] SAML assertions map AD groups to Guidewire role codes
- [ ] Claims adjusters scoped to assigned regions/lines of business
- [ ] Underwriter authority levels enforce binding limits
- [ ] API tokens scoped per module (PC, CC, BC), never cross-module
- [ ] Data classification tiers applied to PII and PHI fields
- [ ] Auditor role is strictly read-only with no write endpoints
- [ ] Role changes logged with effective date and approver
- [ ] Quarterly access review for regulatory compliance

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `403` on Cloud API endpoint | API role missing required resource permission | Add resource grant in GCC Identity & Access |
| Adjuster sees claims outside region | Region filter not set on role assignment | Update role with correct `regionFilter` value |
| SAML login fails | Group claim not mapped in GCC SSO config | Add AD group to SAML attribute mapping |
| Policy data not visible | Data classification tier too restrictive | Review tier assignment, escalate to admin |
| Stale permissions after transfer | Role not updated when user changed teams | Trigger AD sync or manually reassign in GCC |

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)

## Next Steps

See `guidewire-security-basics`.
