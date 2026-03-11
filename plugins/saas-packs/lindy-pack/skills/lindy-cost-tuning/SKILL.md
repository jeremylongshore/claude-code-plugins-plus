---
name: lindy-cost-tuning
description: |
  Optimize Lindy AI costs and manage usage efficiently.
  Use when reducing costs, analyzing usage patterns,
  or optimizing budget allocation.
  Trigger with phrases like "lindy cost", "lindy billing",
  "reduce lindy spend", "lindy budget".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy Cost Tuning

## Overview
Optimize Lindy AI costs by managing active agent count, consolidating automations, and monitoring per-agent execution frequency. Lindy uses per-agent pricing where each active agent incurs a monthly cost regardless of how often it runs.

## Prerequisites
- Lindy Team or Enterprise workspace
- Admin access to agent management and billing
- Understanding of current agent portfolio

## Instructions

### Step 1: Audit Agent Utilization

### Step 2: Consolidate Similar Agents

### Step 3: Deactivate Underused Agents

### Step 4: Optimize Agent Step Efficiency
Reduce per-run costs by minimizing the number of tool calls in each agent:
- Combine multiple LLM calls into a single prompt with structured output
- Cache frequently accessed data (e.g., company directory) as agent context
- Use conditional branching to skip unnecessary steps

### Step 5: Monitor Monthly Spend

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Agent deactivated but still billed | Billing cycle overlap | Check billing date, deactivate before cycle end |
| Consolidated agent too complex | Too many branches | Split into 2-3 focused agents instead of 5+ single-task ones |
| Agent runs increasing cost | Trigger firing too frequently | Adjust trigger schedule or add deduplication |
| Cannot reduce below N agents | Business dependency | Document which agents are critical, optimize the rest |

## Examples

**Basic usage**: Apply lindy cost tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize lindy cost tuning for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [optimization implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Resources

- Official optimization documentation
- Community best practices and patterns
- Related skills in this plugin pack