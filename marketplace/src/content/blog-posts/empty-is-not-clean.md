---
title: "Empty Is Not Clean: Five Fail-Open Bugs in an AI Agent"
description: "One fail-open bug, five disguises: empty args, an empty log, a missing property, a sheared chain, an unset scope. When there's nothing to check, fail closed."
date: "2026-07-13"
tags: ["ai-agents", "typescript", "authentication", "architecture", "claude-code", "testing"]
featured: false
---
A policy said `deny` anything under `/etc`. A Bash call read `/etc/shadow` and came back `{allow, rule: 'trust-bash'}`. No human in the loop. The deny rule was still there, still first in the list, still scoped exactly the way an operator would write it. It just never fired.

Two cold-contributor reviewers reproduced it independently on this policy:

```typescript
const policy = [
  { effect: 'deny', tool: 'Bash', pathPrefix: '/etc' },
  { effect: 'auto_approve', tool: 'Bash', rule: 'trust-bash' },
];
// Bash → /etc/shadow  ⇒  { allow: true, rule: 'trust-bash' }
```

The gate is the policy engine inside `claude-code-slack-channel` — an MCP-mediated Slack agent whose whole reason to exist is that it can *prove* what a tool did: a signed, offline-verifiable audit journal plus a per-tool-call policy engine. If the deny rule can be walked past, none of that matters. This is the story of that bug, and the four other bugs that turned out to be the same bug wearing different clothes.

## The pattern: absence read as success

Every one of these had the same shape — the same fail-open bug. When the data a check needs to make its decision was *absent*, the check defaulted to the permissive answer — allow, pass, clean, covers-all — instead of the safe one. A missing argument. An empty log. A property that isn't there. A chain link that got sheared off. A scope field left unset.

The principle that closes all five: **when a check has nothing to check, it must fail closed.** Default-deny, not default-allow. Absence is not a green light. Absence is the alarm.

## Disguise 1 — empty args made the deny rule vanish

The engine's `evaluate()` takes a `ToolCall` and walks the rules. `matchApplies()` decides whether a rule's scope — `pathPrefix`, `argEquals` — matches the call. The exploit lived one level up, in the *only* production caller.

The MCP `permission_request` handler in `server.ts` never receives structured tool arguments. It gets an `input_preview` string for display and nothing else. So it built the call like this:

```typescript
// server.ts — the sole production caller
const call: ToolCall = {
  tool: req.tool_name,
  input: {},                      // ← no structured args available here
};
const decision = policy.evaluate(call);
```

A `deny` scoped by `pathPrefix: '/etc'` asks: does `input.path` start with `/etc`? Against `input: {}` the answer is no. `matchApplies()` returns no-match, the deny is *silently skipped*, and the next broad `auto_approve` for Bash swallows the call. The scoped rule the operator wrote was invisible precisely because the engine couldn't see what it was scoped on.

The fix does not try to reconstruct the missing args. It can't — they aren't there. Instead, when the gate cannot see the input a scoped `deny`/`require_approval` rule needs, it stops trusting the fall-through:

```typescript
// If a scoped deny/require rule COULD apply but we lack the input
// to know, escalate to a human instead of falling through to auto_approve.
if (scopedRuleNeedsInput && inputIsUnavailable(call)) {
  return { allow: false, escalate: 'require_approval', reason: 'input-unavailable' };
}
```

Not knowing whether a deny applies is treated as "it might" — and "it might deny" routes to a human, never to auto-approve.

## Disguise 2 — a wiped audit log verified clean

The journal's verifier walks the event chain and reports broken links. Zero events means zero broken links. So an *empty* `audit.log` verified clean. An attacker who truncates the entire log to nothing gets a green check — the strongest possible signal from the weakest possible file.

The fix is a floor. `--min-events N` makes verification *fail* when the log holds fewer events than expected:

```
$ verify audit.log --min-events 500
FAIL: expected ≥500 events, found 0
```

Zero is no longer "clean." Zero is "someone deleted the evidence." The flag parser is deliberately fail-closed too: a malformed value throws rather than silently disabling the floor, because a floor you can turn off by fat-fingering it is not a floor. (A later fix routed a space-form negative like `--v2-floor-seq -5` to the value validator so it throws the accurate "must be a non-negative integer" instead of a misleading "missing value.")

## Disguise 3 — a prototype key past a truthiness gate, and the near-miss

Channel-policy reads (`access.channels[id]`) were scattered across seven call sites with inconsistent guards. A bare index read inherits `Object.prototype` members: ask for the channel `'constructor'` or `'toString'` and you get back a truthy function that never belonged to anyone's config — enough to slip past a truthiness-based gate.

Not exploitable today; Slack channel ids match `[CD][A-Z0-9]+` and never take prototype-key forms. But it's a footgun class, and seven inconsistent guards is seven chances for one to drift wrong. The fix routes every read through one chokepoint that returns a policy only for an *own* property:

```typescript
export function getChannelPolicy(access: Access, id: string): ChannelPolicy | undefined {
  return Object.hasOwn(access.channels, id) ? access.channels[id] : undefined;
}
```

One helper, seven callers, no drift. And this is where a fail-closed refactor nearly shipped a fail-open crash.

`access.channels` is *typed* as always-present. It isn't. An `Access` loaded from disk can arrive without it, and `Object.hasOwn(undefined, id)` **throws**. A Gemini audit flagged it HIGH. The old scattered code used `access.channels?.[id]` — optional chaining that safely returns `undefined` when the object is missing. The refactor, in the name of hardening, would have converted a *defined-safe* absence into a thrown exception on every channel read. Whether an unhandled throw at the gate ends up allowing or denying depends on which handler catches it — and "depends on the handler" is exactly the uncertainty a security gate must not have. Defined behavior became undefined behavior at the one point that has to stay defined.

The guard belongs *inside* the one helper, so it can't be forgotten at any of the seven sites:

```typescript
export function getChannelPolicy(access: Access, id: string): ChannelPolicy | undefined {
  const channels = access.channels;
  return channels && Object.hasOwn(channels, id) ? channels[id] : undefined;
}
```

A fail-closed accessor must fail closed. It must not throw. Same discipline, one recursion deeper — the fix for a fail-open bug has to itself fail closed on *its* missing input.

### Why one chokepoint instead of hardening seven sites?

Hardening each of the seven reads in place would have worked on the day it was written. It also would have created seven independent copies of a subtle guard, and the eighth read — the one added six months from now by someone who copied the *simplest* nearby example — would skip it. A chokepoint is not just less code. It's the only version where the correct behavior is the *default* behavior. You can't call the channel-policy lookup wrong because there's only one way to call it.

## Disguise 4 — a sheared, renumbered chain recomputes clean

The genesis-seq pin from an earlier hardening pass was documented as defeating head-truncation. It does — but only on *signed*, key-verified (v2) chains. On an unsigned v1 chain the links are bare keyless SHA-256:

```
hash = sha256(prevHash + canonicalJson(event))
```

A writer-capable attacker shears the head off, renumbers the survivors so the new first event is `seq=1`, and recomputes every hash forward. No secret is required — the formula is public and the file contains everything it needs. The sheared file verifies clean because it *is* internally consistent. It's a smaller, valid-looking journal that never happened.

The close is two optional verification anchors:

```typescript
verify(log, {
  pinnedGenesisHash: 'a1b2…',  // event[0].prevHash MUST equal this operator-held value
  v2FloorSeq: 1,               // every event at seq ≥ N MUST be v2/signed
});
```

`pinnedGenesisHash` is the key move — and it's a different mechanism from the older genesis-*seq* pin. That earlier pin fixed the sequence number, which a renumbering attacker just recomputes. `pinnedGenesisHash` fixes the first event's `prevHash` against a value the operator captured *outside* the file. When an attacker renumbers the chain, the new first event's `prevHash` no longer matches the pinned value — and there's no way to forge a match, because the attacker can't reach into the operator's out-of-band record to change it. That's also why it holds on an unsigned chain: the protection comes from the anchor being external, not from a key.

### Why not a self-describing anchor?

The obvious instinct is to make the file carry its own anchor — stamp the "true" genesis hash into a header, or sign a manifest of the chain's own metadata. That fails for a reason worth stating plainly: **the only forgery a file can reproduce from itself is one an in-file anchor also validates.** If the attacker can rewrite the chain, the attacker can rewrite any anchor stored alongside it. A self-attested anchor gets forged in the same edit as everything it was supposed to protect. A *signed* in-file manifest is only better if the signing key lives somewhere the attacker can't reach — at which point the key is the out-of-band secret, and you've relocated the external-fact requirement, not removed it. The anchor has to be a fact the attacker *cannot* reproduce — and on an unsigned chain the only such fact is one that was never in the file to begin with.

The tradeoff is honest and belongs in the docs: the anchors are only as strong as the operator's out-of-band capture. A key rotation that forgets to record the new head hash loses the cross-file link. Anchors are opt-in — absent, verification is byte-identical to before. You buy real protection with real operational discipline, and the system says so out loud rather than pretending the file can bootstrap its own trust.

## Disguise 5 — a thread-scoped rule silently covered every thread

`matchSubsetOrEqual()` — the subset check behind both `detectShadowing()` and `checkMonotonicity()` — compared tool, channel, actor, `pathPrefix`, and `argEquals`. It never compared `thread_ts`. So a rule scoped to one Slack thread was treated as a rule covering *every* thread.

```typescript
// before: thread_ts absent from the comparison ⇒ "matches all threads"
function matchSubsetOrEqual(a: Rule, b: Rule): boolean {
  return sameTool(a, b) && sameChannel(a, b)
      && sameActor(a, b) && subsetPath(a, b) && subsetArgs(a, b);
  // thread_ts never checked
}
```

The absent field defaulted to "matches all" when the safe default is "matches none." A narrowly-scoped rule got read as maximally broad — the same failure shape as the deny that ignored `/etc`, one layer up in the analysis code instead of the enforcement path. The fix honors `thread_ts` in the subset check, and an unset scope now correctly covers nothing rather than everything.

## The shape of the fail-open bug

Line them up and it's one bug five times. Empty args → skip the deny. Empty log → verified clean. Missing property → truthy prototype value (plus a thrown exception the fix itself almost added). Sheared chain → recomputes valid. Absent thread scope → covers all threads. Every one defaults to *allow / pass / clean / covers-all* when the discriminating data is missing. The permissive branch is the one that runs when there's nothing to run against.

The fix never changes. Make absence fail closed. A gate that can't see its input escalates to a human. A verifier with too few events fails. An accessor with no property returns `undefined` and doesn't throw. A chain proves itself against a fact it can't forge. A scope with no value covers nothing. Same principle, five layers. The one honest exception is the sheared chain: when the discriminating fact can only live *outside* the file, fail-closed becomes something the operator opts into by capturing that fact out-of-band — and the system says so plainly instead of pretending a file can bootstrap its own trust.

None of these surfaced from writing new code. They surfaced from adversarial review pointed at the load-bearing core: a hardening review of the signed journal, two cold-contributor reviewers who reproduced the `/etc/shadow` walk-past, a Gemini audit that caught the crash-on-absent-channels the *fix* almost introduced. Every one was proven revert-to-red — revert the guard and a test goes red, so the guard is doing work no other line does. The suite sits at ~1304 tests, ~96.6% line / 98.2% function coverage, nine gates green.

| Disguise | What was absent | Permissive default | Fail-closed fix |
|---|---|---|---|
| Empty args | Structured tool input to scope on | Deny rule skipped; `auto_approve` wins | Escalate to a human when a scoped rule lacks its input |
| Wiped audit log | Any events in the file | Empty log verifies clean | Fail below a `--min-events` floor |
| Missing property | An own property on the config | Prototype key returns a truthy function | `Object.hasOwn` chokepoint; return `undefined`, never throw |
| Sheared chain | An out-of-band genesis fact | Renumbered chain recomputes valid | Pin the genesis hash externally; a mismatch fails |
| Unset thread scope | `thread_ts` in the subset check | Rule covers every thread | Compare `thread_ts`; no scope covers none |

## Also shipped

Alongside the fail-open work, a set of transport-contract fixes in the same spirit: start the MCP stdio transport *before* Socket Mode so the protocol handshake never blocks on Slack; route all structured logs to stderr because stdout *is* the MCP channel and one stray log line corrupts the protocol; and extract the socket-start and manifest-identity guards into testable seams. A decision-record spike (ADR-004) settled a build-vs-keep question: this system's job is to *prove* what an agent did — offline, self-hosted, deterministic per tool call — so the signed journal is what matters, not prettier approval cards.

That's the throughline for all of it. Guardrails for an AI agent are not features you add on top — they're the property that lets the agent hold a tool at all. An agent you can trust with `Bash` is one whose deny rule fires even when the caller forgot to pass the arguments. Fail-closed discipline is what earns the trust; empty is not clean.

## Related posts

- [Every Safety Gate Has a Failure Direction](/posts/every-safety-gate-has-a-failure-direction/) — the underlying principle: every gate fails in *some* direction, and you have to choose it on purpose.
- [Adversarial Review Before Team Rollout](/posts/adversarial-review-before-team-rollout/) — all five of these bugs came from pointing hostile reviewers at the core before anyone depended on it.
- [When a Relevance Score Broke the Cite-or-Refuse Gate](/posts/relevance-score-broke-cite-or-refuse-gate/) — another fail-open gate, another case of absence quietly reading as permission.
