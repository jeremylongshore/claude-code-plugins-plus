---
name: workflow
description: |
  Use when a task is too large for turn-by-turn orchestration and should run through the big-task workflow lane: system-wide changes, large migrations, repo-wide audits, high-confidence verification, or tasks explicitly asking to run a workflow. Claude Code uses native dynamic workflows; Codex and OpenCode use the portable workflow adapter.
  Trigger with /hyperflow:workflow, "run a workflow", "dynamic workflow", "big task", "large migration", "repo-wide audit".
allowed-tools: Read, Glob, Grep, AskUserQuestion, Skill
argument-hint: "<big task description>"
version: 1.0.0
license: MIT
compatibility: Claude Code native workflows; Codex/OpenCode portable adapter
tags: [workflow, claude-code, codex, opencode, large-task, orchestration, verification]
---

# Workflow

Big-task path for work that is too large for normal turn-by-turn orchestration: system-wide changes, large migrations, repo-wide audits, high-confidence verification, and task prompts that explicitly ask for a workflow.

- In Claude Code, use the host dynamic workflow runtime.
- In Codex, run the portable workflow adapter with Codex subagents when exposed; otherwise run the same phases inline in the current thread.
- In OpenCode, run the portable workflow adapter with Task/subagent dispatch when exposed; otherwise run the same phases inline in the current session.
- In Antigravity, Desktop/web bridge mode, or any host that cannot preserve the adapter phases, say so in one line and route to `/hyperflow:scope` with `chain-mode=auto`.

Claude Code dynamic workflows require Claude Code v2.1.154 or later and can be disabled by `/config`, managed settings, `~/.claude/settings.json`, or `CLAUDE_CODE_DISABLE_WORKFLOWS=1`. When disabled, use the portable adapter if the host is Codex or OpenCode; otherwise route to `/hyperflow:scope` with `chain-mode=auto`.

## Routing Rules

- Run this skill in Claude Code, Codex, and OpenCode.
- Auto-route here when triage returns `flow=deep` or `flow=scientific`, `scope=system-wide`, or the user says `big task`, `large migration`, `repo-wide audit`, `run a workflow`, or `dynamic workflow`.
- Do not route here for moderate multi-file work, routine bug fixes, or a task that needs user sign-off between implementation stages. Big-task workflow runs should not depend on arbitrary mid-run user input; split sign-off-heavy work into separate workflows or use `spec -> scope -> dispatch`.
- Do not set `/effort ultracode` or `xhigh` automatically. The user can enable `/effort ultracode` manually for session-wide workflow selection.

## Provider Contracts

### Claude Code Native Workflow

When this skill runs, ask the Claude Code workflow runtime to create a dynamic workflow for `$ARGUMENTS`. The generated workflow must preserve Hyperflow's doctrine inside the worker prompts and must include these phases:

1. Research and planning
   - Map affected files, dependency edges, tests, docs, and risk boundaries.
   - Read `.hyperflow/profile.md`, `.hyperflow/architecture.md`, `.hyperflow/conventions.md`, `.hyperflow/testing.md`, and `.hyperflow/memory/index.md` when present.
   - Produce a concise execution graph with parallelizable units and dependencies.

2. Parallel implementation or investigation
   - Fan out independent agents by subsystem or file family.
   - Keep each agent brief specific: objective, files in scope, constraints, acceptance criteria, and test expectations.
   - Use the lightest model/stage that can safely do the work when the runtime supports model routing.

3. Adversarial verification
   - Run independent verification agents against each implementation or finding.
   - For audits, verify each finding before reporting it.
   - For implementation, check cross-file integration, regression risk, security-sensitive paths, and missed tests.

4. Quality gates and repair loop
   - Run the project lint, typecheck, build, and relevant tests from `.hyperflow/testing.md` or detected package scripts.
   - Retry focused fixes only for verified failures.
   - Never use `--no-verify`; never force-push to main or master.

5. Final synthesis
   - Return one coordinated result with completed work, verification evidence, unresolved risks, changed files, and next actions.
   - For durable project learnings, identify what should be appended to `.hyperflow/memory/`, but do not invent memory entries unrelated to the run.

### Codex Portable Workflow Adapter

Codex does not provide Claude Code's dynamic workflow runtime. Treat `/hyperflow:workflow` as a custom Hyperflow workflow envelope around Codex subagents and inline fallback:

1. Research and planning
   - Read the same `.hyperflow/` cache files listed above when present.
   - Write or update `.hyperflow/tasks/<slug>.md` for implementation or audit work that needs durable progress tracking.
   - Build an execution graph with parallelizable units, dependencies, expected commits, and verification commands.

2. Parallel implementation or investigation
   - If Codex subagent tools are exposed, dispatch independent searcher/worker/writer units together and collect their results before review.
   - Map implementation and writing tasks to worker subagents; map codebase research to explorer/search subagents.
   - If subagents are unavailable, run each unit inline with explicit worker and reviewer labels.

3. Adversarial verification
   - Run a separate verification pass for each completed unit before reporting it.
   - Use Codex thinking defaults for verification and final integration review.

4. Quality gates and commits
   - Run the detected lint, typecheck, build, and relevant tests.
   - Commit each accepted unit separately using conventional commits.
   - Never use `--no-verify`; never request `xhigh`.

5. Final synthesis
   - Return changed files, verification evidence, unresolved risks, and next actions.

### OpenCode Portable Workflow Adapter

OpenCode does not provide Claude Code's dynamic workflow runtime. Treat `/hyperflow:workflow` as a custom Hyperflow workflow envelope around OpenCode's task/subagent facilities and inline fallback:

1. Research and planning
   - Read the same `.hyperflow/` cache files listed above when present.
   - Write or update `.hyperflow/tasks/<slug>.md` for implementation or audit work that needs durable progress tracking.
   - Build an execution graph with parallelizable units, dependencies, expected commits, and verification commands.

2. Parallel implementation or investigation
   - If OpenCode exposes Task/subagent dispatch, send independent implementation or investigation units through that path.
   - Keep each subtask bounded by objective, files in scope, constraints, acceptance criteria, and tests.
   - If task dispatch is unavailable, run each unit inline with explicit worker and reviewer labels.

3. Adversarial verification
   - Run a separate verification pass for each completed unit before reporting it.
   - Use the configured thinking model for verification and final integration review.

4. Quality gates and commits
   - Run the detected lint, typecheck, build, and relevant tests.
   - Commit each accepted unit separately using conventional commits.
   - Never use `--no-verify`.

5. Final synthesis
   - Return changed files, verification evidence, unresolved risks, and next actions.

## Claude Code Prompt Skeleton

Use this shape when handing the task to the workflow runtime:

```text
Create a dynamic workflow for this Hyperflow big-task run.

Task:
<user task>

Doctrine:
- Preserve Hyperflow autonomy: execute reversible work without invented confirmations.
- Ask only for genuine ambiguity after codebase research.
- Keep plans, task decompositions, audits, and memory under .hyperflow/ when files are needed.
- Use conventional commits, one distinct task per commit.
- Never use --no-verify and never force-push to main/master.
- Respect the Hyperflow security blocklist in skills/hyperflow/security.md.

Required phases:
1. Research and planning.
2. Parallel implementation or investigation.
3. Adversarial verification.
4. Quality gates and focused repair loop.
5. Final synthesis.

Acceptance:
- Every substantive result is independently checked before being reported.
- Quality gates run or are explicitly marked unavailable with the command attempted.
- The final answer includes evidence, changed files, unresolved risks, and next actions.
```

## Save For Reuse

When a run succeeds and the user will repeat it, mention that Claude Code can save the generated workflow from `/workflows` with `s`. Project workflows save under `.claude/workflows/`; personal workflows save under `~/.claude/workflows/`. Do not create those files directly from this skill because plugin packaging does not currently ship `.claude/workflows/` as a first-class component.

Codex and OpenCode adapters are not saved through `/workflows`; repeatable behavior comes from this skill, `.hyperflow/tasks/`, project memory, and provider-specific subagent/task configuration.
