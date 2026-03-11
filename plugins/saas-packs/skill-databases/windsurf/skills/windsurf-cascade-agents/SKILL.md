---
name: "windsurf-cascade-agents"
description: |
  Create custom Cascade agent configurations for specialized tasks. Activate when users mention
  "custom cascade agent", "specialized ai agent", "domain-specific cascade", "agent configuration",
  or "custom ai behavior". Handles custom agent creation and configuration. Use when working with windsurf cascade agents functionality. Trigger with phrases like "windsurf cascade agents", "windsurf agents", "windsurf".
allowed-tools: "Read,Write,Edit,Bash(cmd:*),Grep,Glob"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---

# Windsurf Cascade Agents

## Overview

This skill enables creation of specialized Cascade agents tailored for specific domains or tasks. Custom agents can be configured with domain knowledge, specialized prompts, and focused capabilities. Use cases include security review agents, API design agents, performance optimization agents, and documentation writers that understand your project's specific conventions and requirements.

## Prerequisites

- Windsurf IDE with Cascade Pro or Enterprise
- Understanding of prompt engineering principles
- Domain knowledge to encode in agent context
- Project documentation and conventions documented
- Test scenarios for agent validation

## Instructions

1. **Define Agent Purpose**
2. **Create System Prompt**
3. **Configure Context Sources**
4. **Set Activation Triggers**
5. **Test and Refine**


See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output

- Custom agent configurations in registry
- Domain-specific system prompts
- Context files with specialized knowledge
- Activation trigger mappings

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Windsurf Custom Agents Guide](https://docs.windsurf.ai/features/custom-agents)
- [Prompt Engineering Best Practices](https://docs.windsurf.ai/guides/prompt-engineering)
- [Agent Context Management](https://docs.windsurf.ai/features/context-management)
