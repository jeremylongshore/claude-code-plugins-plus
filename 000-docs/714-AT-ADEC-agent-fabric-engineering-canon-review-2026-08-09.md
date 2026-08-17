# Agent Communication Fabric — engineering canon review

**Date:** 2026-08-09 · **Panel:** 6 named-thinker reviewers · **Status:** advisory input to the open calls in `713 § 5`
**Inputs:** `712-RL-RSRC` (research), `713-AT-DECR` (ISEDC business council)
**Verbatim reviews:** `~/.claude/skills/exec-decision-council/sessions/2026-08-09-agent-communication-fabric/canon/{kleppmann,lamport,armstrong,hickey,thompson,beck}.md`
**Bead:** `claude-f3ql`

---

## 1. Why this panel exists

The ISEDC council (`713`) is seven **business** value-systems — CFO, GC, CMO, CSO, CISO, CTO, VP-DevRel. It adjudicated licensing, positioning, scope, and cost, and it caught four factual defects in the research. What it could not do is stress the *engineering* claims, because a durable-messaging-with-identity substrate is a distributed-systems artifact and none of those seats is a distributed-systems seat.

This is that panel: Kleppmann (consistency, append-only substrate), Lamport (ordering, coordination), Armstrong (failure modes, supervision), Hickey (data model, simple-vs-easy), Thompson (composability, minimalism), Beck (test discipline, feedback loops).

**It found five substantive defects the business council missed, and it answered the operator's open question about adversarial composition with unusual convergence.**

## 2. New defects — none of these appear in 712 or 713

### D1 — The journal and the queue are two independently-written stores with no reconciliation invariant (Kleppmann)

712 § 8 makes the queue the system of record. § A.1 praises CCSC's hash-chained journal. **Neither document says whether message-delivery events are written into the journal at all, or live only in the queue.** If they are siblings, we inherit the dual-write problem `mcp_agent_mail` papers over with a compensating delete-and-re-raise (`app.py:5607-5627`) — which itself leaves a torn window if the process dies between the delete and the re-raise propagating.

> "Don't compensate, derive. The mutable view (queue, cursors, delivery state) should be a deterministic materialization of the append-only log, not a second independently-written store that needs reconciliation after the fact."

CCSC's own code already states the correct split — `supervisor.ts:93-95`: *"the on-disk session file stays the source of truth… the lease fences writes, it does not replace the file."*

**Kleppmann rates this above identity as most-costly-to-recover-from**, on the grounds that a wrong identity model is a known singular error with a known fix, whereas this produces the bug class that looks fine for months and then disagrees in a one-in-ten-thousand crash window with no protocol-level answer for which store is right.

### D2 — The delivery-ack boundary is undefined (Armstrong)

The design says fsync-before-ack and kernel-released `flock`. **It never says whether the cursor advances on *read* or on *consumer-ack-of-processing*.**

> "If cursor-advance is synchronous with the read call returning bytes, this is at-most-once delivery wearing at-least-once clothing. A reading process that crashes after the flock read but before it actually uses the message… has a permanently vanished message with the cursor already past it — and that produces **no error signal at all**, the exact failure class the design elsewhere refuses to accept."

This is the design's own central promise ("a message sent to an agent that is asleep still arrives") failing under precisely the crash the document was written to survive. **No row in § 9's test plan covers it.** Armstrong rates it most-costly.

### D3 — The fencing token needs a durable *check*, not just a durable *counter* (Lamport)

713 § Q0 binds "durable monotonic fencing token" as a v1 blocker. Lamport's sharpening: that phrase is doing double duty.

> "If this ships with a durable counter but an in-memory acceptance check, the system will pass every test that exercises 'the old holder crashed cleanly' and fail exactly once, at scale, when the storage layer itself restarts mid-contention."

Minimal correct construction: persist the counter, CAS-increment it under `BEGIN IMMEDIATE`, fsync before telling the new holder it won, **and** have the storage layer reject `token < max_accepted_token_for_R` where that maximum is read from durable state on every check. The etcd-lease / ZooKeeper-zxid / Raft-term pattern.

Kleppmann independently confirmed the underlying flaw from source: `supervisor.ts:89` mints from a **process-monotonic** counter, which resets on restart, so a restarted supervisor can mint a token ≤ one already granted. Split-brain by omission.

### D4 — Cross-machine ordering is undefined, and `flock` over NFS reintroduces the silent failure (Kleppmann)

`flock` is advisory, single-host, kernel-scoped. It gives a genuine total order on one machine. The V1 roadmap item "cross-machine over SSH" breaks that the moment there is more than one serialization point, and ULID gives approximate wall-clock order, not happens-before.

> "'The readers are LLMs, keep it greppable' is a legitimate reason to keep the serialization format flat — it is not a legitimate reason to skip a causality primitive, because those are orthogonal axes. A hybrid-logical-clock component is still one small token on one greppable line."

Separately: `flock` over NFS has decades of inconsistent-to-absent support, so two readers on two NFS clients can each believe they hold an exclusive lock — *the exact "no error signal at all" failure `beb`'s design was written to make impossible, silently reintroduced by deployment topology.*

### D5 — `principal_auth` as a closed enum is a distributed migration waiting to happen (Hickey)

713 § Q4 reserves `principal_auth` as an enum (`ssh-forcecommand` | `peercred` | `unauthenticated-local`).

> "A field whose value tells a consumer how to interpret another field is a discriminated union wearing a string costume, and a closed enum on a signed, unversioned envelope means every new auth mechanism is a distributed migration — every verifier on every machine has to learn the new tag simultaneously or silently mis-trust messages tagged with it."

Fix: open, namespaced string; push verification logic into a lookup table external to the envelope, versioned separately. The envelope stays dumb data.

**Also flagged (Lamport):** no **no-duplicate-delivery** invariant exists. Resolver rungs 1 (live push) and 2 (enqueue + doorbell) are not mutually exclusive in time — a peer can go live→disconnected mid-push and get both.

## 3. The operator's question: agents composed of adversarial sub-agents

Asked because the pattern demonstrably worked — a 7-seat council found four defects in a document marked `[VERIFIED]` with line citations. **All six reviewers answered, and they converge on the same three-part answer.**

**(a) It does not belong in the transport. Unanimous.**

- **Thompson:** "Mail moves a byte-capped line from a name to a name. Whether five sub-agents argued before one of them called `send` is not the fabric's business, any more than sendmail needs to know whether the human writing the letter argued with themselves first." He notes the council needed *zero* fabric primitives to do its work — if the fabric grows consensus or voting primitives, that is the same creep as leases and delegation lifecycle.
- **Kleppmann:** it should be **invisible to the bus** — state-machine replication collapsing multiple writers to one. The composite's coordinator holds the credential; deliberation happens below the addressing boundary. Channel-derived identity already gives this.
- **Hickey:** a message stays a **value** no matter how many disagreeing sub-agents produced it. It goes wrong "the instant a consumer's *routing* or the substrate's *delivery behavior* branches on whether dissent is present — that smuggles judgment into the transport."
- **Armstrong:** clean split — good for irreversible decisions, bad for the send path.

**(b) But there is one real thing, and it must be decided now.**

Kleppmann and Lamport arrived at it independently, from different directions.

- **Kleppmann:** if contestedness should be first-class evidence, that is a **payload-schema** decision, not a substrate one — a dissent record is a sibling event in the same hash chain, linked by `correlation_id`, pointing at contested events by their content-addressed hash. No BFT, no voting protocol. But it needs a reserved slot **now**, for exactly the reason `principal_auth` was reserved: slots cannot be retrofitted onto a live signed chain.
- **Lamport, sharper:** this is **not** strictly above the messaging layer, because it touches the identity invariant at one precise point.

  > "Channel-derived identity proves *who* signed, never *whether the signer's internal process actually decided* what it signed. A composite that authenticates cleanly can still emit a message its own quorum never approved — a tamper-evident record of an internal fabrication."

  His fix: reserve a `decision_provenance` field (`unanimous` / `quorum-N-of-M` / `designated-writer-with-veto` / `unspecified`) from commit one, even null in v1.

**(c) As a *practice* rather than an architecture, it is cheap and should be routinized. (Beck)**

> "It's a testing strategy, not an architecture, and conflating the two is the risk… Right now it worked because it was novel and high-stakes. Left as a one-off ceremony, the next research doc gets written by one voice again and the next defect ships quiet."

His cheap routine version is not "convene seven seats." It is: **require independent re-verification of every `[VERIFIED]` citation by someone who did not write it** — even a single adversarial subagent whose only job is "re-read the cited line; does the code match the English sentence, yes or no."

**Verdict.** The instinct is right and the placement was wrong. Adversarial composition belongs *inside an agent* (below the addressing boundary) or *outside the fabric* (as a user of it) — never in the transport. One envelope slot, reserved now, is the entire substrate-level consequence.

## 4. Where the canon contradicts the business council

| Topic | ISEDC (713) | Canon | Resolution |
|---|---|---|---|
| Most-costly decision | Identity envelope (3 of 7 seats) | Split: Kleppmann → journal/queue reconciliation; Armstrong → delivery-ack boundary; Lamport → fencing check-side durability; Thompson/Hickey/Beck → identity envelope | Identity keeps plurality across **both** panels; D1–D3 join it as unretrofittable-class |
| Mesh in v1 | 7/7 no mesh | Agree — but reject the reasoning. "Citing ExaDev against durable queues confuses a bad implementation with a bad category" (CTO seat, restated by Armstrong) | Conclusion stands, rationale replaced |
| Protocol surfaces | ACP admitted 5/7; A2A off-by-default; herdr v1.x | Thompson and Hickey both go **further than the CFO**: cut ACP, A2A, herdr, OTel, capability discovery, delegation lifecycle from v0 entirely | Canon strengthens the CFO dissent |
| Formal methods | not considered | Lamport: spec **only** the resolver + lease + cursor interleaving. Explicitly refuses ceremony elsewhere — wire framing is a fuzzing problem, C0/C1 is property-based testing, notify-never-advances is a type-system invariant "more correct than a TLA+ proof of a rule the type checker already makes vacuously true" | Adopt the narrow scope |
| Build vs probe | CFO dissent 1/7 | Beck sequences it **regardless of who wins Q0**: ship the probe first, and have the probe specifically exercise the four reserved envelope fields | See § 5 |

## 5. The synthesis that dissolves the Q0 deadlock

The CFO's "build nothing yet" and the near-unanimous "the identity envelope is the one unretrofittable thing" look opposed. Beck's sequencing shows they are not:

> **Ship the probe first — and make the probe exercise the envelope shape.**

Cheap to be wrong about mesh-vs-queue, catastrophic to be wrong about the envelope. A ~200-line probe that sends and receives while carrying `principal` / `principal_auth` / `key_id` / `sig` (plus, per § 3, a `decision_provenance` slot) tests the only decision that cannot be reversed, costs almost nothing, satisfies the demand gate, and is compatible with every Q0 position on the table.

Thompson's floor, for scope: **three verbs — `send`, `recv`, `ack`.** "If you can't explain a fourth verb in one sentence without the word 'future,' cut it."

## 6. Actions this panel adds

1. **Decide the journal↔queue relationship before any code.** One must be a deterministic materialization of the other. Write the reconciliation invariant down. (D1)
2. **Define and test the delivery-ack boundary** — read-advances-cursor vs consumer-ack-advances-cursor. Currently unspecified and untested. (D2)
3. **Extend the v1 fencing-token blocker to the check side**, not just the counter. (D3)
4. **State cross-machine ordering as undefined** until an HLC lands, and test `flock` under the actual deployment filesystem. (D4)
5. **Make `principal_auth` an open namespaced string**, not a closed enum. (D5)
6. **Reserve a decision-provenance / dissent slot in v0.** (§ 3b)
7. **Add a no-duplicate-delivery invariant** and dedup by ULID at the recipient. (Lamport)
8. **Fix `lib.ts:1821`** — the comment still claims "C0/C1" over a C0-only regex. Beck: don't just fix the comment, write the test that should have existed, watch it fail, then decide honestly whether to implement C1 or narrow the promise. *A comment that describes behaviour no test enforces is a promise nobody's keeping.*
9. **Split § 9's test plan** into "port an existing test" (cheap — `checkChannel` already has one) versus "author net-new" (multi-process harness, offline-then-return, injection corpus), and estimate separately so the expensive novel ones don't get quietly dropped.
10. **Add a `cloc`-vs-claimed-LOC doc-lint** and a mutation-cite requirement on `[VERIFIED]` tags: `[VERIFIED: path:line, mutation: <test that dies>]`. Downgrade to `[INFERENCE]` at write time when no killing test can be cited. (Beck — this is the mechanical fix for defects 1 and 3 in `713 § 2`.)
11. **Scope `doctor` read-only.** Thompson: if it writes `authorized_keys`, "you've built a broker with extra steps," and nobody has asked who audits the tool that writes the trust anchor.

## 7. Provenance

Six reviews, run independently, each given the same architecture brief and the operator's question. Verbatim text preserved at the path in the header. Claims attributed to CCSC source (`supervisor.ts:89`, `:93-95`, `lib.ts:1821`) were verified by more than one reviewer independently.
