# 6767-c-DR-STND-claude-code-extensions-standard.md

**Document Type**: Developer Resource - Standard (DR-STND)
**Document ID**: 6767-c-DR-STND-claude-code-extensions-standard
**Title**: Claude Code Extensions Standard (Unified)
**Version**: 3.0.0
**Status**: CANONICAL (Enterprise-Only)
**Date**: 2025-12-20
**Supersedes**: 6767-a (plugins), 6767-b (skills)
**Superseded By**: 6767-h (master spec)
**Authority**: Intent Solutions (Enterprise Marketplace)

---

## TRUTH INVARIANTS (ENTERPRISE MODE)

**MODE**: ENTERPRISE MODE ALWAYS ON. No "Anthropic-minimum" fallback. All fields marked "REQUIRED" are REQUIRED.

**CORE RULES**:

1. **allowed-tools Format**:
   - ✅ CORRECT: CSV string → `allowed-tools: "Read,Write,Grep,Glob"`
   - ❌ WRONG: YAML array → `allowed-tools: [Read, Write, Grep]`
   - Violation: CRITICAL ERROR (`SKILL_022`)

2. **Bash Scoping**:
   - ✅ CORRECT: Scoped → `Bash(git:*)`, `Bash(npm:*)`, `Bash(python:*)`
   - ❌ WRONG: Unscoped → `Bash`
   - Violation: CRITICAL ERROR (`SKILL_024`)

3. **Path Portability**:
   - ✅ CORRECT: `${CLAUDE_PLUGIN_ROOT}/...` or `{baseDir}/...`
   - ❌ WRONG: `/home/user/...` or `~/...`
   - Violation: CRITICAL ERROR (`SKILL_103`, `SEC_005`)

4. **Naming Convention**:
   - Pattern: `^[a-z0-9-]+$` (kebab-case only)
   - Max length: 64 chars
   - Reserved words: NO "claude" or "anthropic"
   - Violation: CRITICAL ERROR (`NAMING_001`, `NAMING_002`, `NAMING_003`)

5. **Versioning**:
   - Format: SemVer `MAJOR.MINOR.PATCH` (3 parts)
   - Example: `1.0.0`, `2.3.1`
   - Violation: CRITICAL ERROR (`PLUGIN_012`, `SKILL_032`)

6. **Directory Structure**:
   - `.claude-plugin/` contains ONLY `plugin.json`
   - Component dirs (skills/, agents/, commands/) at plugin root, NOT inside `.claude-plugin/`
   - Violation: CRITICAL ERROR (`DIR_002`, `DIR_005`)

7. **Security**:
   - NO hardcoded secrets, API keys, .env files committed
   - Secrets via environment variables ONLY
   - Exemptions: ONLY `tests/fixtures/**` + known test patterns (EXAMPLE, DUMMY, test-)
   - Violation: CRITICAL ERROR (`SEC_001`, `SEC_002`, `SEC_003`, `SEC_004`)

8. **Context Hygiene**:
   - SKILL.md body ≤ 5,000 words / 500 lines / ~7,500 tokens
   - Heavy content in `references/` directory (loaded on-demand)
   - Violation: HIGH ERROR (`SKILL_100`, `SKILL_101`)

9. **Discoverability**:
   - Description MUST include "Use when..." phrase
   - Description MUST include 2-6 trigger phrases
   - Violation: HIGH ERROR (`SKILL_015`, `SKILL_016`)

10. **Required Fields (Enterprise)**:
    - Plugin: name, version, description, author (name + email), license, keywords
    - Skill: name, description, allowed-tools (CSV), version, author, license, tags
    - Violation: CRITICAL ERROR (various `PLUGIN_*`, `SKILL_*` codes)

**VALIDATION**:
- Validator runs in ENTERPRISE MODE ONLY
- CRITICAL/HIGH errors BLOCK PR merge
- Deterministic error codes (6767-d schema)

**NO EXCEPTIONS**: These rules apply to ALL plugins/skills, regardless of size or complexity.

---

## 1. Purpose and Scope

### 1.1 Purpose

This specification defines the **unified standard** for all Claude Code extension types:
- **Plugins** (containers: manifest, metadata, lifecycle)
- **Skills** (capabilities: workflows, tool authorization, context)
- **Agents** (subagents: delegation, specialization, model selection)
- **Commands** (slash commands: user-triggered prompts)
- **Hooks** (event handlers: lifecycle automation)
- **MCP Servers** (Model Context Protocol: external tool integration)

This standard operates in **ENTERPRISE MODE ONLY**. There is no "Anthropic-minimum" mode. All requirements herein are MANDATORY for marketplace publication, CI gates, and production deployment.

### 1.2 Scope

**In Scope:**
- Directory structure and naming conventions
- Manifest schemas (plugin.json, SKILL.md frontmatter, agent.md, hooks.json, .mcp.json)
- Security constraints (secrets, paths, tool scoping)
- Context hygiene (progressive disclosure, .claudeignore, size limits)
- Portability (environment variables, relative paths)
- Discoverability (descriptions, trigger phrases, router guidance)
- Validation and CI enforcement

**Out of Scope:**
- Runtime execution behavior (covered by Claude Code core)
- User interface design (covered by Claude frontend specs)
- Third-party integrations (covered by MCP protocol spec)

---

## 2. Key Definitions

### 2.1 Extension Types

| Type | Definition | Primary File | Location |
|------|------------|--------------|----------|
| **Plugin** | Container for skills/agents/commands/hooks/MCP servers | `plugin.json` | `.claude-plugin/plugin.json` |
| **Skill** | Capability that teaches Claude a workflow or process | `SKILL.md` | `skills/<skill-name>/SKILL.md` |
| **Agent** | Specialized subagent for complex, multi-step tasks | `agent.md` (frontmatter) | `agents/<agent-name>.md` |
| **Command** | User-triggered slash command that expands to a prompt | `command.md` (optional frontmatter) | `commands/<command-name>.md` |
| **Hook** | Event handler that runs on lifecycle events | `hooks.json` | `hooks/hooks.json` OR inline in plugin.json |
| **MCP Server** | External tool server using Model Context Protocol | `.mcp.json` | `.mcp.json` OR inline in plugin.json |

### 2.2 Container vs Capability

- **Container** (Plugin): Metadata and lifecycle management. The `.claude-plugin/plugin.json` file is the plugin manifest.
- **Capability** (Skill/Agent/Command): Actual functionality. Lives in component directories at plugin root.
- **Integration** (Hook/MCP): Automation and external tools. Configured via JSON.

**Critical Rule**: `.claude-plugin/` contains ONLY `plugin.json`. All component directories (skills/, agents/, commands/, hooks/) MUST be at plugin root, NOT inside `.claude-plugin/`.

### 2.3 Enterprise vs Anthropic-Minimum

**This spec operates in ENTERPRISE MODE ONLY**. Historical "Anthropic-minimum" mode is deprecated. All fields marked "Enterprise Required" in this spec are REQUIRED. Validators, CI gates, and marketplaces MUST enforce enterprise requirements.

---

## 3. Directory Structure

### 3.1 Plugin Root Anatomy

```
my-plugin/                              ← Plugin root
├── .claude-plugin/                     ← Metadata directory
│   └── plugin.json                     ← ONLY file allowed here
├── skills/                             ← Optional: skill capabilities
│   └── <skill-name>/
│       ├── SKILL.md                    ← Skill definition (frontmatter + body)
│       └── references/                 ← Optional: heavy tables/docs
├── agents/                             ← Optional: agent definitions
│   └── <agent-name>.md                 ← Agent definition (frontmatter + body)
├── commands/                           ← Optional: slash commands
│   └── <command-name>.md               ← Command definition
├── hooks/                              ← Optional: event hooks
│   └── hooks.json                      ← Hook configuration
├── scripts/                            ← Optional: helper scripts
│   ├── validate_standards.py
│   └── ...
├── .mcp.json                           ← Optional: MCP server config
├── .claudeignore                       ← Optional: context exclusions
├── README.md                           ← Required: documentation
└── 000-docs/                           ← Optional: project docs (if complex)
    └── (flat structure, NNN-CC-ABCD naming)
```

### 3.2 Critical Constraints

**MUST**:
- `.claude-plugin/` contains ONLY `plugin.json` (no other files)
- Component directories (skills/, agents/, commands/, hooks/) at plugin root (NOT inside `.claude-plugin/`)
- Only create directories you use (NO empty placeholders)
- Plugin name, skill names, agent names MUST be kebab-case
- All paths MUST be relative or use `${CLAUDE_PLUGIN_ROOT}` / `{baseDir}`

**MUST NOT**:
- Place any components inside `.claude-plugin/` besides plugin.json
- Use absolute paths (e.g., `/home/user/...`)
- Hardcode secrets or API keys
- Commit `.env` files
- Use uppercase letters in names

---

## 4. Plugin Manifest (plugin.json)

### 4.1 Schema (Enterprise Required Fields)

```json
{
  "name": "my-plugin-name",              // REQUIRED: kebab-case, max 64 chars, ^[a-z0-9-]+$
  "version": "1.0.0",                    // REQUIRED: SemVer (MAJOR.MINOR.PATCH)
  "description": "...",                  // REQUIRED: brief explanation
  "author": {                            // REQUIRED: author object
    "name": "Developer Name",            // REQUIRED: author name
    "email": "dev@example.com"           // REQUIRED: author email
  },
  "license": "MIT",                      // REQUIRED: SPDX identifier
  "keywords": ["tag1", "tag2"],          // REQUIRED: array of strings
  "homepage": "https://...",             // OPTIONAL: documentation URL
  "repository": "https://github.com/...", // OPTIONAL: source URL
  "commands": "./commands/",             // OPTIONAL: path(s) to commands
  "agents": "./agents/",                 // OPTIONAL: path(s) to agents
  "skills": ["./skills/skill-1/"],       // OPTIONAL: array of skill paths
  "hooks": "./hooks/hooks.json",         // OPTIONAL: path or inline config
  "mcpServers": {                        // OPTIONAL: MCP server config
    "server-name": {
      "command": "python",
      "args": ["${CLAUDE_PLUGIN_ROOT}/bin/server.py"]
    }
  }
}
```

### 4.2 Field Constraints (Enterprise)

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | ✅ REQUIRED | kebab-case, max 64 chars, pattern `^[a-z0-9-]+$`, no "claude" or "anthropic" |
| `version` | string | ✅ REQUIRED | SemVer (MAJOR.MINOR.PATCH), 3 parts |
| `description` | string | ✅ REQUIRED | Non-empty, max 1024 chars |
| `author` | object | ✅ REQUIRED | MUST have `name` and `email` |
| `author.name` | string | ✅ REQUIRED | Non-empty |
| `author.email` | string | ✅ REQUIRED | Valid email format |
| `license` | string | ✅ REQUIRED | SPDX identifier (MIT, Apache-2.0, Proprietary, etc.) |
| `keywords` | array | ✅ REQUIRED | Array of strings, min 1 item |
| `homepage` | string | OPTIONAL | Valid URL if present |
| `repository` | string | OPTIONAL | Valid URL if present |
| `commands` | string or array | OPTIONAL | Path(s) to command directories |
| `agents` | string or array | OPTIONAL | Path(s) to agent files/directories |
| `skills` | string or array | OPTIONAL | Path(s) to skill directories |
| `hooks` | string or object | OPTIONAL | Path to hooks.json OR inline config |
| `mcpServers` | object | OPTIONAL | MCP server configuration |

### 4.3 Portability Rules

**Environment Variable**: `${CLAUDE_PLUGIN_ROOT}`
- Expands to plugin root directory at runtime
- MUST be used for all plugin-relative paths in `plugin.json`, hooks, MCP servers
- Example: `"${CLAUDE_PLUGIN_ROOT}/bin/server.py"`

**MUST NOT**:
- Use absolute paths (e.g., `/home/jeremy/...`)
- Use `~` or `$HOME` (not portable)
- Use `.` or `..` for parent traversal (security risk)

**MUST**:
- Use `${CLAUDE_PLUGIN_ROOT}` for plugin-internal paths
- Use relative paths within plugin root where possible
- Validate all paths in validator

---

## 5. Skills

### 5.1 Skill Anatomy

**Location**: `skills/<skill-name>/SKILL.md`

**Structure**:
1. **Frontmatter** (YAML): Metadata and configuration
2. **Body** (Markdown): Instructions, workflow, examples, error handling

### 5.2 Frontmatter Schema (Enterprise Required)

```yaml
---
name: skill-name                       # REQUIRED: kebab-case, max 64 chars, ^[a-z0-9-]+$
description: "..."                     # REQUIRED: max 1024 chars, third-person, includes "Use when..." + triggers
allowed-tools: "Read,Write,Grep,Glob"  # REQUIRED: CSV string (NOT YAML array)
version: "1.0.0"                       # REQUIRED: SemVer
author: "Name <email>"                 # REQUIRED: Name + email
license: "MIT"                         # REQUIRED: SPDX identifier
tags: ["tag1", "tag2"]                 # REQUIRED: array of strings
model: "inherit"                       # OPTIONAL: model override (inherit, sonnet, opus, haiku)
mode: false                            # OPTIONAL: categorize as mode (default false)
disable-model-invocation: false        # OPTIONAL: hide from auto-discovery (default false)
---
```

### 5.3 Field Constraints (Enterprise)

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | ✅ REQUIRED | kebab-case, max 64 chars, pattern `^[a-z0-9-]+$`, no "claude" or "anthropic" |
| `description` | string | ✅ REQUIRED | Max 1024 chars, third-person voice, MUST include "Use when..." + trigger phrases |
| `allowed-tools` | string | ✅ REQUIRED | CSV string (comma-separated), NOT YAML array. Example: "Read,Write,Grep" |
| `version` | string | ✅ REQUIRED | SemVer (MAJOR.MINOR.PATCH) |
| `author` | string | ✅ REQUIRED | Format: "Name <email>" or "Name" |
| `license` | string | ✅ REQUIRED | SPDX identifier |
| `tags` | array | ✅ REQUIRED | Array of strings, min 1 item (marketplace discoverability) |
| `model` | string | OPTIONAL | "inherit" (default), "sonnet", "opus", "haiku", or specific model ID |
| `mode` | boolean | OPTIONAL | Default false. Set true for mode commands (separate UI section) |
| `disable-model-invocation` | boolean | OPTIONAL | Default false. Set true to remove from auto-discovery |

### 5.4 Description Formula (REQUIRED)

**Template**:
```
[Primary capabilities]. [Secondary features]. Use when [scenarios]. Trigger with "[phrases]", "[synonyms]", or "[common-terms]".
```

**Example (Good)**:
```yaml
description: "Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction. Trigger with 'process pdf', 'extract from pdf', or 'merge pdfs'."
```

**Example (Bad)**:
```yaml
description: "Helps with documents"  # ❌ Missing: Use when, triggers, specifics
```

### 5.5 allowed-tools (CRITICAL: CSV String NOT YAML Array)

**CORRECT** (CSV string):
```yaml
allowed-tools: "Read,Write,Grep,Glob,Bash(git status:*),Bash(git diff:*)"
```

**WRONG** (YAML array):
```yaml
allowed-tools:           # ❌ INVALID (will be rejected by validator)
  - Read
  - Write
  - Bash
```

**Tool Scoping** (Enterprise Security Policy):
- Prefer minimal tools: `Read,Write,Grep,Glob`
- If Bash needed, scope it: `Bash(git:*)`, `Bash(npm:*)`, `Bash(python:*)`
- NEVER grant unscoped `Bash` (security risk)
- Unscoped Bash MUST be flagged as CRITICAL error by validator

### 5.6 Body Constraints (Enterprise Context Hygiene)

| Constraint | Limit | Rationale |
|------------|-------|-----------|
| **Max word count** | 5,000 words | Context window hygiene |
| **Max line count** | 500 lines | Progressive disclosure |
| **Max tokens** | ~7,500 tokens | LLM context budget |
| **Path format** | `{baseDir}/...` | Portability (no absolute paths) |
| **Reference depth** | 1 level | Prevent reference chains (SKILL.md → ref.md OK; SKILL.md → ref1.md → ref2.md NOT OK) |

**Progressive Disclosure Pattern**:
- SKILL.md contains workflow, instructions, examples
- Heavy tables/data go in `references/` directory
- References loaded on-demand, not always in context
- Example: `{baseDir}/skills/my-skill/references/error-codes.md`

### 5.7 Required Sections (Enterprise Quality Standard)

1. **Title** (H1): Skill name
2. **Purpose** (1-2 sentences): What this skill does
3. **Overview** (3-5 sentences): How it works
4. **Prerequisites**: Required tools, dependencies, environment setup
5. **Instructions**: Step-by-step numbered workflow
6. **Output**: What the skill produces
7. **Error Handling**: Minimum 4 failure cases with cause + recovery
8. **Examples**: 2-3 examples with input/output pairs
9. **Resources**: Links to references, documentation

---

## 6. Agents

### 6.1 Agent Anatomy

**Location**: `agents/<agent-name>.md`

**Structure**:
1. **Frontmatter** (YAML): Metadata and configuration
2. **Body** (Markdown): Delegation criteria, specialization, instructions

### 6.2 Frontmatter Schema (Enterprise)

```yaml
---
name: agent-name                       # REQUIRED: Agent identifier
description: "..."                     # REQUIRED: When Claude should delegate to this agent
tools: "Read,Write,Grep,Glob"          # OPTIONAL: CSV string (inherits all if omitted)
model: "inherit"                       # OPTIONAL: model override
permissionMode: "auto"                 # OPTIONAL: permission mode
skills: "skill-1,skill-2"              # OPTIONAL: comma-separated skill names to auto-load
---
```

### 6.3 Field Constraints

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | ✅ REQUIRED | Agent identifier (kebab-case recommended) |
| `description` | string | ✅ REQUIRED | When Claude should delegate (clear criteria) |
| `tools` | string | OPTIONAL | CSV string (inherits all if omitted) |
| `model` | string | OPTIONAL | Model override (inherit, sonnet, opus, haiku) |
| `permissionMode` | string | OPTIONAL | Permission mode |
| `skills` | string | OPTIONAL | Comma-separated skill names to auto-load |

---

## 7. Commands

### 7.1 Command Anatomy

**Location**: `commands/<command-name>.md`

**Invocation**: User types `/<command-name>` (filename without .md)

**Structure**:
1. **Frontmatter** (YAML, optional): Metadata
2. **Body** (Markdown): Prompt text that expands when command is invoked

### 7.2 Frontmatter Schema (Optional)

```yaml
---
description: "Brief explanation"       # OPTIONAL: What this command does
allowed-tools: "Read,Write,Grep"       # OPTIONAL: CSV string (tool restrictions)
---
```

---

## 8. Hooks

### 8.1 Hook Configuration

**Location**: `hooks/hooks.json` OR inline in `plugin.json` under `"hooks"` key

**Events**:
- `PreToolUse` (matcher required)
- `PostToolUse` (matcher required)
- `PermissionRequest` (matcher required)
- `UserPromptSubmit`
- `Stop`
- `SubagentStop`
- `SessionStart` (matcher required)
- `SessionEnd`
- `PreCompact` (matcher required)
- `Notification` (matcher optional)

### 8.2 Hook Types

1. **command**: Execute bash command
2. **prompt**: LLM-based evaluation

### 8.3 Output Schema

```json
{
  "continue": true,                    // Boolean: continue or block
  "stopReason": "...",                 // Optional: reason for stopping
  "suppressOutput": false,             // Boolean: hide output
  "systemMessage": "...",              // String: message to LLM
  "hookSpecificOutput": {}             // Object: event-specific fields
}
```

### 8.4 Security Constraints

**MUST**:
- Set timeouts on all hooks (prevent hangs)
- Scope bash commands (no unrestricted bash)
- Validate paths (prevent traversal)
- Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths

**MUST NOT**:
- Execute arbitrary user input without sanitization
- Allow unbounded network calls
- Expose sensitive data in logs

---

## 9. MCP Servers

### 9.1 MCP Configuration

**Location**: `.mcp.json` OR inline in `plugin.json` under `"mcpServers"` key

**Schema**:
```json
{
  "server-name": {
    "command": "python",               // Command to execute
    "args": [                          // Arguments
      "${CLAUDE_PLUGIN_ROOT}/bin/server.py"
    ],
    "env": {                           // Optional: environment variables
      "API_KEY": "${MY_API_KEY}"
    }
  }
}
```

### 9.2 Portability Rules

**MUST**:
- Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths
- Use environment variables for secrets (e.g., `${MY_API_KEY}`)
- Document required environment variables in README

**MUST NOT**:
- Hardcode absolute paths
- Hardcode secrets or API keys
- Assume specific directory structure outside plugin root

---

## 10. Security Constraints (Enterprise Policy)

### 10.1 Secrets and Credentials

**MUST NOT**:
- Hardcode API keys, tokens, passwords in code/config
- Commit `.env` files
- Commit credential files
- Log sensitive data
- Pass unvalidated user input to shell

**MUST**:
- Use environment variables for secrets
- Add `.env` to `.gitignore`
- Document required env vars in README (with `.env.example`)
- Sanitize all inputs
- Use `${VARIABLE_NAME}` syntax in configs

### 10.2 Tool Scoping

**Bash Tool Scoping** (CRITICAL):
- ✅ GOOD: `Bash(git status:*)`, `Bash(npm run test:*)`, `Bash(python -m:*)`
- ❌ BAD: `Bash` (unscoped - allows arbitrary commands)

**Validator MUST**:
- Flag unscoped `Bash` as CRITICAL error
- Require explicit scoping: `Bash(command:*)` or `Bash(command subcommand:*)`

### 10.3 Path Safety

**MUST NOT**:
- Use absolute paths (e.g., `/home/user/...`)
- Use `..` for parent traversal (security risk)
- Allow user-controlled paths without validation

**MUST**:
- Use `${CLAUDE_PLUGIN_ROOT}` for plugin paths
- Use `{baseDir}` for repo-relative skill references
- Validate all paths to prevent traversal

### 10.4 Secret Scanning (Enterprise Validator)

**Exemptions** (minimal allowlist):
- `tests/fixtures/**` (explicit test data directory)
- Files containing known test patterns: `EXAMPLE`, `DUMMY`, `test-`, etc.

**Scanned Everywhere Else**:
- All source code (including non-fixture test code)
- All configuration files
- All documentation

**Detected Patterns**:
- API keys (32+ char alphanumeric)
- AWS keys (`AKIA...`)
- SSH keys (`-----BEGIN RSA PRIVATE KEY-----`)
- Emails (PII in non-author contexts)
- Credit cards

**Severity**: CRITICAL (blocks PR, fails CI)

---

## 11. Context Hygiene (Enterprise Policy)

### 11.1 Progressive Disclosure

**Problem**: Loading all plugin content into context wastes tokens.

**Solution**:
- Keep SKILL.md body ≤ 5,000 words
- Move heavy tables/data to `references/` directory
- Load references on-demand, not always in context
- Use `.claudeignore` to exclude non-essential files

### 11.2 .claudeignore Pattern

**Purpose**: Exclude files from context to save tokens.

**Example**:
```
# Build artifacts
*.pyc
__pycache__/
.venv/
node_modules/

# Heavy data files
data/
fixtures/
*.log
*.csv

# Documentation (load on-demand)
docs/
examples/
```

### 11.3 Size Limits (Enterprise Quality)

| Component | Limit | Enforced By |
|-----------|-------|-------------|
| SKILL.md body | 5,000 words / 500 lines / ~7,500 tokens | Validator (CRITICAL) |
| Plugin description | 1,024 characters | Validator (CRITICAL) |
| Skill description | 1,024 characters | Validator (CRITICAL) |
| Reference docs | No hard limit (loaded on-demand) | N/A |

---

## 12. Discoverability (Router Guidance)

### 12.1 Description Best Practices

**Goal**: Help Claude's router decide when to invoke a skill/agent.

**Formula**:
```
[Capabilities]. Use when [user scenarios]. Trigger with "[phrases]", "[synonyms]".
```

**Good Example**:
```
Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction. Trigger with "process pdf", "extract from pdf", or "merge pdfs".
```

**Bad Examples**:
- "Helps with PDFs" (too vague)
- "PDF processing tool" (no triggers, no scenarios)
- "Extracts text..." (missing "Use when", missing triggers)

### 12.2 Third-Person Voice (Required)

**Descriptions MUST**:
- Use third-person voice ("Extracts...", "Processes...", not "I extract...")
- Be objective (not promotional: "amazing tool", "best solution")
- Include concrete scenarios ("when user uploads PDF", not "when needed")

---

## 13. Versioning and Deprecation

### 13.1 Semantic Versioning (SemVer)

**Required Format**: `MAJOR.MINOR.PATCH`

**Rules**:
- **MAJOR**: Breaking changes (incompatible API changes)
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes, documentation

**Examples**:
- ✅ `1.0.0`, `2.3.1`, `0.1.0`
- ❌ `v1.0`, `1.0`, `1` (missing parts)

### 13.2 Deprecation Process

1. **Mark deprecated** in description: `[DEPRECATED] Old command...`
2. **Keep working** for one minor version (e.g., 1.3.x)
3. **Remove** in next major version (e.g., 2.0.0)
4. **Document** in CHANGELOG and README

---

## 14. Compliance Modes

### 14.1 Enterprise Mode (ONLY Mode)

**This spec operates in ENTERPRISE MODE ONLY**. All fields marked "REQUIRED" in this spec are REQUIRED. Validators MUST enforce enterprise requirements.

**Historical Note**: Previous specs (6767-a, 6767-b) distinguished "Anthropic-minimum" vs "Enterprise/Marketplace" requirements. This spec **deprecates** that distinction. Enterprise requirements are now the **ONLY** requirements.

### 14.2 Required Fields Summary

**Plugin**:
- name, version, description, author (name + email), license, keywords

**Skill**:
- name, description, allowed-tools (CSV string), version, author, license, tags

**Agent**:
- name, description

**Command**:
- (No required frontmatter; body is the prompt)

---

## 15. Validation and Enforcement

### 15.1 Validator Requirements

**Every validator MUST**:
- Enforce ALL enterprise requirements (no "Anthropic-min" mode)
- Flag violations with severity: CRITICAL, HIGH, MEDIUM, LOW
- Block CRITICAL and HIGH errors in CI
- Report deterministic, actionable errors

**Validation Categories**:
1. **Manifest**: plugin.json schema, required fields, name format, version format
2. **Directory Structure**: `.claude-plugin/` contains ONLY plugin.json, components at root
3. **Skills**: frontmatter fields, CSV string for allowed-tools, body size limits
4. **Security**: hardcoded secrets, .env files, path traversal, tool scoping
5. **Naming**: kebab-case, max length, reserved words

### 15.2 CI Gates (Enterprise Policy)

**PR Workflow**:
- Run validator in enterprise mode
- Block PR on CRITICAL or HIGH errors
- Report all findings

**Main Branch Workflow**:
- Run comprehensive validation (enterprise mode)
- Run security scans (secrets, dependencies)
- Generate coverage reports
- Archive validation artifacts

### 15.3 Error Reporting Format

**Required Fields**:
- Severity: CRITICAL | HIGH | MEDIUM | LOW
- File path: Exact location of violation
- Field: Which field/rule violated
- Expected: What was expected
- Actual: What was found
- Fix: How to remediate (actionable guidance)

**Example**:
```
[CRITICAL] skills/my-skill/SKILL.md
  Field: allowed-tools
  Expected: CSV string (e.g., "Read,Write,Bash(git:*)")
  Actual: YAML array format
  Fix: Change frontmatter to: allowed-tools: "Read,Write,Bash(git:*)"
```

---

## 16. Governance and Updates

### 16.1 Authority

This specification is maintained by **Intent Solutions** for the **Enterprise Marketplace**.

**Contact**: jeremy@intentsolutions.io

### 16.2 Change Process

1. **Propose change** via GitHub issue or pull request
2. **Review** by maintainers (Intent Solutions)
3. **Approve** via consensus
4. **Update version**:
   - MAJOR: Breaking changes
   - MINOR: New requirements (backward-compatible)
   - PATCH: Clarifications, typo fixes
5. **Publish** updated spec
6. **Deprecate** old versions (if breaking)

### 16.3 Backward Compatibility

**Breaking Changes**:
- Require MAJOR version bump
- Must include migration guide
- Old version marked DEPRECATED
- Grace period: 1 quarter (3 months)

**Non-Breaking Changes**:
- New optional fields: MINOR bump
- Clarifications: PATCH bump

---

## 17. References

### 17.1 Related Standards

- **6767-d**: Schema definition (machine-readable validation rules)
- **6767-e**: Validation and CI gates (enforcement specification)
- **Document Filing System v4.2**: 000-docs/ structure and naming

### 17.2 Deprecated Standards

- **6767-a**: Claude Code Plugins Standard (v2.x) - DEPRECATED
- **6767-b**: Claude Skills Standard (v2.x) - DEPRECATED

**Superseded By**: This specification (6767-c v3.0.0)

### 17.3 External Standards

- **Semantic Versioning**: https://semver.org/
- **SPDX License Identifiers**: https://spdx.org/licenses/
- **Kebab Case**: https://en.wikipedia.org/wiki/Letter_case#Kebab_case
- **Model Context Protocol**: https://modelcontextprotocol.io/

---

## 18. Appendix: Examples

### 18.1 Minimal Plugin (Enterprise Compliant)

**Directory**:
```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
└── README.md
```

**plugin.json**:
```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Example plugin for demonstration",
  "author": {
    "name": "Developer Name",
    "email": "dev@example.com"
  },
  "license": "MIT",
  "keywords": ["example", "demo"]
}
```

### 18.2 Plugin with Skills (Enterprise Compliant)

**Directory**:
```
analytics-plugin/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── data-analysis/
│       ├── SKILL.md
│       └── references/
│           └── error-codes.md
└── README.md
```

**skills/data-analysis/SKILL.md**:
```yaml
---
name: data-analysis
description: "Analyze datasets with statistical methods, generate visualizations, and export reports. Use when user provides data files or requests analysis, charts, or statistical summaries. Trigger with 'analyze data', 'create chart', or 'statistical analysis'."
allowed-tools: "Read,Write,Grep,Glob,Bash(python:*)"
version: "1.0.0"
author: "Analytics Team <analytics@example.com>"
license: "MIT"
tags: ["analytics", "statistics", "visualization"]
---

# Data Analysis Skill

## Purpose
Analyze datasets and generate insights.

## Instructions
1. Read data file
2. Validate schema
3. Compute statistics
4. Generate visualizations
5. Export report

## Error Handling
- **Missing columns**: Check schema, prompt user for column names
- **Invalid data types**: Convert or skip rows with errors
- **Empty dataset**: Return error message with guidance
- **Memory limits**: Sample large datasets before full processing

## Examples
...
```

---

**END OF SPECIFICATION**

**Version**: 3.0.0
**Status**: CANONICAL (Enterprise-Only)
**Date**: 2025-12-20
