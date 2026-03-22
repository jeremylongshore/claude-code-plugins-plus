---
name: lindy-upgrade-migration
description: |
  Manage Lindy agent configuration changes, platform updates, and migrations.
  Use when reconfiguring agents, handling platform changes,
  or migrating agents between workspaces.
  Trigger with phrases like "upgrade lindy", "lindy migration",
  "lindy reconfigure", "update lindy agents", "lindy workspace migration".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, migration]

---
# Lindy Upgrade & Migration

## Overview
Lindy is a managed platform — agents run on Lindy's infrastructure. "Upgrades"
mean reconfiguring agents for new capabilities, migrating agents between workspaces,
or adapting to platform changes. Key concern: agents with webhooks, Lindymail,
and phone numbers require reconfiguration after migration.

## Prerequisites
- Admin access to source and target Lindy workspaces
- Inventory of all agents, triggers, and integrations
- Migration window scheduled for customer-facing agents

## Instructions

### Step 1: Inventory Current Agents
Document every agent before making changes:

| Agent Name | Trigger Type | Actions | Integrations | Webhook URL | Phone # |
|-----------|-------------|---------|--------------|-------------|---------|
| Support Bot | Email Received | Gmail Reply, Slack Notify | Gmail, Slack | N/A | N/A |
| Lead Router | Webhook | Sheets Update, Slack DM | Sheets, Slack | `https://public.lindy.ai/...` | N/A |
| Phone Screener | Call Received | Transfer, Agent Send | Phone | N/A | +1-555-0100 |

### Step 2: Export Agent Configurations
For each agent, document:
- **Prompt**: Copy full text from Settings > Prompt
- **Model**: Which AI model is selected
- **Skills/Actions**: List all action steps and their configurations
- **Trigger filters**: Copy filter conditions
- **Knowledge Base**: Note all sources (files, URLs, integrations)
- **Memories**: Export any persistent memories
- **Exit conditions**: Copy all condition text

### Step 3: Plan Migration Order
```
Phase 1: Internal-only agents (no customer impact)
  → Migrate, test, verify for 24-48 hours

Phase 2: Low-risk customer-facing agents (email triage, notifications)
  → Migrate during low-traffic window
  → Monitor for 24 hours

Phase 3: Critical agents (phone, live chat, lead routing)
  → Migrate with rollback plan ready
  → Keep old agent active in parallel for 48 hours
```

### Step 4: Migrate Agent to New Workspace
**Option A — Template sharing**:
1. In source workspace: Share agent as **Template**
2. In target workspace: Import template
3. Reconfigure integrations (OAuth tokens are NOT transferred)
4. Re-authorize all connected services

**Option B — Manual recreation**:
1. Create new agent in target workspace
2. Paste saved prompt
3. Recreate trigger with same configuration
4. Re-add all actions and configure fields
5. Upload knowledge base files
6. Re-create memories

### Step 5: Reconfigure Webhooks, Email, and Phone
These require special attention — they are NOT automatically transferred:

**Webhooks**:
- New agent gets a NEW webhook URL
- Update all calling systems with the new URL
- Generate new webhook secret
- Update all clients with new Bearer token

**Lindymail** (Lindy-assigned email addresses):
- New agent gets a new Lindymail address
- Update forwarding rules and any published email addresses

**Phone numbers**:
- Phone numbers may need to be re-provisioned ($10/month each)
- Update IVR systems and published phone numbers
- Test call quality and language settings

### Step 6: Parallel Run & Cutover
```
Day 1-2: Both old and new agents active
  → Route test traffic to new agent
  → Compare task completion rates and output quality

Day 3: Gradual cutover
  → Redirect 50% of traffic to new agent
  → Monitor error rates and credit consumption

Day 4: Full cutover
  → Route 100% to new agent
  → Keep old agent paused (not deleted) for 7 days

Day 11: Cleanup
  → Delete old agent after 7-day safety window
```

### Step 7: Verify Post-Migration
- [ ] All triggers firing correctly
- [ ] All actions completing successfully
- [ ] Knowledge base returning relevant results
- [ ] Webhook URLs updated in all calling systems
- [ ] Phone numbers tested (inbound and outbound)
- [ ] Credit consumption within expected range
- [ ] Team members have correct access in new workspace

## Common Migration Scenarios

### Scenario: Consolidating Multiple Agents
When you have too many single-purpose agents:
1. Identify agents with overlapping triggers
2. Merge prompts into sections (use `## Billing`, `## Technical`, etc.)
3. Add conditions to route based on content
4. Reduce total active agents → lower costs

### Scenario: Upgrading Agent Capabilities
When Lindy adds new features (new actions, new models):
1. Review [Lindy Changelog](https://www.lindy.ai/changelog)
2. Update model selection if better options available
3. Replace workaround actions with new native actions
4. Test thoroughly — model changes affect output quality

### Scenario: Environment Promotion (Dev to Prod)
1. Share dev agent as Template
2. Import in production workspace
3. Re-authorize all production integrations
4. Update webhook URLs to production endpoints
5. Verify trigger filters match production requirements

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook URL changed | New agent gets new URL | Update all callers with new URL |
| Integration auth failed | OAuth not transferred | Re-authorize in new workspace |
| Knowledge base empty | Files not re-uploaded | Upload files to new agent's KB |
| Phone number unavailable | Not re-provisioned | Purchase new number in settings |
| Memory lost | Memories not exported | Manually re-create critical memories |

## Resources
- [Lindy Changelog](https://www.lindy.ai/changelog)
- [Lindy Templates](https://docs.lindy.ai/fundamentals/lindy-101/templates)
- [Lindy Documentation](https://docs.lindy.ai)

## Next Steps
Proceed to Pro tier skills for advanced CI integration, deployment, and performance.
