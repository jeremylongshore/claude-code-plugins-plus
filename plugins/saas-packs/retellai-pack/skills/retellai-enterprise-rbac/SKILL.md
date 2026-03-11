---
name: retellai-enterprise-rbac
description: |
  Configure Retell AI enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Retell AI.
  Trigger with phrases like "retellai SSO", "retellai RBAC",
  "retellai enterprise", "retellai roles", "retellai permissions", "retellai SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Retell AI Enterprise RBAC

## Overview
Control access to Retell AI voice agents, phone numbers, and call recordings through organization-level roles and API key management. Retell uses per-minute pricing for voice calls, so RBAC must govern who can create voice agents, assign phone numbers, access call recordings, and modify agent prompts.

## Prerequisites
- Retell AI account with team plan (per-minute call pricing)
- Organization admin access at dashboard.retellai.com
- At least one phone number provisioned

## Instructions

### Step 1: Define Role-Based Access for Voice Operations
```yaml
# retell-rbac-matrix.yaml
roles:
  org_admin:
    permissions: [manage_members, manage_billing, manage_phone_numbers, all_agent_ops, access_all_recordings]
  agent_developer:
    permissions: [create_agent, edit_agent_prompt, test_agent, view_own_call_logs]
    restrictions: [cannot_assign_phone_numbers, cannot_access_billing]
  call_operator:
    permissions: [trigger_outbound_calls, view_call_logs, listen_recordings]
    restrictions: [cannot_edit_agents, cannot_manage_members]
  auditor:
    permissions: [view_call_logs, listen_recordings, export_transcripts]
    restrictions: [read_only]
```

### Step 2: Create Scoped API Keys
```bash
set -euo pipefail
# Key for the voice agent development team
curl -X POST https://api.retellai.com/v1/api-keys \
  -H "Authorization: Bearer $RETELL_ADMIN_KEY" \
  -d '{
    "name": "agent-dev-team",
    "scopes": ["agent:read", "agent:write", "call:read"],
    "rate_limit_rpm": 60
  }'

# Key for the call center integration (outbound calls only)
curl -X POST https://api.retellai.com/v1/api-keys \
  -H "Authorization: Bearer $RETELL_ADMIN_KEY" \
  -d '{
    "name": "call-center-prod",
    "scopes": ["call:create", "call:read"],
    "rate_limit_rpm": 200  # HTTP 200 OK
  }'
```

### Step 3: Protect Agent Prompt Changes
```bash
set -euo pipefail
# List all agents and their last-modified timestamps
curl https://api.retellai.com/v1/agents \
  -H "Authorization: Bearer $RETELL_ADMIN_KEY" | \
  jq '.[] | {agent_id, agent_name, last_modified_at, modified_by}'

# Require approval for prompt changes to production agents
# Implement via your CI/CD pipeline: agent config stored in git, changes require PR review
```

### Step 4: Control Phone Number Assignment
Only org admins should assign phone numbers to agents, as each number incurs monthly costs and represents the company's voice identity:
```bash
set -euo pipefail
# Assign a phone number to a specific agent (admin only)
curl -X POST https://api.retellai.com/v1/phone-numbers/pn_abc123/assign \
  -H "Authorization: Bearer $RETELL_ADMIN_KEY" \
  -d '{"agent_id": "agt_xyz789"}'
```

### Step 5: Audit Call Recordings and Transcripts
```bash
set -euo pipefail
# Review recent calls with cost data
curl "https://api.retellai.com/v1/calls?limit=20&sort=-created_at" \
  -H "Authorization: Bearer $RETELL_ADMIN_KEY" | \
  jq '.[] | {call_id, agent_name, duration_minutes, cost_usd, caller_number, created_at}'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `403` on agent update | Key missing `agent:write` scope | Create key with write scope |
| Phone number unassigned | Admin removed assignment | Reassign via phone number API |
| Call recording inaccessible | Retention policy expired | Extend retention in org settings |
| Agent prompt regression | Unauthorized edit | Store configs in git, require PR reviews |

## Examples

**Basic usage**: Apply retellai enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize retellai enterprise rbac for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official Retellai Enterprise Rbac documentation
- Community best practices and patterns
- Related skills in this plugin pack