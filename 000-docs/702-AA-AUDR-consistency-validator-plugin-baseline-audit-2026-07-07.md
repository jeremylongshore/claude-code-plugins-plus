# Validation baseline audit — 000-jeremy-content-consistency-validator (first-party plugin)

**Date:** 2026-07-07 · **Scope:** full validator pass over
`plugins/productivity/000-jeremy-content-consistency-validator/` — plugin manifest, skill
at marketplace tier, command at standard tier, agents directory. **Purpose:** freeze the
as-is baseline before the #991 multi-agent rebuild, and attach it to the submission
paperwork (`docs/PRD.md`, `docs/ADR.md`, `docs/ONE-PAGER.md`) filed per the tier→docs
matrix in `700-DR-GUID-skill-submission-standard.md` (first-party, flagship track).

---

## 1. Layer-by-layer results

| Layer                    | Artifact                                                   | Result                                                                                               |
| ------------------------ | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Plugin manifest          | `.claude-plugin/plugin.json`                               | Canonical path; complete — `name`, `description`, `version` 2.0.0, `author`, `repository`, `license` |
| Skill (marketplace tier) | `skills/000-jeremy-content-consistency-validator/SKILL.md` | **Grade A, 100/100 — 0 errors, 6 warnings** (verbatim below)                                         |
| Command (standard tier)  | `commands/validate-consistency.md`                         | **PASS** — legacy format; Anthropic guidance says new plugins use `skills/`                          |
| Agents                   | `agents/`                                                  | **Absent** — zero agents exist; `/validate-agent` had nothing to grade                               |

## 2. The 6 marketplace-tier warnings (verbatim)

1. `allowed-tools` declares `Grep` but the body never references it (over-permissive/stale).
2. `allowed-tools` declares `Read` but the body never references it (over-permissive/stale).
3. `allowed-tools` declares `WebSearch` but the body never references it (over-permissive/stale).
4. The `## Report Format` section is a 6-word stub.
5. Missing conditional field `argument-hint`.
6. The body carries time-sensitive dates/versions that can go stale.

## 3. Diagnosis — A/100 on paper, hollow in practice (the shadowing defect)

The grade and the product's actual condition diverge, and the mechanism is known
(epic **#991**): Jeremy invokes `/validate-consistency` constantly, but **skill
precedence resolves to the global `~/.claude` skill** of the same name — the installed
plugin is shadowed in its own author's environment. Unexercised, the plugin copy has
drifted into a **thin shell (682-word SKILL.md)** while the global skill carries the full
engine: project-type auto-detect, a source-of-truth hierarchy, and deterministic drift
checks. The warning cluster above is the symptom set of that drift — a stale tool grant
(warnings 1–3), a stub section (warning 4), and staleness-prone body content (warning 6)
are what a shadowed, unmaintained copy looks like at A/100.

**Disposition:** a rebuild per Fable's recommendation — multi-agent architecture — is
scoped in issue **#991**. The current single-pass architecture is recorded honestly in
`docs/ADR.md` with status "superseded-in-planning"; the rebuild files its own ADR. The
PRD describes the product contract and holds across the rebuild.

## 4. Cross-references

- Epic: `jeremylongshore/claude-code-plugins-plus-skills#991` (rebuild scope)
- Umbrella: `#984` (marketplace quality pipeline)
- Submission standard: `000-docs/700-DR-GUID-skill-submission-standard.md`
- Paperwork filed with this baseline:
  `plugins/productivity/000-jeremy-content-consistency-validator/docs/{PRD,ADR,ONE-PAGER}.md`
