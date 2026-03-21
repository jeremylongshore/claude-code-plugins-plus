# Gap Analysis: Our Skill Creator vs Anthropic Standards

Sources: [AgentSkills.io spec](https://agentskills.io/specification) · [Anthropic docs](https://code.claude.com/docs/en/skills) · [anthropics/skills repo](https://github.com/anthropics/skills)

Comparison of our skill-creator implementation against:
- AgentSkills.io specification (canonical open standard)
- Anthropic best practices (platform.claude.com)
- anthropics/skills official skill-creator
- Claude Code runtime extensions

---

## What We Over-Specify (Relaxed or Removed)

| Issue | Our Requirement | Anthropic Standard | Resolution |
|-------|----------------|-------------------|------------|
| `version` as required frontmatter | Top-level required field | Not in spec; use `metadata.version` | Kept as top-level field (marketplace validator scores at top-level); AgentSkills.io spec also allows under metadata |
| `author` as required frontmatter | Top-level required field | Not in spec; use `metadata.author` | Kept as top-level field (marketplace validator scores at top-level); AgentSkills.io spec also allows under metadata |
| `license` as required | Required in Enterprise tier | Optional in AgentSkills.io spec | Optional (Enterprise recommends) |
| `tags` field | Listed as optional | Not in official spec at all | Kept as top-level field (used by marketplace and discovery) |
| Mandatory "Use when" phrase | Error if missing | Natural language, no exact phrase | Recommend but don't enforce exact wording |
| Mandatory "Trigger with" phrase | Error if missing | Not an Anthropic requirement | Removed as requirement |
| 8 mandatory body sections | Error if any missing | "No format restrictions" | Recommended sections, not mandatory |
| Unscoped Bash as error | Hard error | Experimental feature (allowed-tools) | Warning in Standard tier, error in Enterprise |
| Hardcoded model ID | `claude-opus-4-5-20251101` | Use `inherit` or omit | Default to `inherit` |

---

## What We're Missing (Added)

| Feature | Source | Priority | Status |
|---------|--------|----------|--------|
| `compatibility` field | AgentSkills.io spec | Medium | Added to frontmatter spec |
| `argument-hint` field | Claude Code extension | Medium | Added to frontmatter spec |
| `user-invocable` field | Claude Code extension | Medium | Added to frontmatter spec |
| `context: fork` field | Claude Code extension | High | Added to frontmatter spec |
| `agent` field (subagent type) | Claude Code extension | High | Added to frontmatter spec |
| `hooks` field (skill-scoped) | Claude Code extension | Medium | Added to frontmatter spec |
| String substitutions | Claude Code runtime | High | Added to source-of-truth |
| Dynamic context injection (`` !`cmd` ``) | Claude Code runtime | Medium | Added to source-of-truth |
| Degrees of freedom concept | Anthropic engineering blog | High | Added to SKILL.md instructions |
| Evaluation-driven development | Anthropic best practices | High | Added to SKILL.md instructions |
| Claude A/B iterative methodology | Anthropic best practices | Medium | Referenced in evaluation section |
| Gerund naming recommendation | Anthropic best practices | Low | Added to naming guidance |
| MCP tool references | Claude Code runtime | Medium | Added to allowed-tools docs |
| Plan-validate-execute pattern | Anthropic best practices | Medium | Added to workflows.md |
| Visual output generation pattern | Anthropic best practices | Low | Added to output-patterns.md |
| Token budget awareness | Claude Code runtime | High | Added to source-of-truth |
| `SLASH_COMMAND_TOOL_CHAR_BUDGET` | Claude Code internals | Low | Documented in token budget |
| Anthropic official validation checklist | platform.claude.com | High | Integrated into validation |
| `metadata` as home for author/version | AgentSkills.io spec | High | Primary recommendation |

---

## What We Do Well (Kept)

| Strength | Value | Kept In |
|----------|-------|---------|
| Interactive wizard | Great UX for skill creation | SKILL.md Step 1 (streamlined) |
| Validation script | Automated quality assurance | validate-skill.py (rewritten) |
| Error handling table format | Clear, scannable error docs | Templates and examples |
| Quality grading system | Enterprise accountability | Enterprise tier (default) |
| Template with placeholders | Fast skill scaffolding | skill-template.md (updated) |
| Multiple validation tiers | Flexible strictness | Standard + Enterprise tiers |
| Resource existence checking | Catches broken references | validate-skill.py |
| `{baseDir}` path convention | Portable, no absolute paths | All templates and docs |
| Scoped Bash enforcement | Security best practice | Enterprise tier default |

---

## Migration Summary

### For Existing Skills

Existing skills that pass our old validator will mostly pass the new one because:
- Enterprise tier (default) still checks `metadata.author`, `metadata.version`, scoped tools
- The body section checks are warnings, not errors
- "Use when" / "Trigger with" are now recommended patterns, not hard requirements

### Breaking Changes

1. `version`, `author`, and `tags` are top-level fields (marketplace validator scores them here; AgentSkills.io spec also allows under `metadata`)
2. Hardcoded model IDs trigger a warning (use `inherit` or short names)

### New Capabilities

Skills can now use:
- `$ARGUMENTS` for dynamic input
- `context: fork` for subagent execution
- `hooks` for lifecycle automation
- `compatibility` for environment requirements
- `argument-hint` for better autocomplete UX
- `effort` for model reasoning override (v2.1.80)
