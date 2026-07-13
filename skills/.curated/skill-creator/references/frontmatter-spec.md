# Frontmatter Field Specification

Complete reference for SKILL.md and agent frontmatter fields.

**Source**: https://code.claude.com/docs/en/skills (Anthropic, 2026)

---

## Skill Frontmatter — Anthropic Standard (11 fields)

### name

- **Type**: string
- **Default**: directory name (if omitted)
- **Format**: kebab-case (lowercase letters, numbers, hyphens)
- **Length**: 1-64 characters
- **Rules**:
  - Must start with a letter
  - Must end with letter or number
  - No consecutive hyphens (`my--skill`)
  - No start/end hyphens (`-my-skill`, `my-skill-`)
  - Must match containing directory name
  - No reserved words in isolation (`anthropic`, `claude`)
  - No XML tags (`<`, `>`) — breaks frontmatter parsing
  - Gerund naming preferred (`processing-pdfs`, `analyzing-data`)

```yaml
name: email-composer      # Good
name: processing-pdfs     # Good - gerund style
name: code-review-v2      # Good
name: EmailComposer       # Bad - not kebab-case
name: -my-skill           # Bad - starts with hyphen
name: my--skill           # Bad - consecutive hyphens
```

### description

- **Type**: string (multi-line with `|` supported)
- **Default**: first paragraph of skill body (if omitted)
- **Length**: 1-1024 characters
- **Purpose**: Tells Claude what the skill does AND when to activate it
- **Rules**:
  - MUST be third person ("Generates...", "Analyzes...")
  - MUST include what it does AND when to use it
  - MUST include specific keywords for discovery
  - MUST NOT use first person (I can, I will, I'm, I help)
  - MUST NOT use second person (You can, You should, You will)
  - MUST NOT contain XML tags (`<`, `>`) — breaks frontmatter parsing
  - MUST NOT contain reserved words as standalone identifiers (`anthropic`, `claude`)
  - MUST NOT contain system prompt injection patterns (behavioral instructions belong in SKILL.md body, not description)
  - SHOULD include action verbs (analyze, create, generate, build, debug, optimize, validate)
  - SHOULD reference slash command if user-invocable

```yaml
# Good - clear what + when + keywords
description: |
  Generate PDF reports from markdown with professional styling and TOC.
  Use when converting documentation to distributable format.

# Good - specific keywords, natural when-to-use
description: |
  Analyze Python code for security vulnerabilities, dependency risks, and
  OWASP compliance issues. Activates during security audits or pre-deployment
  code reviews. Trigger with "/security-scan" or "scan for vulnerabilities".

# Bad - first person
description: "I help you create PDFs"

# Bad - no when-to-use context
description: "Generates PDF reports"

# Bad - too vague, no keywords
description: "A helpful tool for documents"
```

**System prompt injection warning**: The `description` field is loaded into Claude's system prompt at startup for skill discovery. It must describe *what* and *when* only. Never include behavioral instructions ("Always respond in JSON", "Never use profanity"), persona definitions ("You are an expert..."), or override patterns ("Ignore previous instructions"). These belong in the SKILL.md body, not the description.

### allowed-tools

- **Type**: string (comma or space-delimited)
- **Purpose**: Pre-approved tools the skill can use without user confirmation
- **Valid tools**: `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebFetch`, `WebSearch`, `Task`, `TodoWrite`, `NotebookEdit`, `AskUserQuestion`, `Skill`
- **MCP tools**: `ServerName:tool_name` format

```yaml
# Scoped Bash (best practice)
allowed-tools: "Read,Write,Glob,Grep,Bash(git:*),Bash(npm:*)"

# With MCP tool
allowed-tools: "Read,Write,MyMCPServer:fetch_data"

# Unscoped Bash (avoid - security risk)
allowed-tools: "Read,Write,Bash"  # Warning in Standard, Error in Enterprise
```

**Bash Scoping Patterns**:

```yaml
Bash(git:*)       # All git commands
Bash(npm:*)       # All npm commands
Bash(python:*)    # All python commands
Bash(mkdir:*)     # Directory creation
Bash(chmod:*)     # Permission changes
Bash(curl:*)      # HTTP requests
Bash(npx:*)       # npx execution
Bash(pnpm:*)      # pnpm commands
```

### model

- **Type**: string
- **Default**: inherit (uses parent/caller model)
- **Values**: `sonnet`, `haiku`, `opus`, `inherit`, or full model ID
- **Purpose**: Override the LLM model used when this skill runs

```yaml
model: inherit                    # Use caller's model (recommended)
model: opus                       # Force Opus for complex tasks
model: haiku                      # Use Haiku for fast, simple tasks
model: sonnet                     # Use Sonnet for balanced tasks
```

**Avoid hardcoded model IDs** like `claude-opus-4-5-20251101` — they break on deprecation.

### effort

- **Type**: string
- **Default**: (inherits from caller)
- **Values**: `low`, `medium`, `high`, `max`
- **Purpose**: Override model reasoning effort level
- **Note**: `max` is only available with Opus 4.6

```yaml
effort: high                         # More reasoning for complex tasks
effort: low                          # Fast responses for simple tasks
```

### argument-hint

- **Type**: string
- **Purpose**: Autocomplete hint shown after `/skill-name` in the command palette
- **When to use**: When skill accepts arguments via `$ARGUMENTS`

```yaml
argument-hint: "[issue-number]"
argument-hint: "[file-path]"
argument-hint: "[search-query]"
argument-hint: "<component-name>"
```

### context

- **Type**: string
- **Values**: `fork` (only valid value)
- **Purpose**: Execute skill in isolated subagent context
- **When to use**: Long-running tasks, tasks that need isolation from main conversation

```yaml
context: fork  # Run in subagent
```

### agent

- **Type**: string
- **Requires**: `context: fork` must also be set
- **Purpose**: Specify subagent type when running in fork context
- **Values**: `Explore`, `Plan`, `general-purpose`, or custom agent name

```yaml
context: fork
agent: Explore          # Fast codebase exploration
```

### user-invocable

- **Type**: boolean
- **Default**: true
- **Purpose**: Control visibility in `/` command menu
- **When to use**: Set `false` for background knowledge skills that inform behavior

```yaml
user-invocable: false  # Hidden from / menu, loaded as background knowledge
user-invocable: true   # Visible in / menu (default)
```

### disable-model-invocation

- **Type**: boolean
- **Default**: false
- **Purpose**: Prevent Claude from auto-activating; require explicit `/name` invocation

```yaml
disable-model-invocation: true   # Only via /skill-name
disable-model-invocation: false  # Can activate via natural language (default)
```

### hooks

- **Type**: object
- **Purpose**: Skill-scoped lifecycle hooks
- **Events**: `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `SessionStart`, `SessionEnd`

```yaml
hooks:
  PreToolUse:
    - command: "echo 'Tool about to be used'"
      event: PreToolUse
  PostToolUse:
    - command: "${CLAUDE_PLUGIN_ROOT}/scripts/post-check.sh"
      event: PostToolUse
```

---

## Enterprise Additions (5 fields, marketplace-required)

These fields are NOT part of the Anthropic runtime spec but are required by the Tons of Skills marketplace validator for published plugins. The 100-point enterprise grading system scores these at the top level.

### version

- **Type**: string
- **Format**: Semver (`X.Y.Z`)
- **Purpose**: Skill version for tracking updates and marketplace display

```yaml
version: 1.0.0
version: 2.3.1
```

### author

- **Type**: string
- **Format**: `Name <email>` (email required for Enterprise tier)
- **Purpose**: Skill author identification

```yaml
author: Jeremy Longshore <jeremy@intentsolutions.io>
```

### license

- **Type**: string
- **Format**: SPDX identifier or bundled file reference
- **Purpose**: License for the skill

```yaml
license: MIT
license: Apache-2.0
license: Complete terms in LICENSE.txt
```

### compatible-with

- **Type**: string (comma-separated)
- **Purpose**: Platforms this skill is compatible with
- **Valid values**: `claude-code`, `codex`, `openclaw`, `aider`, `continue`, `cursor`, `windsurf`

```yaml
compatible-with: claude-code, codex, openclaw
compatible-with: claude-code
```

### tags

- **Type**: array of strings
- **Purpose**: Discovery tags for categorization and search

```yaml
tags: [devops, ci, automation]
tags: [security, python, code-review]
```

**Total skill frontmatter**: 16 fields (11 Anthropic + 5 enterprise)

---

## Agent Frontmatter — Anthropic Standard (14 fields)

Agent files live in `agents/*.md`. Key difference from skills: agents use `disallowedTools` (denylist) while skills use `allowed-tools` (allowlist).

### name

- **Type**: string
- **Required**: Yes
- **Purpose**: Unique identifier for the agent

```yaml
name: code-reviewer
```

### description

- **Type**: string
- **Required**: Yes
- **Length**: 20-200 characters
- **Purpose**: Agent's specialty — shown in agent selection UI

```yaml
description: "Reviews code for bugs, performance issues, and style violations"
```

### model

- **Type**: string
- **Values**: `sonnet`, `haiku`, `opus`, `inherit`
- **Purpose**: Override LLM model for this agent

```yaml
model: opus
```

### effort

- **Type**: string
- **Values**: `low`, `medium`, `high`, `max`
- **Purpose**: Override reasoning effort for agent turns

```yaml
effort: high
```

### maxTurns

- **Type**: integer
- **Purpose**: Max agentic loop iterations before stopping
- **Added**: v2.1.78

```yaml
maxTurns: 10
maxTurns: 25
```

### tools

- **Type**: string (comma-separated)
- **Purpose**: Tool allowlist (same format as skill `allowed-tools`)

```yaml
tools: "Read,Glob,Grep,Bash(git:*)"
```

### disallowedTools

- **Type**: string (comma-separated)
- **Purpose**: Tool denylist — block specific tools (opposite of allowlist)

```yaml
disallowedTools: "mcp__dangerous_server,Write"
```

### skills

- **Type**: array
- **Purpose**: Skill names to preload when agent activates

```yaml
skills: [code-review, test-generator]
```

### mcpServers

- **Type**: object or array
- **Purpose**: MCP server configurations available to the agent
- **Plugin restriction**: NOT supported in plugin agents (ignored silently by runtime)

```yaml
mcpServers:
  myserver:
    command: "node"
    args: ["server.js"]
```

### hooks

- **Type**: object
- **Purpose**: Agent-scoped lifecycle hooks
- **Plugin restriction**: NOT supported in plugin agents (ignored silently by runtime)

```yaml
hooks:
  PreToolUse:
    - command: "echo 'pre-hook'"
```

### memory

- **Type**: string
- **Values**: `user`, `project`, `local`
- **Purpose**: Memory persistence scope for the agent

```yaml
memory: project
```

### background

- **Type**: boolean
- **Purpose**: Run agent as a background task

```yaml
background: true
```

### isolation

- **Type**: string
- **Values**: `worktree` (only valid value)
- **Purpose**: Run agent in an isolated git worktree

```yaml
isolation: worktree
```

### permissionMode

- **Type**: string
- **Values**: `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan`
- **Purpose**: Permission behavior for the agent
- **Plugin restriction**: NOT supported in plugin agents (ignored silently by runtime)

```yaml
permissionMode: acceptEdits
```

---

## plugin.json Field Summary (8 allowed fields)

The `.claude-plugin/plugin.json` manifest defines plugin identity. CI rejects any fields not in this list.

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `name` | string | Yes | Plugin name (kebab-case) |
| `version` | string | Yes | Semver version |
| `description` | string | Yes | Plugin description |
| `author` | string | Yes | Author name or `Name <email>` |
| `repository` | string | No | GitHub repository URL |
| `homepage` | string | No | Plugin homepage URL |
| `license` | string | No | SPDX license identifier |
| `keywords` | array | No | Discovery keywords |

```json
{
  "name": "my-plugin",
  "version": "2.0.0",
  "description": "What this plugin does",
  "author": "Name <email>",
  "repository": "https://github.com/user/repo",
  "license": "MIT",
  "keywords": ["devops", "automation"]
}
```

---

## Deprecated / Invalid Fields

| Field | Status | Notes |
|-------|--------|-------|
| `when_to_use` | Deprecated | Move content to `description` |
| `mode` | Deprecated | Use `disable-model-invocation` instead |
| `compatibility` | Invalid | AgentSkills.io field, not in Anthropic spec. Document requirements in skill body instead. |
| `metadata` | Invalid | AgentSkills.io field, not in Anthropic spec. Use top-level fields (`author`, `version`, `license`, `tags`). |
| `capabilities` | Invalid | Invented field, never part of any spec |
| `expertise_level` | Invalid | Invented field, never part of any spec |
| `activation_priority` | Invalid | Invented field, never part of any spec |

The marketplace validator will flag these fields as errors in Enterprise tier validation.

---

## Recommended Field Order

### Skill (SKILL.md)

```yaml
---
# Anthropic standard
name: skill-name
description: |
  What it does. Use when [scenario].
  Trigger with "/skill-name" or "[natural phrase]".
allowed-tools: "Read,Write,Glob,Grep,Bash(git:*)"
model: inherit
# effort: high
argument-hint: "[arg]"
# context: fork
# agent: general-purpose
user-invocable: true
disable-model-invocation: false
# hooks: {}

# Enterprise additions (marketplace-required)
version: 1.0.0
author: Name <email>
license: MIT
compatible-with: claude-code, codex, openclaw
tags: [devops, automation]
---
```

### Agent (agents/*.md)

```yaml
---
# Required
name: agent-name
description: "20-200 char description of the agent's specialty"

# Model control
model: opus
effort: high
maxTurns: 15

# Tool access
tools: "Read,Write,Glob,Grep,Bash(git:*)"
# disallowedTools: "mcp__dangerous_server"

# Preloaded skills
# skills: [code-review, test-generator]

# Execution
# background: false
# isolation: worktree
# memory: project

# NOT supported in plugin agents (ignored by runtime):
# hooks: {}
# mcpServers: {}
# permissionMode: default
---
```
