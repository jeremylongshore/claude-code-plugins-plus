# Agent consultation

How a specialist asks another specialist for help mid-task. The lateral sibling of downward sub-agent fan-out
([DOCTRINE.md](DOCTRINE.md) rule 18) — same depth-1 / budget-capped discipline, but the peer is an equal, not a
sub-worker. This is the canonical contract; [DOCTRINE.md](DOCTRINE.md) rule 19 is the one-paragraph summary.

## Universal by construction

**Every agent in [`../../agents/`](../../agents/) — current and future — can ask and be asked, automatically.** There
is no opt-in field, flag, or charter edit. The protocol lives in the *shared scaffolding* every dispatched agent
already receives ([worker-prompt.md](worker-prompt.md), [reviewer-prompt.md](reviewer-prompt.md), and the dispatch
Composer's specialist injection), so a new `agents/<name>.md` participates the moment the file exists. The consult
**allowlist is the live `agents/` directory**, resolved by file existence — not a hand-maintained list. A charter's
`Composes with:` line is reused only as a *recommended-peer hint* surfaced in the prompt; it never gates who may be
asked.

## Signal format

A worker that needs a decision outside its lane STOPS and emits, in place of its normal output:

```
CONSULT: <peer-agent> — <one-line question>
CONSULT-CONTEXT:
  <≤5 lines: the file / decision / constraint the peer needs to answer>
```

`<peer-agent>` is any name resolving to `agents/<name>.md`. Modeled on the `OVERSIZE:` escape hatch in
[worker-prompt.md](worker-prompt.md) — emit-and-stop, never partial work across a domain boundary.

## Hybrid routing — who brokers

- **Build-time workers (dispatch) → orchestrator-brokered.** The worker emits the `CONSULT:` signal and stops; it
  never calls `Agent` laterally itself. The Team Lead brokers (below). This keeps the Layer-2 iron rule *"Workers
  never coordinate"* literally true — the worker emits a signal exactly as it does for `OVERSIZE`/`ESCALATE`.
- **Design-time decision agents (plan) → direct.** `architect`, `designer`, `analyst`, and any future decision agent
  may dispatch a peer directly via their own `Agent` tool within the budget below, then fold the answer into their
  own output. Decision agents already own decisions, so a direct consult does not cross a role boundary.

## Broker loop (orchestrator)

1. Read the `CONSULT:` signal from the worker output.
2. Resolve `<peer-agent>` to `agents/<name>.md`. If no such file exists, do not block — inject
   `Consultation unavailable: <peer> not found; proceed with best judgment.` and re-dispatch.
3. Dispatch the peer with a **consultation brief**: the question, the `CONSULT-CONTEXT`, and the framing *"You are
   being consulted, not taking over. Answer the question in ≤ 8 lines. Do not redesign the task."*
4. Re-dispatch the original worker with `Consultation answer from <peer>:` prepended to its brief. The worker resumes
   from where it stopped.

Reviewer `CONSULT:` signals broker identically — the verdict is held until the brokered answer returns, then the
reviewer is re-dispatched to finish the review.

## Caps (mirror fan-out rule 18)

- **Depth = 1.** A consulted peer may NOT itself emit a `CONSULT:` — no consult-of-consult, no cycles.
- **Budget:** ≤ 2 consults per worker task; ≤ 3 per design-time decision agent. Consult tokens roll into the
  parent's usage line tagged `(N consults)`; the chain `budget` is the ceiling.
- **Allowlist = the live `agents/` registry.** Any registered specialist may be named; `Composes with:` only ranks
  the most relevant peers in the prompt hint.
- **Never overrides a halt.** A `security-reviewer` `SECURITY_VIOLATION` or a worker `BLOCKED:` still stops the
  pipeline. Consultation cannot reopen a halt or downgrade a security verdict.
- **Peer error → ESCALATE, never block.** If the consulted peer errors or times out, fall back to failure-recovery
  ([failure-recovery.md](failure-recovery.md)): the worker proceeds with a caveat or the step escalates; the chain
  never waits forever on a consult.

## Worked examples

- **frontend worker → designer** — `CONSULT: designer — which spacing token for the card gutter, 16 or 24?` Broker
  dispatches designer; answer injected; worker resumes the build.
- **architect (design-time) → motion** — while drafting §2 data flow, the architect directly asks `motion` whether a
  shared-element transition is feasible at the proposed list size before committing the interaction to the spec.
- **designer → motion** — a motion-heavy screen: the designer hands the heavy-motion treatment to `motion` for the
  easing/orchestration detail, keeping ownership of the overall motion language.
- **analyst → database-reviewer** — `CONSULT: database-reviewer — is a partial index on (tenant_id, status) the right
  call for this read pattern?` before recommending an approach.
