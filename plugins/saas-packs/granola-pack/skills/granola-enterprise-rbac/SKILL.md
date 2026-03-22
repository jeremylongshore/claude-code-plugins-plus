---
name: granola-enterprise-rbac
description: |
  Configure enterprise role-based access control for Granola workspaces.
  Use when defining user roles, setting sharing permissions, configuring SSO group mappings,
  or implementing least-privilege access for meeting data.
  Trigger: "granola roles", "granola permissions", "granola access control",
  "granola RBAC", "granola admin roles".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, rbac, enterprise, security]

---
# Granola Enterprise RBAC

## Overview
Configure role-based access control for Granola with SSO group mapping, per-workspace permissions, sharing policies, and audit logging. Granola's role hierarchy controls who can create, share, and manage meeting notes across the organization.

## Prerequisites
- Granola Enterprise plan ($35+/user/month)
- Organization admin access
- SSO configured (Okta, Azure AD, or Google Workspace)
- SCIM provisioning enabled (recommended for automated role assignment)

## Instructions

### Step 1 — Understand the Role Hierarchy

```
Organization Owner (1-2 people)
  │   Full control: billing, SSO, org settings, all workspaces
  │
  ├── Workspace Admin (per department)
  │     Manage workspace: members, integrations, settings
  │     All member capabilities
  │
  ├── Team Lead
  │     View team analytics, manage folder structure
  │     All member capabilities
  │
  ├── Member (default role)
  │     Create notes, share internally, use integrations
  │
  ├── Viewer
  │     Read-only access to shared notes
  │     Cannot create or record meetings
  │
  └── Guest (external)
      Single workspace access, read-only
      Time-limited (30-day default expiration)
```

### Step 2 — Permission Matrix

| Permission | Owner | WS Admin | Lead | Member | Viewer | Guest |
|-----------|-------|----------|------|--------|--------|-------|
| Record meetings | Yes | Yes | Yes | Yes | No | No |
| Create notes | Yes | Yes | Yes | Yes | No | No |
| Share internally | Yes | Yes | Yes | Yes | No | No |
| Share externally | Yes | Yes | Policy | Policy | No | No |
| View shared notes | Yes | Yes | Yes | Yes | Yes | Yes |
| Manage integrations | Yes | Yes | No | No | No | No |
| Manage members | Yes | Yes | No | No | No | No |
| View analytics | Yes | Yes | Yes | No | No | No |
| Configure retention | Yes | Yes | No | No | No | No |
| Manage billing | Yes | No | No | No | No | No |
| Configure SSO/SCIM | Yes | No | No | No | No | No |

### Step 3 — Map SSO Groups to Roles

Configure in Organization Settings > Security > SSO > Group Mapping:

| SSO Group (IdP) | Granola Workspace | Granola Role |
|-----------------|------------------|-------------|
| `engineering-all` | Engineering | Member |
| `engineering-leads` | Engineering | Admin |
| `sales-team` | Sales | Member |
| `sales-managers` | Sales | Admin |
| `product-team` | Product | Member |
| `hr-team` | HR | Member |
| `hr-directors` | HR | Admin |
| `executives` | Executive | Admin |
| `contractors-eng` | Engineering | Guest |

**Multi-workspace membership:**
A user can belong to multiple workspaces with different roles:
- Sarah Chen: Engineering (Member) + Product (Admin) + Executive (Viewer)
- Mike Johnson: Sales (Admin) + Engineering (Guest for cross-team visibility)

### Step 4 — Configure Sharing Policies

Set per-workspace sharing rules to control data flow:

**Standard workspaces (Engineering, Product, Sales):**
```
Workspace Settings > Sharing:
  Internal sharing: Automatic within workspace members
  Cross-workspace: Allowed with admin approval
  External sharing: Allowed with link expiration (30 days)
  Public links: Disabled
```

**Confidential workspaces (HR, Executive):**
```
Workspace Settings > Sharing:
  Internal sharing: Manual only (no auto-share)
  Cross-workspace: Disabled
  External sharing: Disabled
  Public links: Disabled
  Note visibility: Creator + explicitly added viewers only
```

### Step 5 — Implement Least Privilege

Follow the principle of least privilege for role assignments:

1. **Default new users to Member** — sufficient for 90% of use cases
2. **Promote to Admin only for workspace managers** — IT leads, department heads
3. **Use Viewer for stakeholders** who need to read notes but not create them
4. **Time-limit Guest access** — 30-day default, renew explicitly
5. **Review access quarterly:**

```markdown
## Quarterly Access Review Checklist

- [ ] Pull current user list: Settings > Team
- [ ] Verify each user's role matches current job function
- [ ] Deactivate users who have left the organization
- [ ] Downgrade over-privileged users (Admin → Member where appropriate)
- [ ] Remove expired Guest accounts
- [ ] Verify SSO group mappings match current org chart
- [ ] Review sharing policy compliance per workspace
- [ ] Check audit logs for unusual access patterns
```

### Step 6 — Enable Audit Logging

Enterprise audit logging captures:

| Event | What's Logged |
|-------|--------------|
| User login | Who, when, from where (IP) |
| Note created | Creator, meeting, workspace |
| Note shared | Sharer, recipient, method (Slack/Notion/link) |
| Note exported | Who exported, which note |
| Role changed | Admin, user affected, old role → new role |
| Integration connected/disconnected | Who, which integration |
| Workspace settings changed | Admin, what changed |

Access audit logs: Organization Settings > **Security** > **Audit Log**

**Export audit logs** for SIEM integration (Enterprise):
- Granola can export audit events to external systems
- Contact Granola support for Splunk/Datadog/SIEM integration

### Step 7 — Handle User Lifecycle

**Onboarding:**
1. User added to SSO group → SCIM provisions account → JIT assigns workspace + role
2. First login: SSO authenticates, Granola provisions based on group mapping
3. User can immediately record meetings in assigned workspaces

**Role change:**
1. Update SSO group membership in IdP
2. SCIM sync updates Granola role (within sync interval, typically 1-15 min)
3. Or manually: Workspace Settings > Members > change role

**Offboarding:**
1. Disable user in IdP → SCIM deactivates Granola account
2. User loses access immediately
3. Their shared notes remain visible to workspace members
4. Their private notes are inaccessible (retained per retention policy)
5. Reassign ownership of shared folders if needed

## Output
- Role hierarchy defined and documented
- SSO group mappings configured for automated provisioning
- Per-workspace sharing policies enforced
- Audit logging enabled with SIEM export (if applicable)
- User lifecycle procedures (onboard/offboard) established
- Quarterly access review cadence scheduled

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| User can't access workspace | Wrong SSO group | Verify IdP group membership |
| External sharing blocked unexpectedly | Workspace policy override | Review workspace sharing settings |
| Guest access expired | 30-day time limit | Re-invite the guest or extend expiration |
| SCIM sync delayed | IdP sync interval too long | Trigger manual sync in IdP, or adjust interval |
| Orphaned accounts after termination | SCIM deprovisioning not configured | Enable deprovisioning in SCIM settings |

## Resources
- [Security Standards](https://docs.granola.ai/help-center/consent-security-privacy/our-security-standards)
- [Privacy & Data FAQs](https://docs.granola.ai/help-center/consent-security-privacy/security-privacy-data-faqs)
- [Enterprise API (admin access)](https://docs.granola.ai/help-center/sharing/integrations/enterprise-api)

## Next Steps
Proceed to `granola-migration-deep-dive` for migrating from other meeting note tools.
