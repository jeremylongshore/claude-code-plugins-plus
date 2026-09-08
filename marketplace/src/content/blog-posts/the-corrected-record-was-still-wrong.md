---
title: "The Primary Record Settles What a Derived One Assumed"
description: "A derived record inherits facts from other derived records. Four systems in one day carried a confident wrong fact until a primary source settled it."
date: "2026-09-06"
tags: ["architecture", "governance", "postgres", "data-integrity", "ai-agents", "devops"]
featured: false
canonical: "https://startaitools.com/posts/the-corrected-record-was-still-wrong/"
---
A legal packet had already been corrected once. That is what made the day worth
writing down. The name on the drafts was wrong, somebody caught it, somebody
fixed it against the records we had, and the fixed version was still wrong. On
2026-09-06 the same shape showed up three more times, on systems that share no
code: a homepage publishing three different star counts, a ratified security
record, and a migration linter that counted an index build inside a log
message.

The common mechanism is boring and it costs a lot. A derived record is any
statement of fact produced from another statement of fact rather than from the
thing itself. Repo files describing an entity. An audit summarizing a record. A
grep counting SQL. Each one is cheap to read and confident by default, because
a derived record carries no expiry on its source unless someone builds one in.
Only a primary record settles it: the state filing, the GitHub API, the
governing section, the parsed statement.

## The correction that was itself derived

The legal packet's entity name had been fixed once already, from repo records.
Those repo records had normalized the name at some earlier point, so the
correction inherited the normalization. Commit `da39e57b` says it plainly:

> the audit had corrected the name once from repo records that had normalized
> it; the primary record produced 2026-09-06 shows both earlier forms were wrong
> and the state of formation was an assumption the drafts had baked into
> governing law and forum.

The Certificate of Formation and the IRS EIN record arrived and closed two
standing assumptions as false. A-02, the name spelling: the registered entity is
**IntentSolutions.io LLC**. A-01, the state of formation: Delaware, file
10329498, formed 2025-09-11, registered agent Harvard Business Services.

The name was a find-and-replace. The state of formation cost more, because it
had never been written down as a fact anywhere. It was an assumption, and it had
already propagated into meaning, since the governing-law and forum clauses of
the contract templates were built on top of it. A wrong string is a lint. A
wrong premise underneath a clause is a different category of problem, and no
amount of internal review would have surfaced it, because every document in the
packet agreed with every other document in the packet.

Enforcement shipped with the correction, and the shape of the enforcement
matters more than the value it now accepts. The validator does not check that
the entity string looks plausible. It rejects the two specific forms we now know
are retired:

```bash
$ ci/validate-legal-packet.sh --selftest
[selftest] accepts: IntentSolutions.io LLC ....................... ok
[selftest] rejects: retired form A (pre-normalization) ........... ok
[selftest] rejects: retired form B (repo-normalized) ............. ok
[selftest] 3/3 passed

$ ci/validate-legal-packet.sh
entity string: IntentSolutions.io LLC (43 files checked)
exit 0
```

The retired forms are not printed here for the same reason the selftest labels
them A and B: repeating a wrong name in public copy is how it gets re-derived.
Formation screenshots live outside the repo. The EIN, street address, and phone
never enter it.

## Formation state and governing law are separate questions

The obvious move, once the formation state lands, is to sweep governing law and
forum to Delaware and be done. We did the opposite. Alabama law and Baldwin
County stay in the drafts, flagged as open counsel question C-14.

Formation state and choice of governing law are different questions that happen
to share a word. The business operates in Alabama, the founder is in Alabama,
and the restrictive-covenant analysis (the clause set that actually bites in a
dispute) is an Alabama-law question. Switching the contracts to Delaware because
the certificate says Delaware would be a second derived conclusion stacked on
the first one, produced by exactly the reasoning that caused the original
problem: an inference from a nearby fact, written down with the confidence of a
finding.

The correct output of a primary-record check is a smaller set of facts and a
larger set of explicit questions. C-14 is a question with a name and an owner.
It is unresolved, and it is no longer silently assumed, which is where it sat
yesterday.

## Three star counts, none of them from GitHub

Track two is the company homepage. The 451-line audit of the live
intentsolutions.io found it publishing three contradictory star counts for the
same repository, two of them above the verified figure. None of the three was
read from GitHub. Each was typed into a component from whatever earlier copy
the author had in front of them, and each component agreed with itself, so
[every review the page had passed](https://startaitools.com/posts/the-lane-that-reviewed-nothing/) was
a review of derived numbers against other derived numbers. The same audit found a hero leading with retired Google
infrastructure, five service lines, a booking calendar, and a contact form
posting to an unrouted path.

PR #49 shipped v3.0.0 as the fix: a static Astro rebuild derived from a written
gateway brief, with React and the animation libraries removed, and 17 routes,
30 dead components, 12.5 MB of unreferenced media, and 20 runtime dependencies
deleted. The part that answers the thesis is smaller than the rebuild. Every
figure on the page rendered from `src/data/receipts.json`, which
`scripts/refresh-receipts.mjs` writes from GitHub, tonsofskills.com, skills.sh,
the Lab results page, and the field-notes RSS. Each value carries a
`verified_at`. CI refreshes the file before deploy and fails the build when a
value goes stale:

```js
const MAX_AGE_DAYS = 7;
for (const [key, r] of Object.entries(receipts)) {
  const ageDays = (Date.now() - Date.parse(r.verified_at)) / 86400000;
  if (ageDays > MAX_AGE_DAYS) {
    fail(`${key} verified_at is ${ageDays.toFixed(1)}d old (max ${MAX_AGE_DAYS})`);
  }
}
```

A count with a `verified_at` is still a derived record. The difference is that
it now expires, and the build knows the expiry. A second gate,
`scripts/check-copy.mjs`, failed on retired strings, dollar figures, dashes, and
hand-typed counts, so while it was live the old failure could not be typed back
in.

PR #51 reverted the whole rebuild the same day. The owner's call, verbatim:
"roll back to original please." The zinc theme, the React islands, all 29
routes, the media, the dependencies, and the pre-rebuild CLAUDE.md all came
back, with one merge conflict in the auto-generated CHANGELOG. We took a clean
revert over a partial keep so main matches the last known live state exactly; a
partial keep produces a fourth thing that was never live and never reviewed as
a whole. The audit doc stayed on main, because a revert only removes what the
reverted PR added, and the audit was independently true.

This instance is a variant of the other three, and it is worth saying so. The
brief was executed faithfully. What the revert corrected was not a false fact
but a direction, and the only primary record for the direction is the owner.
The second attempt did not guess at copy again. It put the live page in front
of eight independent reader seats in one Workflow, with a ninth seat for
synthesis, and filed the result as a 455-line review. The verdict was 8 of 8
that the page does not represent the vision and that the fix is mostly
subtraction. The headline vote split 6 to 2, and the merged recommendation
ships both lines, the majority as H1 and the challenger in the eyebrow slot,
because a 6/2 split and an 8/0 agreement are different facts about the copy
and a single recommendation erases the difference. The synthesis escalated two
items to the owner instead of resolving them, one being that several seats had
written founder-biography detail into public copy against a standing
instruction. A panel of readers is another derived record. The escalation is
the step that reached primary.

## A ratified record whose "no bead owed" was false

Track three ran on `intent-longbox`. Seven PRs on multi-tenant isolation
merged the same day (#95 through #101: compound tenant keys, row-level security
as a contracting shape, a single identity door, store-domain claims, membership
policies, self-service second factor, webhook replay defense), and records 060
through 065 were ratified. The compound key from #95 carries its whole
isolation argument in the three lines before the close:

```sql
CREATE TABLE scan_result (
  id          uuid NOT NULL,
  shop_id     uuid NOT NULL REFERENCES shop(id),
  session_id  uuid NOT NULL,
  PRIMARY KEY (id, shop_id),
  FOREIGN KEY (session_id, shop_id)
    REFERENCES scan_session (id, shop_id) ON DELETE CASCADE
);
```

The tenant travels in the composite key, so a foreign key check cannot resolve against
another shop's row even when the application forgets its predicate.

Then the gate audit read record 065 and found its ground false. The record
claimed no follow-up work was owed. The remaining cross-tenant edges were not
actually exempt under record 062 section 4, which is the section the claim
leaned on. Two beads were filed as a result, E03-D37 and E03-D38. D37 then moved
from P3 to P2 because two of the remaining single-column tenant edges were
reproduced as exploitable on head: a device credential revocation planted across
shops, and a global UNIQUE on credential retirement evaluated with row-level
security off.

A ratified record is a derived record. Record 062 section 4 sits closer to
primary, and reading it directly is what broke the claim.

## The linter that counted a sentence

The best small instance of the day came from the Postgres migration lint written to
enforce the 044 index-lock rule. That rule caps how many index builds a single
migration may take a heavy lock for. The lint counted index builds with a text
grep, which meant it counted this:

```plpgsql
-- migration 039, inside a DO block
DO $$
BEGIN
  RAISE NOTICE 'rebuilding: CREATE INDEX on inventory_item may take minutes';
END $$;
```

A string literal inside a log message. The grep read it as a sixth index build
and failed the migration. A count of SQL objects was being derived from prose
about SQL objects, inside the same file.

Invariant review caught it before the lint shipped, and the note went on the
bead so the name-collision lint being added next would avoid inheriting the same
false positive. That bead then absorbed a second rule: `DROP CONSTRAINT` on a
live table takes the same lock declaration the `CREATE INDEX` rule already
demands. Migration 039's eleven ACCESS EXCLUSIVE locks come from `DROP
CONSTRAINT`, and 044 section 9 never reached that statement.

## What it cost

One failure that day was a different shape, a rule you can step around rather
than a wrong fact, and it belongs in the record. One commit went in with
`--no-verify` after four attempts to get the pre-commit hook's unit chain to
finish under a load average above 40. The change was `.beads/issues.jsonl`
only, which no pre-commit stage tests, so the risk on that commit was near
zero. The hole in the discipline is real anyway. A gate you can step around
under load will be stepped around again, and the honest fix is making the hook
cheap enough to always run.

The day ran 6 project-days across 21.75 hours of wall span, with 25
failure-to-fix moments and 7 course-corrections in the session digest. The
`intent-longbox` chain ran on Claude Fable 5.1 across 9 sessions and 967
minutes, with 48 agent dispatches and 35 resumes. That ratio describes the work
better than the turn count does: most of it was dispatching a reviewer and
later resuming it for a verdict. The gate audit that refuted record 065 is one
of those 48. The `claude-code-plugins` thread ran on GPT-5.6 Sol via Codex, and
every one of its five course-corrections was a containment instruction ("read
only: do not edit, push, comment, merge, close") or a demand for a verdict from
evidence already gathered. None corrected a wrong answer. The legal thread ran
on Claude Fable 5.1 across 6 sessions and 1306 minutes, and included one agent
run interrupted mid-flight because I was messaging counsel on LinkedIn in real
time and needed a specific message sent right then.

## Change what the checker keys on

When a checker is wrong, fixing the value is half the job. Change what the
checker keys on.

The legal validator stopped accepting whatever string the repo files agreed on
and started rejecting two named retired forms. The receipts gate stopped
trusting a committed number and started failing on `verified_at` age; it went
out with the revert and is the first thing the second attempt brings back. The
migration lint is being moved off text grep onto parsed statements; that one is
filed on a bead, not shipped. And the site copy stopped being resolved inside
the panel and started being escalated to the owner, with the dissent preserved
on the way up.

Every one of those is the same move: take the authority away from the derived
artifact and give it to something closer to the thing.

## Also shipped

- **intent-os document filing.** `business-plan/gateway/` moved into
  `000-docs/163-PP-gateway-vision/` (files 164 to 171) and `legal/` into
  `000-docs/172-BL-legal-packet/` (files 173 to 214). Two clusters instead of
  one nested folder, because the standard forbids folders within folders. Every
  cross-reference, lint ignore, repo index, CLAUDE.md, README, and
  partner-network cockpit pointer was repointed, and source-form sha256 values
  were verified identical before and after the rename before regenerating the
  manifest. The validator got the same treatment as everything above: re-rooted
  at the cluster and keyed by category codes instead of positional filenames,
  since file position is a derived property that any rename breaks.
- **Five Reddit introduction posts** for r/ClaudeAI, r/SideProject,
  r/vibecoding, r/startups, and r/Entrepreneur, value-first, with posting rules
  (one account, home connection, comment before posting, and links omitted where
  the sub forbids them). Five distinct story posts rather than one generic post
  copied five times, because identical cross-posting is what gets flagged.
- **Legal drafts alongside the entity correction:** a two-member member-managed
  Delaware operating agreement, a customer-facing security statement claiming no
  certifications because we hold none, and a beads epic (`spine-0ce`) with seven
  children, one per purchase, filing, or decision only the owner can execute.
- **omarchy-omatrail-entry**, a frontier survival game in QML and JavaScript,
  over 3,000 lines of rules and views, plus `bin/omatrail-state`, an
  end-to-end harness with save fixtures, and an `evidence/render-matrix`
  carrying per-scene PNGs next to render-proof JSON. A nine-document design
  workbook landed alongside it in omarchy.

## FAQ

### Why does a text grep fail at counting SQL objects?

A grep counts text, not statements. The Postgres migration lint on 2026-09-06
searched for CREATE INDEX and matched a RAISE NOTICE message that described an
index build in prose. It counted that sentence as a sixth index build and
failed the migration. The fix that is filed, and not yet shipped, is to parse
the statements instead of searching for words about them.

### What is the difference between a primary record and a derived record?

A primary record is the thing itself: the state filing, the GitHub API, the
governing section of a ratified record, the parsed SQL statement. A derived
record is any statement of fact produced from another statement of fact rather
than from the thing. Repo files describing an entity, an audit summarizing a
record, a grep counting SQL. A derived record carries no expiry on its source
unless someone builds one in.

### How do I stop a checker from re-deriving the same wrong answer?

Change what the checker keys on. The legal validator stopped accepting whatever
string the repo files agreed on and started rejecting two named retired forms.
The receipts gate keyed on `verified_at` age instead of a committed number
while it was live, and it comes back with the second attempt. The migration
lint is being moved from text grep to parsed statements. Each move takes
authority away from the derived artifact and gives it to something closer to
the thing.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Why does a text grep fail at counting SQL objects?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "A grep counts text, not statements. The Postgres migration lint on 2026-09-06 searched for CREATE INDEX and matched a RAISE NOTICE message that described an index build in prose. It counted that sentence as a sixth index build and failed the migration. The fix that is filed, and not yet shipped, is to parse the statements instead of searching for words about them."
      }
    },
    {
      "@type": "Question",
      "name": "What is the difference between a primary record and a derived record?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "A primary record is the thing itself: the state filing, the GitHub API, the governing section of a ratified record, the parsed SQL statement. A derived record is any statement of fact produced from another statement of fact rather than from the thing. Repo files describing an entity, an audit summarizing a record, a grep counting SQL. A derived record carries no expiry on its source unless someone builds one in."
      }
    },
    {
      "@type": "Question",
      "name": "How do I stop a checker from re-deriving the same wrong answer?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Change what the checker keys on. The legal validator stopped accepting whatever string the repo files agreed on and started rejecting two named retired forms. The receipts gate keyed on verified_at age instead of a committed number while it was live, and it comes back with the second attempt. The migration lint is being moved from text grep to parsed statements. Each move takes authority away from the derived artifact and gives it to something closer to the thing."
      }
    }
  ]
}
</script>

## Related posts

- [Auditing Written Claims Against Their Artifacts](https://startaitools.com/posts/the-second-review-that-audits-the-claims/)
- [A Closed Epic Is a Claim, Not a Fact](https://startaitools.com/posts/we-told-the-auditors-to-refute-us/)
- [When a Gate Should Re-Run the Step Instead of Trusting Its Receipt](https://startaitools.com/posts/stop-trusting-the-stored-claim/)
