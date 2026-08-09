# Edge pruning — the cost case and the security case

## The evidence

**Zhang et al., "Cut the Crap: An Economical Communication Pipeline for LLM-based Multi-Agent Systems"**
(AgentPrune; arXiv:2410.02506, ICLR). First work to formally define **communication redundancy** in
multi-agent pipelines. It performs one-shot pruning on the spatial-temporal message-passing graph and
reports, across six benchmarks:

- Results comparable to state-of-the-art topologies at **$5.6 versus $43.7**.
- **28.1%–72.8% token reduction** when dropped into existing multi-agent frameworks.
- Successful defence against **two types of agent-based adversarial attack**, with a 3.5%–10.8%
  performance improvement in those settings.

Read the third bullet carefully. Pruning is normally justified on cost, and the cost result is large.
The security result is the more interesting one: an edge an adversarial message can travel is an edge
worth not having. **Edge count is a security metric as well as a budget line.**

State this as evidence, not assurance. These are benchmark results from one method on one set of tasks.
Pruning a specific production graph is expected to help; it is not a guaranteed property.

## Classifying an edge

Every edge is one of two kinds, and the distinction drives every prune decision:

**Decision-carrying** — the receiver behaves differently because this message arrived. Removing it
changes what the system does. Keep.

**Status-carrying** — the message informs, and the receiver would eventually reach the same state
another way. Removing it changes only when the receiver knows. Candidate for pruning.

The test that separates them: *if this message were dropped, would any subsequent decision differ?* If
the honest answer is "it would just be slower to notice," it is status.

## Push-to-pull conversion

The highest-value prune is not deletion — it is converting a push into a pull:

```
before   worker ──status──▶ supervisor        (edge; can amplify; can close a cycle)
after    worker ──write──▶ store ◀──read── supervisor   (no agent-to-agent edge at all)
```

The information still flows. The edge in the *agent* graph is gone, which means it cannot amplify,
cannot participate in a cycle, and costs no model call. The `agent-mailbox` skill in this pack is one
implementation of that store.

This single move usually removes most status edges in a supervisor topology.

## Pruning procedure

1. Enumerate every edge with its trigger and its payload class.
2. Label each decision-carrying or status-carrying. Where uncertain, label decision-carrying — the
   conservative direction is keeping an edge, not cutting one.
3. Convert status edges to push-to-pull where a durable store exists.
4. Delete status edges with no consumer that acts on them. These accumulate as agents are refactored
   and their old notifications are never removed.
5. Re-run cycle detection. Pruning frequently breaks cycles as a side effect, which is the acyclicity
   fix arriving for free.
6. State edge count before and after as two numbers. A prune with no number is a claim.

## What not to prune

- **Error and escalation edges.** Cutting these makes failures silent. A loop is expensive; a silent
  failure is worse.
- **The only edge into a node.** That node becomes unreachable. Obvious in a diagram, easy to miss in a
  list of edges.
- **Edges on the trust seam.** The single audited protocol edge to an outside party is load-bearing.
  Pruning it means someone will route around the seam instead.
- **Anything on the happy path to save tokens.** Cost-driven pruning of decision-carrying edges trades
  correctness for spend, which is the wrong direction of the trade this evidence supports.

## Reporting

```text
EDGE          worker-a → supervisor
TRIGGER       task completion
CLASS         status-carrying
VERDICT       prune → push-to-pull (supervisor reads task state)
CYCLE EFFECT  breaks supervisor→worker-a→supervisor
EDGES         12 → 9
```

The `CYCLE EFFECT` line is the one that justifies pruning to a sceptic. Cost savings are arguable;
removing a cycle is structural.
