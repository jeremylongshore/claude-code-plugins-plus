---
name: agent-creator
description: 'Create production-grade agent definitions for Claude Code plugins. Use
  when building

  new agents, adding agents to plugins, or designing autonomous agent configurations.

  Trigger with "create an agent", "build an agent", "make an agent that...",

  "add an agent to my plugin", or "/agent-creator".

  '
allowed-tools: Read, Write, Edit, Glob, Grep, AskUserQuestion
version: 1.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
tags:
  - agents
  - plugins
  - development
  - scaffolding
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---

# Agent Creator

Create high-quality agent configurations for Claude Code plugins.

## Overview

Translates user requirements into precisely-tuned agent specifications that follow the
Anthropic agent frontmatter spec. Handles persona design, instruction architecture,
tool selection, and triggering configuration. Produces agents that pass the enterprise
validator.

**Important**: Read any project-specific `CLAUDE.md` for coding standards and patterns
before creating agents. Agents should align with the project's conventions.

## Prerequisites

- Target plugin directory must exist with `.claude-plugin/plugin.json`
- Or specify a standalone location (global `~/.claude/` or project `.claude/`)

## Instructions

### Step 1: Gather Requirements

Use AskUserQuestion to collect:

```
AGENT CREATOR
================================================================

What kind of agent do you need?

Please describe:
  1. What should the agent DO? (core purpose)
  2. Where should it live? (plugin path or standalone)
```

If the conversation already contains context (e.g., "turn this into an agent"),
extract the details and confirm before proceeding.

### Step 2: Design the Agent

From the user's description, determine:

**Identity:**

- **Name**: kebab-case, 3-50 chars, descriptive of function (e.g., `code-reviewer`, `test-generator`)
- **Description**: Starts with "Use this agent when..." — this drives activation
- **Model**: Default `inherit` unless user specifies. Use `sonnet` for complex reasoning, `haiku` for simple tasks

**Capabilities:**

- Extract 3-6 core capabilities from the user's description
- Each capability should be a concrete, actionable behavior

**Triggering:**

- Write a description that captures both explicit triggers ("create a code review")
  and proactive triggers (when the user's context implies the agent should activate)

### Step 3: Architect the System Prompt

Build a comprehensive body that includes:

1. **Role statement** — one sentence establishing the expert persona
2. **Core responsibilities** — numbered list of 3-6 primary duties
3. **Detailed process** — step-by-step methodology for the agent's main workflow
4. **Quality standards** — what "good" looks like for this agent's output
5. **Output format** — expected structure of the agent's deliverables
6. **Edge cases** — how to handle ambiguous or unexpected inputs

Guidelines:

- 500-3,000 words for the body
- Be specific — vague instructions produce vague agents
- Include decision-making frameworks appropriate to the domain
- Add self-verification steps where quality matters
- Reference project context from CLAUDE.md when relevant

### Step 4: Select Frontmatter Fields

**Required (Anthropic spec)** — only these two:

```yaml
---
name: { identifier } # lowercase + hyphens
description: 'Use this agent when {triggering conditions}.'
---
```

**Optional (Anthropic spec)** — pick the ones you need:

```yaml
# Tools — default is "inherit all tools from parent". Use `tools` to allowlist
# specific tools, OR `disallowedTools` to remove specific tools from the inherited
# pool. Both can coexist; if both set, disallowedTools applies first then tools
# resolves against the remaining pool.
tools: Read, Glob, Grep, Bash # allowlist (canonical example pattern)
# disallowedTools: Write, Edit       # denylist alternative

# Model — defaults to `inherit` (uses main conversation's model)
model: sonnet # sonnet | opus | haiku | inherit | full-id


# Permissions — default | acceptEdits | auto | dontAsk | bypassPermissions | plan
# permissionMode: default

# Execution control
# maxTurns: 10                        # max agentic turns before stop
# effort: medium                      # low | medium | high | xhigh | max
# background: false                   # run as background task
# isolation: worktree                 # run in temp git worktree (file-edit isolation)

# Persistent memory across sessions — user | project | local
# memory: user

# UI display color — red | blue | green | yellow | purple | orange | pink | cyan
# (NOTE: `teal` and other off-list colors are not valid)
# color: blue

# Auto-submit a first user turn when this agent runs as the main session agent
# (via --agent or the `agent` setting). Commands and skills processed.
# initialPrompt: "Introduce yourself and ask the user what they need help with."

# Preload skills into agent's context at startup (not just descriptions)
# skills:
#   - api-conventions
#   - error-handling-patterns

# Scope MCP servers to this agent (separate from main-session MCP config)
# mcpServers:
#   - playwright:
#       type: stdio
#       command: npx
#       args: ["-y", "@playwright/mcp@latest"]

# Lifecycle hooks (PreToolUse, PostToolUse, Stop, etc.)
# hooks:
#   PreToolUse:
#     - matcher: "Bash"
#       hooks:
#         - type: command
#           command: "./scripts/validate-command.sh"
```

**Key differences from skills**:

- **Field name for tools**: agents use `tools` (allowlist) and/or `disallowedTools` (denylist). Skills use `allowed-tools`. Different field names for the same concept.
- **Both forms valid for agents**: `tools: Read, Bash` (allowlist) is the canonical Anthropic example pattern. `disallowedTools: Write, Edit` (denylist) is for "inherit everything except X" cases. The Anthropic example sub-agents at `references/anthropic-example-subagents.md` all use the `tools` allowlist.

**IS-extension fields (NOT in Anthropic spec — avoid)**:

The following fields appear in some legacy IS agents but are **not part of Anthropic's published sub-agents spec**: `capabilities`, `expertise_level`, `activation_priority`. The IS validator flags them as "Non-standard. Not in Anthropic spec." Don't include them in new agents — bake equivalent context into the agent's body prose if needed.

> See `references/anthropic-sub-agents-spec.md` for the full canonical spec (verbatim from `code.claude.com/docs/en/sub-agents`, refreshed 2026-05-08). See `references/anthropic-example-subagents.md` for the four canonical Anthropic example agents (Code reviewer / Debugger / Data scientist / Database query validator) — anchor your generated agents on these patterns.

### Step 5: Write the Agent File

Use the Write tool to create `agents/{name}.md` in the target location.

Structure:

```markdown
---
{ frontmatter }
---

{Role statement}

## Core Responsibilities

1. {responsibility}
2. {responsibility}
   ...

## Process

{Step-by-step methodology}

## Quality Standards

{What good output looks like}

## Output Format

{Expected structure}

## Edge Cases

{How to handle unusual inputs}
```

### Step 6: Report

Present summary to user:

```
AGENT CREATED: {name}
================================================================

File:     {path}/agents/{name}.md
Triggers: {when it activates}
Model:    {model choice}

How to test:
  {suggest a test prompt that should trigger this agent}

Validate:
  python3 scripts/validate-skills-schema.py --enterprise {plugin-path}/
```

## Output

An `agents/{name}.md` file with proper frontmatter and comprehensive system prompt.

## Error Handling

| Error              | Cause                              | Solution                                                 |
| ------------------ | ---------------------------------- | -------------------------------------------------------- |
| Name conflict      | Agent file already exists          | Ask user to confirm overwrite or pick new name           |
| No plugin.json     | Target isn't a valid plugin        | Create plugin structure first or pick different location |
| Vague requirements | User description too generic       | Ask clarifying questions before generating               |
| Too complex        | Requirements span multiple domains | Suggest splitting into multiple specialized agents       |

## Examples

### Simple Agent

```
User: create an agent that reviews code for quality
Assistant: [Asks clarifying questions]
           [Creates agents/code-reviewer.md with review methodology]

AGENT CREATED: code-reviewer
  File: agents/code-reviewer.md
  Triggers: "review this code", "code quality check", after code is written
```

### Domain-Specific Agent

```
User: I need an agent for my database plugin that optimizes slow queries
Assistant: [Reads plugin CLAUDE.md for context]
           [Creates agents/query-optimizer.md with EXPLAIN plan analysis,
            index recommendations, query rewrite suggestions]

AGENT CREATED: query-optimizer
  File: plugins/database/my-plugin/agents/query-optimizer.md
  Triggers: "optimize this query", "why is this query slow", EXPLAIN analysis
```

### Agent with Restricted Tools

```
User: build a read-only analysis agent that should never modify files
Assistant: [Creates agent with disallowedTools: Write, Edit]

AGENT CREATED: read-only-analyzer
  disallowedTools: Write, Edit, Bash
  Triggers: "analyze this codebase", "read-only review"
```

## Resources

- Anthropic agent spec: agents use `disallowedTools` (denylist), not `allowed-tools`
- **Anthropic spec fields** (per `references/anthropic-sub-agents-spec.md`, captured 2026-05-08 from `code.claude.com/docs/en/sub-agents`):
  - **Required**: `name`, `description`
  - **Optional**: `tools` (allowlist), `disallowedTools` (denylist), `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation`, `color` (enum: red/blue/green/yellow/purple/orange/pink/cyan), `initialPrompt`
- **IS-extension fields (NOT in Anthropic spec)**: `capabilities`, `expertise_level`, `activation_priority`. Avoid in new agents; the IS validator flags them as "Non-standard."
- **Canonical Anthropic example agents** (read these before generating): `references/anthropic-example-subagents.md` — Code reviewer, Debugger, Data scientist, Database query validator
- Reference implementation: `/home/jeremy/anthropic/claude-code/plugins/plugin-dev/agents/agent-creator.md`
