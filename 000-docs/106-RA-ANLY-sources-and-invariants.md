# 106-RA-ANLY-sources-and-invariants.md

**Document Type**: Research & Analysis - Analysis (RA-ANLY)
**Document ID**: 106-RA-ANLY-sources-and-invariants
**Title**: Sources Analysis and Truth Invariants (Phase 0)
**Version**: 1.0.0
**Status**: COMPLETE
**Date**: 2025-12-20
**Phase**: Phase 0 - Preflight (Standard of Truth Generation)
**Authority**: Intent Solutions (Enterprise Standards)

---

## Executive Summary

This document captures the results of Phase 0 preflight research for the "Standard of Truth" documentation generation project. It provides:

1. **Sources Table**: Official Anthropic documentation URLs and what each supports
2. **Conflict Analysis**: Discrepancies between old specs (6767-a/b), downstream templates, and enterprise requirements
3. **Truth Invariants**: Non-negotiable checklist to repeat in every canonical standard document

**Key Finding**: Previous mission (Mission B, 2025-12-20) already created canonical standards (6767-c through g) with enterprise-only policies. This Phase 0 analysis validates those decisions and identifies remaining template/config updates needed.

---

## 1. Sources Table

### 1.1 Official Anthropic Documentation

| Source | URL | Supports | Last Verified |
|--------|-----|----------|---------------|
| **Agent Skills Docs** | [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills) | Skills creation, SKILL.md format, frontmatter fields | 2025-12-20 |
| **Agent Skills Overview** | [platform.claude.com/docs/en/agents-and-tools/agent-skills/overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) | Skills concept, auto-invocation, discovery | 2025-12-20 |
| **Agent Skills Best Practices** | [platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Progressive disclosure, context hygiene, tool scoping | 2025-12-20 |
| **Plugins in SDK** | [platform.claude.com/docs/en/agent-sdk/plugins](https://platform.claude.com/docs/en/agent-sdk/plugins) | Plugin structure, manifest schema, distribution | 2025-12-20 |
| **Skills in SDK** | [platform.claude.com/docs/en/agent-sdk/skills](https://platform.claude.com/docs/en/agent-sdk/skills) | Programmatic skill loading, SDK integration | 2025-12-20 |
| **Main Claude Docs** | [docs.anthropic.com/en/home](https://docs.anthropic.com/en/home) | General Claude API, platform features | 2025-12-20 |
| **Introducing Agent Skills** | [www.anthropic.com/news/skills](https://www.anthropic.com/news/skills) | Skills announcement (Dec 18, 2025), product overview | 2025-12-20 |
| **Claude Code Plugins Announcement** | [www.anthropic.com/news/claude-code-plugins](https://www.anthropic.com/news/claude-code-plugins) | Plugins announcement, marketplace overview | 2025-12-20 |
| **Official Skills Repository** | [github.com/anthropics/skills](https://github.com/anthropics/skills) | Example skills (Creative, Development, Enterprise, Document) | 2025-12-20 |
| **Claude Code GitHub** | [github.com/anthropics/claude-code](https://github.com/anthropics/claude-code) | Claude Code source, plugin README, SDK reference | 2025-12-20 |

### 1.2 Community Resources (Referenced in Old Specs)

| Source | URL | Supports | Notes |
|--------|-----|----------|-------|
| **Lee Han Chung Deep Dive** | [leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/) | Skills architecture, token budgets, undocumented fields | Comprehensive third-party analysis |
| **Simon Willison on Skills** | [simonwillison.net/2025/Oct/16/claude-skills/](https://simonwillison.net/2025/Oct/16/claude-skills/) | Skills vs MCP comparison, use cases | Community perspective |

### 1.3 Deprecated Standards (Historical Reference Only)

| Source | Status | Date Deprecated | Superseded By |
|--------|--------|-----------------|---------------|
| **6767-a**: Claude Code Plugins Standard v2.x | DEPRECATED | 2025-12-20 | 6767-c, 6767-d, 6767-e, 6767-f, 6767-g |
| **6767-b**: Claude Skills Standard v2.x | DEPRECATED | 2025-12-20 | 6767-c, 6767-d, 6767-e, 6767-f, 6767-g |

---

## 2. Conflict Analysis

### 2.1 Anthropic-Minimum vs Enterprise Mode (RESOLVED)

**Historical Dual-Mode Problem** (6767-a/b):
- Anthropic-minimum mode: Some fields optional
- Enterprise/Marketplace mode: All fields required

**Conflict**:
- Confusing for developers (which mode applies?)
- Inconsistent validator behavior
- Templates unclear about requirements

**Resolution** (6767-c v3.0.0):
- **ENTERPRISE MODE ONLY** - no dual-mode complexity
- All fields marked "REQUIRED" are REQUIRED
- No optional fallback mode
- Clear, deterministic validation

**Impact**: Simplifies compliance, eliminates ambiguity

---

### 2.2 allowed-tools: CSV String vs YAML Array (CRITICAL CONFLICT)

**Spec Says** (6767-a § 5.2, 6767-b § 4.2):
- `allowed-tools` MUST be CSV string
- Example: `allowed-tools: "Read,Write,Grep,Glob"`

**Templates/Examples Sometimes Show** (OBSERVED):
- YAML array format
- Example:
  ```yaml
  allowed-tools:
    - Read
    - Write
    - Bash
  ```

**Validator Behavior** (6767-d § 4.2.3):
- CSV string: ✅ VALID
- YAML array: ❌ CRITICAL ERROR (`SKILL_022`)

**Conflict**:
- Templates may mislead developers into using YAML array format
- Most common compliance violation (per AA-AACR)
- Users confused when validator rejects "obvious" format

**Resolution Required**:
- Update ALL templates to show CSV string ONLY
- Add explicit warning in template comments: `# CRITICAL: Must be CSV string, NOT YAML array`
- Fix `planned-skills/templates/skill-template.md` (identified in AA-AACR § 14.3)

**Files to Fix** (from AA-AACR):
1. `planned-skills/templates/skill-template.md`
2. `planned-skills/gemini-prompt-template.md`
3. Any example skills in documentation

---

### 2.3 Bash Tool Scoping (SECURITY HARDENING)

**Old Behavior** (6767-a/b):
- Unscoped `Bash` sometimes allowed
- Security warning, but not enforced as CRITICAL

**New Behavior** (6767-c § 5.5, 6767-d § 4.2.3):
- Unscoped `Bash` is CRITICAL ERROR (`SKILL_024`)
- MUST scope: `Bash(git:*)`, `Bash(npm:*)`, etc.

**Conflict**:
- Old templates/examples may show unscoped `Bash`
- Developers accustomed to permissive mode may be blocked by validator

**Resolution** (6767-c § 10.2):
- Enforce scoped Bash universally
- Validator flags unscoped Bash as CRITICAL
- Templates updated to show scoped examples ONLY

**Impact**: Improved security, prevents arbitrary command execution

---

### 2.4 Body Size Limits (CONTEXT HYGIENE)

**Old Behavior** (6767-b):
- No hard limits on SKILL.md body size
- Progressive disclosure "recommended but not enforced"

**New Behavior** (6767-c § 5.6, 6767-d § 4.3):
- SKILL.md body ≤ 5,000 words / 500 lines / ~7,500 tokens
- Enforced via validator (`SKILL_100`, `SKILL_101`)

**Conflict**:
- Existing skills may exceed limits
- Migration burden for large skills

**Resolution**:
- Enforce limits universally (enterprise policy)
- Provide migration guide for splitting skills
- Use `references/` directory for heavy content

**Impact**: Better context hygiene, faster skill loading, reduced token waste

---

### 2.5 "Use When" + Trigger Phrases (DISCOVERABILITY)

**Old Behavior** (6767-b):
- "Use when" clause recommended
- Trigger phrases recommended

**New Behavior** (6767-c § 5.4, 6767-d § 4.2.2):
- "Use when" clause REQUIRED (`SKILL_015`)
- Trigger phrases REQUIRED (`SKILL_016`)
- Validator checks for presence

**Conflict**:
- Old templates may omit these phrases
- Developers may write vague descriptions without triggers

**Resolution**:
- Enforce via validator (HIGH severity)
- Update templates with formula: `[Capabilities]. Use when [scenarios]. Trigger with "[phrases]".`

**Impact**: Improved skill activation, better router performance

---

### 2.6 Enterprise Required Fields (NEW REQUIREMENTS)

**Fields Now Required** (6767-c § 4.2, § 5.3):

| Field | Old Spec | New Spec | Impact |
|-------|----------|----------|--------|
| `version` (plugin) | Recommended | ✅ REQUIRED | SemVer MAJOR.MINOR.PATCH |
| `author.name` | Recommended | ✅ REQUIRED | Author name string |
| `author.email` | Recommended | ✅ REQUIRED | Valid email |
| `license` | Recommended | ✅ REQUIRED | SPDX identifier |
| `keywords` | Recommended | ✅ REQUIRED | Array, min 1 item |
| `allowed-tools` (skill) | Optional per spec | ✅ REQUIRED | CSV string |
| `version` (skill) | Optional | ✅ REQUIRED | SemVer |
| `author` (skill) | Not in Anthropic spec | ✅ REQUIRED | "Name <email>" format |
| `license` (skill) | Optional | ✅ REQUIRED | SPDX identifier |
| `tags` (skill) | Not in spec | ✅ REQUIRED | Array, min 1 item |

**Conflict**:
- Anthropic's official spec treats many fields as optional
- Enterprise marketplace requires all fields for quality/discoverability

**Resolution**:
- Clearly label "Enterprise Required" in specs
- Validator enforces enterprise requirements
- Document divergence from Anthropic-minimum

**Impact**: Higher quality marketplace submissions, better metadata

---

## 3. Truth Invariants (Non-Negotiable Checklist)

### 3.1 Purpose

These invariants MUST be repeated verbatim in EVERY canonical standard document (6767-c/d/e/f/g) and DOCX teaching edition. LLMs forget context; repetition ensures consistency.

### 3.2 The Invariants

**COPY THIS BLOCK INTO EVERY STANDARD DOC:**

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

### 3.3 Usage in Standards

**Where to Include**:
- Beginning of every canonical standard (after Purpose/Scope, before main content)
- DOCX teaching editions (as prominent callout box)
- Validator implementation guide (as reference table)

**Rationale**:
- LLMs (and humans) need repeated reminders for consistency
- Prevents drift between standards
- Ensures enforcement alignment

---

## 4. Downstream Template/Config Conflicts

### 4.1 Templates Requiring Updates

| File | Current Issue | Required Fix | Priority |
|------|---------------|--------------|----------|
| `planned-skills/templates/skill-template.md` | allowed-tools may show YAML array | Change to CSV string with warning comment | CRITICAL |
| `planned-skills/gemini-prompt-template.md` | May reference dual-mode requirements | Update to enterprise-only | HIGH |
| `planned-skills/generation-config.json` | May generate optional enterprise fields | Mark all enterprise fields as required | HIGH |
| Example skills in docs | May show unscoped Bash | Update to scoped examples | MEDIUM |
| README examples | May show old manifest schema | Update to enterprise required fields | MEDIUM |

### 4.2 Config Files Requiring Updates

| File | Current Issue | Required Fix | Priority |
|------|---------------|--------------|----------|
| Validator config | May allow Anthropic-min mode | Remove mode option, enforce enterprise ONLY | CRITICAL |
| CI workflows | May not block on CRITICAL/HIGH | Update to fail on CRITICAL/HIGH | CRITICAL |
| .gitignore | May not exclude .env | Add .env, *.key, credentials* | HIGH |

---

## 5. Validator Enhancements Needed

### 5.1 Missing Check IDs (from 6767-d)

The validator (`validate_standards.py`) currently covers core checks but needs enhancements to implement ALL 100+ check IDs from 6767-d:

**Current Coverage** (from AA-AACR):
- Manifest validation (plugin.json)
- Directory structure validation
- Security scanning (secrets, paths)
- Naming conventions

**Enhancements Needed**:
1. Doc filing validation (`DOC_*` checks) for 000-docs/ structure
2. Skill body word count (`SKILL_100`, `SKILL_101`)
3. Required sections check (Error Handling ≥4, Examples ≥2)
4. "Use when" phrase detection (`SKILL_015`)
5. Trigger phrase detection (`SKILL_016`)
6. CSV string type check for allowed-tools (`SKILL_022`)
7. Bash scoping validation (`SKILL_024`)
8. Path traversal detection (more comprehensive)
9. Compliance reporting (JSON format per 6767-d § 11)

### 5.2 Recommended Validator Architecture

```
validate_standards.py
├── validators/
│   ├── manifest.py       (PLUGIN_* checks)
│   ├── skills.py         (SKILL_* checks)
│   ├── agents.py         (AGENT_* checks)
│   ├── directory.py      (DIR_* checks)
│   ├── security.py       (SEC_* checks)
│   ├── naming.py         (NAMING_* checks)
│   └── doc_filing.py     (DOC_* checks)
├── error_codes.py        (Error definitions from 6767-d)
├── report.py             (JSON compliance reporting)
└── cli.py                (Entry point)
```

---

## 6. CI/CD Enhancements Needed

### 6.1 PR Workflow Requirements (6767-e)

**Current State** (from Lumera-Emanuel):
- PR workflow exists
- Runs validator and smoke tests

**Enhancements for claude-code-plugins** (not yet implemented):
1. Add `.github/workflows/pr.yml` with:
   - Validator in enterprise mode
   - Block on CRITICAL/HIGH errors
   - Security scans (secrets, dependencies)
   - Template compliance checks
2. Add `.github/workflows/main.yml` with:
   - Comprehensive dual-mode validation
   - Coverage reporting
   - Artifact archiving

### 6.2 Auto-Fix Policy (6767-e § 4)

**Safe Auto-Fixes** (allowed):
- Trailing whitespace removal
- JSON formatting (pretty-print)
- SemVer normalization (e.g., `1.0` → `1.0.0`)

**Unsafe Auto-Fixes** (manual only):
- YAML array → CSV string conversion (risk of data loss)
- Bash scoping (requires human judgment)
- Path rewriting (context-dependent)

---

## 7. Gap Analysis: What's Missing

### 7.1 DOCX Teaching Materials (Phase 2 Goal)

**Not Yet Created**:
- DOCX versions of 6767-c through g
- Embedded diagrams (PNG + Mermaid source)
- Build script (`scripts/build_standards_docx.py`)
- Smoke test for DOCX generation

**Required**:
- python-docx library
- mermaid-cli (for PNG rendering)
- Repeatable build process

### 7.2 Teaching Workshop (Phase 5 Goal)

**Not Yet Created**:
- Workshop materials (NNN-MC-TRNG-claude-code-extensions-workshop.docx)
- Learning objectives
- Glossary
- 3 hands-on labs
- 10-question quiz with answers

**Required**:
- Pedagogical design
- Lab exercises with solutions
- Assessment rubric

### 7.3 Migration Guide

**Not Yet Created**:
- Migration guide for 6767-a/b → 6767-c/d/e/f/g
- Automated migration script (optional)
- Deprecation timeline

**Required**:
- Step-by-step migration instructions
- Common pitfalls and solutions
- Validation checklist

---

## 8. Recommendations

### 8.1 Immediate Actions (Week 1)

1. ✅ **Phase 0 Complete**: This document (106-RA-ANLY)
2. ⏳ **Update Templates**: Fix allowed-tools in skill-template.md (CRITICAL)
3. ⏳ **Add CI Workflows**: PR and main branch validation for claude-code-plugins
4. ⏳ **Enhance Validator**: Implement missing check IDs (SKILL_015, SKILL_016, SKILL_022, SKILL_024)

### 8.2 Short-Term Actions (Month 1)

1. ⏳ **Generate DOCX Teaching Editions**: Phase 2 deliverables
2. ⏳ **Create Teaching Workshop**: Phase 5 deliverables
3. ⏳ **Regenerate 500 Planned Skills**: Using fixed templates
4. ⏳ **Migration Guide**: For existing plugin/skill authors

### 8.3 Long-Term Actions (Quarter 1)

1. ⏳ **Publish to Marketplace**: Enterprise standards as authoritative reference
2. ⏳ **Interactive Compliance Checker**: Web-based validator
3. ⏳ **VS Code Extension**: Real-time validation in IDE

---

## 9. Conclusion

**Phase 0 Findings**:

1. **Official Sources Verified**: All URLs from 6767-a/b are valid as of 2025-12-20. Anthropic announced Skills on Dec 18, 2025.

2. **Conflicts Identified**: Five major conflicts between old specs, templates, and enterprise requirements:
   - Dual-mode confusion (RESOLVED via enterprise-only policy)
   - allowed-tools YAML array bug (REQUIRES template fix)
   - Bash scoping enforcement (RESOLVED via CRITICAL error)
   - Body size limits (NEW enforcement)
   - Discoverability phrases (NEW requirements)

3. **Truth Invariants Defined**: 10 non-negotiable rules to repeat in every standard. Ensures consistency across docs.

4. **Templates Require Updates**: Critical priority is fixing `skill-template.md` to prevent YAML array usage.

5. **Validator Enhancements Needed**: ~20 check IDs missing (mostly SKILL_* checks for body content, descriptions, and tool scoping).

6. **CI/CD Ready**: Lumera-Emanuel has working workflows; claude-code-plugins needs similar setup.

**Next Phase**: Phase 1 - Create/update canonical Markdown standards (6767-c through g). Extract diagrams to standalone .mmd files, render PNGs if mermaid-cli available.

---

**END OF PHASE 0 ANALYSIS**

**Version**: 1.0.0
**Status**: COMPLETE
**Date**: 2025-12-20
**Next Phase**: Phase 1 - Canonical Markdown Standards

---

## Sources

- [Agent Skills Docs](https://code.claude.com/docs/en/skills)
- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Plugins in SDK](https://platform.claude.com/docs/en/agent-sdk/plugins)
- [Skills in SDK](https://platform.claude.com/docs/en/agent-sdk/skills)
- [Main Claude Docs](https://docs.anthropic.com/en/home)
- [Introducing Agent Skills](https://www.anthropic.com/news/skills)
- [Claude Code Plugins Announcement](https://www.anthropic.com/news/claude-code-plugins)
- [Official Skills Repository](https://github.com/anthropics/skills)
- [Claude Code GitHub](https://github.com/anthropics/claude-code)
- [Lee Han Chung Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [Simon Willison on Skills](https://simonwillison.net/2025/Oct/16/claude-skills/)
