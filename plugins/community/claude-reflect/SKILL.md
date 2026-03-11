---
name: claude-reflect
description: |
  Execute self-learning system that captures corrections during sessions and syncs them to CLAUDE.md.
  Use when discussing learnings, corrections, or when the user mentions remembering something.
  Trigger with phrases like "remember this", "don't forget", "use X not Y", or "actually...".
allowed-tools: Read, Write, Edit, Bash(jq:*), Bash(cat:*)
version: 1.4.1
license: MIT
author: Bayram Annakov <bayram.annakov@gmail.com>
compatible-with: claude-code, codex, openclaw
---
# Claude Reflect - Self-Learning System

A two-stage system that helps Claude Code learn from user corrections.

## How It Works

**Stage 1: Capture (Automatic)**
Hooks detect correction patterns ("no, use X", "actually...", "use X not Y") and queue them to `~/.claude/learnings-queue.json`.

**Stage 2: Process (Manual)**
User runs `/reflect` to review and apply queued learnings to CLAUDE.md files.

## Available Commands

| Command | Purpose |
|---------|---------|
| `/reflect` | Process queued learnings with human review |
| `/reflect --scan-history` | Scan past sessions for missed learnings |
| `/reflect --dry-run` | Preview changes without applying |
| `/skip-reflect` | Discard all queued learnings |
| `/view-queue` | View pending learnings without processing |

## When to Remind Users

Remind users about `/reflect` when:
- They complete a feature or meaningful work unit
- They make corrections you should remember for future sessions
- They explicitly say "remember this" or similar
- Context is about to compact and queue has items

## Correction Detection Patterns

High-confidence corrections:
- Tool rejections (user stops an action with guidance)
- "no, use X" / "don't use Y"
- "actually..." / "I meant..."
- "use X not Y" / "X instead of Y"
- "remember:" (explicit marker)

## CLAUDE.md Destinations

- `~/.claude/CLAUDE.md` - Global learnings (model names, general patterns)
- `./CLAUDE.md` - Project-specific learnings (conventions, tools, structure)

## Example Interaction

```
User: no, use gpt-5.1 not gpt-5 for reasoning tasks
Claude: Got it, I'll use gpt-5.1 for reasoning tasks.

[Hook captures this correction to queue]

User: /reflect
Claude: Found 1 learning queued. "Use gpt-5.1 for reasoning tasks"
        Scope: global
        Apply to ~/.claude/CLAUDE.md? [y/n]
```

## Overview

Execute self-learning system that captures corrections during sessions and syncs them to CLAUDE.

## Prerequisites

- Access to the Claude Reflect environment or API
- Required CLI tools installed and authenticated
- Familiarity with Claude Reflect concepts and terminology

## Instructions

1. Assess the current state of the Claude Reflect configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with Claude Reflect |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply claude reflect to a standard project setup with default configuration options.

**Advanced scenario**: Customize claude reflect for production environments with multiple constraints and team-specific requirements.

## Resources

- Official Claude Reflect documentation
- Community best practices and patterns
- Related skills in this plugin pack