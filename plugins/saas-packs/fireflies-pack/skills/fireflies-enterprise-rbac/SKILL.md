---
name: fireflies-enterprise-rbac
description: |
  Configure Fireflies.ai enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Fireflies.ai.
  Trigger with phrases like "fireflies SSO", "fireflies RBAC",
  "fireflies enterprise", "fireflies roles", "fireflies permissions", "fireflies SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Fireflies Enterprise RBAC

## Overview
Manage who can record, view, and share meeting transcripts in Fireflies.ai. Fireflies uses per-seat licensing with three workspace roles: Admin, Member, and Guest. Admins control recording policies, transcript visibility, and integration settings. Privacy controls determine whether transcripts are visible to the meeting organizer only, all attendees, or the entire workspace.

## Prerequisites
- Fireflies Business or Enterprise plan (per-seat pricing)
- Workspace admin privileges
- Calendar integration (Google Calendar or Outlook) connected

## Instructions

### Step 1: Configure Workspace Privacy Settings
Navigate to Fireflies Settings > Privacy:
```yaml
# Recommended enterprise privacy configuration
transcript_visibility: "attendees_only"   # Only meeting participants see transcript
auto_record: "internal_only"              # Only record meetings with internal participants
external_sharing: "admin_approval"        # External links require admin approval
download_permissions: "admins_only"       # Only admins can download raw audio
data_retention: "365_days"                # Auto-delete transcripts after 1 year
```

### Step 2: Manage Team Members via API
```bash
# Add a new member
curl -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -d '{"query": "mutation { addTeamMember(email: \"new@company.com\", role: MEMBER) { id email role } }"}'

# List all team members and their roles
curl -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -d '{"query": "{ teamMembers { id email role last_active } }"}'
```

### Step 3: Create Channel-Based Access Groups
Organize transcripts into channels (e.g., Sales, Engineering, Leadership) so team members only see transcripts relevant to their department:
```bash
# Create a private channel for leadership meetings
curl -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -d '{"query": "mutation { createChannel(name: \"Leadership\", visibility: PRIVATE, memberIds: [\"id1\", \"id2\"]) { id } }"}'
```

### Step 4: Configure SSO (Enterprise Only)
In Fireflies Admin > Security > SSO, enable SAML 2.0 and map IdP groups:
- `Engineering` -> Member (auto-record internal meetings)
- `Sales` -> Member (auto-record all meetings including external)
- `IT-Admins` -> Admin (full workspace control)

Enable "Enforce SSO" to require SSO for all workspace members.

### Step 5: Audit Transcript Access
```bash
# Query who accessed a specific transcript
curl -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -d '{"query": "{ transcript(id: \"tr_abc123\") { title views { user_email accessed_at } shares { shared_with shared_by } } }"}'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Bot not joining meetings | Calendar not connected | Re-authorize calendar integration |
| Transcript not visible | Privacy set to organizer-only | Change to attendees_only or add to channel |
| Seat limit exceeded | Too many active members | Remove inactive members or upgrade plan |
| SSO login fails | SAML assertion clock skew | Sync server clocks, allow 5-min skew tolerance |

## Examples
```bash
# Bulk remove inactive members (no activity in 90 days)
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -d '{"query": "{ teamMembers { id email last_active } }"}' | \
  jq -r '.data.teamMembers[] | select(.last_active < "2025-12-01") | .id' | \
  xargs -I{} echo "Remove member {}"
```
