# Frontmatter Specification

Complete reference for SKILL.md YAML frontmatter fields.

---

## Required Fields

### `name`
- **Type:** string
- **Format:** kebab-case (`a-z`, `0-9`, hyphens)
- **Max length:** 64 characters
- **Convention:** Must match directory name. Gerund form preferred (`processing-pdfs` not `pdf-processor`).
- **Validation:** Error if missing, warning if not kebab-case or mismatches folder name.

### `description`
- **Type:** string (multiline with `|`)
- **Min length:** 20 characters
- **Max length:** 1024 characters
- **Requirements:**
  - Third person voice (no "I can" or "You should")
  - Must include "Use when ..." phrase (+3 marketplace pts)
  - Must include "Trigger with ..." phrase (+3 marketplace pts)
  - Action verb near start (analyze, create, deploy, etc.)
  - No reserved words in isolation (anthropic, claude)
- **Best practice:** Front-load distinctive keywords. Add "Make sure to use whenever..." for aggressive activation.

---

## Identity Fields (Top-Level)

These MUST be top-level fields. Do NOT nest under `metadata:`.

### `version`
- **Type:** string
- **Format:** Semver (`X.Y.Z`)
- **Example:** `1.0.0`
- **Validation:** Error if not semver format.

### `author`
- **Type:** string
- **Format:** `Name <email>`
- **Example:** `Jeremy Longshore <jeremy@intentsolutions.io>`
- **Validation:** Warning if no email included.

### `license`
- **Type:** string
- **Format:** SPDX identifier
- **Default:** `MIT`

### `allowed-tools`
- **Type:** string (CSV format, NOT YAML array)
- **Valid tools:** Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task, TodoWrite, NotebookEdit, AskUserQuestion, Skill
- **Bash scoping:** Must be scoped — `Bash(git:*)`, `Bash(npm:*)`, `Bash(python3:*)`. Unscoped `Bash` is an error.
- **MCP tools:** `ServerName:tool_name`
- **Example:** `"Read,Write,Edit,Glob,Grep,Bash(git:*),Bash(npm:*)"`
- **Validation:** Error if unscoped Bash, error if unknown tool name.

---

## Optional Fields (Anthropic Spec)

### `model`
- **Type:** string
- **Values:** `inherit` (default), `sonnet`, `haiku`, `opus`, or `claude-*` model ID
- **When to use:** Only override when the skill specifically needs a different model capability.

### `argument-hint`
- **Type:** string
- **Max length:** 200 characters
- **Purpose:** Autocomplete hint shown in `/name` menu.
- **Example:** `"<file-path>"`, `"[version-tag]"`

### `context`
- **Type:** string
- **Values:** `fork`
- **Purpose:** Run skill in an isolated subagent context.

### `agent`
- **Type:** string
- **Purpose:** Specify subagent type when using `context: fork`.
- **Values:** Any valid agent type (e.g., `general-purpose`, `Explore`)

### `user-invocable`
- **Type:** boolean
- **Default:** `true`
- **Purpose:** Set `false` to hide from `/` menu. Skill still activates via model matching.

### `disable-model-invocation`
- **Type:** boolean
- **Default:** `false`
- **Purpose:** Set `true` to prevent auto-activation. Only triggers via explicit `/name` command.

### `hooks`
- **Type:** object
- **Purpose:** Skill-scoped lifecycle hooks (pre-tool-call, post-tool-call, etc.)

---

## Extended Fields (Marketplace)

These are recognized by the Intent Solutions marketplace but not part of the core Anthropic spec.

### `compatible-with`
- **Type:** string (CSV) or array
- **Values:** `claude-code`, `codex`, `openclaw`, `aider`, `continue`, `cursor`, `windsurf`
- **Purpose:** Declare which AI coding platforms this skill works with.

### `compatibility`
- **Type:** string
- **Purpose:** Environment requirements (e.g., `"Node.js >= 18"`, `"Python 3.10+"`)

### `tags`
- **Type:** array of strings
- **Purpose:** Discovery tags for marketplace search.
- **Example:** `[devops, ci, deployment]`

---

## Deprecated Fields

### `when_to_use`
- **Status:** Deprecated
- **Migration:** Move content into the `description` field using "Use when ..." pattern.

### `metadata` (as parent for identity fields)
- **Status:** Anti-pattern
- **Migration:** Move `author`, `version`, `license` to top-level.
