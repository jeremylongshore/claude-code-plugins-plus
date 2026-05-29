---
name: appaudit
description: "Operator-grade system analysis for any engineer \u2014 clear enough\
  \ for day-one\nonboarding, deep enough for principal-level architecture review.\
  \ Use when\nauditing a new codebase, creating operations playbooks, or documenting\n\
  architectural tradeoffs. Trigger with \"/appaudit\", \"audit this system\".\n"
allowed-tools: Read,Bash(ls:*,mkdir:*,git:*,wc:*),Glob,Grep,Write
model: opus
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
tags:
  - devops
  - audit
  - operations
  - onboarding
  - architecture
  - tradeoffs
compatibility: Designed for Claude Code
---

# Universal Operator-Grade System Analysis v2

Produces a verifiable operational guide (10K-20K words) that equips any engineer to understand, operate, and reason about a system.

## Overview

Covers architecture, operations, security, cost, tradeoffs, failure modes, and recommendations. Output follows the `000-docs/` filing convention. Every claim must be verifiable from the codebase.

Every section targets two readers simultaneously: a first-week engineer who needs clarity, and a principal engineer who needs depth.

## Prerequisites

- Git repository with source code
- `000-docs/` directory (created automatically if missing)

## Output Template

!`cat ${CLAUDE_SKILL_DIR}/references/output-template.md`

## Writing Guidelines

!`cat ${CLAUDE_SKILL_DIR}/references/writing-guidelines.md`

## Instructions

Execute each phase in order.

### Phase 1: Initial Survey

1. Read README.md, CHANGELOG.md, project root files
2. Check for CLAUDE.md, AGENTS.md, operational docs
3. Identify package manifests (package.json, requirements.txt, go.mod, Cargo.toml)
4. Scan infrastructure directories (terraform/, infrastructure/, k8s/, docker/)
5. Find CI/CD configs (.github/workflows/, .gitlab-ci.yml, Jenkinsfile)
6. Review configuration files (.env.example, docker-compose.yml, config/)
7. Read git log for architectural decision commits ("refactor", "migrate", "replace")
8. Identify scaffolded vs implemented (TODO comments, empty modules)

### Phase 2: Deep Dive

1. Analyze source code structure and architectural patterns
2. Review test coverage and quality metrics
3. Examine deployment workflows and environments
4. Study monitoring, logging, and alerting setup
5. Assess security controls and compliance posture
6. Document dependencies and third-party integrations
7. Identify architectural boundaries — where the seams are and why
8. Find load-bearing code — what breaks everything if it fails
9. Trace the critical data path end-to-end
10. Catalog what was explicitly NOT built and why

### Phase 3: Tradeoff Analysis

For each major architectural decision, answer:

1. **What was chosen?** — The actual approach
2. **What was the alternative?** — What else was considered
3. **Why this over that?** — The deciding factor
4. **What did we give up?** — The explicit cost
5. **When does this break?** — The scaling limit or assumption that could change

Common areas: database, architecture style, state management, sync vs async, build vs buy, testing strategy, deployment model.

### Phase 4: Synthesis

1. Identify gaps, risks, and immediate priorities
2. Create actionable recommendations with timelines
3. Generate the document per the Output Template above

### Document Numbering

```bash
LAST_NUM=$(ls -1 000-docs/ 2>/dev/null | grep -E "^[0-9]{3}-" | tail -1 | cut -d'-' -f1)
NEXT_NUM=$(printf "%03d" $((10#${LAST_NUM:-0} + 1)))
```

Output path: `000-docs/${NEXT_NUM}-AA-AUDT-appaudit-devops-playbook.md`

## Output

The Output Template (injected above) has 13 sections plus appendices. Key sections:

- **Section 1**: "This System in 5 Minutes" — write last, put first
- **Section 4**: "Design Decisions & Tradeoffs" — the senior-depth section
- **Section 6**: "Getting Started" — the junior-accessible section
- **Section 8**: "Things That Will Bite You" — real sharp edges

Follow the Writing Guidelines (injected above) for tone, quality gates, and anti-patterns.

After writing, display a summary:

```
Document: 000-docs/NNN-AA-AUDT-appaudit-devops-playbook.md
Health Score: XX/100

Tradeoffs Documented: N
Findings: N high, N medium, N low
```

## Examples

**Example 1**: `/appaudit` on a TypeScript monorepo

```
Document: 000-docs/042-AA-AUDT-appaudit-devops-playbook.md
Health Score: 72/100

Tradeoffs Documented:
1. SQLite over PostgreSQL — simplicity, revisit at multi-tenant
2. Deterministic rules over LLM judgment — auditability
3. Git as mirror not database — separation of concerns

Findings:
1. [HIGH] 2 packages scaffolded only
2. [MEDIUM] No production deployment workflow
3. [LOW] No monitoring infrastructure
```

**Example 2**: `/appaudit` — creates the full operator guide in `000-docs/`

## Error Handling

- `000-docs/` missing: create with `mkdir -p 000-docs`
- No package manifests: note as gap, check for Makefile/scripts
- No infrastructure directory: document as "IaC: Not implemented"
- Git repo not initialized: warn and proceed with file-only analysis

## Resources

- [Anthropic Claude Code Skills Spec](https://docs.anthropic.com/en/docs/claude-code/skills)
- Output template and writing guidelines are injected above via preprocessing
