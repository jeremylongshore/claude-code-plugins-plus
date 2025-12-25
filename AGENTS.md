# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

---

## 🚨 MANDATORY: Session Continuation Protocol

**CRITICAL**: When this session continues after context compaction/summarization:

**YOU MUST IMMEDIATELY RUN**:
```bash
bd ready
```

**WHY**: After context loss, beads is your ONLY source of truth for:
- What tasks are in progress
- What was being worked on before context compaction
- What's blocked/ready to work on
- Project status and next steps

**THIS IS NON-NEGOTIABLE**: Do NOT proceed with ANY work until you've run `bd ready`.

**Failure to read beads after context compaction = working blind = wasted effort**

---

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

---

You are Codex running in a ZERO-CONTEXT terminal session.
Repo: jeremylongshore/claude-code-plugins-plus-skills
Mission (Phase 0): Make the repo clean, explainable, and ready for Phase 1+ work. Do NOT redesign UI, do NOT change branding/colors. This phase is “make it sane,” not “make it pretty.”

HARD RULES
- Do not touch marketplace/src/pages or any UI/CSS in Phase 0. Phase 0 is docs + repo hygiene only.
- Work in a NEW feature branch for Phase 0. Main must remain clean.
- Our doc system: 000-docs is FLAT (no subdirectories). If you find nested docs, flatten them (move + rename).
- Track all Phase 0 work in Beads as a parent epic with child tasks (and dependencies).
- Before you say “done,” you MUST:
  1) run a clean local verification loop (tooling + basic builds/tests that are feasible)
  2) write an AAR using the repo’s AAR template and save it to 000-docs/
  3) produce a handoff summary: epics/tasks, commits, and how to verify.

OUTPUTS REQUIRED (in this order)
A) Evidence snapshot
B) Phase 0 Beads epic tree (parent/child tasks + dependencies)
C) Exact commands you ran (copy/pasteable)
D) Files changed list (paths) + rationale
E) AAR path + contents summary (do not omit bead IDs / commits)
F) PR link or next action to open PR

────────────────────────────────────────────────────────────
A) EVIDENCE SNAPSHOT (NO CHANGES YET)
1) Print:
   - git status
   - git branch -vv
   - git log -15 --oneline
   - ls -la
   - tree -L 2 000-docs (or find 000-docs -maxdepth 2 -type d)
   - list lockfiles: find . -maxdepth 3 -name "*lock*" -o -name "pnpm-lock.yaml" -o -name "package-lock.json" -o -name "yarn.lock" -o -name "bun.lockb"

2) Identify “source of truth” areas:
   - marketplace/ (Astro site)
   - packages/cli (CLI)
   - plugins/mcp/* (plugins)
   - scripts/ (validators)

────────────────────────────────────────────────────────────
B) CREATE PHASE 0 BEADS STRUCTURE
Create parent epic:
- EPIC: Phase 0 — Repo Stabilization + Operator Clarity

Create child tasks (minimum set):
0.0 Branch Hygiene + Baseline
  - Create feature branch: feature/phase-0-repo-stabilization
  - Confirm main is untouched
  - Confirm CI status on current default branch (just collect links, don’t “fix” CI in Phase 0)

0.1 000-docs Flatten + Naming Compliance
  - Enforce: NO subfolders in 000-docs
  - Move/rename docs into 000-docs root
  - Create a “Doc Index” markdown file (single page) listing key docs + what they are

0.2 Repo Map (Operator README for repo internals)
  - Create 000-docs/NNN-OP-RMAP-repo-map.md explaining:
    - what each top-level folder is for
    - what is buildable, what is deployable
    - what workflows exist (validate/deploy)
    - “golden paths” for local dev (commands)

0.3 Dependency Manager Inventory (NO policy changes yet)
  - Document what uses pnpm vs npm vs bun (facts only)
  - Identify why marketplace has package-lock.json while root uses pnpm-lock.yaml
  - Identify any “two lockfile” confusion points
  - DO NOT attempt to migrate managers in Phase 0 (that is Phase 1 decision)

0.4 Branch + Release Discipline Document
  - Create 000-docs/NNN-OP-BRCH-branch-and-release-flow.md defining:
    - One clean main
    - Feature branch per phase
    - CI must be green before merge
    - Squash merge with commit message format
    - After merge: tag + deploy rules (if applicable)

0.5 “Known Issues” Punchlist for Phase 1+
  - Create 000-docs/NNN-RA-P0PL-phase-1-punchlist.md
  - Include: lockfile mismatch evidence, pnpm versioning, analytics-dashboard workspace removal, homepage search UX requirement mismatch, etc.
  - This is a factual list + references to files / CI logs.

Set dependencies:
- 0.1 blocks AAR completion (AAR must reference final doc structure)
- 0.2 depends on 0.1
- 0.4 depends on 0.0
- 0.5 depends on 0.0 + 0.3

────────────────────────────────────────────────────────────
C) IMPLEMENT PHASE 0 CHANGES
1) Create branch:
   git checkout -b feature/phase-0-repo-stabilization

2) 000-docs flattening:
   - Move nested docs up into 000-docs/
   - Rename to comply with our naming standard
   - Delete obvious duplicates ONLY if you can prove equivalence; otherwise keep and mark “DEPRECATED” inside the doc.

3) Create the three operator docs (Repo Map, Branch Flow, Punchlist) and Doc Index.

4) Keep changes minimal and reversible:
   - No refactors
   - No UI changes
   - No dependency upgrades
   - No lockfile regeneration in Phase 0 (Phase 1)

────────────────────────────────────────────────────────────
D) VERIFICATION LOOP (BEFORE CLAIMING DONE)
Run:
- markdown lint if available (optional)
- Ensure 000-docs has no subdirs: find 000-docs -mindepth 1 -type d should return nothing
- Ensure docs are readable and links/paths referenced exist

────────────────────────────────────────────────────────────
E) WRITE AAR (MANDATORY)
Use the repo’s AAR template.
Save to: 000-docs/NNN-AA-AACR-phase-0-repo-stabilization.md

AAR MUST INCLUDE:
- Phase number (0)
- CST timestamp
- Bead epic ID + child bead IDs
- PR link (or “PR not opened yet” + why)
- Commits
- “How to verify” commands
- Risks/Gotchas
- Next actions (Phase 1 candidates)

────────────────────────────────────────────────────────────
F) COMMIT + PR
- One or a small number of commits, message format:
  "phase0(docs): flatten 000-docs + add repo operator map"
- Push branch
- Open PR to main with a concise summary and verification steps

STOP CONDITIONS
- If you discover CI failures or lockfile drift, DO NOT fix them in Phase 0.
  Record them in the Phase 1 punchlist with exact evidence and file paths.

When finished, print the Outputs Required (A–F) and nothing else.
