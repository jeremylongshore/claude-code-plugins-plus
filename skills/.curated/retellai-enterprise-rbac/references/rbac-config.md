# RBAC Configuration Examples

## Role-Based Access Matrix

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

## Scoped API Keys

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
    "rate_limit_rpm": 200
  }'
```

## Agent Prompt Protection

```bash
set -euo pipefail
# List all agents and their last-modified timestamps
curl https://api.retellai.com/v1/agents \
  -H "Authorization: Bearer $RETELL_ADMIN_KEY" | \
  jq '.[] | {agent_id, agent_name, last_modified_at, modified_by}'

# Require approval for prompt changes to production agents
# Implement via CI/CD pipeline: agent config stored in git, changes require PR review
```

## Phone Number Assignment

```bash
set -euo pipefail
# Assign a phone number to a specific agent (admin only)
curl -X POST https://api.retellai.com/v1/phone-numbers/pn_abc123/assign \
  -H "Authorization: Bearer $RETELL_ADMIN_KEY" \
  -d '{"agent_id": "agt_xyz789"}'
```

## Call Recording Audit

```bash
set -euo pipefail
# Review recent calls with cost data
curl "https://api.retellai.com/v1/calls?limit=20&sort=-created_at" \
  -H "Authorization: Bearer $RETELL_ADMIN_KEY" | \
  jq '.[] | {call_id, agent_name, duration_minutes, cost_usd, caller_number, created_at}'
```
