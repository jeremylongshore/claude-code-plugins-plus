# Triage playbook — divergence first, then category, then mode

## The procedure

1. **State intended and actual.** Both, explicitly. A triage that skips this becomes a search for
   something that looks wrong, and something always does.
2. **Find the first divergence.** Read forward, not backward from the symptom. Mark the earliest turn
   where the run left the intended path.
3. **Classify the category** with the three-question ladder, stopping at the first yes.
4. **Name the mode** and cite its identifier.
5. **Route the fix** to the level the category names.
6. **Say why the other two levels are wrong.** This is what stops the fix from being re-litigated by
   someone who read only the symptom.

## Why divergence-first

The loudest symptom is almost never the defect. A run that ends with an off-topic section will produce
an obviously-bad writer output at turn 9; the cause is frequently an incomplete handoff at turn 4. Both
are real observations. Only one is fixable.

The rule: **the first divergence is the diagnosis; everything after it is consequence.** A fix applied
downstream of the divergence changes the symptom and preserves the cause, which is worse than no fix
because it consumes the evidence.

## Fix-level routing

| Category | Level | What actually changes | What will not help |
| --- | --- | --- | --- |
| FC1 system design | System author | Task specification, role boundaries, termination condition, history strategy | Better models; more agents |
| FC2 inter-agent misalignment | Topology and protocol | Structured handoff payloads, an acknowledgment step, removing or redirecting an edge | Tuning either agent's prompt |
| FC3 task verification | Verification | Adding a verifier, or correcting one that passes bad output | Improving the producer |

The FC2 row is the one to internalize. When the defect is in the conversation, both agents are behaving
reasonably given what they received. Prompt tuning on either side is work that cannot succeed, and it
is where most debugging effort goes.

## Mode-to-fix quick reference

| Mode | First thing to try |
| --- | --- |
| FM-1.1 disobey task spec | Move the constraint into the agent's input, not the system preamble |
| FM-1.2 disobey role spec | Narrow the agent's tools — a role boundary the tools enforce is not one a prompt has to |
| FM-1.3 step repetition | Make the step's completion observable to the agent that repeats it |
| FM-1.4 loss of history | Pass references to durable state rather than replaying transcripts |
| FM-1.5 unaware of termination | Define the stop condition explicitly; a rate limit is not a stop condition |
| FM-2.1 conversation reset | Persist context outside the conversation — a mailbox or a store |
| FM-2.2 fail to ask | Make asking a legitimate, low-cost output rather than a failure |
| FM-2.3 task derailment | Re-anchor each handoff to the original task statement |
| FM-2.4 information withholding | Make the handoff payload structured with required fields |
| FM-2.5 ignored input | Add an acknowledgment step; an unacknowledged message is a dropped one |
| FM-2.6 reasoning-action mismatch | Shorten the gap between plan and act; act on the stated plan, not a re-derivation |
| FM-3.1 premature termination | Define completion as a checkable property, not an agent's judgment |
| FM-3.2 no verification | Add one. Absence is the common case, not weakness |
| FM-3.3 incorrect verification | Check what the verifier checks — often the wrong property, confidently |

## Handing off to other skills

- **Loop or runaway cost** — classify the mode here (usually FM-1.3 or FM-1.5), then hand the graph to
  `topology-safety` for cycle detection and limiter sizing. Naming the mode and breaking the cycle are
  separate jobs, and doing only the second leaves the run incorrect but cheap.
- **Repeated FC2 findings across runs** — the topology is wrong, not the run. Take it to
  `comms-topology`. Chronic information withholding usually means a supervisor shape where a pipeline
  was needed, or handoffs carrying prose where they should carry structure.
- **Cross-organization participants** — misalignment across a trust boundary needs a typed contract, not
  a better handoff convention. That is `a2a-protocol`.

## Provisional diagnoses

A trace missing agents or turns yields a provisional finding. Say so in the triage block itself, with
what is missing and what it would change. A provisional diagnosis reported as final sends the fix to
the wrong level with full confidence, which is the failure this whole procedure exists to avoid.
