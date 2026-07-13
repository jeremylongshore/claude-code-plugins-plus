---
title: "The Kernel Must Not Import Its Agents"
description: "We extracted a stateful watcher agent from a governance kernel and enforced a one-way agent-to-kernel dependency edge — the kernel must not import its agents."
date: "2026-07-12"
tags: ["architecture", "agents", "dependency-management", "governance", "refactoring"]
featured: false
---
There is a moment in the life of every framework where an application-shaped thing has grown up inside it. It started as a demo, a reference implementation, a "let's just prove the primitives work" spike. Then it kept running. Now it has cron entries, an operator surface, a test pack, and traceability rows — and it lives in the same repository as the primitives it was only ever meant to exercise.

On 2026-07-12 we did the extraction. We pulled a stateful watcher agent out of a governance kernel and gave it its own leaf repository. The interesting part is not that we moved files. It is the single rule that made the move safe, and that made the resulting kernel worth trusting:

> **The kernel must not import its agents.** When you split an agent out of its governance kernel, the dependency must point from the agent to the kernel — never the reverse.

This is the agent-framework restatement of a much older law: *the framework must not depend on the application*, and *the composition root lives in the leaf*. Everything below is one concrete execution of that law.

In practice the agent repo imports the kernel's published contracts as a pinned dependency, composing governance primitives like the trigger interface and policy engine. The kernel has zero knowledge of the agent's existence — no import, no reference, no coupling. That one-way edge is what keeps the kernel small, independently verifiable, and trustworthy as a standalone governance system.

## The two systems

**`agent-governance-plane` (AGP)** is the governance *kernel*. It owns the durable governance primitives and nothing else: a policy engine, a Docker sandbox for tool execution, Slack human-in-the-loop (HITL) approval, and an Ed25519-signed, hash-chained audit journal. Its doctrine line is worth memorizing because it dictates the whole shape:

> The model proposes; the deterministic system decides and records.

Every autonomous tool call passes through the same governed path:

```text
trigger → policy gate → (if risky) human approval → sandboxed exec → signed journal
```

**`bob-the-intendant`** is the new *leaf* product repo. It composes AGP as a pinned dependency and owns the agent/composition layer. Its product category is "governed background agents" — long-lived processes that wake on a trigger and want to do something a human might not want them to do unsupervised. AGP is what keeps them honest. Bob is what makes them useful.

Before the extraction, the watcher lived inside AGP. After it, AGP has zero knowledge that the watcher exists, and Bob owns it outright.

## The invariant we were protecting

The boundary has two halves, and they are not the same rule. The headline half is the thesis: **the kernel imports nothing from the leaf** — it does not know the agents that compose it exist. The mirror half constrains the leaf: **the leaf may import only the kernel's frozen contracts, never the daemon's internals** — where "the daemon" is the kernel's live governance loop (`runMediated()`) and the machinery around it. The composed agent composes the contracts the kernel publishes; it never reaches past them into implementation.

Put together, the two halves define one edge: it runs from agent (leaf) to kernel, touches only the published surface, and never runs the other way. A governance kernel that imports the agents it governs breaks the acyclic-dependency rule — it is a governance kernel you cannot reason about. You can no longer point at it and say "this small thing decides and records; here is its trust boundary" — because its [trust boundary](/posts/govern-at-merge-untrusted-union/) now includes every agent that ever leaked into it.

So the extraction had two acceptance tests, both structural:

- After extraction, **AGP has zero knowledge of the watcher.** No import, no CLI command, no template, no traceability row.
- After extraction, **Bob has zero references to removed AGP modules.** It composes contracts that still exist; it points at nothing that was deleted.

## What moved out, what stayed in

The discipline of the move is entirely in *where the cut runs*. The cut runs exactly along the contract boundary — the bounded context between kernel and leaf: agent-specific composition leaves, primitives stay.

Moved **out** of the kernel and into the leaf:

```text
src/triggers/github-watcher/     # the trigger-woken GitHub watcher agent
src/cli/commands/watch.ts        # `agp watch` — the operator surface a human runs
templates/github-watcher/        # the per-agent template test packs
RTM REQ-043 / 045 / 046 / 047 / 048 / 049   # this agent's traceability rows
Journey J2 + the "run-governed-watch" persona flow
```

Stayed **in** the kernel, because these are the primitives the agent *composes*, not the agent itself:

```text
trigger-source contract (RTM REQ-050)   # the frozen interface the agent fires through
daemon runMediated() loop (REQ-042)     # the governance loop itself
journal cross-chain causal-pointer (REQ-044)   # a journal primitive
```

Notice the requirements-traceability discipline here, because it is the part most teams skip. REQ-042 and REQ-044 were *re-anchored to the retained code* — the rows didn't get deleted, they got re-pointed at the primitives that stayed. The agent's own rows (REQ-043/045/046/047/048/049) followed the agent into the leaf's docs. Traceability is a graph, and when you cut the code graph you have to cut the requirements graph along the same line or your "signed audit of everything" claim quietly develops holes.

## The dependency edge

This is the entire point of the exercise, in one picture:

```text
        ┌───────────────────────────────────────────────┐
        │  bob-the-intendant  (LEAF — the application)   │
        │                                                │
        │   • github-watcher agent                       │
        │   • `bob watch` operator CLI                   │
        │   • template test packs                        │
        │   • J2 / run-governed-watch persona flow       │
        │                                                │
        │        imports  agp/src/... (contracts only)   │
        └───────────────────────┬───────────────────────┘
                                 │   pinned dependency
                                 │   ONE WAY — leaf → kernel
                                 ▼
        ┌───────────────────────────────────────────────┐
        │  agent-governance-plane  (KERNEL — frozen)     │
        │                                                │
        │   • trigger-source contract   (REQ-050)        │
        │   • runMediated() gov. loop   (REQ-042)        │
        │   • policy engine · Docker sandbox             │
        │   • Slack HITL · Ed25519 hash-chained journal  │
        │                                                │
        │        knows NOTHING about the watcher         │
        └───────────────────────────────────────────────┘
```

Bob consumes AGP as a **pinned dependency**. The watcher's imports were rewired from in-tree relative paths to `agp/src/...`. There is no arrow back up. The kernel cannot see the leaf, cannot import the leaf, and does not know the leaf exists. That is not an accident of the current file layout — it is the property we spent the day buying.

## Three tradeoffs, and why each went the way it did

Every real extraction is a sequence of forks in the road. Three of them carried the design.

**1. Clean removal + a cross-repo pinned-dependency edge — over keeping the watcher as a flag-gated in-tree spike.** The tempting cheap move is to leave the watcher in AGP behind a feature flag and call it "disabled." We chose the harder cut. A flag-gated agent left in-tree keeps the boundary muddy: the code is still *there*, still importable, still one careless `import` away from the kernel depending on its own agent. The flag protects runtime behavior; it does nothing for the dependency graph. We wanted the kernel to physically shrink to contracts, so that the invariant is enforced by *absence*, not by a boolean.

**2. Composing AGP as a pinned dependency — over vendoring or forking the kernel.** The frozen contracts and the trigger-source interface must be authored in exactly one place: AGP. If the leaf vendored or forked the kernel, those contracts would exist in two copies, and two copies of a contract drift — slowly, silently, and always at the worst time. Importing a pinned version means the leaf reads the contracts, never owns them. One author, one source of truth, one thing to version.

**3. Owning the watcher locally in the leaf — over importing `agp/src/triggers`.** This is the mirror image of tradeoff 2, and it is what makes the cut *symmetric*. After extraction the kernel no longer has the watcher modules, so the leaf cannot import them from AGP — they aren't there anymore. The leaf must own the watcher outright to build against the post-extraction kernel. Contracts: imported. Agent: owned. That split *is* the boundary.

## Why it was a breaking change on both sides

Extraction that touches a published surface is a breaking change by definition, and honest versioning has to say so.

- **On the kernel:** `agp watch` was **removed** from the AGP CLI. `BREAKING CHANGE` — the governed watcher now ships in the leaf. Anyone who typed `agp watch` has to move.
- **On the leaf:** the CLI was renamed `intendants → bob`; the npm package was renamed `@intentsolutions/intendants → @intentsolutions/bob-the-intendant`. `BREAKING CHANGE` on both the binary name and the package name.

You cannot smuggle a change like this through as a patch. The whole value of the extraction is that consumers can *reason* about the kernel independently — and that reasoning depends on the kernel's version number telling the truth.

## The part everyone underestimates: it was a live migration

Here is the detail worth teaching, because it is the one that bites. The watcher was not a dormant module. It was **running in production** on a cron: `~/bin/intendants-release-watch.sh`, firing on a schedule, in a governed loop, on a real repo.

Extracting a *running* component is a live-migration problem, not a code move. If you merge the kernel PR that removes `agp watch` while production cron still calls `agp watch`, you have — for however long it takes to notice — a production job pointed at [a command that no longer exists](/posts/every-safety-gate-has-a-failure-direction/).

So the order was inverted deliberately:

```bash
# 1. Repoint the production cron to the LEAF's command FIRST,
#    while `agp watch` still exists in the merged kernel.
#    ~/bin/intendants-release-watch.sh  →  `bob watch ...`

# 2. THEN merge the kernel PR that removes `agp watch`.
```

At no instant was production pointed at a command that didn't exist. The cutover of the running process precedes the removal of the thing it used to call. This is the same expand/contract pattern database migrations use — you add the new path, move traffic, and only then remove the old path — applied to a CLI command instead of a column.

The releases were coordinated to match:

- **AGP cut `v0.1.100`** — the post-extraction clean kernel.
- **The leaf cut `v0.0.1`, then `v0.0.2`.**
- During the work, the leaf pinned the post-extraction *commit* of AGP; once the kernel PR merged, it **repinned to the `v0.1.100` release tag.** Pin to a commit while the edge is in flight; pin to a tag once the edge is real.

## Verification: link the evidence, don't say "verified"

The whole claim of a governance kernel is auditability, so the extraction has to be auditable too. Both sides landed green.

**Kernel branch (post-extraction clean AGP):**

```text
bun run typecheck      0 errors
bun test               360 pass / 8 skip / 0 fail
coverage (lines)       94.46%   (gate ≥ 90)
coverage (funcs)       91.80%   (gate ≥ 88)
lint                   clean
claim-scan             PASS
doc-drift              PASS
audit-harness verify   OK
escape-scan            REFUSE=0 / CHALLENGE=0 / FLAG=0
```

**Leaf, built against the post-extraction kernel:**

```text
bun run typecheck      0 errors
bun test               52 pass / 0 fail  (10 files)
references to removed AGP modules:   ZERO
  (no `agp/src/triggers`, no `agp/src/cli/commands/watch`)
```

That last line is the acceptance test made mechanical. "Bob has zero references to removed AGP modules" is not a vibe — it is a grep that returns nothing. The kernel's side has the mirror check: nothing in AGP mentions the watcher. Two structural assertions, both green, and the invariant is proven rather than asserted.

## The generalizable principle

Strip away the specific repos and here is what is left, for anyone building an agent framework, a policy layer, or any governance kernel that other things compose.

If your governance kernel imports the agents it governs, three things break at once:

1. **You cannot ship or version the kernel independently.** Its releases are hostage to every agent tangled into it; a change in one agent forces a kernel release, and the kernel's version number stops meaning anything.
2. **You cannot reason about the kernel's trust boundary in isolation.** "Here is the small deterministic thing that decides and records" is only a true sentence if the small thing has a fixed edge. Import an agent and the boundary now wraps that agent's code too.
3. **Every new agent widens the kernel's attack and verification surface.** The set of things you must audit to trust the kernel grows with every agent you add — which is exactly backwards, because the kernel is supposed to be the *fixed point* you audit once. The watcher we just extracted was one such agent; every agent we *don't* extract would fold exactly this cost back into the kernel, which is why the extraction is a repeatable discipline and not a one-off cleanup.

Extracting agents into leaves keeps the kernel a small, independently-verifiable dependency with a stable trust boundary. That is not architectural neatness for its own sake — it is the entire reason to have a governance kernel in the first place. The one-way edge, agent → kernel, is what makes "a signed audit log of every tool call" a claim you can verify by looking at the kernel *alone*, without first reading every agent that happens to use it. The direction of a single dependency arrow is the difference between a trust boundary and a wish.
