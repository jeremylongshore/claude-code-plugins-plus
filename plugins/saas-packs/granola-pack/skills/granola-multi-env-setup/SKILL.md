---
name: granola-multi-env-setup
description: |
  Configure Granola across multiple workspaces and teams with SSO/SCIM provisioning.
  Use when setting up department-level workspaces, configuring user provisioning,
  or managing enterprise-scale Granola deployments.
  Trigger: "granola workspaces", "granola multi-team", "granola SSO",
  "granola SCIM", "granola organization setup".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, deployment, scaling, enterprise]

---
# Granola Multi-Environment Setup

## Overview
Configure Granola for multi-workspace enterprise deployments with SSO-based user provisioning, per-workspace integration configuration, and compliance controls. Each workspace operates as an isolated unit with its own folders, integrations, sharing rules, and retention policies.

## Prerequisites
- Granola Enterprise plan ($35+/user/month)
- Organization admin access in Granola
- Identity provider configured (Okta, Azure AD, or Google Workspace)
- Team structure and workspace plan documented

## Instructions

### Step 1 — Plan Workspace Structure

Map your organization to Granola workspaces:

| Workspace | Owner | Members | Purpose |
|-----------|-------|---------|---------|
| Engineering | VP Engineering | All engineers | Sprint planning, architecture, standups |
| Sales | VP Sales | Sales team + SDRs | Discovery calls, demos, pipeline reviews |
| Product | Head of Product | PMs + designers | Customer feedback, design reviews, PRDs |
| Customer Success | CS Lead | CS managers | Onboarding calls, QBRs, escalations |
| HR | HR Director | HR team | Interviews, 1-on-1s, performance reviews |
| Executive | CEO | C-suite | Board meetings, strategy, M&A |

### Step 2 — Create Workspaces

1. Navigate to Organization Settings > **Workspaces**
2. For each workspace:
   - **Name:** Department name (e.g., "Engineering")
   - **Description:** Purpose and scope
   - **Owner:** Department lead (Workspace Admin role)
   - **Privacy:** Private (members only) or Internal (org-visible)
   - **Default sharing:** Private for new notes

### Step 3 — Configure SSO and User Provisioning

**SSO Setup (Okta example):**
1. Organization Settings > **Security** > **SSO**
2. Choose SAML 2.0 or OIDC
3. Configure in your IdP:
   - Entity ID: `https://app.granola.ai/sso/{org-slug}`
   - ACS URL: `https://app.granola.ai/sso/callback`
   - Name ID: Email address
4. Test with a pilot user before enforcing org-wide

**SCIM Provisioning:**
1. Organization Settings > **Security** > **SCIM**
2. Generate SCIM token
3. Configure in your IdP:
   - SCIM endpoint: `https://api.granola.ai/scim/v2/{org-id}`
   - Bearer token: Generated in step 2
4. Map IdP groups to Granola workspaces and roles:

| IdP Group | Granola Workspace | Role |
|-----------|------------------|------|
| `granola-engineering` | Engineering | Member |
| `granola-engineering-leads` | Engineering | Admin |
| `granola-sales` | Sales | Member |
| `granola-hr` | HR | Member |
| `granola-executives` | Executive | Admin |

**Just-in-Time (JIT) Provisioning:**
Enable JIT so users are auto-provisioned on first SSO login without manual invitation. Map their IdP groups to workspace membership.

### Step 4 — Configure Per-Workspace Integrations

Each workspace can have independent integration configurations:

| Workspace | Slack Channel | CRM | Notion Database | Task Tool |
|-----------|-------------|-----|----------------|-----------|
| Engineering | #eng-meetings | — | Engineering Wiki | Linear |
| Sales | #sales-notes | HubSpot | Sales Playbook | — |
| Product | #product-feedback | — | Product Insights | Linear |
| Customer Success | #cs-updates | Attio | CS Knowledge Base | — |
| HR | (none) | — | (none) | — |
| Executive | (none) | — | Private Board DB | — |

Configure in each workspace: Settings > Integrations. Each workspace's integrations are independent — connecting Slack in Engineering does not affect Sales.

### Step 5 — Set Compliance Controls Per Workspace

| Workspace | Data Retention (Notes) | Data Retention (Transcripts) | External Sharing | Audit Logging |
|-----------|----------------------|----------------------------|-----------------|---------------|
| Engineering | 2 years | 90 days | Allowed (admin approval) | On |
| Sales | 1 year | 90 days | Allowed (for client follow-up) | On |
| Product | 2 years | 90 days | Allowed (admin approval) | On |
| HR | **90 days** | **30 days** | **Prohibited** | On |
| Executive | **Custom (legal hold)** | **30 days** | **Prohibited** | On |

**Sensitive workspace hardening (HR, Executive):**
```
Workspace Settings > Security:
  External sharing: Disabled
  Public links: Disabled
  Link expiration: 7 days (if any sharing enabled)
  MFA required: Yes (beyond SSO)
  Session timeout: 4 hours
  AI training opt-out: Enforced
  IP allowlist: Enabled (office IPs only)
```

### Step 6 — Role Hierarchy and Permissions

| Role | Create Notes | Share Internally | Share Externally | Manage Members | Manage Settings |
|------|-------------|-----------------|-----------------|---------------|----------------|
| Org Owner | Yes | Yes | Yes | Yes (all workspaces) | Yes (org-level) |
| Workspace Admin | Yes | Yes | Yes (if policy allows) | Yes (own workspace) | Yes (workspace) |
| Team Lead | Yes | Yes | Yes (if policy allows) | View only | No |
| Member | Yes | Yes | No (unless admin approves) | No | No |
| Viewer | No | Read-only | No | No | No |
| Guest | No | Single workspace read | No | No | No |

### Step 7 — Validate and Monitor

**Validation checklist:**
- [ ] All workspaces created with correct owners
- [ ] SSO login tested with users from each IdP group
- [ ] SCIM sync verified (user added to IdP group → appears in workspace)
- [ ] Per-workspace integrations tested with sample meetings
- [ ] Compliance settings verified for sensitive workspaces (HR, Executive)
- [ ] Cross-workspace search working for admin users
- [ ] Audit logs capturing expected events

**Ongoing monitoring:**
- Monthly: Review workspace membership, deactivate departed users
- Quarterly: Access review across all workspaces (principle of least privilege)
- Annual: Re-certify compliance settings, update retention policies

## Output
- Multi-workspace topology deployed and configured
- SSO and SCIM provisioning operational
- Per-workspace integrations connected and tested
- Compliance controls applied with sensitive workspace hardening
- Role hierarchy documented and enforced

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| User lands in wrong workspace | SSO group mapping incorrect | Fix IdP group → workspace mapping |
| SCIM sync fails | Token expired or endpoint wrong | Regenerate SCIM token, verify endpoint URL |
| Cross-workspace notes invisible | User not added to target workspace | Add user to workspace or grant Viewer role |
| Integration not syncing in workspace | Connected to different workspace | Reconnect integration within the correct workspace context |
| JIT provisioning creates duplicate users | Multiple IdP groups | Consolidate groups, ensure one user maps to one account |

## Resources
- [Granola Enterprise](https://www.granola.ai/security)
- [Signing In and Calendar Connection](https://docs.granola.ai/help-center/signing-in-and-connecting-your-calendar)
- [Sign In with Microsoft](https://docs.granola.ai/help-center/sign-in-with-microsoft)
- [Security Standards](https://docs.granola.ai/help-center/consent-security-privacy/our-security-standards)

## Next Steps
Proceed to `granola-observability` for meeting analytics and monitoring.
