---
name: audit-plugin
description: Performs a deep review of the Claude Code plugin, skill, or sub-agent defined in the current project against official best practices. Documents findings as GitHub issues and writes a prioritised fix plan to the project CLAUDE.md. Use when the user says audit this plugin, review this skill, check this agent, or audit addon.
allowed-tools: Read Glob Grep Bash WebSearch WebFetch
disable-model-invocation: true
---

# Audit Plugin

Project: !`basename $(git rev-parse --show-toplevel 2>/dev/null) 2>/dev/null || basename $PWD`
Branch: !`git branch --show-current 2>/dev/null || echo "unknown"`

Reviews the Claude Code addon in the current project (plugin, skill, sub-agent, or a combination)
against official Claude Code best practices. Generates actionable GitHub issues and a prioritised
fix plan.

## Step 0: Pre-flight check

```bash
gh auth status 2>&1 || { echo "ERROR: gh is not authenticated. Run: gh auth login"; exit 1; }
```

## Step 1: Identify what kind of addon this project defines

Scan for known Claude Code addon files:

```bash
find . -not -path './.git/*' \( \
  -name 'plugin.json' -path '*/.claude-plugin/*' \
  -o -name 'SKILL.md' -path '*/skills/*' \
  -o -name '*.md' -path '*/agents/*' \
\) 2>/dev/null
```

Read each file found. Build a mental model of:

- Plugin manifest (`.claude-plugin/plugin.json`) — name, version, declared agents/skills
- Skills (`skills/<name>/SKILL.md`) — frontmatter fields, body structure, tool declarations
- Agents (`agents/<name>.md`) — frontmatter fields, description examples, tool restrictions

## Step 2: Fetch current best-practice documentation

Use WebFetch to retrieve up-to-date guidance from these known URLs:

- Skills: `https://code.claude.com/docs/en/skills`
- Sub-agents: `https://code.claude.com/docs/en/agents`
- Plugins: `https://code.claude.com/docs/en/plugins`

If any URL returns an error, use WebSearch to find the current equivalent under `code.claude.com`.
Summarise the key quality criteria from each source.

## Step 3: Evaluate against best practices

For **plugin.json**, check:

- Required fields present: `name`, `version`, `description`, `author`, `license`
- `minVersion` set to a current compatible value
- Keywords are relevant and searchable
- `description` is concise and accurate

For **each SKILL.md**, check:

- `description` is a single unbroken line under 1,536 characters (combined with `when_to_use`)
- `allowed-tools` is set and follows least-privilege (only tools the skill actually needs)
- Body is under 500 lines; large reference content moved to separate files
- Shell injection blocks (`` !`command` ``) are used where live context would help
- Step numbering is clear and actionable
- Code blocks specify a language
- Prose lines are ≤ 120 characters
- No personalised language in formal content (no "you", "your" in instructions)

For **each agent `.md`**, check:

- `description` is a quoted single-line string with proper `<example>` blocks for auto-delegation
- `model`, `color`, `maxTurns`, `memory`, `tools` and `initialPrompt` fields are present where appropriate
- Agent body is clear, focused, and actionable
- Description examples use current delegation language (no "Task tool" narration)
- `tools` list follows least-privilege

## Step 4: Generate GitHub issues

For each distinct finding, create a GitHub issue:

```bash
gh issue create \
  --title "<type>: <brief description>" \
  --body "$(cat <<'EOF'
## Finding

<description of the problem>

## Expected

<what best practice requires>

## Current

<what the file actually has>

## Suggested fix

<concrete change to make>
EOF
)" \
  --label "enhancement"
```

Group closely related findings into a single issue where it makes sense.
Use `--label "bug"` for broken or non-compliant fields, `--label "enhancement"` for improvements.

Note the issue numbers as you go.

## Step 5: Write prioritised fix plan to CLAUDE.md

Append or update a section in the project `CLAUDE.md` under the heading
`## Audit Findings — <today's date>`:

```markdown
## Audit Findings — YYYY-MM-DD

Issues generated from `/audit-plugin` review. Suggested fix order:

### Group 1 — Correctness (fix first)

- #N: <title>
- #N: <title>

### Group 2 — Best-Practice Compliance

- #N: <title>
- #N: <title>

### Group 3 — Quality Improvements

- #N: <title>
- #N: <title>
```

Order groups by: correctness blockers first, then compliance, then polish.

## Step 6: Report summary

Output a brief summary:

- Total issues created (with links)
- Top-priority fix
- Link to the CLAUDE.md section added
