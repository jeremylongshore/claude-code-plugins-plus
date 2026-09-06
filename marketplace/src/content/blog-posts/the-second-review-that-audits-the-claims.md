---
title: "Auditing Written Claims Against Their Artifacts"
description: "A second review pass checks written claims against the artifacts they cite. It repaired about twenty statements of fact in records already treated as done."
date: "2026-09-05"
tags: ["security", "testing", "architecture", "ai-agents", "typescript"]
featured: false
canonical: "https://startaitools.com/posts/the-second-review-that-audits-the-claims/"
---
Code review asks whether the decision was correct. It almost never asks whether
the paragraph describing the decision is accurate. On 2026-09-05 I watched that
gap open in two places with nothing in common, neither language nor reviewer: a
multi-tenant SaaS built under a heavy evidence discipline, and a stack of
contract drafts with no software in them at all. The two records had reached
different stages. The `intent-longbox` records had been through a dispatched review and
in some cases a ratification. The legal packet had passed only its author, who
committed it as a finished deliverable with `[COUNSEL:]` markers still in the
text. Both were carrying claims that were false.

Roughly twenty statements of fact got repaired across that one day. Nine in one
commit, eight in another, one security claim withdrawn after a reviewer measured
it false, and one use of the word "proved" downgraded to the rung its evidence
actually reached. The count runs per false claim rather than per place it was
written, so the withdrawn security claim counts once even though several sites in
the record carried it, and the downgrade counts once across two register rows. Every one of those records had already been read by a
reviewer, and in two cases had already been ratified.

The thesis I came out with: a review that only checks decisions leaves the
prose ungated, and the prose is what everyone downstream cites.

## Two review lanes, and only one of them reads sentences

The `intent-longbox` repo runs work through what I call the two-lens cannon. Two
named reviewer agents take a change from different value systems, currently
`security-auditor` and `martin-kleppmann-reviewer`, and each returns a verdict.
Alongside them sit two narrower jobs: a gate auditor, whose mandate is the
record rather than the code, and an invariant reviewer, which checks that the
system's stated invariants still hold. On some changes a MiniMax adversarial
review runs on top of that.

The day's volume was real. On main, 2026-09-05 changed 191 files, 42,385 lines
added and 1,433 deleted, across 33 commits and seven merged pull requests (#88
to #94). The features were substantial on
their own. The seven merged that day:

| PR | Diff | What landed |
|----|------|-------------|
| #90 | +11645/-865 | PostgreSQL row-level security with transaction-local tenant context, plus property tests |
| #94 | +9916/-330 | The first factor and the privileged-session shape |
| #92 | +8981/-81 | A Longbox-origin predicate so a staff session outside a break-glass grant is visible |
| #88 | +9557/-86 | Least-privilege organization and location RBAC, trustworthy actor audit |
| #93 | +663/-23 | N:1 authorization decisions under an idempotent replay, refusing the dedup key |
| #89 | +543/-158 | `noPropertyAccessFromIndexSignature` turned on |
| #91 | +1223/-109 | The causal reference persisted on two tables |

Two more pieces the day leaned on had merged the night before: TOTP and recovery
codes for owner and support roles in #82, and connector OAuth with least scopes
and uninstall revocation in #87.

None of those features is the story. The story is the five commits that followed
them, each one repairing a written record that the first review had already
cleared.

## Nine fact repairs from one gate audit

Commit `2173407` carries the plainest version of the split, and it took two
lanes to get there. The gate auditor returned NOT-READY. Every decision item in
the record passed. Six statements of fact did not. The invariant reviewer, run
against the same head, returned PASS-WITH-NOTES and found three more.

```
gate audit verdict:        NOT-READY
  decision items:          all verified as recorded
  fact repairs:            6
  scope:                   paperwork only, no ruling moved

invariant re-verification: PASS-WITH-NOTES
  further fact repairs:    3
```

Read that verdict twice. The engineering was right. The document describing the
engineering could not be cited. The six repairs:

1. A test file held 21 cases, and the record said 18. That pushed the bead's
   unit total from 34 to 37, and two separate registers were carrying 34.
2. Three beads described as "proposed, not yet created" already existed. The
   session had filed them while the branch was in flight, so every "proposed"
   hedge got replaced with a real id.
3. A section asserted an act that had not happened. The phrase "is corrected
   accordingly" was false at the moment someone typed it, because nothing had
   done the correcting. It is true now by a different route, with the who and
   the when named.
4. A residual finding, R9, had no owning bead. A residual nobody owns is a
   residual nobody reads twice.
5. A citation of the three-layers quote pointed at `034:447` when the quote sits
   at `034:449`. The repair also named `034:445-447` separately, which is the
   K1 trigger, a different quote entirely.
6. A register cell claimed a status its evidence did not support, reading
   VERIFIED by execution across both halves when only the refusing half had
   been run.

```
citation repair, three-layers quote
  before: 034:447
  after:  034:449

cited separately by the same repair
  034:445-447   (the K1 trigger)
```

That fifth one looks like a typo and is not. A line-number citation is a promise
that a reader who follows it lands on the sentence being quoted. Land two lines
short and the reader meets a different claim, then either loses trust in the
record or keeps reading and inherits the wrong quote. The commit describes the
gap as one line; the diff shows two. I have left both readings visible rather
than picking the tidier one.

### The three the invariant lane found

The gate auditor reads the record against its own citations. The invariant
reviewer reads the record against the running system, which is why the three it
turned up are heavier.

Section 6.3 of the record claimed there was nothing to repair. That was false by
exactly one. A UNIQUE index on `shop.shopify_domain`, added by migration 026 back
when `shop` carried no policy, is precisely the shape section 6.3 warns about,
and the bead inherited it the moment it policied `shop`. Reproduced under shop
B's tenant context, claiming a domain that shop A already holds returns 23505,
and claiming an unused one returns UPDATE 1. Two different answers, decided by a
row the caller is not allowed to see. That is a one-bit oracle on which Shopify
stores are Longbox customers. It is latent today because no route writes
`shopify_domain`, and latent is a schedule rather than a verdict. Section 6.3 now
names it and routes it to an existing bead's class instead of inventing a new
rule for it.

The second was a new residual, R10. The domain-claim check in `receiveCallback`
has a TOCTOU window: the SELECT runs in one scope and the write runs in a
separate transaction under the shop's tenant context, so two concurrent installs
of the same store can both pass the check. The commit named the window and took
neither of the two obvious fixes. Moving the check inside the transaction puts
it under a tenant context where other shops' rows are invisible, so it would
fail open, which is worse than the bug. Running the whole install in the service
scope needs exactly the policy widening the security lens had just punished. The
durable fix is the serialization point the database already owns, which is the
unique index above, so the residual sits and waits for the bead that covers it.

The third repair is the one I would put in front of anyone who thinks this lane
is pedantry. A register cell's reproduction command named a GUC that does not
exist. `longbox.service_scope` names the SQL function, while the setting itself is
called `longbox.service`. Run verbatim, the cell returned zero rows.

```
in the record:  current_setting('longbox.service_scope')   ->  0 rows
the real GUC:   current_setting('longbox.service')
```

The commit called it the worst kind of evidence, because it looks checkable and
appears to disprove the claim it supports. A reader who runs it sees an empty
result and concludes the invariant is broken. A reader who does not run it
carries a citation that has never worked. The cell now reproduces standalone.

Six plus three is the nine. The commit message carries a line I have kept: a
record whose decisions are right and whose facts are wrong is still a record
that cannot be cited. The same shape showed up earlier this year in [Every Verdict Carries the Scope It Actually Ran](https://startaitools.com/posts/a-green-result-only-covers-what-it-ran/), where a green result was reporting on less than it claimed.

## Eight statements, and two ratified records a rebase damaged

Commit `af3aa84` came out of the next gate re-audit. Same shape of verdict:
NOT-READY on paperwork only, every ruling verified as recorded and built,
nothing moved a decision. Eight repairs this time, and two of them were damage
rather than drift.

The first piece of damage was in an append log. A rebase reconciliation filter
had silently dropped a ratified entry belonging to a different branch, because
that row's own text happened to mention the current branch's bead id. The filter
matched on a substring and took a stranger's row with it. An append log that
loses an entry has stopped being an append log.

The repair restored the row verbatim from `origin/main` and showed the
restoration accounted for by a set diff rather than by an eyeball:

```
git show origin/main:000-docs/016-OD-REGS-longbox-source-register.md > /tmp/main-appends
# extract entry ids from both sides, compare as sets
# result: all 32 of main's appends present and accounted for on the branch
```

Restoring the text is the easy half. Showing that nothing else went missing in
the same filter pass is the half that makes the record citable again, and a set
diff is the cheapest instrument that does it.

The second piece of damage was subtler. A ratified record's table cell had been
edited in place instead of appended to. The amendment was correct. Its form was
illegal. In a record with a version and a ratification date, an in-place edit
rewrites what a reader who cited the earlier version thought they were citing.
The repair restored main's sentence verbatim and appended the new pin after it.
The record's version number did not move, because the amendment is the same
amendment; only its shape changed.

Six of the other repairs in that commit:

- A heading cited a stale commit while the section above it had already been
  corrected to a newer one.
- A section called a commit "the main this branch is rebased onto" when it was
  the merge base, and main was a different commit.
- Two sections routed a decision row to a bead as OPEN when the bead was CLOSED.
  The fix restated it as a closed ruling rather than deleting the row, so a
  reader who met the property in the earlier version is not left hunting a fix
  that is never coming.
- A claim of "all twelve invariants proved against a database" was really eleven
  of fourteen. The record had counted twelve invariants; the real total is
  fourteen, of which eleven carry database evidence. One of the remaining three
  is an architecture gate and two are unit-level, so the word "all" was claiming
  database evidence that three invariants do not have.
- "Gains five cases" was seven.
- Every duration quoted as a measured property (24 hours, 15 minutes, 30 days)
  was relabeled a provisional constant.

That last one is the one I would defend hardest. The real argument in that
section is that each act outlives the session that created it, and that argument
holds whatever the constants are. Quoting the numbers as durations stated a
property nobody had measured, and it invited a future reader to treat a config
value as a finding.

## The claim a reviewer measured false

Commit `177cd3d` is the centerpiece, because a reviewer did not argue about
wording. It ran the thing.

The record claimed that a tighter per-identifier sign-in rate bucket "closes" a
user-enumeration timing oracle, and that a known address and an unknown address
"start refusing fast at the same attempt count". The reviewer measured minute
two, the first minute after the bucket refills, which is exactly when a warmed
known address falls out of it. The result:

```
warmed KNOWN address:     6 to 16 ms on 4 of 5 attempts
UNKNOWN address:          about 600 ms on 5 of 5 attempts
```

An attacker with a stopwatch can read that difference through any amount of
network jitter. The claim was false.

The root cause was a window mismatch nobody had costed:

```
per-identifier sign-in rate bucket:  refills every 1 minute
LOCKOUT_WINDOW_MS:                   15 minutes
```

A warmed known address drops out of the one-minute bucket and falls back onto
its fifteen-minute lockout path roughly fourteen times an hour, and every time
it does, it answers cheap. What the tighter bucket actually bought was a rate
cut on the oracle, from roughly 120 observations a minute down to roughly 5. A
rate cut is a real security improvement. It is a different improvement from the
one the record advertised.

One section of that record, R10, had said this correctly the whole time:
"narrows the window rather than closing the class". Six other sites in the
record and the source contradicted it, or eight, depending on which part of the
commit you read: it counts six and its own list names eight. All of them were
corrected to match the one
that was right, which is a satisfying shape for a repair: the truth was already
in the building, outnumbered.

### Adding nothing was the right call

No fix shipped with that correction, and the decision was deliberate.

Closing the class means hashing while blocked, so that a refused known address
pays the same CPU as an unknown one. A ratified document in this system refuses
that, and the bead doing the correction has no mandate to reopen it.

The alternative that lost was widening the lockout window to match the bucket.
That is a two-line change and it would have made the two paths agree. It also
changes another ratified document's delay from inside a bead that never argued
for touching it. Buying an accurate sentence by quietly editing somebody else's
ratified constant is a worse trade than living with a narrowed residual.

So what stands is a narrowed residual with its own row in the register. Someone
will pick that row up with a mandate that covers it.

There was a bookkeeping consequence too. Two claim ids, C47 and C48, collided:
another bead's C47 and C48 had landed on main in parallel, so the register
briefly carried four rows under two ids. The ratified ids kept their numbers,
this branch's renumbered to C49 and C50, and the renumbering went into an append
rather than happening quietly. A claim id that moves without a note is a
citation nobody can follow backwards.

## Downgrading "proved" to the rung the artifact reached

Commit `2e7f3d2` came from a MiniMax adversarial review that pressed on a single
word in two register rows. It was written the night before and landed on main in
the first hour of the 5th, through PR #89. Both rows said a compiler-flag-flip result was "proved able to fail",
while linking only to CI runs where the flag was on.

That is a structural argument that flipping the flag would produce the outcome.
The record presented it as a recording of an actual flip. The governing rule in this repo is
narrow and useful: a claim may not use a stronger rung than the artifact it
cites.

What the CI runs actually prove is that the flag is set in the repository's
config, and that the dot access is what the compiler refuses, since a bracket
twin compiles right beside it. They do not prove that the flag is the reason.
Establishing that requires flipping it, which is a local reproduction, so it got
recorded as one, with the command that produces it:

```
sed -i 's/"noPropertyAccessFromIndexSignature": true/"noPropertyAccessFromIndexSignature": false/' tsconfig.json
pnpm vitest run tests/contract/signature-fields-are-not-dot-accessed.test.ts
# 2 failed | 4 passed
```

I re-ran that at the commit rather than quoting the earlier session's output,
which matters more than it sounds: a number copied forward from a previous
session is a claim about a commit nobody checked. The two that fail are
`is set in the repository's tsconfig` (12 ms) and `refuses fields.series in
src/services with TS4111` (13.68 s). `tsconfig.json` was restored afterwards,
which is why it is absent from the diff.

### The seventh CI case that lost

The obvious response is to add a seventh CI case that does the flip
automatically. I turned it down for three reasons, and the third one decided it.

A CI version has to either mutate the repository's own `tsconfig.json`, which is
the same hazard another bead forbids one level up for `src/`, and this time on
the file every other test is judged by; or compile against a modified copy of
the config, which is exactly what an existing case named `compiles the scratch
tree against the repository's own tsconfig` exists to rule out. Both options
undo a guarantee that is already paid for.

The third reason is cost. It would add a fourth `tsc` spawn to a test file the
same reviewer had already flagged as the second slowest in the unit lane. A
written command a reader can re-run in thirty seconds beats a permanent tax on
every run for the same evidence.

### The reviewer got audited back

The same MiniMax review produced a finding I declined, and the arithmetic is
worth showing because it is the honest half of this whole approach.

It called a per-directory split HIGH severity, on the grounds that
"65 + 9 + 63 = 77, which is 60 short of 137".

```
python3 -c 'print(65+9+63)'
137
```

The split reconciles exactly. The row stands as written. An adversarial reviewer
is a model pointed at the work with a narrow mandate, and it is fallible in
exactly the way everything else in the loop is fallible. The layer only earns
its keep if its findings go through the same evidence test the work does. Every
finding it raised that day got checked; one of them did not survive.

## The review that was drafted instead of dispatched

Commit `91cd7c5`, which landed in PR #94, fixed the worst process defect of the day, and it is the one I
would have caught last if the gate auditor had not been looking.

A record had shipped at v1.0.0 with a section containing two lens positions that
the builder had written himself. The cannon was never dispatched. Somebody wrote
what a reviewer might plausibly say instead of asking the reviewer. A draft of
what a reviewer might say is not a review, and the record had been carrying it
as one.

When the real cannon ran, both lenses returned ACCEPT-WITH-CHANGES, the gate
auditor returned NOT-READY on facts, and the invariant reviewer returned
PASS-WITH-NOTES. Two of the findings were enforcement rather than prose, so the
record went to a minor version instead of a patch, because v1.0.0 had been wrong
about two things rather than merely silent on them.

Three real behavior changes fell out of that dispatch.

**A privileged sign-in now revokes the person's other live privileged chains at
that shop.** A session expiry bounds the session, and it does not bound the acts
the session performed. Using the provisional constants as they stand today, a
copied cookie mints a 24-hour invitation and a 15-minute enrollment code, and it
leaves a permanent owner membership and a 30-day device credential standing
after the session dies. Eviction is now an act
the owner can perform. It is scoped to the same shop rather than sweeping a
person globally, because the wider version would unilaterally widen another
record's cross-tenant scope union from inside a bead that never argued for it.

**Naming a second owner on an invitation now re-presents the second factor in
the request**, and refuses without it. Of every act in that flow, this is the one
whose damage no expiry bounds: a second owner outlives every session, every
token, and every device. It was extracted into its own transaction rather than
folded into the existing call, so the lock-order lint reads the two anchors
truthfully instead of being dodged by a merge.

**The sign-in path took its own provisional per-identifier rate constant instead
of borrowing the device class constant.** The measurement that forced it:

```
same-class refusals, sign-in path:   5.7 ms
device-class refusals:               449 ms
```

Constant in the body and not on the clock. On an anonymous internet-facing
route, that is an enumeration oracle for who works at which shop.

## The same failure outside software

The second instance came out of `intent-os`, in commit `03e22943`: an
independent adversarial audit of the partner-network legal packet. Six read-only
streams plus eighteen scenarios, 177 findings, 25 root-cause groups.

The v0.1 packet it audited had been drafted the same day, six and a half hours
earlier, at commit `bedc4d4e` (14:30 to 21:02). No reviewer had touched it. The
`[COUNSEL:]` markers in its own text say as much, and no `legal/review/`
directory existed until the audit commit created one. It had passed its author
and been committed as a finished deliverable, which is a weaker gate than the
Longbox records cleared and a more common one.

What the second pass found:

- Every document named the wrong legal entity.
- A signature block was pre-filled with a non-office title, for a 50/50 LLC with
  no signing authority on file.
- A flow-down was promised with no artifact behind it, and the packet
  contradicted itself on precedence.
- Liability caps were left blank in a way that reads as an absence of any cap.
- The packet contradicted the firm's own doctrine on classification.
- The practitioner layer carried nothing on security, data, AI, or open source.
- It was about to be signed by a person in Germany, on a contractor form scoped
  to US individuals only.

Every one of those is a false or missing statement of fact in a document that
was already being treated as done. There is no compiler anywhere near it, and there is
no test suite either. The failure mode transferred cleanly anyway.

The remediation is the part I would reuse. Every executable draft got a
canonical banner at the top and above every signature row: DRAFT, ATTORNEY
REVIEW REQUIRED, NOT APPROVED FOR SIGNATURE OR USE. Signer and title were left
blank pending an open decision. The contractor form was renamed from "member" to
"practitioner", restructured as a master agreement plus Work Orders, and held to
US individuals only.

The discipline that makes that audit trustworthy is what it refused to do. Every
legal judgment was registered as an open decision (D-01 through D-22) or a
counsel question (C-01 through C-28) rather than being decided. The audit's
authority stops where counsel's begins, and an audit that quietly rules on a
question it has no standing to rule on has become the thing it was checking.

It also shipped an enforcement script:

```
ci/validate-legal-packet.sh     # 12 checks
pnpm run validate:legal-packet  # wired into CI
```

Twelve checks, plus a planted-fixture self-test: every check has to be shown to
fire against a deliberately broken fixture before it counts. A check that has
never failed is a check nobody has tested.

Source integrity was handled the same way. The files under `legal/sources/` were
hash-matched against a manifest recorded before any edit, and 14 of 14 matched.

Two facts were explicitly marked provisional and not verified in that session:
the Alabama statutory texts, because Justia returned 403 and the legislature
site was unresolvable; and the Secretary of State record, because it sits behind
an interactive form. Marking a fact as not verified, by name, with the reason,
is the same discipline as the rest of the day pointed inward. The alternative is
a packet where verified and assumed look identical to the next reader.

## What the second lane cost

Numbers first, because this approach is not free and the bill should be visible.

| Measure, 2026-09-05 | What the first review produced | What the second lane added |
|---|---|---|
| Statements of fact repaired | 0 | about 20 |
| Rulings changed by the repairs | 0 | 0 |
| Security claims withdrawn as measured false | 0 | 1 |
| Evidence rungs downgraded | 0 | 1 |
| Ratified records restored after rebase damage | 0 | 2 |
| Reviewer findings declined on arithmetic | 0 | 1 |

The zero in the second row is the interesting one. Not one repair moved a
decision. Every ruling the first review cleared survived the second review
intact. The code was right the whole time, and the record describing it was
wrong in about twenty places.

The other number, 42,385 lines added, deserves an honest reading too. A large fraction of
that day's diff is records about records: registers, appends, gate audits,
residual rows, claim ids. That is the cost line.

## Tradeoffs

**This is expensive, and the expense is mostly wall-clock.** Every one of those
four repair commits came after the feature work was already merged-quality. The
gate auditor, the invariant reviewer, the two lenses, and the adversarial pass
each add a round trip, and each audit cycle can come back NOT-READY on paperwork
that changes no behavior. A team optimizing for cycle time will hate this and
will be right to.

**The audit trail is load-bearing, which means it is also a liability.** Append
logs, ratified records, claim ids, and version pins only work if nothing edits
them in place. Two of the day's repairs exist because a routine rebase damaged
records nobody was watching. The heavier the paper trail, the more surface a
mechanical operation has to corrupt, and rebases do not read your conventions.

**Fabricating a review is a live failure mode.** Commit `91cd7c5` exists because
somebody drafted the two lens positions instead of dispatching the cannon, and
that got all the way to v1.0.0. A process with a named review step invites
someone to satisfy the step's shape without paying its cost. The only defense I
have found is a separate auditor whose mandate includes checking that the review
happened at all.

**The adversarial layer is itself unreliable.** The same MiniMax review that
produced the best correction of the day also produced a HIGH-severity finding
built on 65 + 9 + 63 = 77. If you take these findings on authority you will
degrade your record instead of improving it. Every finding has to be checked,
which means the second lane needs a third posture: audit the auditor.

The scope where this pays is narrow. If nobody outside the session that wrote a
record ever cites it, the second lane buys nothing. The value shows up once a
claim in a document becomes an input to a later decision, a partner
conversation, a security posture, or a signature. Most weekend projects have no
record with that property. A multi-tenant system holding other people's data
does, and so does a stack of contracts about to be signed.

## Where a claims audit sits in wider practice

The idea is not new anywhere except in how it gets applied to AI-generated work.
The analogy I keep reaching for is accounting reconciliation, where the entry
and the check on the entry are deliberately different jobs. I have no artifact
that says other fields adopted the split for the reason I am describing, so take
that as a shape I find useful rather than as evidence from the day.

Software collapsed those into one step called code review, and it mostly worked
while humans wrote both the code and the paragraph describing it, because the
person typing the paragraph had just done the work and remembered the details.

That property weakens when an agent writes the paragraph. Agents produce fluent,
plausible, well-structured prose about work at a rate no human reviewer reads
carefully, and the failure mode is specific: the sentence is shaped exactly like
a true sentence. "All twelve invariants proved against a database" reads
identically to the accurate version. Only a pass that opens the artifact and
counts can tell them apart.

The rung rule generalizes better than anything else I took from the day. Every
claim sits at a rung: argued, implied, observed, measured, proved. Every artifact
supports some rung. Enforcing that the claim never outranks its artifact is a
mechanical check a reviewer can perform without domain expertise, and it caught
both the "proved" downgrade and the oracle withdrawal.

## Also shipped

`intent-os` also carried a second track that day, ten commits of an eleven-commit
day. A gateway
business-plan vision cluster was filed at v0.1 verbatim with five gap beads,
advanced to v0.2 (`dbd3cd9f`, `8cccfbe0`), then put through a council review (`ac07d920`): 13 thinker-canon seats plus
an SI practice partner and a hyperscaler partner-program director, over five
adversarially re-verified research packets, with dissent preserved and nine
follow-on beads opened. The recorded rationale for the shape was that a workflow
of 26 agents beat a single synthesis pass, because the seats had to argue
independently before any dissent existed to preserve.

`intent-solutions-landing` took one field-notes content commit.
`claude-code-plugins` took seven commits on main: three dependency chores, a
marketplace-sync fix for Windows, two plugin feature commits, and the
dual-publish of the field note.

## Frequently asked questions

### Can code review find false claims in the documentation?

Code review checks whether the decisions are right. It almost never checks whether the paragraph describing the decision is accurate. A review that only checks decisions leaves the prose ungated, and the prose is what everyone downstream cites. In the 2026-09-05 example, roughly twenty statements of fact got repaired across the day, and every ruling the first review cleared survived the second review intact.

### What is an evidence rung?

Every claim sits at a rung (argued, implied, observed, measured, proved) and every artifact supports some rung. The rule is that a claim may not use a stronger rung than the artifact it cites. It is a mechanical check a reviewer can perform without domain expertise. On 2026-09-05 one claim moved from "proved able to fail" to a recorded local reproduction, because the artifact was a CI run with the flag already on, which never showed the flag was the reason.

### When should you run a second review lane for claims?

The scope where this pays is narrow. If nobody outside the session that wrote a record ever cites it, the second lane buys nothing. The value shows up once a claim in a document becomes an input to a later decision, a partner conversation, a security posture, or a signature. A multi-tenant system holding other people's data qualifies, and so does a stack of contracts about to be signed.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {"@type": "Question", "name": "Can code review find false claims in the documentation?", "acceptedAnswer": {"@type": "Answer", "text": "Code review checks whether the decisions are right. It almost never checks whether the paragraph describing the decision is accurate. A review that only checks decisions leaves the prose ungated, and the prose is what everyone downstream cites. In the 2026-09-05 example, roughly twenty statements of fact got repaired across the day, and every ruling the first review cleared survived the second review intact."}},
    {"@type": "Question", "name": "What is an evidence rung?", "acceptedAnswer": {"@type": "Answer", "text": "Every claim sits at a rung (argued, implied, observed, measured, proved) and every artifact supports some rung. The rule is that a claim may not use a stronger rung than the artifact it cites. It is a mechanical check a reviewer can perform without domain expertise. On 2026-09-05 one claim moved from proved able to fail to a recorded local reproduction, because the artifact was a CI run with the flag already on, which never showed the flag was the reason."}},
    {"@type": "Question", "name": "When should you run a second review lane for claims?", "acceptedAnswer": {"@type": "Answer", "text": "The scope where this pays is narrow. If nobody outside the session that wrote a record ever cites it, the second lane buys nothing. The value shows up once a claim in a document becomes an input to a later decision, a partner conversation, a security posture, or a signature. A multi-tenant system holding other people's data qualifies, and so does a stack of contracts about to be signed."}}
  ]
}
</script>

## Related Posts

- [Wrong-Mode Green Is Not a Gate](https://startaitools.com/posts/wrong-mode-green-is-not-a-gate/)
- [Every Check Should Report What It Did Not Look At](https://startaitools.com/posts/the-lane-that-reviewed-nothing/)
- [Bind the Receipt to the Commit It Installed](https://startaitools.com/posts/the-commit-the-test-actually-installed/)
