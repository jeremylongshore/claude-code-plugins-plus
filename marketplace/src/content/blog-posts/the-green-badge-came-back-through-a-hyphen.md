---
title: "Refusing to Classify Beats Matching Harder"
description: "A status classifier should refuse wording it cannot positively recognize. A negation guard closed one bypass in a governance view, and a hyphen walked past it."
date: "2026-08-24"
tags: ["debugging", "architecture", "python", "testing", "devops"]
featured: false
canonical: "https://startaitools.com/posts/the-green-badge-came-back-through-a-hyphen/"
---
Mission Control is the internal governance dashboard over the Intent Solutions estate. One of its views composes the decision log into a page: one row per governance record, each row carrying a status of ratified, pending, deferred, superseded, or unknown. The composer that produces those rows is `ops/decisions-view/compose.py`.

The house law for that view is parse-or-UNKNOWN. If the composer cannot read a record's status off the documented convention, the row lands on unknown and says so loudly. Nothing is inferred.

The composer's classifier, the `classify_status` function, violated that law on its first settlement review, and then violated it again after the fix.

## The original bug: substring matching in the status classifier

Here is what the classifier looked like before any of this started.

```python
STATUS_TOKENS = (
    ("SUPERSEDED", "superseded"),
    ("PENDING", "pending"),
    ("DEFER", "deferred"),
    ("RATIFIED", "ratified"),
    ("DECIDED", "ratified"),
)


def classify_status(status_raw):
    upper = status_raw.upper()
    for token, status in STATUS_TOKENS:
        if token in upper:
            return status
    return None
```

`if token in upper` is a substring containment test. `RATIFIED` is a substring of `UNRATIFIED`. `DECIDED` is a substring of `UNDECIDED`. `RATIFIED` is also a substring of `NOT YET RATIFIED`.

So three real classes of governance record (`UNDECIDED`, `UNRATIFIED DRAFT`, `NOT YET RATIFIED`) all classified as ratified and rendered the calm green badge. The page reported the exact opposite of what the record said. An independent code review found it during the B7.6 settlement walk and filed it CRITICAL, which is the correct severity: a dashboard that says settled over an unsettled record is worse than a dashboard that is down, because nobody goes and reads the record.

## Round 1: word boundaries plus a negation refusal

The round-1 fix was two changes, not one.

First, the tokens became compiled patterns anchored at word boundaries, so containment stopped being the matching rule.

Second, and this is the part that carries the argument, a negation check ran *before* any positive match and refused classification outright.

```python
NEGATED_STATUS = re.compile(
    r"\b(NOT|NEVER|NO|NON|WITHOUT|UN(?:RATIFIED|DECIDED|APPROVED|SETTLED))\b")
STATUS_TOKENS = (
    (re.compile(r"\bSUPERSEDED\b"), "superseded"),
    (re.compile(r"\bPENDING\b"), "pending"),
    (re.compile(r"\bDEFER"), "deferred"),
    (re.compile(r"\bRATIFIED\b"), "ratified"),
    (re.compile(r"\bDECIDED\b"), "ratified"),
)


def classify_status(status_raw):
    """Returns (status, None) on a classified token, or (None, reason)."""
    upper = status_raw.upper()
    if NEGATED_STATUS.search(upper):
        return None, ("Status wording contains a negation token ...")
    for token, status in STATUS_TOKENS:
        if token.search(upper):
            return status, None
    return None, ("Status text matches no documented mapping token "
                  "(SUPERSEDED/PENDING/DEFER/RATIFIED/DECIDED)")
```

Note the return type changed from a bare status to a `(status, reason)` pair. A refusal now has to explain itself, which means the unknown row on the page carries the specific reason it landed there rather than a shrug.

The stated rationale in the commit body was negation refusal over negation classification: UNKNOWN is the only safe landing for wording the mapping does not positively recognize. Two fixtures went in with it (D908 and D909, by their decision IDs) and drills 2, 6, and 7 were extended to cover them.

Three more defects rode along in the same commit, all in the renderer:

- Rows missing a required file or title string now hit a clean rc=2 refusal. They used to raise a KeyError traceback, which is a refusal too, just an ugly one that looks like a crash instead of a decision.
- The summary can no longer disagree with the rows beneath it. `entries_total`, the sum of `status_counts`, and the escalation `entries_pending` are all cross-checked against what actually rendered. A summary that is computed independently of the rows will eventually drift from them.
- `esc()` escapes backslashes first, so a backslash in the input cannot re-arm a special character that a later escape step introduces. Escaping order is not a style question.

That shipped, and the settlement review re-ran against it.

## Round 2: the badge came back through a hyphen

The round-2 review demonstrated a bypass on the same day: `UN-RATIFIED` and `UN DECIDED`.

Walk it through the round-1 code. `NEGATED_STATUS` looks for `UNRATIFIED` as one word. `UN-RATIFIED` is not that word. The hyphen is a word boundary, so the negation pattern misses. Then `STATUS_TOKENS` runs `\bRATIFIED\b` against `UN-RATIFIED`, and the boundary between `UN-` and `RATIFIED` is a real word boundary, so `RATIFIED` matches positively.

The green badge came back, and it came back through a negation pattern that only recognized the fused single-word form. Word boundaries are a wall between whole words. They are not a wall between a prefix and the word it negates, and a negation guard whose token list only spells the attached form inherits that gap for free.

### Why word boundaries do not block prefixes

A word boundary is a transition between a word character and a non-word character. A hyphen is a non-word character and a space is a non-word character, so `UN-RATIFIED` and `UN RATIFIED` both carry a real boundary between the prefix and the token. That means two things at once. The negation pattern, if it only knows `UNRATIFIED` as a single word, does not match. The positive pattern `\bRATIFIED\b` then matches cleanly against the right half. Word boundaries are not a defense against a prefix, because the prefix is on the other side of the boundary. The only thing that covers the separated form is a pattern that names the separation.

The round-2 fix widened the negation pattern to recognize the detached prefix form.

```python
NEGATED_STATUS = re.compile(
    r"\b(NOT|NEVER|NO|NON|WITHOUT)\b"
    r"|\bUN[-\s]?(?:RATIFIED|DECIDED|APPROVED|SETTLED|PENDING|DEFERRED|"
    r"SUPERSEDED)\b")
```

`UN[-\s]?` covers `UNRATIFIED`, `UN-RATIFIED`, and `UN RATIFIED` in one alternation, and the token list behind it grew to cover the states that round 1 had not enumerated (`PENDING`, `DEFERRED`, `SUPERSEDED`). Two more fixtures went in, numbered by ledger position and decision ID: 110/D910 for the hyphenated form and 111/D911 for the spaced form, and the fixture ledger reached 11 entries with the drill counts now derived from the ledger instead of hardcoded next to it.

## Why not just fix the regex harder: refusal ordering against pattern breadth

This is the obvious objection and it deserves a straight answer, because the round-2 fix *is* a better regex. So what distinguishes it from the round-1 fix, which was also a better regex?

The ordering. Both rounds kept the same structural property: the refusal check runs first and returns unconditionally, and the positive matcher never gets to vote on a string that the negation guard has claimed. Round 1 established that structure. Round 2 only widened the pattern feeding it.

That matters because the failure mode is asymmetric. If the negation pattern is too narrow, a record gets classified wrongly and shows a confident green badge. If the negation pattern is too broad, a record that could have been read lands on unknown with a stated reason, and a human goes and reads it. One of those is a silent lie and the other is visible extra work. [Every Safety Gate Has a Failure Direction](https://startaitools.com/posts/every-safety-gate-has-a-failure-direction/) works the same asymmetry through a set of pull-request gates.

So the choice was an explicit `UN[-\s]?TOKEN` prefix rather than a standalone `\bUN\b` negator. A bare `UN` negator would have been broader still, but it swallows unrelated words that happen to contain or abut `UN`, and breadth is only free up to the point where it starts refusing records that are perfectly readable. The prefix form covers the demonstrated bypass without reaching past it.

So the precise claim is narrower than "stop using regex" and more useful. Match as hard as you like on the refusal condition, and widen it the moment a bypass is demonstrated. Do not widen the acceptance condition to compensate, and never let it run first. Round 1 and round 2 are both better regexes. What makes them fixes rather than patches is that both of them added breadth on the side where being wrong costs a human ten minutes, not on the side where being wrong prints a false green badge. That ordering is the durable property. The pattern behind it will keep needing edits, and that is fine, because a too narrow refusal fails loudly the next time somebody writes a new negation and a review catches it. [The Refusal Nobody Heard](https://startaitools.com/posts/the-refusal-nobody-heard/) is the failure mode on the other side of that bet: a guard that refused correctly and had nothing wired to listen.

## Verification, and what did not change

The classifier was probed against every reproduction the round-2 reviewer supplied (`UN-RATIFIED DRAFT`, `UN RATIFIED`, `Un-Ratified`, `UN-DECIDED`), all resolving to unknown with the negation reason attached. It was also probed against the adversarial cases that must *not* trip the guard: `RE-RATIFIED` and `NOTWITHSTANDING` kept their prior classifications, along with all five live modern records. `run-proof.sh` ran green with the extended drill.

Live truth was unchanged through the whole episode: 66 records at 3 ratified, 1 deferred, 0 superseded, 1 pending, 61 unknown, escalation unknown. That is the honest framing from the round-1 commit body, and it is worth repeating. The fix changes what a hostile future record could do to the page. It does not change what today's page says. Nobody had actually filed an `UN-RATIFIED` record yet.

## The evidence bundle got refused too

The round-2 audit returned `EVIDENCE_INCOMPLETE` on a second and completely unrelated ground. The rollback receipt in the evidence bundle named the prior commit, while the bundle README described a future re-rehearsal as already done.

The receipt was rewritten as a ledger of executed rehearsals only. Three entries, each with a recorded tree hash, no future-tense claims. A stale seven-entry fixture count in the slice README got corrected in the same pass.

This is the same defect class as the classifier, one layer up. A document that asserts a rehearsal happened because it was scheduled to happen is inferring past a fact it does not have, exactly like a classifier reporting ratified because `RATIFIED` appeared somewhere in the string.

## The same lesson, from the other direction

The founder-view hardening landed the same day, under `spine-bxp.8`, and it carries the sharper version of the point.

The schema `founder-portfolio-view.v0` went 1.0.0 to 1.1.0. The coverage-present rule now requires a present, nonzero `populations.governed` as a standalone law, rather than one enforced only transitively through the upstream contract, so an omission upstream can no longer smuggle a coverage claim through. The renderer picked up the backslash-first escaping law at value level across reasons, states, count keys, and `observed_at`, plus structural validation that cleanly refuses non-dict sections, non-dict payloads, unknown section names, and missing envelope fields at rc=2 instead of a traceback.

The interesting part is what the new drill found. The coverage-present branch had zero drill coverage. Exercising it for the first time exposed a latent CRITICAL: the upstream ownership state `governed` was outside the view's section enum, which means the founder view would have hard FATALed on the exact day the estate actually became governed.

That bug was scheduled to fire on success. Every test to date passed because the condition it depended on had never been true yet, and the day it became true is the day the dashboard goes down. Undrilled branches do not fail on the schedule you would pick.

The fix widened the enum verbatim rather than mapping `governed` to `ready`, because the house law is that upstream state passes through verbatim. Same instinct as the negation guard: do not translate a value you do not own into one you do.

Verification: `run-proof.sh` green across 13 drill groups, `schemas/validate.py` green over 72 schemas with 119 valid and 144 invalid fixtures. The regenerated page surfaced the capability matrix as stale-loud at 126 hours, which is honest drift shown rather than suppressed.

## Settling the epic

`decision-log/065` (D216) closed the lifecycle. B7.1 through B7.6 closed with independent evidence. `spine-bxp.7` was formally deferred and never closed, carrying a full re-entry authority chain, which is the difference between deciding not to do something and quietly dropping it. The guardian pass returned APPROVE, and the fact that it ran after the settlement rather than before it was recorded rather than smoothed over.

The final integrated audit ran on merged main and returned EVIDENCE_COMPLETE on three dimensions: no false-green (every dark source renders dark), no disclosure drift (gate clean over 1622 files plus a manual sweep), and cross-view consistency (the B6 producers-absent story identical across views, populations consistent, all provenance lines resolving).

One thing is owed and named in the CHANGELOG rather than buried: the `mc:matrix` regen. The committed capability-matrix page trails its local state artifact by about two days. That is outside B7 scope and it is written down where the next person will hit it. A page that trails its own state artifact and says so is the document-layer version of the unknown badge, which is the entire point.

## Also shipped

One more instance of the same instinct, at a different layer. The claude-code-plugins marketplace finally enforced its own census deadline, a month after that deadline passed. Refusing to list a source that cannot pass the bar is the catalog-level version of refusing to classify a string the mapping cannot read. A whole-catalog quality census on 2026-07-08 put failing sources on a fix-or-removed clock with notify issues filed upstream and a deadline of 2026-07-22. On 2026-08-23, `census-watch --enforce` re-validated every notified skill at upstream default-branch HEAD using `validate-skills-schema.py --marketplace`. Clusters still failing had their `sources.yaml` entries removed (dated NOTE comments left in place), their mirror directories under `plugins/` deleted, and their catalog entries removed: 27 source entries across two clusters, `numman-ali/n-skills` and `wondelai/skills`, landing as 343 files changed and 72,206 deletions. Re-listing is explicitly welcome once the skills pass the validator.

A cascade of template-stamped pack delistings followed the same procedure: Veeva, Wispr, StackBlitz, and duplicate placeholder skills pulled from the Together pack. Separately, `fix(freshie): make stub detection deterministic` landed, and the Adobe pack's skill sections were completed rather than removed.

Worth being precise about what is and is not interesting there. The line counts are large because deleting a mirrored catalog is mechanically large. What matters is that a deadline the marketplace published against itself a month and a half earlier was actually enforced against its own inventory, on a re-validation run, with the removal criteria unchanged from the announcement.

Elsewhere: one journal post landed on comehomealabama. A self-updating profile card shipped to the GitHub profile repo and was reverted the same day. The previous day's post dual-published to tonsofskills.com/blog and went into the intent-solutions-landing field notes.

## Related Posts

[Every Safety Gate Has a Failure Direction](https://startaitools.com/posts/every-safety-gate-has-a-failure-direction/) works the same asymmetry through a set of shell gates on every pull request: which way a gate falls when it cannot tell is the whole design.

[Reject PII at the Source: A Disclosure Gate at Intake](https://startaitools.com/posts/disclosure-gate-reject-pii-at-source/) applies refusal at the data boundary rather than attempting interpretation downstream.

[Software Supply Chain Security After Axios](https://startaitools.com/posts/software-supply-chain-security/) covers the harder version of the same problem: a source that clears every bar you set and is still hostile. The census only bounds the easy case, sources that cannot clear the bar at all.
