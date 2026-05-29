---
name: validate-skillmd
description: |
  Validate a SKILL.md file against the four-tier validation system: Tier 0 (locate),
  Tier 1 (standard or marketplace grading per the IS 100-point rubric), Tier 2
  (static production gate — allowed-tools accuracy, auth protocol, dead code, tool
  safety, orchestration bounds), and Tier 3 (JRig 7-layer behavioral eval, opt-in
  via --thorough). Use when creating a new skill, checking skill quality, preparing
  for marketplace submission, running deep quality analysis, or gating a skill for
  production. Trigger with "validate this skill", "grade my skill", "deep eval",
  "check SKILL.md", "validate thorough", "/validate-skillmd".
allowed-tools: 'Read,Edit,Write,Bash(python3:*),Bash(j-rig:*),Bash(node:*),Glob,Grep,AskUserQuestion'
version: 5.0.1
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Designed for Claude Code; requires Python 3, optionally JRig CLI for Tier 3
tags: [validation, skill-quality, marketplace, grading, deep-eval, jrig, behavioral-eval]
user-invocable: true
argument-hint: '[path-to-SKILL.md] [--marketplace|--deep|--thorough]'
---

# Validate SKILL.md

Grade any SKILL.md file against the Intent Solutions rubric (validator v7.0 / schema 3.3.1). Four-tier validation: **Tier 0** (locate), **Tier 1** (standard or marketplace grading), **Tier 2** (static production gate), **Tier 3** (JRig behavioral eval — opt-in).

Source of truth: `/skill-creator` validation workflow + `~/000-projects/claude-code-plugins/000-docs/SCHEMA_CHANGELOG.md` + `~/000-projects/j-rig-binary-eval/` (Tier 3).

## Overview

Schema 3.3.1 enforces the 8-field IS enterprise required-field set at marketplace tier (`name`, `description`, `allowed-tools`, `version`, `author`, `license`, `compatibility`, `tags`). Anthropic's spec floor (`name` + `description` only) sits underneath; the IS rubric sits on top. **Modes**:

- **Standard** (default): Mirrors `platform.claude.com/docs/en/agents-and-tools/agent-skills/overview` exactly. Required: `name`, `description`. Everything else is silent unless invalid type/value. Fast (~10 sec).
- **Marketplace** (`--marketplace`): 8-field enterprise required set + 100-point IS rubric. **Missing required fields = ERROR, not warning.** The `--enterprise` flag is a deprecated alias. Fast (~10 sec).
- **Deep** (`--deep`): Intent Solutions Deep Evaluation Engine — 10 weighted dimensions, trust badges, Elo competitive ranking, optional LLM quality assessment via Groq. Fast (~30 sec).
- **Thorough** (`--thorough`): Adds **Tier 3 JRig behavioral eval** on top of Tier 1+2. Runs 7-layer eval across Haiku/Sonnet/Opus. **Slow** (~10–30 min) and **costs ~$2–5 per skill in API spend** — opt-in only. Right for production-gating, not iterative authoring.

> **Performance + cost note**: Tiers 0–2 run in seconds and are free. Tier 3 (JRig) is opt-in because behavioral eval across the model matrix is genuinely expensive. Default invocations stay fast; `--thorough` is for the moment a skill is being promoted to production or marketplace-verified.

## Prerequisites

- Python 3 with `pyyaml` installed
- Validator script: `~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py` (v7.0+)
- For `--thorough` (Tier 3): JRig CLI on PATH (`jrig --version` returns ≥ v0.14.0). Install: `cd ~/000-projects/j-rig-binary-eval && pnpm install && pnpm build && pnpm link --global`. Tier 3 is opt-in; the rest of the skill works without JRig installed.

## Schema Reminder — Frontmatter Fields

Every SKILL.md must have:

```yaml
name: my-skill # Required (Anthropic)
description: | # Required (Anthropic)
  What it does. Use when ...
```

Optional fields the validator accepts (validates only when present):

```yaml
# Per Anthropic + AgentSkills.io spec
allowed-tools: 'Read,Write,Bash(git:*)'
license: MIT
compatibility: 'Designed for Claude Code' # Free-text, max 500 chars per agentskills.io/specification
metadata: { category: devops } # Arbitrary key-value mapping

# Per code.claude.com/docs/en/skills
model: inherit
effort: medium
argument-hint: '[file-path]'
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

### `compatibility` Field Examples (per `agentskills.io/specification`)

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
python3 ~/000-projects/claude-code-plugins/scripts/batch-remediate.py --migrate-compatible-with --root <path>
```

## Instructions

### Step 1: Locate the Skill

If path provided via `$ARGUMENTS`, use it directly. Otherwise:

- Check current directory for SKILL.md
- Ask user with AskUserQuestion

Common locations:

- `~/.claude/skills/{name}/SKILL.md` (global)
- `.claude/skills/{name}/SKILL.md` (project)

### Step 2: Run Validator

```bash
# Standard tier (default — Anthropic spec exactly)
python3 ~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py <path>

# Marketplace tier (full 100-point rubric, polish recommendations as warnings)
python3 ~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py --marketplace <path>

# Deep evaluation (10 dimensions, badges, Elo ranking)
python3 ~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py --deep <path>

# Deep + LLM quality assessment via Groq (requires GROQ_API_KEY)
python3 ~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py --deep --thorough <path>

# Deep eval with JSON/markdown/HTML report output
python3 ~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py --deep --report-format json <path>
python3 ~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py --deep --report-format html <path>

# Marketplace + write to compliance DB
python3 ~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py --marketplace --populate-db ~/000-projects/claude-code-plugins/freshie/inventory.sqlite <path>

# Show D/F grade skills in full scan
python3 ~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py --marketplace --show-low-grades

# Minimum grade gate (exits 1 if any skill below threshold)
python3 ~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py --marketplace --min-grade B <path>
```

Default to marketplace tier when the user is preparing for marketplace submission. Use `--deep` for functional quality assessment beyond structural compliance. The `--enterprise` flag still works as a deprecated alias for `--marketplace`.

**v6.0 Deep Evaluation Engine:** 10 weighted dimensions (triggering accuracy 0.25, orchestration fitness 0.20, output quality 0.15, scope calibration 0.12, progressive disclosure 0.10, token efficiency 0.06, robustness 0.05, structural completeness 0.03, code template quality 0.02, ecosystem coherence 0.02). Anti-pattern detection with 5% penalty each. Elo competitive ranking. Trust badges (Flagship/Established/Emerging/Early). Optional LLM-as-judge via Groq free tier.

### Step 2.5: Tier 2 — Static Production Gate

After Tier 1 grading and before any behavioral eval, run five inline static checks. These catch obvious production blockers in seconds without needing JRig. **Always run** regardless of mode (standard/marketplace/deep/thorough); each is binary pass/fail.

#### 2.5.1 `allowed-tools` accuracy

Every tool declared in `allowed-tools` should actually be referenced somewhere in the skill body or its `references/`/`scripts/`. Conversely, every tool the skill calls should be declared.

```bash
# Extract declared tools (handles CSV string, space-separated, and YAML list forms — schema 3.3.1)
declared=$(python3 -c "import yaml,sys; fm=yaml.safe_load(open('${1}').read().split('---')[1]); t=fm.get('allowed-tools',''); print(t if isinstance(t,str) else ' '.join(t))")

# Each declared base tool (Read, Write, Bash, etc.) must appear in the body
for tool in $(echo "$declared" | grep -oE '[A-Z][a-zA-Z]+' | sort -u); do
  if ! grep -q "$tool" "${1}"; then
    echo "FAIL: tool '$tool' declared but not referenced in body"
  fi
done
```

**Fail when**: tool declared but never used (over-permissive — attack surface) OR tool used but never declared (will prompt user every invocation, defeating allowed-tools).

#### 2.5.2 Auth protocol documented (when applicable)

If the skill mentions an external API (any URL, `curl`, `fetch`, MCP server, OAuth flow, API key reference), an authentication method must be documented in the body or in `references/auth.md` / `references/api-surface.md`.

```bash
# Heuristic: look for API indicators
if grep -qE "(curl |fetch\(|mcp__|API_KEY|TOKEN|OAuth|Bearer )" "${1}"; then
  if ! grep -qiE "(authentication|auth method|api key|bearer token|oauth flow|credentials)" "${1}"; then
    echo "FAIL: external API referenced but no auth protocol documented"
  fi
fi
```

**Fail when**: API surface is referenced but a future engineer reading the skill couldn't tell how authentication happens.

#### 2.5.3 Dead-code / unreachable-branch sanity

Conditional structures that can never fire (e.g., `if false`, mutually exclusive guards, sections that contradict an earlier hard-fail).

```bash
# Conservative checks — flag for human review, don't auto-fail
grep -nE "^(if false|if \[ false \]|elif false)" "${1}" && echo "WARN: literal-false branch found"
grep -cE "^### " "${1}" # If section count grossly exceeds the table-of-contents count → drift
```

**Warn when**: a literal-false branch is found OR the body contains sections not present in the table of contents (silent drift).

#### 2.5.4 Tool-safety combo flagging

Dangerous combinations require explicit justification:

| Combo                                            | Why dangerous                                       |
| ------------------------------------------------ | --------------------------------------------------- |
| `Bash` (unscoped) + `WebFetch`                   | Can fetch arbitrary content + execute it            |
| `Bash` (unscoped) + `Write`                      | Can write executable scripts to arbitrary locations |
| `Bash(curl:*)` + `Bash(sh:*)`                    | Curl-pipe-shell pattern                             |
| `Bash(rm:*)` not paired with explicit safe-paths | Unbounded delete authority                          |

```bash
# Check for unscoped Bash + dangerous companion
if grep -qE "^allowed-tools:.*\bBash\b" "${1}" && \
   ! grep -qE "^allowed-tools:.*Bash\(" "${1}" && \
   grep -qE "^allowed-tools:.*\b(Write|WebFetch)\b" "${1}"; then
  if ! grep -qiE "(safety justification|why unscoped Bash|why Bash + )" "${1}"; then
    echo "FAIL: unscoped Bash + Write/WebFetch without safety justification"
  fi
fi
```

**Fail when**: a dangerous combo is declared and the body has no `## Safety Justification` section explaining why the wide scope is necessary.

#### 2.5.5 Orchestration bounds

Skills are NOT plugins. A skill should not spawn other skills, delegate to other agents as a primary control flow, or self-coordinate across sessions. That's `/skill-creator --forge` territory and plugin-level orchestration. Skills do one job.

```bash
# Look for orchestration smells in skills
if grep -qE "(spawn another skill|delegate to /|invoke .* skill|orchestrate across|self-coordinate)" "${1}"; then
  echo "FAIL: skill appears to orchestrate other skills/agents — that belongs at the plugin layer"
fi
```

**Fail when**: the skill body claims it spawns/orchestrates other skills or agents as the primary control flow. Multi-agent synthesis WITHIN one skill invocation (calling subagents to specialize) is fine and expected; cross-skill orchestration is not.

#### Tier 2 verdict

- **All 5 checks pass** → Tier 2 GREEN; proceed.
- **Any FAIL** → Tier 2 RED; the skill is blocked from production promotion until resolved. Tier 3 (JRig) does not run if Tier 2 is RED — fail fast.
- **Only WARN** → Tier 2 YELLOW; log warnings to the unified report; Tier 3 still runs.

### Step 2.7: Tier 3 — JRig 7-Layer Behavioral Eval (opt-in via `--thorough`)

> **Default skipped.** Tier 3 runs only when the user passes `--thorough`. Behavioral eval across the model matrix (Haiku / Sonnet / Opus) takes 10–30 minutes per skill and costs ~$2–$5 in API spend. Right for production-gate moments, not iterative authoring.

#### Prerequisites

- JRig CLI on PATH: `j-rig --version` (note: bin name is `j-rig` with hyphen, not `jrig`)
- Install: `cd ~/000-projects/j-rig-binary-eval/packages/cli && pnpm build && ln -sf $PWD/dist/index.js ~/.local/bin/j-rig`
- For Tier 3B (7-layer eval): API keys for Haiku, Sonnet, Opus configured per JRig docs

If JRig isn't on PATH, the skill emits a placeholder verdict and a one-line install hint, then continues to Step 3 (grade report) without blocking. **Tier 3 absence does not mean a skill fails** — only Tier 1+2 are mandatory.

#### Tier 3A: JRig package-integrity check (deterministic, fast, free)

Run JRig's `check` command on the **skill directory** (not the SKILL.md path). Returns deterministic pass/warn/error verdicts on package structure: SKILL.md exists + parses, name present, description length, deprecated patterns, time-sensitive content, etc.

```bash
# JSON output for parsing into the unified report
j-rig check "$(dirname "${1}")" --json
```

This is a separate concern from the IS spec-compliance check (Tier 1) — JRig's `check` is structural, not rubric-based. The Anthropic + AgentSkills.io spec snapshots in `000-docs/` are read by the IS validator (`scripts/validate-skills-schema.py`), not by JRig directly. The two are complementary: IS validator scores against the spec rubric; JRig verifies the package shape and surfaces structural anti-patterns.

**Verdict mapping**:

- All `severity: "pass"` → Tier 3A GREEN
- Any `severity: "warning"` → Tier 3A YELLOW (non-blocking; surfaced in unified report)
- Any `severity: "error"` → Tier 3A RED (blocks production promotion)

#### Tier 3B: 7-Layer Behavioral Eval (execution-based, slow, $)

```bash
# Default invocation — Sonnet only, no DB persistence
j-rig eval "$(dirname "${1}")" --json

# Full model matrix with DB persistence
j-rig eval "$(dirname "${1}")" \
  --models haiku,sonnet,opus \
  --db ~/000-projects/claude-code-plugins/freshie/inventory.sqlite \
  --json

# Skip specific layers (when iterating)
j-rig eval "$(dirname "${1}")" --no-trigger --no-functional --json
```

Eval spec source: JRig reads `<skill-dir>/eval-spec.yaml` if present, or use `--spec <path>` to point at one elsewhere. When no spec exists, JRig generates a default spec from the SKILL.md frontmatter (trigger phrases extracted from `description`).

Layers:

1. **Trigger quality**: precision/recall on user prompts that should and should not activate the skill
2. **Functional quality**: task completion + output format match against gold cases
3. **Regression protection**: sacred-case suite cannot break (skill is locked-down on these)
4. **Baseline value**: skill output beats naked Claude on the same prompt; if not, flag for obsolescence
5. **Model variance**: independent pass/fail per Haiku / Sonnet / Opus; flags any model where the skill collapses
6. **Rollout safety**: prompt-leakage detection, unsafe-pattern surfacing, jailbreak resistance
7. **Cost / latency**: per-invocation token + wall-clock — must beat declared budget

#### Tier 3 verdict

- **All 7 layers pass on all 3 models** → Tier 3 GREEN; skill is JRig-Verified.
- **Any layer fails on any model** → Tier 3 RED; report which layer + which model + recommended remediation. Block production promotion.
- **JRig unavailable** → Tier 3 SKIPPED; emit a one-line note in the unified report; do not block.

#### Persist results to Freshie

JRig writes its own SQLite DB by default (`j-rig.db` in cwd, or `--db <path>`). To unify with Freshie, point `--db` at `freshie/inventory.sqlite`:

```bash
j-rig eval "$(dirname "${1}")" \
  --models haiku,sonnet,opus \
  --db ~/000-projects/claude-code-plugins/freshie/inventory.sqlite
```

JRig manages its own tables in that DB; cross-table joins to `skill_compliance` happen in the Freshie rebuild script. The unified-report rendering reads both:

```sql
-- Inferred join (actual table names per j-rig schema)
SELECT s.skill_path, s.score, s.grade, j.passed, j.layers_passed, j.baseline_delta
FROM skill_compliance s
LEFT JOIN jrig_eval_results j ON j.skill_path = s.skill_path;
```

Forward-looking: once JRig adds explicit `--append-skill-compliance` mode, the `skill_compliance` table can carry these columns directly:

- `jrig_passed` (boolean)
- `jrig_tier_blocked` (1–7 if any)
- `jrig_baseline_delta` (numeric — skill output vs. naked Claude on same prompt)

Until then, the join above is the integration surface.

#### Snapshot refresh workflow (quarterly)

Tier 3A reads versioned snapshots, NOT live Anthropic / AgentSkills.io docs. Live-fetching from CI is a rate-limit + flakiness risk. The snapshot refresh is a separate PR cadence:

1. Quarterly cron (or manual trigger) fetches latest specs from `code.claude.com/docs/en/skills` and `agentskills.io/specification`.
2. Writes to `000-docs/anthropic-skills-spec-snapshot.md` + `000-docs/agentskills-spec-snapshot.md`.
3. Opens a PR with the diff.
4. PR review = the human gate that catches breaking spec changes before they reach validation.

This isolates "the spec changed" events from per-skill validation runs.

### Step 3: Present Unified Report (all tiers)

Parse the combined output of Tiers 1–3 (or 1+2 when Tier 3 is skipped) and present:

**Production verdict**: PASS / FAIL / VERIFIED (when Tier 3 ran and all 7 layers green)

```
┌─ TIER 1: Marketplace grade ─────────────────────────────┐
│ Grade: [LETTER] ([SCORE]/100)                           │
│                                                          │
│ Pillar              | Score | Notes                      │
│ Progressive Disc.   | X/30  | Token economy, structure   │
│ Ease of Use         | X/25  | Metadata, discoverability  │
│ Utility             | X/20  | Problem solving, examples  │
│ Spec Compliance     | X/15  | Frontmatter, naming        │
│ Writing Style       | X/10  | Voice, objectivity         │
│ Modifiers           | +/-X  | Bonuses/penalties          │
└──────────────────────────────────────────────────────────┘

┌─ TIER 2: Static production gate ────────────────────────┐
│ allowed-tools accuracy:    PASS / FAIL                   │
│ Auth protocol documented:  PASS / FAIL / N/A             │
│ Dead code / drift:         PASS / WARN                   │
│ Tool-safety combo:         PASS / FAIL                   │
│ Orchestration bounds:      PASS / FAIL                   │
│ Verdict:                   GREEN / YELLOW / RED          │
└──────────────────────────────────────────────────────────┘

┌─ TIER 3: JRig behavioral eval (only if --thorough) ─────┐
│ 3A spec compliance:        PASS / FAIL                   │
│ 3B Layer 1 trigger:        Haiku|Sonnet|Opus → P/F      │
│    Layer 2 functional:     Haiku|Sonnet|Opus → P/F      │
│    Layer 3 regression:     Haiku|Sonnet|Opus → P/F      │
│    Layer 4 baseline:       Haiku|Sonnet|Opus → P/F      │
│    Layer 5 model variance: Haiku|Sonnet|Opus → P/F      │
│    Layer 6 rollout safety: Haiku|Sonnet|Opus → P/F      │
│    Layer 7 cost/latency:   Haiku|Sonnet|Opus → P/F      │
│ Baseline delta:            +N% vs. naked Claude          │
│ Verdict:                   VERIFIED / BLOCKED / SKIPPED  │
└──────────────────────────────────────────────────────────┘
```

**Final verdict logic**:

| Tier 1 | Tier 2 | Tier 3   | Final                                                                |
| ------ | ------ | -------- | -------------------------------------------------------------------- |
| ≥B     | GREEN  | VERIFIED | **PRODUCTION READY (JRig-Verified)**                                 |
| ≥B     | GREEN  | SKIPPED  | **PRODUCTION READY (unverified)**                                    |
| ≥B     | YELLOW | \*       | **PRODUCTION READY with warnings**                                   |
| any    | RED    | \*       | **BLOCKED** — fix Tier 2 fails before promoting                      |
| <B     | \*     | \*       | **BLOCKED** — bring grade to B+ before promoting                     |
| ≥B     | GREEN  | BLOCKED  | **BLOCKED** — JRig found behavioral regression; fix before promoting |

Grade scale: A (90+), B (80-89), C (70-79), D (60-69), F (<60)

### Step 4: Prioritized Fix Recommendations

List fixes sorted by point value (highest first):

**Top improvements:**

1. {fix description} (+N pts)
2. {fix description} (+N pts)
3. {fix description} (+N pts)

Common high-value fixes:

- Add "Use when" to description (+3 pts marketplace tier)
- Add "Trigger with" to description (+3 pts marketplace tier)
- Extract long content to references/ (up to +10 pts on token_economy)
- Add missing sections: Overview (+4), Prerequisites (+2), Output (+2), Error Handling (+2)
- Migrate `compatible-with` → `compatibility` (deprecation warning fix; run `batch-remediate.py --migrate-compatible-with`)
- Add `compatibility:` field with one of the AgentSkills.io examples (+1 pt on metadata quality)
- Add external resource links (+1 pt modifier)
- Add DCI directives for discovery (file existence, git status, tool versions) (+1 pt modifier)
- Add TOC to reference files >100 lines (+1 pt modifier)
- Add feedback loops for quality-critical workflows (+2 pts utility)
- Remove time-sensitive information (+1 pt modifier)
- Ensure consistent terminology throughout (+1 pt writing style)

### Step 5: Review Structural Advisors

The validator emits INFO-level structural suggestions (marketplace tier):

- **Split to commands**: 3+ kebab-case `## operation-name` sections detected without `commands/` directory → suggest splitting into individual `commands/*.md` files
- **Offload to references**: Body sections >20 lines (Output, Error Handling, Examples, etc.) without `references/` directory → suggest moving to `references/` with relative markdown links
- **DCI opportunities**: Skill performs file existence checks, git operations, or tool version detection without DCI → suggest `!`command`` directives

### Step 6: Auto-Fix (if requested or grade below B)

If grade < B (80), ask user: "Fix issues automatically?"

If approved, apply in order:

1. Add missing sections (Overview, Prerequisites, Output, Error Handling, Examples)
2. Add "Use when" / "Trigger with" to description if missing
3. Move `author`/`version`/`license` from nested `metadata` to top-level (or vice versa per AgentSkills.io spec — both valid)
4. Migrate `compatible-with` → `compatibility` via `batch-remediate.py --migrate-compatible-with`
5. Fix text references to use relative markdown links: `[file](references/file.md)`; keep `${CLAUDE_SKILL_DIR}/` for DCI/bash only
6. Split long SKILL.md (>500 lines) into references/ with relative links
7. Scope unscoped Bash tools: `Bash` → `Bash(command:*)`
8. Add DCI directives for common discovery patterns (file checks, git status)
9. If 3+ operation sections found, offer to split into commands/\*.md files
10. Add TOC to reference files >100 lines
11. Flag time-sensitive content for review (dates, version numbers, URLs that may go stale)

After fixes, re-run validator and show before/after comparison.

## Output

Final report includes:

- Production verdict (PASS / FAIL / VERIFIED)
- Tier 1 letter grade with numeric score + pillar breakdown table
- Tier 2 static-gate pass/fail per check (5 checks)
- Tier 3 JRig results per layer × per model (when `--thorough`); SKIPPED otherwise
- Warning/error list from validator
- Prioritized fix recommendations with point values
- Before/after comparison if auto-fix was applied
- Source citation for each spec-grounded claim
- One-line install hint for JRig if Tier 3 was requested but JRig is missing

## Error Handling

| Error                                 | Recovery                                           |
| ------------------------------------- | -------------------------------------------------- |
| File not found                        | Suggest `Glob` to find SKILL.md files nearby       |
| Python not available                  | Read SKILL.md manually, check frontmatter by hand  |
| Validator script missing              | Fall back to manual checks against rubric pillars  |
| YAML parse error                      | Report the parse error line, suggest fix           |
| `compatible-with` deprecation warning | Run `batch-remediate.py --migrate-compatible-with` |

## Examples

**Validate a specific skill:**

```
/validate-skillmd ~/.claude/skills/repo-sweep/SKILL.md
```

**Marketplace grading (recommended for marketplace submissions):**

```
/validate-skillmd --marketplace path/to/SKILL.md
```

**Natural language:**

```
grade my skill
check skill quality
```

## Resources

- [Anthropic Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Anthropic Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [AgentSkills.io Specification](https://agentskills.io/specification)
- Schema log: `~/000-projects/claude-code-plugins/000-docs/SCHEMA_CHANGELOG.md`
- Master spec: `~/000-projects/claude-code-plugins/000-docs/6767-b-SPEC-DR-STND-claude-skills-standard.md`
- Source of truth: `/skill-creator` (Steps V1-V5 in validation workflow)
