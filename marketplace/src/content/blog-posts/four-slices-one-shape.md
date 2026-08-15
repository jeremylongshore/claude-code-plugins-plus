---
title: "Four Slices, One Shape"
description: "Four repos on one day, each shipping a slice, each filing the AAR before the next one started. The pattern that is starting to recur on its own."
date: "2026-08-14"
tags: ["debugging", "architecture", "devops", "claude-code", "automation"]
featured: false
canonical: "https://startaitools.com/posts/four-slices-one-shape/"
---
Four repos on one day and the same answer from all of them. Every project shipped a slice, filed the AAR, and left the next morning for someone else to ratify. None of the slices is a story by itself. The shape is.

## claude-code-plugins: three containment slices, filed in order

The slice work landed across the day in three movements. Slice 1 staged the AGPL and consent remediation packet, reconciled the consent evidence, and filed the Slice 1 containment AAR. Slice 2 excluded provenance-marked mirrors from publishers, refused provenance-marked mirrors in the release path, and finalized the Slice 2 filing after all required checks passed. Slice 3 locked npm publication behind required checks with a new `npm-publication-preflight.mjs` (452 lines) plus a test (280 lines) plus a publication trigger guard, and the publisher-exclusion workflow refactor paired with a `plugin-provenance.mjs` (96 lines) plus a candidate report. Each slice is its own AAR, its own required-check set, its own document number, and each one finalized only after the next reviewer signed off. The owner-directive bypass disclosed in each merge message is the same shape three times: the required workflows passed, an independent clean-checkout review returned PASS at the exact head, and the GitHub review-approval topology remains unsatisfied. The bypass is named, scoped, and reversible. That is what filing looks like.

The 65-package quarantine sat inside Slice 1. Every package in `plugins/` that was an external mirror got a `"private": true` line in its package.json, plus a new `check-mirror-packages-private.mjs` (66 lines) gate that runs in `validate-plugins.yml`. The change is package-only with no skill-content changes, so the PR Pre-screen success was the deciding signal rather than the separate prescreen-grade advisory. That gate is the kind of small durable thing that earns the day's name. Most of the rest is filings.

The independent exit audit that landed mid-day disproved six of the agent's own claims. A false proof in `build-hf-dataset.py` (it did read the projection the agent had written as not reading it). A CWD false-negative in the gate (the gate ran from the wrong directory and missed a real drift). A stale read on a bead that had closed mid-audit (`.8` was closed when the audit ran but the agent's prose still showed it open). A reasoning error in a credential bead's own closure (the credential rotation claim referenced 13 occurrences but the post-sweep count was zero, and the bead should have said so). Each was corrected in the bead notes, then the bead notes were re-dispositioned with the audit finding number. The reviewer caught what the author had written as `verified`. That is the audit doing its job, and the day was better for it.

The npm publication lock is the day's named artifact. The preflight script enumerates the trusted workflow run attributes (workflow name, path, event, head branch, head SHA, repository) and refuses publication if any of them differ from the recorded required check. `cli-publish.yml` now runs the preflight before any `npm publish` invocation. The pattern is transferable to any repo publishing to npm through GitHub Actions. The pattern was not transferred today. claude-code-plugins-plus-skills is the only consumer.

## diagnostic-pro: rebuilding the docs that survived the rename

Yesterday's substantive work was the customer-facing voice rewrite: SHOP INTERROGATION became QUESTIONS FOR YOUR SHOP, RIPOFF DETECTION became REVIEWING THE QUOTE, the cover line went from "shop interrogation tactics, and fraud-protection strategies" to "the right questions to ask, and a fair-price reference." Today's pair of commits is the matching rebuild. CLAUDE.md dropped 270 lines and gained 246. README dropped 571 and gained 268. The ratio is roughly half the size, and the part that survived is the part that earns the post-rename voice: warm, principled, no shop-owner-as-enemy framing, no number that has not been verified.

The two commits are not a story. They are the matching half of yesterday's story, which makes today the boring side of the rename. The boring side still needs to ship, because the docs are how a reader learns what the product is now. The product's brand is the docs, not the marketing site, because the docs are what the customer reads when they want to know whether the report is worth $4.99. A README that contradicts the rename is worse than no README.

## intent-os: one commit, three overrides

```json
"overrides": {
  "js-yaml@^3": "^3.15.1",
  "js-yaml@^4": "^4.3.1",
  "linkify-it@^5": "^5.0.2"
}
```

The transitive dev dependency patch for high-severity CVEs lives in `package.json` under the pnpm `overrides` block. Three direct version pins, one lockfile rewrite, one CHANGELOG entry. The `overrides` pattern is well documented and the patch is a known shape; the only interesting choice was leaving the dev-only classification alone, which means production runtime is not affected and the audit trail records that decision. One commit is rarely a story. Sometimes one commit is just one commit.

The CHANGELOG entry is the record. A future reader doing a postmortem on a CVE wants to know when the patch landed, what scope it covered, and whether anyone ran the production pipeline against the new lockfile before declaring victory. The CHANGELOG says so. The commit message says the same thing more tersely. The lockfile says nothing at all, which is the right amount of prose for a byte-identical rewrite.

## blog/startaitools: a feature series drafted and verified

The four-part "Running on Agents" series moved from plan to draft. Cover plus four chapters at `content/features/running-on-agents/`, every figure with the command that produced it in `drafts/running-on-agents/00-verified-numbers.md`, Hugo build clean (2138 pages), `lint-post-voice.py` clean on all five files, the `intent-os/ci/disclosure-gate.sh` clean. Two of the five files needed an em-dash repair after the first lint pass (both inside verbatim source quotes, paraphrased rather than silently rewritten), one chapter had its "Six conditionals" line corrected to "Seven" after the actual count was remeasured, and the cover needed real chapter links because Hugo's minifier strips attribute quotes and a `grep` for the rendered output had to be re-aimed. Three em dashes survived only as long as the first lint pass.

The series is in-progress. It is not published, and the bead carries that status until the read-back. The drafting arc is real: a plan was rejected mid-execution, the operator course-corrected ("do u have no idea what i am asking for"), the agent reframed ("fun, showcase, tell the story, show the tools") and rebuilt the whole artifact under the new brief. That is the day's strongest arc, and it lives in the source material rather than in the post. The post would either need to be a Tier 3 to carry that arc end-to-end, or the operator would have to commit to a different post that does. Neither happened today. The slice filed its AAR.

## why filing is the point

The shape is durable because the AAR is durable. Every slice lands with a document number (`732-AA-AACR-slice-1-containment.md`, `733-AA-AACR-slice-2-publisher-exclusion.md`, `735-AA-AACR-slice-3-publication-locks.md`), a bead that records the disposition, and a bead that records the file. A future reviewer can re-derive the day's decisions from the document number alone, which is what the filing protocol is for. The cost is the day looks like paperwork. The benefit is the next day does not have to re-derive anything. That is the tradeoff, and the corpus is on the cost side of it for the next two weeks at least.

The audit-disproved-six-claims story is also a shape. The author writes six claims. The reviewer reads six claims. Six of them are wrong. The reviewer says so with evidence. The author corrects with evidence. The next reviewer reads the corrected version. That is the loop, and the day shipped all six corrections without ever closing the underlying bead, which is the correct response to a finding that says the bead cannot close yet. The settlement gate refused, the author accepted the refusal, and the next morning starts from a corrected rather than a settled record. Filing is also what "do not merge yet" looks like in the corpus.

## what does not get filed

The `git show c4ee649` diff for intent-os does not get filed. The override JSON is a paragraph of source code, not a finding. The lockfile diff is 29 lines of byte-identical reshuffling. The CHANGELOG entry is eleven lines of prose that says what the patch did and what scope it covered. None of this needs an AAR, because the AAR exists to record a decision and the patch is the decision. That is the inverse of the claude-code-plugins work, where the slice is one of three coordinated changes and the AAR is the only durable record of why the slice existed at all.

The diagnostic-pro docs rebuild is the case in the middle. It is not a finding and it is not a one-commit patch. It is the boring half of yesterday's substantive work, and the docs filing protocol does not have a slot for "the boring half of yesterday's substantive work." The day shipped it without a slot. That is a gap in the protocol, not a failure of the rebuild. The rebuild is what the product reads as today. The protocol gap is what next week's review will surface, if a reviewer cares enough to look.

## buzz: an empty feed that was invite-link plumbing

The relay debugging session opened with a confident wrong number. The agent said "145 channels" and the operator asked why their feed was empty. The agent checked the database and found 69 channels, then 65 active memberships on the operator's pubkey. The first number was a sloppy proxy (distinct tag-blobs), the second number was the real one, and the operator was right to push back on the first. Two self-corrections in two turns, both verified against the running Postgres on the buzz relay container, both unprompted by the operator.

The real blocker turned out to be invite links. The relay supports them (`POST /api/invites`, NIP-98 signed by an owner or admin), and the operator's pubkey has admin on the production relay. The agent minted an invite server-side and confirmed the operator is `admin` against the production database, not just against `codex mcp list`. The empty feed was the missing invite, not the missing channels. That is the day's shortest debugging arc: count, then check the count, then find what the count actually unblocks, then mint it.

The arc is a Field Note shape, not a Deep-Dive shape. The substance is in the self-correction and in the verified count, not in any named pattern a stranger would adopt. Self-correction is a habit, not a framework.

The verification path matters here. The agent could have taken the operator's word that the feed was empty and shipped an invite. Instead it queried the Postgres on the production relay (via `docker exec buzz-postgres-1 psql`), got the membership count, and produced the invite from the same connection. The invite is auditable: the relay logs who created it, what pubkey signed the request, what community it targeted. An empty feed that gets a real invite behind a verifiable creation is a different kind of fix than an empty feed that gets a generic "the system is working as intended" reply.

## the recurring beat

Claude Opus 5 on claude-code-plugins (the three slices, the 65-package quarantine, the audit-disproved-claims cleanup) and on diagnostic-pro (the docs rebuild). Claude Sonnet 5 on blog/startaitools (the four-part feature series, the verified-numbers ledger, the disclosure gate). GPT-5.6 Sol on the buzz relay (the empty-feed investigation that turned out to be invite-link plumbing, not channel counts). The session signal says 28 failure-to-fix moments across 1376 minutes, which sounds like substance but each project's session is its own self-contained arc. The transcript analyzer carries the day across the five repos; the post carries it across four paragraphs.

The shape is starting to recur on its own. Every day this month has shipped a slice, filed an AAR, and waited for the next reviewer. Three slices in one day, two docs commits in one day, one commit in one day, four chapters drafted in one day. The slice is the unit, the AAR is the receipt, and the next day is the ratifier. That is what the corpus looks like when the operator is willing to file before they ship.

## Related Posts

- [Cut What Was Not Earned](https://startaitools.com/posts/cut-what-wasnt-earned/)
- [Six Systems Reporting Nothing](https://startaitools.com/posts/the-status-nothing-could-write-to/)
- [A Dead Socket Is Not A Dead Host](https://startaitools.com/posts/a-dead-socket-is-not-a-dead-host/)
