---
name: validate-plugin
description: |
  Validate a Claude Code plugin directory against the official Anthropic spec
  and Intent Solutions enterprise standard. Runs structural validation (plugin.json
  fields, file references, permissions) and content validation (SKILL.md grading,
  command/agent frontmatter). Use when building a new plugin, preparing for
  marketplace submission, or auditing existing plugins. Trigger with "validate
  this plugin", "check plugin structure", "grade my plugin", "/validate-plugin".
allowed-tools: Read, Bash(python3:*), Bash(jq:*), Bash(chmod:*), Glob, Grep
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
user-invocable: true
argument-hint: "<plugin-directory-path>"
---

# Validate Plugin

Full plugin directory validator combining structural checks and content grading.

## Overview

Runs the complete validation pipeline against any plugin directory:
1. `validate-all-plugins.sh` for structural validation (plugin.json, file refs, permissions)
2. `validate-skills-schema.py` for content validation with 100-point grading

## Prerequisites

- Python 3 with `pyyaml` installed
- `jq` available on PATH
- Run from the claude-code-plugins repository root

## Instructions

1. Identify the target plugin directory (must contain `.claude-plugin/plugin.json`)
2. Run structural validation:
   ```bash
   ./scripts/validate-all-plugins.sh <plugin-directory>
   ```
3. Run content validation on any SKILL.md files found:
   ```bash
   python3 scripts/validate-skills-schema.py --verbose <path-to-SKILL.md>
   ```
4. If the plugin has commands or agents, validate those too:
   ```bash
   python3 scripts/validate-skills-schema.py --verbose
   ```
5. Report the combined results with per-skill 100-point grades

## Output

Present results in this format:

**Structural Validation:**
- plugin.json: PASS/FAIL (list any invalid fields)
- File references: PASS/FAIL
- Script permissions: PASS/FAIL

**Content Validation (per SKILL.md):**
- Grade: A-F (score/100)
- Errors: list
- Warnings: list

**Summary:**
- Total errors / warnings
- Overall verdict: PASS or FAIL

## Error Handling

- If plugin directory doesn't exist, report and exit
- If plugin.json is missing, report as structural failure
- If Python or jq not available, report as environment issue
- Continue validating remaining files even if one fails

## Examples

**Example 1: Validate a specific plugin**
```
/validate-plugin plugins/skill-enhancers/skill-creator/
```

**Example 2: Validate current directory**
```
validate this plugin
```

## Resources

- [Anthropic Plugins Reference](https://code.claude.com/docs/en/plugins-reference)
- [Anthropic Skills Spec](https://code.claude.com/docs/en/slash-commands)
