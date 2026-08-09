# Building the graph and finding the cycles

## Why acyclicity, not just rate limiting

The multi-agent-learning literature is explicit: "the parallel message-passing update in the undirected
graph with cycles cannot guarantee convergence." The documented response is to model dependencies as
**directed acyclic graphs**, enforce an acyclicity constraint, and project the graph into the
admissible set of DAGs — which the same work notes "removes redundant communication edges for cost
improvement."

Two properties, one structural change. That is why acyclicity is defence #1 and rate limiting is
defence #3: a limiter bounds a loop's cost, while removing the cycle removes the loop.

## Recovering the real graph

A diagram is a claim. Recover edges from the source:

| Edge class | Where it hides |
| --- | --- |
| Direct send | Obvious. Grep the send/publish call. |
| Retry path | Inside a wrapper. The retry is an additional edge with the same endpoints. |
| Error notification | An error handler that messages a peer is an edge that only exists under failure — which is exactly when loops start. |
| Supervisor callback | The return leg. Frequently undrawn because it is "just a result." |
| Self-subscription | An agent subscribed to a channel it also writes to. This is a self-loop hiding in a fan-out. |
| Dynamic dispatch | A send whose destination is computed. Cannot be resolved statically — report it as an unknown edge, never as absent. |

A graph containing unresolved dynamic dispatch is **incomplete**, and a cycle-free verdict on an
incomplete graph is worse than no verdict at all. Label it.

## Detection

Depth-first search with a recursion stack. A back edge to a node on the current stack is a cycle;
report the full path from that node, not just the closing pair. The path is what makes the break
choosable — with only the endpoints, there is no way to pick the weakest edge.

Report every cycle, not just the shortest. Overlapping cycles that share an edge often collapse
together when that shared edge is cut, and that is only visible with the full set.

## Cycle taxonomy and treatment

| Shape | Path | Root cause, usually | Treatment |
| --- | --- | --- | --- |
| Self-loop | A→A | Agent subscribed to a channel it writes to | Self-echo filter on every identity field |
| Ping-pong | A→B→A | Two agents both responding to each other's output | Make one direction terminal, or per-pair window |
| Ring | A→B→C→A | Nobody owned the whole graph | Graph-wide breaker plus cut the weakest edge |
| Diamond return | A→{B,C}→D→A | Supervisor callback drawn as a send | Convert the return to a durable write the supervisor reads |
| Conditional cycle | Only closes on error | Error handler notifies a peer that retries | Make the error path terminal; escalate to a human, not a peer |

The last row is the nastiest, because the graph is acyclic in the happy path and cyclic exactly when
something is already going wrong. Always trace the graph twice — once for success paths, once with
every error handler treated as a live edge.

## Choosing which edge to cut

When a cycle must be broken, cut the edge that is:

1. **Status-carrying rather than decision-carrying.** A status update can become a read; a decision
   cannot.
2. **Lowest fan-in at its destination.** Cutting it disturbs the fewest other paths.
3. **Convertible to a durable write.** A supervisor reading task state is strictly better than a worker
   pushing to a supervisor, because the read cannot amplify.
4. **Not on the error path.** Cutting an error edge tends to make failures silent, which trades a loop
   for an outage nobody notices.

Record the rejected alternatives. A cycle that gets broken at a different edge six months later, with
no memory of why this one was chosen, reintroduces the original problem.

## When a cycle is genuinely required

Some supervisor and negotiation patterns need a return edge. When removal is rejected:

- Bound it with **both** limiters, not just the per-pair one.
- Require the return edge to be **idempotent**, so a replayed message is a no-op rather than a new turn.
- Add a **hop counter or depth budget** to the message itself and drop at the ceiling. This is the only
  defence that bounds a loop structurally rather than by rate.
- Record the decision, the reason, and the budget. An undocumented deliberate cycle is indistinguishable
  from a bug at 3am.
