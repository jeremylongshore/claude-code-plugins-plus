---
name: granola-multi-env-setup
description: |
  Configure Granola across multiple workspaces and team environments.
  Use when setting up multi-team deployments, configuring workspace hierarchies,
  or managing enterprise-scale Granola installations.
  Trigger with phrases like "granola workspaces", "granola multi-team",
  "granola environments", "granola organization", "granola multi-env".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Multi-Environment Setup

## Overview
Configure Granola for multi-workspace and multi-team enterprise deployments.

## Prerequisites
- Granola Business or Enterprise plan
- Organization admin access
- Team structure defined
- SSO configured (recommended)

## Workspace Architecture

### Workspace Hierarchy
```
Organization (acme-corp)
├── Corporate Workspace
│   ├── Settings: Strictest privacy
│   ├── Access: Executive team only
│   └── Integrations: Private Notion
├── Engineering Workspace
│   ├── Settings: Team sharing
│   ├── Access: Engineering org
│   └── Integrations: Linear, GitHub
├── Sales Workspace
│   ├── Settings: CRM sync enabled
│   ├── Access: Sales + Success
│   └── Integrations: HubSpot, Gong
├── Customer Success Workspace
│   ├── Settings: CRM sync enabled
│   ├── Access: CS team
│   └── Integrations: HubSpot, Zendesk
└── HR Workspace
    ├── Settings: Confidential
    ├── Access: HR only
    └── Integrations: Greenhouse
```

## Workspace Creation

### Step 1: Plan Workspace Structure
```markdown
## Workspace Planning Template

For each workspace, define:
- Name: [Workspace Name]
- Purpose: [Primary use case]
- Owner: [Admin name/email]
- Members: [Group or individuals]
- Access Level: [Public/Private/Confidential]
- Integrations: [List required]
- Templates: [Shared/Custom]
- Retention: [Days/Months/Forever]
```

### Step 2: Create Workspaces
```markdown
## Workspace Creation

1. Organization Settings > Workspaces
2. Click "Create Workspace"
3. Configure:
   - Name: Engineering
   - Slug: engineering
   - Description: Engineering team meetings
   - Owner: eng-lead@company.com
4. Save and proceed to settings
```

### Step 3: Configure Per-Workspace Settings
```yaml
# Engineering Workspace Settings
Workspace: Engineering

Privacy:
  default_sharing: team
  external_sharing: disabled
  transcript_access: members_only

Integrations:
  - Slack: #dev-meetings channel
  - Linear: Auto-create tasks
  - Notion: Engineering wiki database
  - GitHub: Link PRs in notes

Templates:
  - Sprint Planning
  - Code Review
  - Tech Design
  - 1:1 Engineering

Retention:
  notes: 1 year
  transcripts: 90 days
  audio: 7 days

Permissions:
  - Admins: Full access
  - Members: Create, edit own
  - Viewers: Read only (for PMs)
```

## User Management

### User Provisioning
```markdown
## Provisioning Methods

Manual:
1. Settings > Members
2. Invite by email
3. Assign to workspace(s)
4. Set role

SSO/SCIM:
1. Configure SSO provider
2. Enable SCIM provisioning
3. Map groups to workspaces
4. Roles assigned by group

JIT (Just-in-Time):
1. Enable JIT provisioning
2. User signs in via SSO
3. Auto-added to default workspace
4. Upgrade as needed
```

### Role Definitions
| Role | Permissions | Use Case |
|------|------------|----------|
| Owner | Full admin + billing | Organization owner |
| Admin | Workspace management | Team leads |
| Member | Create + edit notes | Regular users |
| Viewer | Read only | Stakeholders |
| Guest | Single workspace | Contractors |

### Group Mappings
```yaml
# SSO Group → Granola Workspace Mapping

SSO Groups:
  engineering-team:
    workspace: Engineering
    role: member

  engineering-leads:
    workspace: Engineering
    role: admin

  sales-team:
    workspace: Sales
    role: member

  all-employees:
    workspace: General
    role: member
```

## Integration Per Environment

### Environment-Specific Integrations
```yaml
# Production Environment
Environment: Production

Workspaces:
  Sales:
    hubspot:
      portal_id: prod-12345  # port 12345 - example/test
      sync: bidirectional
      auto_create: true
    slack:
      workspace: acme-corp
      channel: #sales-meetings

  Engineering:
    linear:
      team_id: ENG
      auto_tasks: true
    github:
      org: acme-corp
      repo_linking: true

# Staging Environment (for testing)
Environment: Staging

Workspaces:
  Test-Sales:
    hubspot:
      portal_id: sandbox-67890  # 67890 = configured value
      sync: unidirectional
      auto_create: false
```

### Integration Testing
```markdown
## Pre-Production Testing

For each integration:
1. [ ] Test in staging workspace
2. [ ] Verify data flow
3. [ ] Check permissions
4. [ ] Validate error handling
5. [ ] Document configuration
6. [ ] Enable in production
```

## Cross-Workspace Features

### Shared Templates
```markdown
## Organization Templates

Location: Organization Settings > Templates

Template Sharing:
- Organization-wide templates
- Workspace-specific templates
- Personal templates

Hierarchy:
Org Templates > Workspace Templates > Personal Templates

Administration:
- Org templates: Org admins only
- Workspace templates: Workspace admins
- Personal: Individual users
```

### Cross-Workspace Search
```markdown
## Search Configuration

Enable:
1. Settings > Search > Cross-workspace search
2. Select participating workspaces
3. Configure access levels

Visibility Rules:
- Only sees notes they have access to
- Respects workspace permissions
- Excludes confidential workspaces
```

## Compliance Configuration

### Per-Workspace Compliance
```yaml
# HR Workspace - Strict Compliance
Workspace: HR

Compliance Settings:
  data_residency: us-west-2
  encryption: customer-managed-keys
  audit_logging: enabled
  retention:
    override: 30 days
    legal_hold: supported
  sharing:
    external: prohibited
    download: restricted
  access:
    mfa_required: true
    session_timeout: 4 hours
```

### Audit Configuration
```markdown
## Audit Log Settings

Events Logged:
- User sign-in/out
- Note created/edited/deleted
- Sharing changes
- Export requests
- Admin actions

Retention: 2 years
Export: Daily to SIEM
Format: JSON
Destination: Splunk/Datadog
```

## Environment Promotion

### Staging to Production
```markdown
## Configuration Promotion

1. Test in Staging Workspace
   - Create test workspace
   - Configure integrations
   - Validate with sample data

2. Document Configuration
   - Export settings (JSON)
   - Screenshot integrations
   - Note manual steps

3. Promote to Production
   - Create production workspace
   - Apply documented settings
   - Re-authorize integrations
   - Verify connections

4. Validate
   - Test meeting capture
   - Verify integration flow
   - Confirm permissions
   - Monitor for 24 hours
```

## Troubleshooting Multi-Env

### Common Issues
| Issue | Cause | Solution |
|-------|-------|----------|
| User in wrong workspace | SSO mapping error | Check group assignments |
| Integration not syncing | Wrong environment config | Verify API keys |
| Notes not visible | Permission mismatch | Check role assignment |
| Cross-workspace search failing | Feature not enabled | Enable in org settings |

## Resources
- [Granola Enterprise Admin](https://granola.ai/admin)
- [SSO Configuration](https://granola.ai/help/sso)
- [SCIM Provisioning](https://granola.ai/help/scim)

## Next Steps
Proceed to `granola-observability` for monitoring and analytics.

## Instructions

1. Assess the current state of the deployment configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with deployment |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply granola multi env setup to a standard project setup with default configuration options.

**Advanced scenario**: Customize granola multi env setup for production environments with multiple constraints and team-specific requirements.