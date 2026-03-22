---
name: lindy-enterprise-rbac
description: |
  Configure enterprise role-based access control for Lindy AI workspaces.
  Use when setting up team permissions, managing workspace access,
  or implementing enterprise security policies with SSO/SCIM.
  Trigger with phrases like "lindy permissions", "lindy RBAC",
  "lindy access control", "lindy enterprise security", "lindy SSO".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, security, rbac]

---
# Lindy Enterprise RBAC

## Overview
Lindy organizes access around **workspaces** where agents live. Team members
are assigned roles that control who can create, modify, run, or observe agents
and their execution history. Enterprise features add SSO, SCIM, audit logs,
and granular permission controls.

## Prerequisites
- Lindy Team ($49.99/mo + $19.99/seat) or Enterprise plan
- Workspace owner privileges
- Team members invited to the workspace

## Lindy Role Model

| Role | Create Agents | Edit Agents | Run Agents | View Tasks | Manage Team |
|------|:------------:|:-----------:|:----------:|:----------:|:-----------:|
| **Owner** | Yes | Yes | Yes | Yes | Yes |
| **Editor** | Yes | Yes | Yes | Yes | No |
| **Viewer** | No | No | No | Yes | No |

## Instructions

### Step 1: Map Organizational Roles to Lindy Roles
| Org Role | Lindy Role | Rationale |
|---------|-----------|-----------|
| Engineering Lead | Owner | Full workspace control |
| Developer | Editor | Build and modify agents |
| Ops/Support | Editor | Run agents and configure workflows |
| Manager | Viewer | Monitor task execution and metrics |
| Stakeholder | Viewer | Read-only access to results |

### Step 2: Invite Team Members
1. Go to **Settings > Team** in the Lindy dashboard
2. Click **Invite Member**
3. Enter email address
4. Select role: Owner, Editor, or Viewer
5. Confirm invitation

**Pro plan**: Each additional seat costs $19.99/month
**Enterprise plan**: Custom pricing with bulk seat discounts

### Step 3: Organize Agents with Folders
Use folders to organize agents by team, function, or environment:
```
Workspace: Acme Corp Production
├── Support/
│   ├── Email Triage Agent
│   ├── FAQ Chatbot
│   └── Escalation Agent
├── Sales/
│   ├── Lead Router
│   ├── Follow-up Agent
│   └── Meeting Scheduler
├── Operations/
│   ├── Daily Report Agent
│   ├── Monitoring Agent
│   └── Data Pipeline Agent
└── Shared/
    ├── Knowledge Base Agent
    └── Notification Agent
```

**Folder permissions**: Share folders with specific team members to control
visibility. Agents in private folders are only visible to the folder owner.

### Step 4: Agent Sharing Controls
Each agent can be shared independently:

| Sharing Level | Who Gets It | What They Can Do |
|--------------|-------------|-----------------|
| **Edit access** | Team collaborators | Edit agent, see all tasks |
| **User access** | Agent consumers | Run agent, trigger workflows |
| **Template** | Anyone with link | Make a copy (no access to original) |

### Step 5: Connection Sharing
Control which team members can use shared integration connections:
- **Private connections**: Only the connection creator can use them
- **Shared connections**: Any team member can use them in their agents
- **Recommendation**: Keep sensitive connections (payment gateways, databases) private

### Step 6: API Key Isolation
Create separate API keys per integration purpose:

| API Key | Purpose | Scope | Rotation |
|---------|---------|-------|----------|
| `lnd_prod_app_xxxx` | Application webhook triggers | Production only | 90 days |
| `lnd_prod_ci_xxxx` | CI/CD smoke tests | Test agents only | 90 days |
| `lnd_prod_monitor_xxxx` | Monitoring/observability | Read-only | 90 days |

Revoke keys immediately when a team member with access leaves the organization.

### Step 7: Enterprise Security Features

**SSO (Single Sign-On)**:
- SAML-based authentication
- Configure in Enterprise settings
- Users authenticate through your identity provider
- Automatic session management

**SCIM (User Provisioning)**:
- Automated user creation and deactivation
- Sync with your identity provider (Okta, Azure AD, etc.)
- When an employee leaves, SCIM automatically revokes Lindy access
- Group mappings to Lindy roles

**Audit Logs**:
- Complete activity trail for compliance
- Track who created, modified, or deleted agents
- Track who accessed task data
- Export for security review

**Encryption**:
- AES-256 encryption at rest
- TLS encryption in transit
- No data sharing between workspaces

### Step 8: Offboarding Procedure
When a team member leaves:
1. SCIM auto-deactivates their account (Enterprise) or manually remove
2. Revoke any API keys they had access to
3. Transfer ownership of agents they created
4. Review and re-authorize any integrations they set up
5. Audit recent task history for their agents

## Access Control Checklist
- [ ] Team roles mapped to Lindy roles
- [ ] All team members invited with appropriate role
- [ ] Agents organized in folders by team/function
- [ ] Sensitive agents in private folders
- [ ] Connections shared only as needed
- [ ] Separate API keys per integration purpose
- [ ] Key rotation schedule (90-day max)
- [ ] Enterprise: SSO enabled
- [ ] Enterprise: SCIM configured
- [ ] Enterprise: Audit log review scheduled (monthly)
- [ ] Offboarding procedure documented

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `403 Forbidden` on agent create | User has Viewer role | Promote to Editor |
| Agent not visible to teammate | Agent in private folder | Move to shared folder |
| API key returns `401` | Key revoked or expired | Generate new key |
| Cannot delete workspace | Not the Owner | Transfer ownership first |
| SSO login fails | SAML misconfigured | Verify IdP metadata and assertions |
| SCIM not syncing | Endpoint URL wrong | Check SCIM endpoint in IdP config |

## Resources
- [Lindy Documentation](https://docs.lindy.ai)
- [Lindy Security](https://www.lindy.ai/security)
- [Lindy Pricing](https://www.lindy.ai/pricing)

## Next Steps
Proceed to `lindy-migration-deep-dive` for platform migration strategies.
