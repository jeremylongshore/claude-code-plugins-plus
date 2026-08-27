# Schema Reminder — Frontmatter Fields

Every SKILL.md must have:

```yaml
name: my-skill                  # Required (Anthropic)
description: |                  # Required (Anthropic)
  What it does. Use when ...
```

Optional fields the validator accepts (validates only when present):

```yaml
# Per Anthropic + AgentSkills.io spec
allowed-tools: "Read,Write,Bash(git:*)"
license: MIT
compatibility: "Designed for Claude Code"   # Free-text, max 500 chars per agentskills.io/specification
metadata: { category: devops }              # Arbitrary key-value mapping

# Per code.claude.com/docs/en/skills
model: inherit
effort: medium
argument-hint: "[file-path]"
context: fork
agent: Explore
user-invocable: true
disable-model-invocation: false
hooks: { ... }

# Marketplace polish (Intent Solutions extension — recommended for submission)
version: 1.0.0
author: Name <email>
tags: [devops, ci]
```

## `compatibility` Field Examples (per `agentskills.io/specification`)

The `compatibility` field is a free-text string, max 500 characters. It indicates environment requirements (intended product, system packages, network access, etc.). Pick the form that matches your skill:

```yaml
# Single platform
compatibility: "Designed for Claude Code"

# Multi-platform — free-text, no allow-list
compatibility: "Designed for Claude Code, also compatible with Codex and OpenClaw"

# Runtime requirements
compatibility: "Requires Python 3.10+ with uv installed"
compatibility: "Requires git, docker, and jq on PATH"
compatibility: "Node.js >= 18, npm >= 9"

# Platform + tooling
compatibility: "Designed for Claude Code; requires Bash 5+ and rg (ripgrep)"

# Network / capability requirements
compatibility: "Requires network access to api.example.com (port 443)"
```

**Migration**: The deprecated `compatible-with` CSV-platform-list field (`compatible-with: claude-code, codex, openclaw`) was an Intent Solutions invention not in any published spec. Replaced by free-text `compatibility`. Run:

```bash
python3 claude-code-plugins-plus-skills/scripts/batch-remediate.py --migrate-compatible-with --root <path>
```
