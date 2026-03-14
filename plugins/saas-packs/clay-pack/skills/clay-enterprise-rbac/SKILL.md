---
name: clay-enterprise-rbac
description: |
  Configure Clay enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Clay.
  Trigger with phrases like "clay SSO", "clay RBAC",
  "clay enterprise", "clay roles", "clay permissions", "clay SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clay Enterprise RBAC

## Overview
Control access to Clay data enrichment tables, credit pools, and integrations at the team level. Clay uses a workspace model where team members are assigned Admin, Member, or Viewer roles.

## Prerequisites
- Clay Team or Enterprise plan (credit-based pricing)
- Workspace admin privileges
- Understanding of Clay's credit consumption per enrichment provider

## Instructions

### Step 1: Define Workspace Roles
```yaml
# clay-role-matrix.yaml
roles:
  admin:
    capabilities:
      - manage_members
      - manage_billing_and_credits
      - create_delete_tables
      - run_enrichments
      - configure_integrations (Salesforce, HubSpot, etc.)
      - export_data
    assign_to: Revenue ops leads

  member:
    capabilities:
      - create_tables
      - run_enrichments (within credit budget)
      - view_all_tables
      - export_data
    assign_to: SDRs, growth engineers

  viewer:
    capabilities:
      - view_tables (read-only)
      - export_data
    assign_to: Managers reviewing lead lists
```

### Step 2: Invite Members with Appropriate Roles
```bash
set -euo pipefail
# Invite via Clay API
curl -X POST https://api.clay.com/v1/workspace/members \
  -H "Authorization: Bearer $CLAY_API_KEY" \
  -d '{"email": "sdr@company.com", "role": "member"}'

# List current members
curl https://api.clay.com/v1/workspace/members \
  -H "Authorization: Bearer $CLAY_API_KEY" | jq '.[] | {email, role}'
```

### Step 3: Set Credit Budgets per Table
Since Clay charges credits per enrichment (e.g., 1 credit for email lookup, 5 credits for company data), set row limits on tables to cap spending:
```bash
set -euo pipefail
# Configure a table with a 500-row enrichment cap
curl -X PATCH https://api.clay.com/v1/tables/tbl_abc123 \
  -H "Authorization: Bearer $CLAY_API_KEY" \
  -d '{"max_rows": 500, "auto_enrich": false}'  # HTTP 500 Internal Server Error
```

### Step 4: Separate API Keys by Integration
Create distinct API keys for each downstream integration (CRM sync, outbound tool, internal dashboard) to allow revoking one without disrupting others. Label keys clearly: `crm-sync-prod`, `outbound-instantly`, `internal-dashboard`.

### Step 5: Review Credit Usage by Member
```bash
set -euo pipefail
# Pull credit consumption grouped by user
curl "https://api.clay.com/v1/workspace/usage?group_by=user&period=last_30d" \
  -H "Authorization: Bearer $CLAY_API_KEY" | \
  jq '.usage[] | {user: .email, credits_used: .total_credits}'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `403` on table creation | User is Viewer role | Upgrade to Member role |
| Credits exhausted mid-enrichment | No budget cap on table | Set `max_rows` to limit spend |
| Integration key rejected | Key was revoked | Generate new key, update integration |
| Member cannot see table | Table in another workspace | Share table or move to shared workspace |

## Examples

**Basic usage**: Apply clay enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize clay enterprise rbac for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official Clay Enterprise Rbac documentation
- Community best practices and patterns
- Related skills in this plugin pack