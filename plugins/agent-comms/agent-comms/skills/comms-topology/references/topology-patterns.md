# Worked topology patterns

Five shapes that cover most real systems, each with its edge count, the axis that justifies it, and the
failure it invites.

## Pipeline

```
A → B → C
```

**Edges:** N−1. **Justified by:** strictly sequential work where each stage consumes the previous
stage's whole output. **Topology:** direct, unless a stage must survive a restart.

**Invites:** head-of-line blocking. A slow middle stage stalls everything upstream and downstream, and
the symptom appears at the endpoints rather than at the culprit. Instrument per-stage latency, not
just end-to-end.

**Do not** turn a pipeline into a bus because one stage got slow. Fix the stage.

## Fan-out

```
      ┌→ B
A ────┼→ C
      └→ D
```

**Edges:** N−1 from one source. **Justified by:** one event, several independent consumers. This is the
canonical bus case — rule 2 fires.

**Invites:** silent consumer death. With a bus, a subscriber that stops consuming looks identical to one
with nothing to do. Require a liveness signal per subscriber; absence of messages is not evidence of
health.

**Do not** implement this as duplicated mailbox writes. It works until someone adds consumer E and
misses one write site.

## Supervisor

```
        S
    ┌───┼───┐
    A   B   C
```

**Edges:** 2N (down and back). **Justified by:** a coordinator that decomposes work, dispatches, and
reassembles. The most common LLM multi-agent shape, and the one where edge cost concentrates.

**Invites:** the supervisor becoming the context bottleneck — every result flows through one agent's
window. Return references (task ids, artifact handles) upward rather than full payloads, and let the
supervisor fetch only what it must read.

**Also invites** an A→S→B→S→A ring that the supervisor's own retry logic hides. This is where
`topology-safety` earns its place.

## Mesh

```
A ↔ B
↕ ╳ ↕
C ↔ D
```

**Edges:** N(N−1)/2 undirected, N(N−1) directed. **Justified by:** almost nothing.

Mesh is what a system becomes when no topology decision was made. Four agents is six edges; eight
agents is twenty-eight. Every edge is a token cost, a latency path, and a cycle candidate. The
communication-redundancy literature exists because of this shape.

**Fix:** identify the edges that carry decisions rather than status, keep those, and replace the rest
with a mailbox read or a supervisor hop. Pruning to a DAG is the documented move.

## Seam

```
[ org A: direct/supervisor ] ──A2A──▶ [ org B: their business ]
```

**Edges:** one, at the boundary. **Justified by:** rule 1 — a participant outside the trust boundary.

**Invites:** the boundary quietly moving inward. When a partner's agent proves useful, the temptation is
to give it a direct edge to an interior agent "just for this one case." That edge bypasses discovery,
auth, and the versioned contract — the three things the protocol was there to provide.

**Rule:** the seam is a single, named, auditable edge. Interior agents reach the partner through it, not
around it. Every remote capability claim crossing it is reported, never adopted — see the
`a2a-agent-card` skill.

## Choosing between supervisor and pipeline

These two are confused most often. The test is whether stage order is **fixed** or **decided**:

- Fixed order, each stage consumes the last → **pipeline**. No coordinator needed; the shape is the plan.
- Order or membership depends on intermediate results → **supervisor**. Something has to decide, and a
  pipeline has nowhere to put that decision.

A pipeline with conditional branches sprouting inside stages is a supervisor that has not admitted it
yet, and it is harder to debug because the routing logic is scattered across the stages.
