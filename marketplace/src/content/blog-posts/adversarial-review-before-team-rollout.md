---
title: "Adversarial Review: The Six Lenses That Halted a Rollout"
description: "A six-lens adversarial review checked a team knowledge system against live state, broke three shipped assumptions, and gated 18 risks to halt the rollout."
date: "2026-07-09"
tags: ["ai-agents", "security", "architecture", "authentication", "claude-code"]
featured: false
---
"We shipped the safety work" is a feeling, not a fact. Before you hand a shared, governed system to a team, the only thing that converts that feeling into the truth is a structured adversarial review that verifies claims against live state — not against the design doc, and not against the diff.

On 2026-07-09 that review ran against an internal team knowledge system being prepared to open to six people all at once. It validated two judgment calls, broke three, and produced a list of eighteen real risks the plan had not named. The verdict: do not go all-at-once, and do not email anyone a token, until the first gate clears.

That halt was the correct output. This is the story of the method that produced it, the three assumptions it demolished, and the fixes that shipped the same day — every one of which enforces a single boundary: **the model proposes; the deterministic system owns identity, trust, and durable state.**

## The system, in one paragraph

The subject is a "second brain": a governed team knowledge base. Content is captured, run through a deterministic govern pipeline, and — if it survives the gates — promoted into durable memory. Every state change writes a receipt into an append-only, hash-chained ledger, so the store is tamper-evident: you can recompute the chain and detect any row that was altered out of band. Two surfaces front it. A private, tailnet-bound HTTP API is the control plane — it holds the write-gate, the tenant guard, and the audit-actor stamp. A Claude Code plugin (an MCP server) is how people actually talk to it from their editor. Six teammates were about to get access: two admins, four members.

## What shipped, and why it wasn't enough

A "safety before people" pass had already landed. It was real work, not theater: bearer tokens were hashed at rest instead of stored as plaintext; per-user tokens were minted so each teammate carried a distinct identity; an onboarding runbook was written; several hardening items were verified against the running service. On paper, the box marked "make it safe for a team" was checked.

The instinct to stop there is the trap. A safety pass tells you what you *did*. It does not tell you what you *have* — the residual risk, the assumptions you smuggled in, the interactions between a fix and the rest of the system. Those only surface when someone hostile to the plan goes and looks at the live thing. So before flipping the switch, that is exactly what happened.

## The review that verified against live state

An adversarial review checks claims against the running system, not the design doc and not the diff. Independent reviewers each inspect the live service, its databases, and its deployment through a different lens — security, operations, reliability, integrity, rollout, threat model — so an assumption that is locally true but globally false has nowhere to hide.

Six independent engineer agents ran in parallel on the Fable model. Each got the same design brief and one distinct lens. The instruction that made the difference was not "review the plan." It was **verify against real code and live state**: read the repos, query the live databases, recompute the hash chain yourself, check org membership yourself, inspect the running service unit yourself. A review that only reads a diff can confirm the diff does what it says. It cannot catch a claim that is locally true and globally false — and all three of the broken assumptions were exactly that shape.

| Lens | Question it was forced to answer |
|------|----------------------------------|
| Data integrity & correctness | Recompute every hash. Does the store actually verify? Can any path write a durable row without its receipt? |
| Security & secrets | Where do the still-live secrets exist, in every location, including backups? |
| Deployment & operations | What does the service actually run from? What happens on crash-restart or rollback? |
| Reliability & concurrency | Who can write concurrently, and what lock — if any — serializes them? |
| Rollout completeness & teammate UX | What does a real member experience on a bad token, a dead API, or off-network? |
| Adversarial / threat model | Assume a leaked member token. What can it forge, escalate, or clear? |

Independence is the other half of the method, and it is not optional. One reviewer with a six-item checklist shares one set of blind spots across all six items — if their mental model of the system is wrong in a given place, it is wrong for every lens they apply. Six agents that never see each other's work cannot collude into a shared assumption. The security lens does not know the reliability lens exists, so it has no reason to defer to it, and that is exactly why one of them looked at the backups while another looked at the write lock. Deduplication happens *after* independent discovery, never before.

The integrity lens recomputed all 2,186 candidate content hashes rather than trusting the "verified" label. The security lens enumerated every place a live secret's plaintext could exist rather than trusting "we hashed the file."

That is the entire discipline: independent lenses, each grounded in the running system. It cost six agent-runs and the humility to let them contradict the plan. It was worth it, because it broke three things everyone believed were done.

## What the review left standing

Before the breakage, credit where the design earned it — because a review that only ever confirms your fears is as miscalibrated as one that only ever flatters you. The review's two headline validations were calls of *restraint*: it endorsed holding the riskiest feature — the auto-govern path that drives broken call #3 below — as design-only rather than rushing it into the rollout, and it blessed the sequencing that checked migration safety before restarting the live service. In both cases, not shipping yet was the correct instinct.

Two foundational design bets also held up under every lens, and they are worth naming because the fixes below lean on them.

The first is **per-user token identities**. Minting a distinct token per teammate, rather than a shared team secret, looked like extra onboarding friction at the time. It is what makes the entire server-side intake override (below) possible: every request carries a resolvable actor, so the server has something to re-derive trust and authorship *from*. A shared secret would have left it nothing to distinguish — you cannot own identity you cannot tell apart. The friction bought the security model.

The second is the **append-only, hash-chained receipt ledger** itself. The integrity lens recomputed the whole chain and confirmed it does what it claims: alter any promoted row out of band and the recomputation detects it. The atomicity fix that follows does not replace that design — it *protects* it, by closing the one window where a durable row could exist without its receipt. A weaker audit design would have had nothing worth protecting.

Naming what held is not politeness. It is calibration: it tells you the review's "broken" verdicts are signal, not a reviewer reflexively torching everything to look thorough.

## Three calls the review broke

This is the spine of the story. Two shipped decisions survived scrutiny; three did not — and the three that fell are the transferable lessons, because each was a locally reasonable call that the live state proved wrong.

### Broken call #1: hashing in place is not rotation

The safety pass hashed the existing tokens *in place*. It kept the same secret values and just stored their hashes instead of their plaintext, specifically to avoid the churn of re-issuing tokens to everyone. Locally, that reasoning is sound: the credential file no longer holds plaintext, so a read of that file at rest yields nothing usable.

The security lens went and looked at *every* place those secret values lived. Retained encrypted backups — one local, one off-host, and at least one target with no retention limit — already held the **plaintext** of those same still-live secrets, captured before the hashing change. Hashing the file protected it going forward, at rest, in one location. It did nothing for a secret whose plaintext sits in a backup you can restore.

> Re-hashing a value you have already exposed is not protection. Retiring an exposed secret requires **credential rotation** — a genuinely new value — **plus purging the exposure**. If the plaintext still exists anywhere you can restore from, the old secret is live, and hashing its current home is a false sense of safety.

The fix was not "hash harder." It was rotate the tokens to new values and treat the pre-hash backups as compromised. Hash-at-rest was necessary; it was not sufficient, and believing it was sufficient is precisely the failure a live-state review exists to catch.

### Broken call #2: local mode is a single-writer design

To let the system's founder query the brain from any editor session, the plugin was enabled in user-scope *local mode*. Convenient, and locally reasonable: one person, their own machine, direct access. The reliability lens asked the question the plan never did — what does local mode actually *do*?

Local mode runs in-process as owner/admin. It does not go through the HTTP API. That means it bypasses the entire control plane: the write-gate, the tenant guard, and the audit-actor stamp all live on the API surface, and local mode is a side door around all three. Worse, "any editor session" is not one writer. Up to roughly eleven concurrent interactive sessions became **unlocked writers** — none of them taking the single-writer file lock that the nightly cron jobs depend on to serialize their writes.

The concrete failure: a backup taken mid-write, with no lock held, can capture a torn state. Restore it and the brain's own tamper-evidence machinery reports **TAMPER DETECTED** — not because anyone tampered with anything, but because the hash chain was snapshotted between two writes. The safety mechanism fires on its own operator.

> A design built for one writer and one user silently becomes a concurrency-and-authorization surface the instant you make it multi-session. The reach goal — "query from anywhere" — was right. Routing it *around* the single writer was wrong. It should have gone *through* the API's single writer, inheriting the write-gate, the tenant guard, the audit stamp, and the lock.

### Broken call #3: deleting durable rows needs a data-classification check and an all-consumers review

A planned feature — the next thing on the roadmap — would DELETE candidate proposals after they were governed. The reasoning read cleanly if you looked only at the write path: the candidate has been governed, its outcome is recorded, so the row is spent; delete it to keep the table lean.

The integrity lens read the *data-classification doc* and *every consumer* of that table, not just the code that does the delete. The candidates table is documented as insert-only, immutable, and a **non-reproducible source of truth**. Three consumers depend on that:

1. **Provenance.** Remote captures write nowhere else. The candidate row is the *only* copy of what was seen. Delete it and the provenance back-link points at nothing.
2. **The human-review queue** depends on flagged and rejected candidates *staying in place* so a person can adjudicate them later. Delete-on-govern empties the queue out from under the reviewer.
3. **Re-ingest idempotency.** The nightly re-ingest path dedupes against that table. Delete a governed row and the next night re-ingests it as new, re-rejects it, and deletes it again — a permanent nightly re-ingest/re-reject loop.

The plan proposed a "second run is a no-op" test to prove safety. That test would have **passed while missing the loop entirely**, because it seeded the *table* rather than the upstream spool files — so the dedupe it exercised was not the dedupe the loop breaks. A green test against the wrong fixture is worse than no test; it launders the bug.

> A design that deletes durable rows must be checked against the data-classification doc *and* every consumer of that data — review queue, re-ingest idempotency, provenance back-links — not just the code path that performs the write. "Is this row still needed by the thing that wrote it?" is the wrong question. "Who else reads this row, and what is the only copy of it?" is the right one.

## The 18-risk register, gated

Deduplicated across the six engineers, the findings collapsed to eighteen distinct risks. Where two lenses hit the same issue, severity was taken as the **max** across engineers — you do not average a "critical" with a "medium" and call it "high." A flat wall of eighteen findings is not actionable; it is a demoralizing to-do list with no critical path. So the register was **gated** into three tiers, and the gating is what made it usable.

| Gate | Meaning | Representative risks |
|------|---------|----------------------|
| **Gate 0** | Must clear *before any teammate onboards or any token email is sent* | Rotate exposed secrets + purge backups; hash tokens at rest; immutable deploy with lockout guard; durable revoke-by-actor |
| **Gate 1** | Must clear *before the auto-govern feature ships* | Server-side candidate-intake override; atomic promotion; the delete-on-govern redesign |
| **Gate 2** | Hardening — soon, but non-blocking | Additional plugin observability; expiry policy; ancillary rate limits |

Gating converts "here are eighteen problems" into "here is the one blocking set standing between you and a safe rollout." It also makes the halt legible: the verdict "do not go all-at-once and do not email tokens until Gate 0 clears" is a statement about a *specific* tier, not a vague unease. No emails were sent. No teammate was onboarded. That was the correct state to be in, and the gate model is what let everyone agree on it in one sentence.

## The fixes that shipped

Gate 0 and the first Gate 1 items landed the same day. Each is a small, well-reasoned change. Shown below are the ones where the design decision is the point.

### Tokens hashed at rest, with a safe fallback

The token registry now accepts an already-salted `scrypt$salt$hash` value in a record's token field and uses it verbatim, so the credential file can store hashes instead of plaintext bearer secrets. scrypt is a deliberately expensive, memory-hard key-derivation function — a stolen hash is costly to brute-force, unlike a bare SHA-256 digest. Plaintext still works, for operator convenience — and a value that merely *looks* hashed but has non-hex segments falls back to being hashed as plaintext rather than being trusted as a hash.

```js
// A registry record's token field may already be a hashed secret.
// Accept a well-formed scrypt$salt$hash verbatim; otherwise hash it as plaintext.
function resolveToken(field) {
  const parts = field.split('$');
  const isHashed =
    parts.length === 3 &&
    parts[0] === 'scrypt' &&
    /^[0-9a-f]+$/.test(parts[1]) &&   // salt segment must be hex
    /^[0-9a-f]+$/.test(parts[2]);     // hash segment must be hex
  return isHashed ? field : hashToken(field);
}
```

Necessary — but, per broken call #1, **not sufficient on its own.** This fix protects the file at rest. It does nothing about the plaintext already sitting in backups. Rotation plus purge was the other half, and shipping the hash without the rotation would have been the exact false-safety the review flagged. The tension is the lesson: a real fix and an incomplete fix can look identical in a diff.

### Immutable, tag-pinned deploy with a lockout floor-guard and auto-rollback

The service had been running from a *mutable working checkout*. That is three latent failures at once: any rebuild in that repo mutates the live service, a crash-restart can relaunch from a torn or feature-branch build, and there is no immutable artifact to roll back *to*. And there was a sharper trap hiding inside it. Rolling the checkout back *past* the token-hashing change would rebuild the pre-hash registry, which would then double-hash the now-hashed credential file — and lock out all six users at once.

The fix builds immutable, self-contained release directories behind an atomic `current` symlink, and refuses to deploy anything older than the migration that would cause the lockout.

```bash
# Floor guard: never deploy a commit that predates the lockout-inducing token-hash migration.
FLOOR_TAG="token-hash-floor"
if ! git merge-base --is-ancestor "$FLOOR_TAG" "$TARGET_REF"; then
  echo "REFUSE: $TARGET_REF predates $FLOOR_TAG — deploying it would rebuild the" \
       "pre-hash registry, double-hash the credential file, and lock out every user."
  exit 1
fi

# Build an immutable, self-contained release dir: no .git, frozen deps, built once.
REL="/opt/brain/releases/$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short "$TARGET_REF")"
mkdir -p "$REL"
git archive "$TARGET_REF" | tar -x -C "$REL"
( cd "$REL" && install_frozen_deps && build )

# Lockout preflight: the built artifact MUST contain the hash parser, or it will double-hash.
grep -q 'scrypt' "$REL/dist/token-registry.js" || { echo "REFUSE: hash parser missing from build"; exit 1; }

PREV_REL="$(readlink -f /opt/brain/current || true)"   # capture the current target FIRST, for rollback
ln -sfn "$REL" /opt/brain/current                       # atomic promotion via symlink swap
systemctl restart brain-api
```

Then a health gate with auto-rollback, so a bad release un-ships itself:

```bash
if ! curl -fsS --max-time 5 "$HEALTH_ENDPOINT" >/dev/null; then
  echo "post-restart health gate failed — rolling back to previous release"
  ln -sfn "$PREV_REL" /opt/brain/current
  systemctl restart brain-api
  exit 1
fi
```

The `git merge-base --is-ancestor <floor-tag> <target>` check is a **named, transferable ops pattern**: a *floor guard against a lockout-inducing rollback*. Any time a migration makes older code actively dangerous to redeploy — not just wrong, but destructive — pin a floor tag at the migration and refuse to deploy beneath it. Immutability gives you a rollback target; the floor guard makes sure the rollback target can't itself be the disaster.

### Durable revoke-by-actor with a persisted revocation list

Tokens had no expiry, and the only revoke path was in-memory — lost on restart. And now that tokens are hashed at rest, an admin no longer holds any teammate's plaintext bearer secret, so "revoke by value" is impossible for the realistic incident: *a teammate's laptop was stolen.* You cannot revoke a secret you deliberately no longer possess.

So revocation keys off the **audit identity the token already carries**, and persists to an append-only file read at boot.

```js
// Tokens are hashed at rest, so no admin holds a plaintext bearer secret to revoke by value.
// Revoke by the audit identity the token carries; persist it so it survives a restart.
function revokeByActor(actor, reason) {
  revoked.add(actor);                                   // in-memory guard, effective immediately
  appendFileSync(REVOCATION_LIST,                       // append-only ban-list: durable + audit trail
    JSON.stringify({ actor, reason, at: new Date().toISOString() }) + '\n');
}

// At boot, replay the ban-list so a revoked actor stays revoked across restarts.
function loadRevocations() {
  for (const line of readLines(REVOCATION_LIST)) revoked.add(JSON.parse(line).actor);
}
```

The design choice worth naming: a **separate append-only ban-list file** was chosen over mutating the source token file on every incident. Rewriting the credential store during an active incident — the highest-stress moment — is how you fat-finger a lockout. Append-only is safer than rewrite, and it doubles as a revocation audit trail: who was revoked, when, and why, in order, forever.

### Server-side candidate-intake override with a provenance receipt

This is the clearest instance of the whole thesis. In team mode the *client* built the entire candidate object, and the server trusted it verbatim. That means a member — or a leaked member token — could self-assert `trustLevel: 'high'` to clear a minimum-trust gate, forge the `author`, set an arbitrary `tenant`, and clear the "potential secret" flag on their own content. And intake wrote no audit event, so none of it left a trace.

The fix: the server re-derives the fields that decide trust, authorship, and tenancy from the **bearer-token identity**, ignoring the body for exactly those fields, and writes a provenance receipt on every proposal.

```js
// TEAM MODE: the client builds the whole candidate, but the server trusts NONE of it
// for the fields that decide trust, authorship, and tenancy. Re-derive from the token.
function intake(reqBody, auth) {
  const candidate = {
    ...reqBody,
    trustLevel:      auth.trustLevel,          // NOT reqBody — client cannot self-assert 'high'
    author:          auth.actor,               // NOT reqBody — no forging provenance
    tenant:          auth.tenant,              // NOT reqBody — no cross-tenant writes
    potentialSecret: scan(reqBody.content),    // server re-scans; client cannot clear the flag
  };
  writeReceipt('candidate.intake', candidate, auth);   // every proposal leaves a receipt
  return store(candidate);
}
```

Two alternatives were considered and rejected:

- **Reject any candidate that asserts non-default fields.** Brittle. The client always sends a full body, including those fields, on every legitimate proposal — so this would reject every real submission, not just malicious ones.
- **Trim the client body to a minimal DTO at the boundary.** A bigger cross-surface contract change — new schema, new client code, new failure modes — for *no additional safety*, because the override already neutralizes every one of those fields. More work, more blast radius, same result.

The override wins because it is the smallest change that makes the guarantee true: the client proposes a candidate; the server decides what that candidate *is*. Identity, trust, and tenant are server-owned. That sentence is the whole security model in miniature.

### Atomic promotion

The promotion path — moving a governed candidate into durable memory — did roughly five separate autocommits: a supersession update and its event, the memory insert, the graph-edge links, and the "promoted" receipt. A kill mid-promote — the compile cron hitting its timeout, or a plain SIGTERM — could leave a promoted memory with **no "promoted" receipt**. A durable row without its audit receipt violates the product's core promise — every state change has a receipt — and it never self-heals, because nothing re-derives a receipt for a row that already exists.

The fix wraps the whole write block in one [`BEGIN IMMEDIATE`](https://www.sqlite.org/lang_transaction.html) transaction — SQLite's mode for taking the write lock up front instead of deferring it to the first write statement — so the memory and its receipt commit together or not at all.

```js
// Memory row + its "promoted" receipt must commit atomically, or the
// append-only-receipts promise breaks and never self-heals.
function promote(candidateId, auth) {
  const db = this.getDb();               // read-only getter over the shared connection
  db.exec('BEGIN IMMEDIATE');
  try {
    supersedePrior(candidateId);         // supersession update + its event
    const memId = insertMemory(candidateId);
    linkGraphEdges(memId);
    writeReceipt('promoted', memId, auth);   // nested audit inserts degrade to SAVEPOINTs here
    db.exec('COMMIT');
  } catch (e) {
    db.exec('ROLLBACK');
    throw e;
  }
}
```

Two design details carry their own rationale. First, the shared DB connection was exposed via a **read-only getter** rather than threading a new `db` handle through the constructor — so every existing caller's signature stays unchanged, keeping the blast radius small. Second, the nested audit inserts each open their own `BEGIN IMMEDIATE`; inside the outer transaction those degrade to **savepoints**, which preserves the audit chain's anti-fork guarantee rather than fighting it. And the negative control matters: with the outer transaction bypassed, the atomicity tests *fail* — the memory is orphaned — and with it in place they pass. The test catches the real regression, not a tautology that would pass either way.

### Plugin hardening, shipped alongside

The plugin got its own Gate 0 work, because it is the surface six people will actually touch:

- **Local-mode writers now take the same single-writer [`flock(2)`](https://man7.org/linux/man-pages/man2/flock.2.html) advisory lock the cron jobs use** — a real kernel `flock(2)` on the same file, so it interoperates with the cron's `flock(1)`. A PID-lockfile library was rejected precisely because it shares no kernel lock with `flock(1)`; two "locks" that don't see each other are not a lock.

```js
// Local-mode writers take the SAME kernel lock the cron holds (flock(2) <-> flock(1)).
const fd = openSync(LOCK_PATH, 'r');
flockSync(fd, 'ex');
try {
  await writeToBrain(payload);
} finally {
  flockSync(fd, 'un');
}
```

- **Team-mode search now surfaces errors instead of swallowing them into an empty result.** Previously a bad token, a dead API, and being off-network all rendered identically as "the brain found nothing." For a tool whose entire value is *trust by receipts*, silently returning empty on failure is the worst possible failure mode — it teaches the user the brain has no answer when the truth is it never got the question.
- **A new read-only `brain_status` probe** answers "am I connected, in which mode, and do I have a token?" — the three things a confused teammate needs before they can even ask for help.
- **The plugin got its first unit test, lint, and CI gate — *before* it received the review's riskiest changes.** You do not hand new safety-critical code to a surface with no test wall.

## The tradeoffs

None of this was free, and pretending otherwise would undercut the point.

- **The rollout got slower.** All-at-once for six people became "one person proves the path end-to-end, Gate 0 clears, then six." That is the right call, but it is a real delay against a plan that was a switch-flip away from done.
- **There is more operational machinery to maintain now.** Immutable release directories, a floor tag to keep current, a revocation-list file to back up, a health gate and rollback path. Every one of those is a thing that can itself break or drift. Determinism and durability cost surface area; the bet is that the surface is cheaper than the incidents it prevents.
- **Hash-at-rest was a false sense of security until rotation happened.** This is the honest one. For a window, the credential file looked safe while the live secrets sat in plaintext in backups. Anyone reading only the "we hashed the tokens" line would have believed the job was done. The review is the only reason that gap was named before it was a breach instead of after.
- **The review itself has a cost, and it is not just compute.** Six independent agent-runs is the cheap part. The expensive part is the discipline to accept a halt the day before launch — to let a review overrule a plan that felt finished, hold the line on "no tokens emailed until Gate 0 clears," and eat the schedule slip. A review you are unwilling to act on is theater with a receipt. The value was realized only because the verdict was allowed to stop the rollout.

## The boundary underneath all of it

Read the Gate 0 and Gate 1 fixes together and they are not five unrelated patches. They are five expressions of one boundary:

- The server derives identity, trust, and tenant from the token, **not** the request body. *(intake override)*
- Receipts commit atomically with the data they describe. *(atomic promotion)*
- Deploys are immutable artifacts, **not** a mutable checkout. *(tag-pinned release + floor guard)*
- Revocation is durable and keyed to identity, **not** to a plaintext value you no longer hold. *(revoke-by-actor)*
- Credentials live at rest as hashes the system re-derives, **not** as plaintext a disk or a backup can hand back. *(hash-at-rest, paired with rotation)*

**The model — or the client, or the convenient side door — proposes. The deterministic system owns identity, trust, and durable state.** Every place the old design let the proposer also decide what its proposal *was*, the review found a hole, and every fix closed it by moving that decision back to the deterministic side. That boundary is not specific to this system. It is the load-bearing wall of any governed AI system where something upstream is allowed to be creative and something downstream has to be trustworthy.

And there is a standing invariant the review left behind, worth more than any single fix: all-at-once is the right rollout *for six people* — but only after one person has walked the entire path end-to-end and Gate 0 is clear. Confidence at team scale is earned by one proof at individual scale, not asserted by a completed checklist.

The meta-lesson is the method itself. Six independent lenses, each forced to **verify against live state** rather than read the design, are what caught "the backup still holds the plaintext" and "local mode runs as admin, in-process, unlocked." A review that only read the diff would have blessed all three broken calls — because in the diff, all three looked done. The difference between shipping the safety work and *knowing* you shipped it is whether someone went and looked at the running thing with hostile intent, before the people arrived.

## Related Posts

- [The Moat Is the Trust Layer: Turning a Local-RAG App into a BYOK Document-Intelligence Platform](/posts/the-moat-is-the-trust-layer-nexus-byok-rag/) — where adversarially reviewing the *graders* caught the eval suite lying green.
- [Every Safety Gate Has a Failure Direction](/posts/every-safety-gate-has-a-failure-direction/) — why one gate crashes fail-closed on bad data while a swallowed error lets another pass fail-open.
- [Noise-Robust LLM-Judge Evals: Don't Sign a Coin Flip](/posts/noise-robust-signed-llm-judge-evals/) — on not trusting a measurement you haven't proven can go red.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Adversarial Review: The Six Lenses That Halted a Rollout",
  "description": "A six-lens adversarial review checked a team knowledge system against live state, broke three shipped assumptions, and gated 18 risks to halt the rollout.",
  "author": { "@type": "Person", "name": "Jeremy Longshore" },
  "publisher": {
    "@type": "Organization",
    "name": "Start AI Tools",
    "logo": { "@type": "ImageObject", "url": "https://startaitools.com/favicon.ico" }
  },
  "url": "https://startaitools.com/posts/adversarial-review-before-team-rollout/",
  "datePublished": "2026-07-09",
  "keywords": "adversarial review, security review, governed AI system, team rollout, authentication, claude-code",
  "articleSection": "Architecture"
}
</script>
