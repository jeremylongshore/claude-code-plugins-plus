# Claude Code Plugins Standard

**Document ID**: 6767-a-SPEC-MASTER-claude-code-plugins-standard
**Version**: 1.0.0
**Created**: 2025-12-06
**Applies to**: claude-code-plugins-plus repository

---

## Plugin Structure

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # Required: manifest
├── commands/                 # Optional: slash commands
│   └── command-name.md
├── agents/                   # Optional: subagents
│   └── agent-name.md
├── skills/                   # Optional: skills
│   └── skill-name/
│       └── SKILL.md
├── hooks/                    # Optional: event handlers
│   └── hooks.json
├── scripts/                  # Optional: helper scripts
├── .mcp.json                 # Optional: MCP servers
└── README.md                 # Recommended
```

---

## plugin.json Schema

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Kebab-case identifier |

### Recommended Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Semver (1.0.0) |
| `description` | string | What the plugin does |
| `author` | object | `{name, email, url}` |
| `license` | string | SPDX identifier (MIT) |
| `keywords` | array | Discovery tags |
| `repository` | string | Source URL |

### Example

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "What this plugin does",
  "author": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "license": "MIT",
  "keywords": ["category", "tags"]
}
```

---

## Commands

**Location**: `commands/*.md`
**Invocation**: `/command-name`

```markdown
---
description: What this command does
allowed-tools: "Read,Write,Bash"
---

# Command Name

Instructions for Claude when this command is invoked.
```

Frontmatter is optional. `name` derived from filename.

---

## Agents

**Location**: `agents/*.md`
**Invocation**: Claude delegates via Task tool

```markdown
---
name: agent-name
description: When to use this agent
tools: Read, Write, Bash
model: sonnet
---

# Agent Name

You are an expert in X. Your role is to...
```

### Required Frontmatter

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Agent identifier |
| `description` | Yes | When Claude should delegate |
| `tools` | No | Comma-separated tools |
| `model` | No | sonnet, opus, haiku |

---

## Skills

**Location**: `skills/skill-name/SKILL.md`
**Invocation**: Auto-triggered by Claude based on context

```markdown
---
name: skill-name
description: >
  What this skill does and when to activate.
allowed-tools: "Read,Glob,Grep"
version: "1.0.0"
---

# Skill Name

Instructions that transform Claude's behavior.
```

### Required Frontmatter

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Skill identifier |
| `description` | Yes | When to activate |
| `allowed-tools` | Recommended | CSV string of tools |
| `version` | Recommended | Semver |

### Forbidden Fields

Do not use: `author`, `priority`, `audience`, `when_to_use`, `license`

---

## Hooks

**Location**: `hooks/hooks.json`

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/format.sh"
          }
        ]
      }
    ]
  }
}
```

### Valid Events

- `PreToolUse` - Before tool execution
- `PostToolUse` - After tool execution
- `UserPromptSubmit` - User sends message
- `SessionStart` - Session begins
- `SessionEnd` - Session ends

---

## Marketplace Entry

For plugins distributed via marketplace:

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "source": "github:owner/repo/plugins/plugin-name",
  "description": "What it does",
  "keywords": ["tags"]
}
```

---

## Validation Checklist

- [ ] `.claude-plugin/plugin.json` exists
- [ ] `name` field present and kebab-case
- [ ] At least one component (commands/, agents/, skills/, scripts/, .mcp.json)
- [ ] README.md exists
- [ ] Version follows semver
- [ ] Skills use `skill-name/SKILL.md` structure
- [ ] Agents have `name` and `description` in frontmatter

---

## References

- Anthropic Docs: https://docs.anthropic.com/en/docs/claude-code
- Claude Code GitHub: https://github.com/anthropics/claude-code
