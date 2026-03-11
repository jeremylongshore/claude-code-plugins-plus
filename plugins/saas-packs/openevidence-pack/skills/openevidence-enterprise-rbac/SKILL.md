---
name: openevidence-enterprise-rbac
description: |
  Configure OpenEvidence enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for clinical AI applications.
  Trigger with phrases like "openevidence SSO", "openevidence RBAC",
  "openevidence enterprise", "openevidence roles", "openevidence permissions".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Enterprise RBAC

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Configure enterprise-grade role-based access control for OpenEvidence clinical AI integrations. Covers role definitions, SSO (SAML/OIDC), permission middleware, organization management, and secure session handling.

## Prerequisites
- OpenEvidence Enterprise tier subscription
- Identity Provider (IdP) with SAML/OIDC support
- Understanding of role-based access patterns
- HIPAA audit logging infrastructure

## Role Definitions

| Role | Permissions | Use Case |
|------|-------------|----------|
| Physician | Full clinical query, DeepConsult | Active patient care |
| Nurse | Clinical query (no DeepConsult) | Nursing support |
| Pharmacist | Drug-focused queries | Medication management |
| Resident | Clinical query (supervised) | Training |
| Admin | Full access, user management | Platform administration |
| Auditor | Read-only audit logs | Compliance review |
| Integration | API access only | System integration |

## Instructions

### Step 1: Define Roles and Permissions
Create `ClinicalRole` enum and `ClinicalPermissions` interface with boolean flags for clinicalQuery, deepConsult, drugInfo, guidelineAccess, exportResults, viewAuditLogs, manageUsers, manageSettings.

### Step 2: Configure SSO (SAML or OIDC)
Integrate with IdP using `passport-saml` or `passport-openidconnect`. Map IdP groups to clinical roles with priority ordering (Admin > Physician > Pharmacist > Nurse > Resident).

### Step 3: Implement Permission Middleware
Create `requirePermission()` Express middleware that checks `hasPermission(user.role, permission)` and logs denied access attempts to HIPAA audit trail.

### Step 4: Organization Management
Build `OrganizationManager` for multi-tenant setup with configurable settings per org (deepConsult limits, MFA requirements, audit retention).

### Step 5: Configure Session Management
Use Redis-backed sessions with 8-hour maxAge (typical clinical shift), rolling expiry, secure cookies, and re-authentication for sensitive operations.

## Output
- Role definitions with clinical permissions matrix
- SAML/OIDC SSO integration
- Permission middleware for Express routes
- Organization management with multi-tenant support
- Secure session handling with shift-based timeout

## Error Handling
| RBAC Issue | Detection | Resolution |
|------------|-----------|------------|
| SSO login fails | Auth callback error | Check IdP configuration and certificates |
| Wrong role assigned | User reports | Review IdP group-to-role mappings |
| Permission denied | 403 responses | Verify role has required permission |
| Session expired | User redirect | Implement session warning middleware |

## Examples

### Route Protection
```typescript
app.post('/api/clinical/query', requirePermission('clinicalQuery'), queryHandler);
app.post('/api/clinical/deepconsult', requirePermission('deepConsult'), deepConsultHandler);
app.get('/api/admin/audit-logs', requirePermission('viewAuditLogs'), auditLogsHandler);
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)
- [OpenID Connect](https://openid.net/connect/)
- [HIPAA Access Control](https://www.hhs.gov/hipaa/for-professionals/security/guidance/access-control/index.html)