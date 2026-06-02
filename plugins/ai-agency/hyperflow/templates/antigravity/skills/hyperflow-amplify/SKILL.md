---
name: hyperflow-amplify
description: Hyperflow prompt amplifier. Use when a prompt is rough, vague, or under-specified and should be rewritten to high quality before running it — "enhance this prompt", "make this prompt better", "improve my prompt", "rewrite this prompt". Domain-aware: detects the prompt's domain, injects the matching specialist standards + project rules, scores against an 8-dimension rubric, then offers to run it.
---

# hyperflow-amplify — prompt amplifier (Antigravity single-agent)

Turn a rough prompt into the single strongest version, then hand it off. **Amplify never writes code** — it produces a prompt other workflows (or you) execute. Follow the `hyperflow` doctrine.

## Steps

1. **Read intent.** Detect the prompt's domain(s) (frontend/ui, api/db backend, mobile, security, performance, refactor/bugfix/test, devops, docs). Read project rules when present: `AGENTS.md`, `~/.gemini/AGENTS.md`, `.hyperflow/memory/*`. Note the gaps a senior engineer would have to guess.
2. **Amplify.** Rewrite into the single strongest version using this skeleton (adapt section presence — economy is a constraint, never inflate a one-liner into a spec):
   - role / expertise framing (one line)
   - precise task (unambiguous goal)
   - Context (relevant background, current state, inputs)
   - Constraints (domain doctrine standards + project rules — project rules win on conflict)
   - Output (deliverable format + acceptance criteria)
   - Out of scope (explicit anti-goals)
3. **Score** the draft against the 8-dimension rubric (1-5 each): intent clarity · context sufficiency · scope boundaries · structure · domain doctrine injected · output spec · guardrails · economy. If any dimension < 4, revise once.
4. **Present** the amplified prompt in one copy-ready fenced block + a 2-4 line rationale (what changed, which standards/project rules were injected, any flagged ambiguity).
5. **Handoff gate** (AskUserQuestion, 4 options → mark one Recommended): Send to `hyperflow-spec` (Recommended) · Send to `hyperflow-scope` · Send to `hyperflow-dispatch` · Copy only. On a "Send to…" choice, invoke that workflow with the amplified prompt.

## Rules

- Never write code. Project rules override generic persona standards. No AI attribution in the amplified prompt or rationale.
