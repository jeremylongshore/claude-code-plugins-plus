# Skill Validation Rules

Two-tier validation aligned with AgentSkills.io spec + Enterprise extensions.

---

## Validation Tiers

### Standard Tier (AgentSkills.io Minimum)

The baseline. Any skill published to the ecosystem must pass this.

- `name` and `description` are the only required frontmatter fields
- Body format is flexible ("no format restrictions" - Anthropic)
- Under 500 lines
- No absolute paths
- No first/second person in description

### Enterprise Tier (Default for Our Skills)

Everything in Standard, plus:

- `metadata.author` and `metadata.version` present
- `allowed-tools` with scoped Bash
- Recommended sections present (title, instructions, examples)
- Progressive disclosure used (references/ for heavy content)
- Error handling documented
- `{baseDir}` used for all internal paths
- All referenced resources exist

---

## Frontmatter Validation

### Required Fields (Both Tiers)

| Field | Validation |
|-------|-----------|
| `name` | 1-64 chars, kebab-case `^[a-z][a-z0-9-]*[a-z0-9]$`, no consecutive hyphens, no reserved words, matches directory name |
| `description` | 1-1024 chars, non-empty, third person only, no first/second person, specific keywords |

### Enterprise-Required Fields (Top-Level)

| Field | Validation |
|-------|-----------|
| `author` | Non-empty string, email recommended (`Name <email>`) — top-level, NOT in metadata |
| `version` | Semver format (`X.Y.Z`) — top-level, NOT in metadata |
| `license` | Non-empty string (SPDX identifier) — top-level |
| `allowed-tools` | Non-empty, all tools valid, Bash scoped |

### Optional Field Validation

| Field | Validation |
|-------|-----------|
| `license` | Non-empty string if present |
| `compatibility` | 1-500 chars if present |
| `metadata` | Valid YAML object if present |
| `model` | One of: `inherit`, `sonnet`, `haiku`, `opus`, or valid model ID |
| `argument-hint` | Non-empty string if present |
| `disable-model-invocation` | Boolean if present |
| `user-invocable` | Boolean if present |
| `context` | Must be `fork` if present |
| `agent` | Non-empty string if present; requires `context: fork` |
| `hooks` | Valid object with known event keys if present |

### Deprecated Field Warnings

| Field | Warning |
|-------|---------|
| `when_to_use` | Deprecated - move to description |
| `mode` | Deprecated - use `disable-model-invocation` |

**Note**: `version`, `author`, `license`, `tags`, and `compatible-with` are valid top-level fields.
The marketplace 100-point validator scores them at top-level.

---

## Description Validation

### Must Include (Both Tiers)

- What the skill does (action-oriented)
- When to use it (context/triggers)
- Specific keywords for discovery

### Must Not Include (Both Tiers)

| Pattern | Regex | Example |
|---------|-------|---------|
| First person | `\b(I can\|I will\|I'm\|I help)\b` | "I can generate..." |
| Second person | `\b(You can\|You should\|You will)\b` | "You can use..." |

### Recommended (Enterprise)

- Action verbs (analyze, create, generate, build, debug, optimize, validate)
- Slash command reference
- Third person throughout

---

## Body Validation

### Standard Tier

| Check | Level | Detail |
|-------|-------|--------|
| Line count | Error | Must be under 500 lines |
| Absolute paths | Error | No `/home/`, `/Users/`, `C:\` outside code blocks |
| Has H1 title | Warning | Should have `# Title` |

### Enterprise Tier (adds)

| Check | Level | Detail |
|-------|-------|--------|
| Has instructions | Warning | Should have `## Instructions` or step-by-step content |
| Has examples | Warning | Should have `## Examples` or example content |
| Instructions have steps | Warning | Should have numbered steps or `### Step N` headings |
| Error handling | Warning | Should document error cases |
| Resources section | Warning | Should list `{baseDir}/` references if resources exist |
| All `{baseDir}/` refs exist | Error | Referenced scripts, references, templates must exist |
| No path escapes | Error | No `{baseDir}/../` |
| Word count | Warning | Over 5000 words suggests splitting to references |

---

## Tool Validation

### Valid Tool Names

```
Read, Write, Edit, Bash, Glob, Grep,
WebFetch, WebSearch, Task, NotebookEdit,
AskUserQuestion, Skill
```

Plus MCP tools in `ServerName:tool_name` format.

### Bash Scoping

| Tier | Unscoped `Bash` |
|------|-----------------|
| Standard | Warning |
| Enterprise | Error |

Valid scoped patterns:
```
Bash(git:*)
Bash(npm:*)
Bash(python:*)
Bash(mkdir:*)
Bash(chmod:*)
Bash(curl:*)
Bash(docker:*)
```

---

## Anti-Pattern Detection

| Anti-Pattern | Check | Level |
|-------------|-------|-------|
| Windows paths | `C:\` or backslash paths | Error |
| Nested references | `{baseDir}/references/sub/dir/file` | Warning |
| Hardcoded model IDs | `claude-*-20\d{6}` pattern | Warning |
| Voodoo constants | Unexplained magic numbers | Info |
| Over-verbose | >5000 words in SKILL.md | Warning |
| Missing progressive disclosure | >300 lines + no `references/` dir | Warning |

---

## Progressive Disclosure Scoring

| Metric | Score |
|--------|-------|
| SKILL.md under 200 lines | +2 |
| SKILL.md 200-400 lines | +1 |
| SKILL.md 400-500 lines | 0 |
| SKILL.md over 500 lines | -2 |
| Has `references/` directory | +1 |
| Has `scripts/` directory | +1 |
| Description under 200 chars | +1 |
| Description over 500 chars | -1 |

Score 4+: Excellent disclosure. Score 2-3: Good. Score 0-1: Needs improvement.

---

## Token Budget Validation

| Metric | Warning | Error |
|--------|---------|-------|
| Single description length | >500 chars | >1024 chars |
| SKILL.md body tokens (est.) | >4000 | >6000 |
| Estimated: `word_count * 1.3` | | |

---

## String Substitution Validation

If SKILL.md body contains `$ARGUMENTS` or `$0`, `$1`, etc.:
- `argument-hint` SHOULD be set in frontmatter
- Instructions SHOULD handle empty `$ARGUMENTS` case
- `$ARGUMENTS[N]` indexing should be sequential from 0

---

## Validation Process

### Pre-flight
1. File exists and is readable
2. YAML frontmatter parses without error
3. Frontmatter separator (`---`) present at start and end

### Field Validation
1. Required fields present
2. Field types correct
3. Field constraints met
4. No deprecated fields (or warned)

### Body Validation
1. Length within limits
2. Required sections present (Enterprise)
3. No absolute paths
4. Instructions have steps (Enterprise)

### Resource Validation
1. All `{baseDir}/scripts/*` references exist
2. All `{baseDir}/references/*` references exist
3. All `{baseDir}/templates/*` references exist
4. All `{baseDir}/assets/*` references exist
5. No path escape attempts

### Report
- Errors: Must fix (blocks pass)
- Warnings: Should fix (does not block pass)
- Info: Optional improvements
- Score: Progressive disclosure score
- Stats: Word count, line count, token estimate
