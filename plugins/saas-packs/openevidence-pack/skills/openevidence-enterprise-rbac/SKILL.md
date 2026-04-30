---
name: openevidence-enterprise-rbac
description: 'Enterprise Rbac for OpenEvidence.

  Trigger: "openevidence enterprise rbac".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openevidence
- healthcare
compatibility: Designed for Claude Code
---
# OpenEvidence Enterprise RBAC

## Overview

OpenEvidence delivers AI-powered clinical decision support using peer-reviewed medical literature. Enterprise RBAC controls access to clinical queries, PHI-adjacent data, and research datasets. Clinicians query evidence with full access. Researchers access de-identified datasets and can create study cohorts. Admins manage institutional access, SSO configuration, and compliance settings. HIPAA requires strict audit logging of every clinical query, PHI access event, and data export. Institutional access agreements define which evidence libraries each organization can query.

## Role Hierarchy

| Role | Permissions | Scope |
|------|------------|-------|
| Institutional Admin | Manage users, SSO config, compliance settings, usage analytics | Organization-wide |
| Clinician | Query clinical evidence, view full citations, bookmark findings | Institutional library |
| Researcher | Access de-identified datasets, create study cohorts, export data | Approved studies |
| Medical Student | Query evidence with supervised access, no PHI datasets | Educational library |
| Auditor | Read-only access to query logs and compliance reports | Organization-wide |

## Permission Check

```typescript
async function checkClinicalAccess(userId: string, resource: string, accessLevel: string): Promise<boolean> {
  const response = await fetch(`${OE_API}/v1/institutions/${INSTITUTION_ID}/permissions`, {
    headers: { Authorization: `Bearer ${OE_API_TOKEN}`, 'Content-Type': 'application/json' },
  });
  const perms = await response.json();
  const user = perms.members.find((m: any) => m.id === userId);
  if (!user) return false;
  const allowed = ROLE_ACCESS[user.role];
  return allowed?.resources.includes(resource) && allowed.levels.includes(accessLevel);
}
```

## Role Assignment

```typescript
async function assignInstitutionalRole(email: string, role: string, library: string): Promise<void> {
  await fetch(`${OE_API}/v1/institutions/${INSTITUTION_ID}/members`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${OE_API_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, role, libraryAccess: library, hipaaAcknowledged: true }),
  });
}

async function revokeAccess(email: string): Promise<void> {
  await fetch(`${OE_API}/v1/institutions/${INSTITUTION_ID}/members/${email}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${OE_API_TOKEN}` },
  });
}
```

## Audit Logging

```typescript
interface OpenEvidenceAuditEntry {
  timestamp: string; userId: string; role: string;
  action: 'clinical_query' | 'dataset_access' | 'export' | 'phi_view' | 'role_change';
  resource: string; institutionId: string; queryHash?: string; result: 'allowed' | 'denied';
}

function logClinicalAccess(entry: OpenEvidenceAuditEntry): void {
  console.log(JSON.stringify({ ...entry, hipaaCompliant: true }));
}
```

## RBAC Checklist

- [ ] Institutional access agreements define available evidence libraries
- [ ] Clinician role verified against NPI or institutional credentials
- [ ] Researcher access limited to IRB-approved de-identified datasets
- [ ] Medical student access supervised with educational library scope
- [ ] All clinical queries logged with timestamp, user, and query hash
- [ ] PHI access events tracked separately for HIPAA audit readiness
- [ ] Data export restricted to researcher role with approval workflow
- [ ] Quarterly access review aligned with HIPAA compliance cycle

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `403` on clinical query endpoint | User not provisioned at institution | Add user via institutional admin portal |
| Dataset access denied | Study not in user's approved IRB list | Submit IRB approval to institutional admin |
| Export blocked | Role lacks export permission | Upgrade to researcher role with export rights |
| SSO login loop | SAML assertion missing institution claim | Configure institution attribute in IdP SAML settings |
| Query results redacted | Library not included in institutional agreement | Contact OpenEvidence to expand library access |

## Resources

- [OpenEvidence Platform](https://www.openevidence.com)
- [OpenEvidence for Institutions](https://www.openevidence.com/institutions)

## Next Steps

See `openevidence-security-basics`.
