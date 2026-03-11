---
name: "windsurf-cascade-onboarding"
description: |
  Configure Cascade AI agent for new team projects. Activate when users mention
  "setup cascade", "configure windsurf ai", "initialize cascade agent", "new windsurf project",
  or "onboard team to windsurf". Handles agent configuration, context settings, and team defaults. Use when working with windsurf cascade onboarding functionality. Trigger with phrases like "windsurf cascade onboarding", "windsurf onboarding", "windsurf".
allowed-tools: "Read,Write,Edit,Bash(cmd:*),Grep,Glob"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---

# Windsurf Cascade Onboarding

## Overview

This skill enables rapid onboarding of projects to Windsurf with optimized Cascade AI configuration. It covers creating .windsurfrules, setting up project context, configuring team defaults, and establishing best practices for AI-assisted development. Teams can achieve maximum Cascade productivity within the first week of adoption.

## Prerequisites

- Windsurf IDE installed for all team members
- Active Cascade AI subscription
- Project documentation (architecture, conventions)
- Team lead or admin access for configuration
- Understanding of project structure and patterns

## Instructions

1. **Initialize Windsurf Rules**
2. **Configure Cascade Context**
3. **Set Up Team Defaults**
4. **Train Team Members**
5. **Iterate Based on Feedback**


See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output

- Configured .windsurfrules file
- Project context documentation
- Team snippet library
- Onboarding guide for new members

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Windsurf Onboarding Guide](https://docs.windsurf.ai/getting-started/onboarding)
- [Writing Effective .windsurfrules](https://docs.windsurf.ai/features/windsurfrules)
- [Team Best Practices](https://docs.windsurf.ai/guides/team-best-practices)
