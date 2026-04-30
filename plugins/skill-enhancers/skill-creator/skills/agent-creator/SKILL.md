---
name: agent-creator
description: 'Create production-grade agent .md files aligned with the Anthropic 2026
  spec (16-field schema).

  Also validates existing agents against the marketplace compliance rules. Use when
  building custom

  subagents, reviewing agent quality, or creating parallel agent architectures for
  orchestrator skills.

  Trigger with "/agent-creator", "create an agent", "build a subagent", or "validate
  my agent".

  Make sure to use this skill whenever creating agents/*.md files for plugins or standalone
  use.

  '
allowed-tools: Read,Write,Edit,Glob,Grep,Bash(python:*),AskUserQuestion
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
tags:
- agent-creation
- validation
- meta-tooling
- subagents
model: inherit
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Agent Creator

Creates spec-compliant agent .md files following the Anthropic 2026 16-field schema. Supports
both creation of new agents and validation of existing ones.

## Overview

Agent Creator fills the gap between ad-hoc agent files and production-grade agents that pass
marketplace validation. It enforces the Anthropic agent schema (14 valid fields), prevents
common mistakes (using `allowed-tools` instead of `disallowedTools`, adding invalid fields like
`capabilities` or `expertise_level`), and produces agents with substantive body content that
actually guides Claude's behavior.

Key difference from skill-creator: **agents support both `tools` (allowlist) AND `disallowedTools`
(denylist)**, while skills only use `allowed-tools` (allowlist). Agents also support `effort`,
`maxTurns`, `skills`, `memory`, `isolation`, `permissionMode`, `background`, `color`, and
`initialPrompt` — fields that don't exist for skills. The agent body becomes the **system prompt**
that drives the subagent — it does NOT receive the full Claude Code system prompt.

## Prerequisites

- Claude Code CLI with agent support
- Target directory writable (`agents/` within a plugin or `~/.claude/agents/` for standalone)
- Familiarity with what the agent should specialize in

## Instructions

### Mode Detection

Determine user intent from their prompt:
- **Create mode**: "create an agent", "build a subagent", "new agent" -> Step 1
- **Validate mode**: "validate agent", "check agent", "grade agent" -> Validation Workflow

### Step 1: Understand Requirements

Ask the user with AskUserQuestion:

**Agent Identity:**
- Name (kebab-case, 1-64 chars, e.g., `risk-assessor`, `clause-analyzer`)
- Specialty description (20-200 chars — shown in agent selection UI)

**Execution Context:**
- Plugin agent (`plugins/*/agents/`) or standalone (`~/.claude/agents/`)?
- Will it be spawned by an orchestrator skill via `Task` tool?
- Does it need to preload specific skills? (`skills: [skill-name]`)

**Behavioral Controls:**
- Model override? (`sonnet` for speed, `opus` for quality, `inherit` for default)
- Reasoning effort? (`low` for simple, `medium` default, `high` for complex analysis)
- Max iterations? (`maxTurns` — how many tool-use loops before stopping)
- Tools to deny? (`disallowedTools` — denylist approach, opposite of skills)

**Plugin Restrictions (if plugin agent):**
- `hooks` — NOT supported in plugin agents (use plugin-level hooks)
- `mcpServers` — NOT supported in plugin agents
- `permissionMode` — standalone only, NOT plugin agents

### Step 2: Plan the Agent

Before writing, determine:

**Agent Role Clarity:**
The agent body must make three things unambiguous:
1. **What it IS responsible for** — its specific domain/methodology
2. **What it is NOT responsible for** — boundaries with other agents
3. **How it communicates results** — output format and structure

**Body Structure Pattern:**
All production agents should follow this body structure:

| Section | Purpose | Required? |
|---------|---------|-----------|
| `# Title` | Agent name as heading | Yes |
| `## Role` | 2-3 sentence domain description with boundaries | Yes |
| `## Inputs` | Parameters the agent receives when spawned | Yes (if spawned by orchestrator) |
| `## Process` | Step-by-step methodology (numbered steps with ### headings) | Yes |
| `## Output Format` | Structured output spec (JSON, markdown, or table) | Yes |
| `## Guidelines` | Do/don't behavioral rules | Yes |
| `## When Activated` | Trigger conditions (when spawned or auto-detected) | Recommended |
| `## Communication Style` | Tone and formatting preferences | Recommended |
| `## Success Criteria` | What good vs poor output looks like | Recommended |
| `## Examples` | Concrete interaction examples | For complex agents |

**Output Structure Decision:**
- If the agent feeds into an orchestrator: use **JSON output** (machine-parseable)
- If the agent is user-facing: use **markdown output** (human-readable)
- If the agent produces both: JSON primary with markdown summary

### Step 3: Write the Agent File

Generate the agent .md using the template from
`${CLAUDE_SKILL_DIR}/../skill-creator/templates/agent-template.md`.

**Frontmatter Rules (Anthropic 16-field schema):**

See [Anthropic Agent Spec](references/anthropic-agent-spec.md) for the full official reference.

Required fields:
```yaml
name: {agent-name}         # Lowercase letters and hyphens, unique identifier
description: "{specialty}"  # When Claude should delegate to this subagent
```

Optional fields (include only what's needed):
```yaml
tools: "Read, Glob, Grep"  # Allowlist — inherits all tools if omitted
disallowedTools: "Write"   # Denylist — removed from inherited/specified list
model: sonnet              # sonnet|haiku|opus|inherit|full model ID
effort: medium             # low|medium|high|max (max = Opus 4.6 only)
maxTurns: 15               # Max agentic turns before stopping
skills: [skill-name]       # Skills to inject at startup (full content loaded)
memory: project            # user|project|local — persistent cross-session
background: false          # Always run as background task
isolation: worktree        # Run in temporary git worktree
color: blue                # Display: red|blue|green|yellow|purple|orange|pink|cyan
initialPrompt: "..."       # Auto-submitted first turn (--agent mode only)
permissionMode: default    # Standalone only, NOT plugin agents
hooks: {}                  # Standalone only, NOT plugin agents
mcpServers: {}             # Standalone only, NOT plugin agents
```

**Tool access:**
- `tools` = allowlist (like skills' `allowed-tools`)
- `disallowedTools` = denylist (remove specific tools)
- If both set: disallowed applied first, then tools resolved
- If neither set: inherits all tools from parent conversation

**Invalid fields (ERROR — never use these):**
- `capabilities` — looks valid but flagged by validator
- `expertise_level` — invented, not in Anthropic spec
- `activation_priority` — invented, not in Anthropic spec
- `activation_triggers`, `type`, `category` — not in spec
- `allowed-tools` — that's the skill-only syntax; agents use `tools` or `disallowedTools`

**Body Content Guidelines:**

1. **Role section must set boundaries.** Don't just say what the agent does — say what it
   does NOT do. Example: "You analyze contract clauses for risk. You do NOT provide legal
   advice or make recommendations — that is the recommendations agent's responsibility."

2. **Process steps must be concrete.** Each step should tell Claude exactly what to do,
   not vaguely gesture at an activity. Bad: "Analyze the document." Good: "Read the full
   contract. For each clause, extract: (a) the exact text, (b) the clause category from
   the taxonomy below, (c) a plain English summary in one sentence."

3. **Output format must be machine-parseable if feeding an orchestrator.** Use JSON with
   a concrete schema example. Include field descriptions so Claude knows what each field means.

4. **Guidelines should include both DO and DON'T rules.** Example:
   - DO: "Be specific — quote exact clause text, don't paraphrase"
   - DON'T: "Don't make legal recommendations — only identify and score risks"

5. **Keep under 300 lines** (agent body limit — prevents context bloat in subagent window).
   If the agent needs extensive reference material, create a companion skill with
   `references/` directory and preload it via the `skills` field.

### Step 4: Validate the Agent

Run validation against the Anthropic 16-field schema:

**Manual checklist:**

| Check | Rule |
|-------|------|
| `name` present | 1-64 chars, kebab-case |
| `description` present | 20-200 chars |
| No invalid fields | None of: capabilities, expertise_level, activation_priority, type, category |
| No skill-only fields | No `allowed-tools` (use `disallowedTools` instead) |
| Plugin restrictions | No hooks/mcpServers/permissionMode if plugin agent |
| Body has Role section | Clear domain + boundaries |
| Body has Process section | Numbered steps |
| Body has Output Format | Concrete schema example |
| Body has Guidelines | Do/don't rules |
| Body under 300 lines | Offload to references if longer (prevents context bloat) |

**Automated validation:**
```bash
python3 ${CLAUDE_SKILL_DIR}/../skill-creator/scripts/validate-skill.py --agents-only {plugin-dir}/
```

### Step 5: Test the Agent

Test the agent by spawning it via the `Task` tool or the `Agent` tool:

1. Write a test prompt that exercises the agent's core capability
2. Spawn the agent with that prompt
3. Check: Does the output match the declared Output Format?
4. Check: Does the agent stay within its declared Role boundaries?
5. Check: Does it follow the Process steps?
6. Iterate on the body content if the agent strays

### Step 6: Report

Provide a summary:
- Agent name and file path
- Frontmatter field count (of 14 possible)
- Body line count
- Sections present
- Validation result (pass/fail with specific issues)
- Test result summary

## Validation Workflow

When the user wants to validate an existing agent:

1. Locate the agent .md file
2. Parse YAML frontmatter
3. Check against the 16-field Anthropic schema:
   - `name` present and valid (1-64 chars, kebab-case)?
   - `description` present and valid (20-200 chars)?
   - Any invalid fields? (capabilities, expertise_level, activation_priority, etc.)
   - Any skill-only fields? (allowed-tools)
   - Plugin restrictions respected?
4. Check body content:
   - Has `## Role` section?
   - Has `## Process` section with numbered steps?
   - Has `## Output Format` with concrete example?
   - Has `## Guidelines`?
   - Under 300 lines? (agent body limit)
5. Report findings with severity (ERROR/WARNING/INFO)
6. Suggest specific fixes for each issue

## Output

- **Create mode**: A complete agent .md file with valid frontmatter and substantive body,
  plus a creation report with validation status.
- **Validate mode**: A compliance report listing errors, warnings, and info items with
  specific fix recommendations for each.

## Examples

### Subagent for Orchestrator Skill

**Input:** "Create a risk assessment agent that scores contract clauses"

**Output:** `agents/risk-assessor.md` with frontmatter:

```yaml
name: risk-assessor
description: "Score contract clauses for legal and financial risk on a 1-10 scale"
model: sonnet
effort: high
maxTurns: 10
```

Body sections: Role (risk scoring specialist, does NOT make recommendations), Inputs
(contract_text, contract_type, output_path), Process (4 steps: read, categorize, score,
aggregate), Output Format (JSON with clause scores and risk matrix), Guidelines (be specific,
cite clause text, use 4-factor scoring methodology).

### Standalone User-Facing Agent

**Input:** "Create a code review agent"

**Output:** `~/.claude/agents/code-reviewer.md` with frontmatter:

```yaml
name: code-reviewer
description: "Review code for bugs, performance issues, and security vulnerabilities"
effort: high
```

Body sections: Role (code quality specialist), Process (read code, check patterns, identify
issues, suggest fixes), Output Format (markdown with severity-rated findings), Guidelines
(cite line numbers, explain why not just what), Communication Style (direct, educational,
actionable).

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `allowed-tools` in agent | Used skill-only field | Replace with `disallowedTools` (denylist) or remove |
| `capabilities` field | Common mistake — looks valid but isn't in Anthropic spec | Remove field entirely |
| `expertise_level` field | Invented field from community templates | Remove — express expertise in body content |
| Description > 200 chars | Exceeds Anthropic limit | Shorten to 20-200 char range |
| Description < 20 chars | Below minimum | Expand to describe agent's specific specialty |
| `permissionMode` in plugin agent | Standalone-only field used in plugin context | Remove — only valid in `~/.claude/agents/` |
| `hooks` in plugin agent | Plugin agents can't have hooks | Move to plugin-level `hooks/hooks.json` |
| Body has no Process section | Agent lacks step-by-step methodology | Add numbered steps under `## Process` |
| Body over 300 lines | Too long for agent context | Extract reference material to companion skill |

## Resources

- [Anthropic Agent Spec](references/anthropic-agent-spec.md) — Official 16-field schema from code.claude.com/docs/en/sub-agents
- [Agent template](${CLAUDE_SKILL_DIR}/../skill-creator/templates/agent-template.md) — Skeleton with placeholders
- [Frontmatter spec](${CLAUDE_SKILL_DIR}/../skill-creator/references/frontmatter-spec.md) — Field reference (internal)
- [Source of truth](${CLAUDE_SKILL_DIR}/../skill-creator/references/source-of-truth.md) — Canonical spec
- [Validation rules](${CLAUDE_SKILL_DIR}/../skill-creator/references/validation-rules.md) — Agent validation section
