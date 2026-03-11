---
name: lindy-core-workflow-a
description: |
  Core Lindy workflow for creating and configuring AI agents.
  Use when building new agents, defining agent behaviors,
  or setting up agent capabilities.
  Trigger with phrases like "create lindy agent", "build lindy agent",
  "lindy agent workflow", "configure lindy agent".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy Core Workflow A: Agent Creation

## Overview
Complete workflow for creating, configuring, and deploying Lindy AI agents.

## Prerequisites
- Completed `lindy-install-auth` setup
- Understanding of agent use case
- Clear instructions/persona defined

## Instructions

### Step 1: Define Agent Specification
### Step 2: Create the Agent
### Step 3: Configure Agent Tools
### Step 4: Test the Agent

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Fully configured AI agent
- Connected tools and integrations
- Tested agent responses
- Ready for deployment

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Tool not found | Invalid tool name | Check available tools list |
| Instructions too long | Exceeds limit | Summarize or split instructions |
| Model unavailable | Unsupported model | Use default gpt-4 |

## Examples

### Complete Agent Creation Flow
## Resources
- [Lindy Agent Creation](https://docs.lindy.ai/agents/create)
- [Available Tools](https://docs.lindy.ai/tools)
- [Model Options](https://docs.lindy.ai/models)

## Next Steps
Proceed to `lindy-core-workflow-b` for task automation workflows.