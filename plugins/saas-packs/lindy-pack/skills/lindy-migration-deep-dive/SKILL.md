---
name: lindy-migration-deep-dive
description: |
  Advanced migration strategies for moving to Lindy AI from other platforms.
  Use when migrating from Zapier, Make, n8n, custom automations,
  or consolidating fragmented agent systems.
  Trigger with phrases like "lindy migration", "migrate to lindy",
  "zapier to lindy", "switch to lindy", "consolidate automations".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, migration]

---
# Lindy Migration Deep Dive

## Overview
Migrate existing automation workflows from Zapier, Make (Integromat), n8n,
LangChain, or custom code to Lindy AI. Key insight: Lindy replaces rigid
rule-based automations with AI agents that can reason, adapt, and handle
ambiguity — so migration is a redesign opportunity, not a 1:1 translation.

## Prerequisites
- Inventory of existing automations (source platform)
- Lindy workspace ready with required integrations authorized
- Migration timeline approved
- Rollback plan defined for customer-facing workflows

## Migration Source Comparison

| Source Platform | Lindy Equivalent | Key Difference |
|----------------|-----------------|----------------|
| **Zapier Zap** | Lindy Agent | AI reasoning replaces rigid if/then |
| **Make Scenario** | Lindy Agent | No-code builder instead of module chains |
| **n8n Workflow** | Lindy Agent | Managed infra, no self-hosting |
| **LangChain Agent** | Lindy Agent Step | No-code, managed, no Python needed |
| **Custom code** | HTTP Request + Run Code | Less code, AI fills gaps |

## Instructions

### Step 1: Inventory Source Automations
For each existing automation, document:

| Field | Example |
|-------|---------|
| **Name** | Support Email Triage |
| **Trigger** | New email in support@co.com |
| **Steps** | 1. Parse email 2. Classify 3. Route to channel |
| **Integrations** | Gmail, Slack, Sheets |
| **Frequency** | ~50 runs/day |
| **Complexity** | Medium (3 steps, 1 condition) |

### Step 2: Classify Migration Complexity
| Complexity | Criteria | Migration Approach | Time |
|-----------|---------|-------------------|------|
| **Simple** | 1-3 steps, no conditions | Build from scratch in Lindy | 30 min |
| **Medium** | 4-8 steps, conditions | Natural language description to Agent Builder | 1-2 hours |
| **Complex** | 9+ steps, multi-branch, loops | Redesign as multi-agent society | 1-2 days |
| **Custom code** | Python/JS logic | Run Code action + HTTP Request | 2-4 hours |

### Step 3: Migration Strategy by Source

**From Zapier**:
```
Zapier Pattern → Lindy Pattern
────────────────────────────────
Trigger (New Email) → Trigger (Email Received)
Filter Step → Trigger Filter (more efficient)
Formatter → AI Prompt field mode (AI does formatting)
Lookup → Knowledge Base search or HTTP Request
Multi-step Zap → Single agent with conditions
Paths → Conditions (natural language branching)
```

**From Make (Integromat)**:
```
Make Pattern → Lindy Pattern
────────────────────────────────
Scenario → Agent workflow
Module → Action step
Router → Conditions
Iterator → Loop
Aggregator → Run Code action (consolidation logic)
Error Handler → Agent prompt error instructions
```

**From n8n**:
```
n8n Pattern → Lindy Pattern
────────────────────────────────
Trigger Node → Trigger
Function Node → Run Code (Python/JS)
HTTP Request Node → HTTP Request action
IF Node → Condition
Merge Node → Agent step (AI merges intelligently)
```

**From LangChain/Custom Code**:
```
LangChain Pattern → Lindy Pattern
────────────────────────────────
Agent → Agent Step with skills
Tool → Action or HTTP Request
Memory → Lindy Memory (persistent)
Chain → Workflow steps
Vector Store → Knowledge Base
Retrieval Chain → Knowledge Base + AI Prompt
```

### Step 4: Execute Migration (Phased)

**Phase 1: Internal-Only Agents (Days 1-3)**
1. Migrate non-customer-facing automations first
2. Build in Lindy using natural language description
3. Test with real data for 48 hours
4. Compare output quality to source automation
5. Decommission source automation after verification

**Phase 2: Low-Risk Customer-Facing (Days 4-7)**
1. Build Lindy agent alongside existing automation (parallel run)
2. Route 10% of traffic to Lindy agent
3. Compare results for 48 hours
4. Gradually increase to 50%, then 100%
5. Monitor task success rate and response quality

**Phase 3: Critical Workflows (Days 8-14)**
1. Build Lindy agent as exact replacement
2. Test extensively with staging data
3. Schedule cutover during low-traffic window
4. Keep source automation pausable (not deleted) for 7 days
5. Monitor closely for 48 hours post-cutover

### Step 5: Redesign Opportunities
Migration is a chance to improve, not just replicate:

| Old Pattern | Lindy Improvement |
|------------|-------------------|
| Rigid if/then classification | AI classifies naturally, handles edge cases |
| Template-based email responses | AI generates contextual, personalized responses |
| Multiple automations for variations | Single agent with conditions handles all |
| Manual data transformation | Run Code action or AI handles transformation |
| No error handling | Agent prompt includes fallback behavior |

### Step 6: Validate and Cutover
```bash
# Post-migration validation checklist
echo "=== Migration Validation ==="

# 1. Task completion rate
echo "Check: Agent Tasks tab - expect >95% success rate"

# 2. Response quality
echo "Check: Compare 10 agent outputs to old automation outputs"

# 3. Trigger coverage
echo "Check: All events triggering correctly (no missed events)"

# 4. Performance
echo "Check: Task duration within acceptable range"

# 5. Cost
echo "Check: Credit consumption within budget"
```

## Migration Checklist
- [ ] Source system inventory complete
- [ ] Each automation classified by complexity
- [ ] Lindy integrations authorized
- [ ] Phase 1 (internal) agents migrated and verified
- [ ] Phase 2 (low-risk) agents running in parallel
- [ ] Phase 3 (critical) agents tested with staging data
- [ ] Cutover window scheduled
- [ ] Rollback procedure tested
- [ ] Source automations paused (not deleted)
- [ ] 7-day post-cutover monitoring complete
- [ ] Source automations decommissioned

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Output quality lower | AI prompt needs tuning | Add few-shot examples to agent prompt |
| Missing edge cases | Source had specific rules | Add condition branches or prompt instructions |
| Higher cost than expected | Overuse of large models | Right-size models per step |
| Integration auth fails | OAuth not set up in Lindy | Authorize integrations before migration |
| Data format mismatch | Different field names | Map fields in Run Code action |

## Resources
- [Lindy Templates](https://docs.lindy.ai/fundamentals/lindy-101/templates)
- [Lindy Agent Builder](https://www.lindy.ai/blog/ai-agent-tutorial)
- [Lindy Documentation](https://docs.lindy.ai)
- [Lindy vs n8n](https://www.lindy.ai/blog/n8n-ai-agents)

## Next Steps
This completes the Flagship tier. Review Standard and Pro skills for comprehensive
Lindy mastery.
