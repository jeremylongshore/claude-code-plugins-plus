# Granola Workspace Configuration Reference

## Workspace Hierarchy Example

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

## Per-Workspace Settings Template

```yaml
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

## User Provisioning Methods

### Manual Provisioning

1. Settings > Members
2. Invite by email
3. Assign to workspace(s)
4. Set role

### SSO/SCIM Provisioning

1. Configure SSO provider
2. Enable SCIM provisioning
3. Map groups to workspaces
4. Roles assigned by group

### JIT (Just-in-Time) Provisioning

1. Enable JIT provisioning
2. User signs in via SSO
3. Auto-added to default workspace
4. Upgrade as needed

## SSO Group Mapping

```yaml
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

## Environment-Specific Integration Config

```yaml
# Production Environment
Workspaces:
  Sales:
    hubspot:
      portal_id: prod-12345
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
Workspaces:
  Test-Sales:
    hubspot:
      portal_id: sandbox-67890
      sync: unidirectional
      auto_create: false
```

## Compliance Configuration (HR Workspace)

```yaml
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

## Audit Configuration

Events Logged: user sign-in/out, note created/edited/deleted, sharing changes, export requests, admin actions

Retention: 2 years | Export: Daily to SIEM | Format: JSON | Destination: Splunk/Datadog

## Cross-Workspace Features

### Shared Templates

- Organization-wide templates (Org admins only)
- Workspace-specific templates (Workspace admins)
- Personal templates (Individual users)

### Cross-Workspace Search

1. Settings > Search > Cross-workspace search
2. Select participating workspaces
3. Configure access levels
4. Respects workspace permissions, excludes confidential workspaces

## Environment Promotion: Staging to Production

1. Test in staging workspace with sample data
2. Document configuration (export settings as JSON)
3. Create production workspace and apply documented settings
4. Re-authorize integrations and verify connections
5. Monitor for 24 hours after go-live
