---
name: tonone-onboard
description: 'First-run onboarding tour — guided walkthrough of tonone''s 23 agents, key skills, and worktree sessions. Two paths — expert (~90 sec) and newcomer (~8 min). Use when asked "how do I use tonone", "what can tonone do", "show me around", or "first steps".'
allowed-tools: AskUserQuestion
version: 0.8.0
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# tonone-onboard

Cross-agent onboarding tour. Not tied to a single agent.

Always runs. Never checks the marker file — the skill replays the tour regardless
of prior runs. To re-show the SessionStart welcome banner, delete
`~/.config/tonone/onboarded`.

## Step 1: Tier Check

Ask via AskUserQuestion:

> Are you familiar with Claude Code agents?

Options:

- A) Yes — I know CC agents, just show me tonone's capabilities (~90 sec)
- B) No — walk me through the whole thing (~8 min)

---

## Step 2: Expert Path (A)

### What tonone is

23 specialists, 2 teams. Engineering (15 agents) + Product (8 agents). Each owns a
domain. You dispatch them. They don't fight over work — Apex routes automatically.

### Top 5 commands to bookmark

Output this block verbatim:

```
┌─────────────────────────────────────────────────────────────┐
│  /apex-takeover     hand any task to the full team          │
│  /atlas-onboard     generate project docs for day-1 devs   │
│  /forge-audit       infra cost check                        │
│  /relay-ship        deploy your stack                       │
└─────────────────────────────────────────────────────────────┘
```

### Mental model

**Worktree sessions:** Every session gets its own git branch automatically.
Parallel sessions never conflict. Clean sessions auto-remove their branch on close.

### Done

> Run `/apex-takeover` to start. Describe any task and Apex routes it.
>
> Replay this tour any time: `/tonone-onboard`

---

## Step 3: Newcomer Path (B)

### What Claude Code agents are

Claude Code can act as specialized agents — each configured with a persona, domain
knowledge, and a set of skills. Instead of one generalist AI, tonone gives you a
team of 23 specialists. You talk to them like colleagues. They coordinate through
Apex, the engineering lead.

### Meet the team

Output this block verbatim:

```
Engineering Team (15 agents)
─────────────────────────────────────────────────────────────
Apex    Engineering lead — routes tasks, coordinates the team
Atlas   Knowledge engineer — docs, ADRs, onboarding
Forge   Infrastructure — cloud, IaC, cost
Relay   DevOps — CI/CD, deployments, GitOps
Spine   Backend — APIs, system design, performance
Flux    Data — databases, migrations, pipelines
Warden  Security — IAM, secrets, threat modeling
Vigil   Observability — monitoring, alerting, SRE
Prism   Frontend/DX — UI, internal tools, portals
Cortex  ML/AI — LLM integration, evals, RAG
Touch   Mobile — iOS, Android, cross-platform
Volt    Embedded/IoT — firmware, edge, protocols
Lens    Analytics — dashboards, metrics, reporting
Proof   QA — test strategy, E2E, flaky triage
Pave    Platform — dev experience, golden paths

Product Team (8 agents)
─────────────────────────────────────────────────────────────
Helm    Head of Product — briefs, handoff to engineering
Echo    User research — interviews, personas, JTBD
Lumen   Product analytics — OKRs, funnels, A/B tests
Draft   UX design — flows, IA, wireframes
Form    Visual design — brand, tokens, design system
Crest   Strategy — roadmap, prioritization, competitive
Pitch   Marketing — positioning, messaging, GTM
Surge   Growth — acquisition, activation, retention
```

### How to invoke Apex

Run `/apex-takeover` and describe your task. Example:

> Run `/apex-takeover` and say "check our security posture."
> Apex reads the request, dispatches Warden, brings you the result.
> You never invoke Warden directly.

The right agent always gets the job. You don't need to know who to call.

### Worktree sessions

Every session gets an isolated git branch at `.claude/worktrees/`. Sessions editing
the same files don't conflict — they each work on their own branch. When a session
ends with no changes, the branch cleans itself up automatically.

You don't need to manage this. It happens automatically via the SessionStart and
Stop hooks.

### Skill routing

Skill routing tells Claude to use a specialized workflow instead of answering
directly when the request matches a known pattern. This is already configured in
this project's `CLAUDE.md` — see the `## Skill routing` section.

Examples already wired:

- "there's a bug" → `/investigate`
- "ship this" → `/ship`
- "review my diff" → `/review`
- "product idea" → `/office-hours`

You can add your own routing rules to `CLAUDE.md` at any time.

### Next steps — try these first

Output this block verbatim:

```
1. /apex-takeover     describe any task, Apex routes it
2. /atlas-onboard     generate onboarding docs for this project
```

### Done

> You're set. 23 agents, 100+ skills, isolated sessions.
>
> Replay this tour any time: `/tonone-onboard`
> Re-show the install banner: delete `~/.config/tonone/onboarded`
