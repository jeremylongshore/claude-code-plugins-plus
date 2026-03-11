# Lindy Enterprise Rbac - Implementation Guide

# Lindy Enterprise RBAC

## Overview
Manage team-level access control for Lindy AI agents and automations. Lindy organizes access around workspaces where agents live, with team members assigned Owner, Editor, or Viewer roles that govern who can create, modify, run, or merely observe AI agents and their execution history.

## Prerequisites
- Lindy Team or Enterprise plan (per-agent pricing applies)
- Workspace owner or admin privileges
- Team members invited to the Lindy workspace

## Instructions

### Step 1: Map Organizational Roles to Lindy Permissions
```yaml
# lindy-rbac-mapping.yaml
roles:
  workspace_owner:
    permissions: [manage_billing, invite_members, delete_workspace, all_agent_ops]
    assign_to: Engineering leads, department heads
  editor:
    permissions: [create_agent, edit_agent, run_agent, view_runs, manage_tools]
    assign_to: Developers building automations
  viewer:
    permissions: [view_agent, view_runs, trigger_shared_agents]
    assign_to: Stakeholders reviewing agent output
```

### Step 2: Configure Team Membership via API
```bash
# Invite a member with a specific role
curl -X POST https://api.lindy.ai/v1/workspace/members \
  -H "Authorization: Bearer $LINDY_API_KEY" \
  -d '{"email": "dev@company.com", "role": "editor"}'

# List current workspace members and their roles
curl https://api.lindy.ai/v1/workspace/members \
  -H "Authorization: Bearer $LINDY_API_KEY"
```

### Step 3: Restrict Agent Visibility per Team
```bash
# Assign an agent to a specific team folder so only that team sees it
curl -X PATCH https://api.lindy.ai/v1/agents/agt_abc123 \
  -H "Authorization: Bearer $LINDY_API_KEY" \
  -d '{"folder_id": "fld_sales_team", "visibility": "team_only"}'
```

### Step 4: Audit Agent Access
```bash
# Pull the activity log filtered by user and action type
curl "https://api.lindy.ai/v1/workspace/audit-log?actor=dev@company.com&action=agent.run&limit=50" \
  -H "Authorization: Bearer $LINDY_API_KEY"
```

### Step 5: Enforce API Key Scoping
Create separate API keys per integration rather than sharing a single workspace key. Rotate keys on a 90-day schedule and revoke immediately when a team member leaves.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `403 Forbidden` on agent create | User has Viewer role | Promote to Editor in workspace settings |
| Agent not visible to teammate | Agent in private folder | Move to shared team folder or adjust visibility |
| API key returns `401` | Key revoked or expired | Generate new key in workspace settings |
| Cannot delete workspace | Not the Owner | Transfer ownership first via account settings |

## Examples
```bash
# Bulk invite a team from a CSV: email,role
while IFS=, read -r email role; do
  curl -s -X POST https://api.lindy.ai/v1/workspace/members \
    -H "Authorization: Bearer $LINDY_API_KEY" \
    -d "{\"email\": \"$email\", \"role\": \"$role\"}"
done < team-members.csv
```

```bash
# Downgrade all editors to viewers (offboarding a project)
curl -s https://api.lindy.ai/v1/workspace/members \
  -H "Authorization: Bearer $LINDY_API_KEY" | \
  jq -r '.members[] | select(.role=="editor") | .id' | \
  xargs -I{} curl -s -X PATCH "https://api.lindy.ai/v1/workspace/members/{}" \
    -H "Authorization: Bearer $LINDY_API_KEY" \
    -d '{"role": "viewer"}'
```
