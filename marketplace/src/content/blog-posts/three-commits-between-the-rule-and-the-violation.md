---
title: "Three Commits Between the Rule and the Violation"
description: "A changelog gate shipped inert: at fetch-depth 2, git tag --list is empty in CI, so the check exited 0. An AI reviewer caught what the author could not."
date: "2026-08-06"
tags: ["ci", "code-review", "github-actions", "ai-code-review", "testing", "changelog", "devops"]
featured: false
canonical: "https://startaitools.com/posts/three-commits-between-the-rule-and-the-violation/"
---
Understanding a failure mode does not inoculate you against shipping it. This blog has returned to vacuous checks repeatedly over the past two weeks, most recently 2026-08-05 and 2026-08-03. One admission is due: that frequency reads obsessive. But this instance earns publication for its specificity and for what it says about review.

The rationale and the defect shipped in the same commit. Commit `25df411ad` added `check-changelog-coverage.mjs` carrying a header that explains why inert surfaces rot, and in the same diff wired it into a job where it could never run. Two AI reviewers read PR #1162. Greptile submitted a review with no findings. Kilo flagged CRITICAL. That is not an argument about AI reviewers being superior. It is an argument about which questions catch which defects: the author reads `check-changelog-coverage.mjs` and sees the invariant he intended. A reader with no investment reads `fetch-depth: 2` and asks whether tags are present. One reviewer checked the mechanism (what does a shallow clone at `fetch-depth: 2` actually contain). The other checked the intent (is this the right invariant) and found nothing. That asymmetry is what a fresh reader can do that an invested one cannot.

## The Changelog Frozen at March

`claude-code-plugins` shipped v4.33.0 on 2026-05-25. By 2026-08-06, the site advertised that version under a link labeled "what's new" pointing to release notes dated 2026-03-07. Seventeen tagged releases and 556 commits had shipped with no notes at all.

Commit `fa454f5ae` backfilled all 17 entries from `git log` ranges, grouped by conventional-commit type, with real PR links. Where the three existing entries were hand-written prose explaining why each change mattered, reconstructing that voice for releases months old would mean inventing rationale. Each backfilled entry states plainly that it was reconstructed from the tag range. Accurate over readable.

A second finding, deliberately not bundled into the docs backfill: as of that day, 336 commits had merged since v4.33.0 with no tag and no version bump.

## The Gate, Written and Then Shipped Inert

Commit `25df411ad` added `scripts/check-changelog-coverage.mjs`, wired into the validate job. Its invariant: for every `vX.Y.Z` git tag, a matching changelog entry exists with that version in frontmatter. The file header articulates the rationale (paraphrase, dashes removed):

> A changelog rots for the same reason the missing og:image survived five months: nothing in the build depends on it being right. This makes something depend on it.

That og:image is not a hypothetical. It is [a real case from three days earlier](https://startaitools.com/posts/the-check-that-only-confirmed-a-name/): `BaseLayout` advertised `/og-image.png` on 3,830 published pages and the file had never been committed at all. So the header is not vague pattern-awareness. It names a specific worked example, in the same diff that shipped the same failure.

Two design calls worth showing:

**The floor is a constant, pinned deliberately.** The first version computed the floor as the oldest documented entry. Deleting that entry would raise the floor silently, and the gate would report "0 missing" with one fewer release covered. Verified by removing v4.14.0's notes: floor moved to v4.15.0, exit 0. A ratchet a file deletion can loosen is not a ratchet. The constant came from that test. There is a coda: lines 29-32 of that same file still describe the design that was rejected, documenting a derived floor. Line 104 implements the pinned one. The code is correct; the header is stale. Nobody has re-read it. It is the same class sitting inside the exhibit.

```javascript
const FLOOR = '4.14.0';
if (!documented.has(FLOOR)) {
  console.error(
    `The pinned floor v${FLOOR} has no release notes. Either restore them, or\n` +
      `lower FLOOR in this script deliberately, do not let it drift.`,
  );
  process.exit(WARN_ONLY ? 0 : 1);
}
```

**Deliberately not gated:** entry quality and whether unreleased work has notes. Demanding prose nobody has written is how gates get disabled.

Then PR #1162 went up. Kilo Code Review flagged CRITICAL. The finding: `actions/checkout` does not fetch tags by default, and that job uses `fetch-depth: 2`. So `git tag --list` returns EMPTY in CI.

Verified by cloning exactly what CI produces:

```bash
git clone --depth 2 --no-tags file:///path/to/repo cov-test
cd cov-test
git tag --list 'v*'
# (empty)
node scripts/check-changelog-coverage.mjs
# no version tags visible - skipping
# EXIT 0
```

A PR could delete the entire changelog and this silent CI failure would report success. The gate passed because it never ran, not because it verified anything.

## Why Not Full History

The short version, for anyone who arrived here from a search box: `actions/checkout` does not fetch tags by default. Under a shallow clone (`fetch-depth: 2`), `git tag --list` returns empty, so any gate that keys on tags skips itself and exits 0 without checking anything. Reach for `fetch-tags: true` rather than `fetch-depth: 0`, which exposes the tags without paying for full history on every run.

The longer version is that `fetch-depth: 0` would work, but two separate constraints make `fetch-tags: true` the surgical choice. First, the catalog format guard in the same job needs the merge base, so the shallow clone has to stay at `fetch-depth: 2`. Second, a full-history fetch on every PR is a real cost to buy one gate's benefit. `fetch-tags: true` gets the tags without paying for the history.

The fix, ordered so the explanation precedes the change:

```yaml
with:
  fetch-depth: 2
  # fetch-tags is REQUIRED by check-changelog-coverage.mjs below.
  # actions/checkout does not fetch tags by default, so `git tag --list`
  # returned EMPTY and that gate silently exited 0. It never fired in
  # CI at all. Verified by cloning --depth 2 --no-tags and deleting every
  # release note: still exit 0. fetch-depth stays 2 (the catalog format
  # guard needs the merge base); fetch-tags is the surgical addition.
  fetch-tags: true
  persist-credentials: true
```

Kilo raised four other findings in the same review. `git tag --list` takes a GLOB, not a regex, so `v[0-9]*.[0-9]*.[0-9]*` has a literal dot and zero-or-more wildcards and admits shapes it looks like it excludes. It is now filtered in JS with `/^v\d+\.\d+\.\d+$/`. The skip was silent instead of loud, and silence makes a no-op indistinguishable from a pass:

```javascript
if (tags.length === 0) {
  // Loud, not silent. A gate that quietly no-ops is indistinguishable from a
  // passing one, which is precisely how this script shipped inert.
  console.log(
    '::warning title=changelog-coverage::No version tags visible - the gate did NOT run. If this is CI, the checkout needs fetch-tags: true.',
  );
  console.log('changelog-coverage: no version tags visible - SKIPPED (not a pass)');
  process.exit(0);
}
```

Also: `readdirSync` needed recursion so a future `blog/2026/…` grouping cannot silently stop counting posts.

## The Same Shape, Twice More

`intent-os` on the same day hosted two related breaks. The first: `vps-liveness-sweep-test.sh` had an assertion checking that a delivery path was not retired. It invoked `rg`, which was not on a non-interactive script's PATH. Exit 127, else branch taken, assertion reported ok. An always-passing check that verified nothing, because the tool it depended on was never invoked. It passed because its tool was missing, not because the property held. Switched to `grep -E` (POSIX-present).

The second: `run-proof.sh` checked that a database unit FILE existed, then claimed "the receiver unit's Requires= names a real target." Different statements. Rename the target and the file still exists, so the assertion stays green while systemd would refuse to start the receiver. Caught by MiniMax on PR #389 and then lost. The branch was reset to resolve a rebase conflict, and #389 merged without it. An uncommitted fix leaves no trace. The restored version additionally asserts the receiver is ordered `After=` the datastore, not merely `Requires=` it. Proof went from 51 to 52 assertions, 0 failed.

## The Work That Day

Claude Opus 5 and Claude Sonnet 5 drove the analysis. The `intent-os` work spanned 8 sessions: 276 turns, 492 tool calls, 25 errors hit, across 1,189 minutes. The `claude-code-plugins` session was the opposite: 42 turns, 63 tool calls, 43 minutes.

A build that normally took 50 seconds blew past 600. The cause: the model's own astro preview servers left running three days, load average 12. It could not see its own mess until something unrelated broke, which is the same asymmetry as the gate: an external symptom surfaces a blind spot the author cannot see from the inside. It found and killed its own 10 processes, which surfaced five orphaned polling loops from 30 to 35 days prior. One had a `pgrep -f` matching its own subprocess: permanently self-satisfied, unable to ever exit. Each exit condition was verified unreachable before killing. Load went 12.05 to 6.60. A cross-session hazard also surfaced: another session was building the same tree while this one held 17 uncommitted files. It stashed the other session's artifacts, committed, and popped the stash back.

## Also Shipped

- intent-os PR #389: isolated postgres:17.10-alpine for the webhook receiver, pinned by DIGEST, published on 127.0.0.1:5439 so which database you are connected to is answerable from the port.
- PRs #385 and #387: wire channels renamed to `wire-<provider>`, failing loud on unresolved names. The human course-corrected the naming mid-flight.
- Caddy detail: `sudo caddy validate` does not parse only, it builds the config. A log directive creates its output file as the invoking user at mode 0600. Under sudo that is root-owned; the service runs as caddy. Next reload cannot open its log and Caddy rejects the WHOLE config. One sudo on one new vhost stalls a reload for every domain on the host. Verified on Caddy v2.10.2.
- intent-curriculum: 60-item CCAO-F practice exam bank added.

## Why Freshness Is Not Enough

The author is the worst reader of his own gate because he has a model of what the code was supposed to do. Reading `check-changelog-coverage.mjs`, he sees the invariant he intended. When he reads `fetch-depth: 2`, he does not see it as a question because he already answered it: he knows why he chose 2. That model, from the inside, is indistinguishable from a model of what the code actually does. Freshness alone does not fix that, because checking the intent (is this the right invariant) is exactly what the author was already doing and is exactly what cannot catch this.

Greptile was equally fresh. It checked the intent and found no issues. Kilo checked the mechanism: does `actions/checkout` fetch tags. Intent-checking is what the invested reader does; mechanism-checking is what the fresh reader can do differently. Both are needed.

For any gate you write, the question that catches this class is not "is the logic right" but "under what conditions does this exit 0 without running?" That is a question about the environment, not the code, which is why it survives code review and lands in production. Understanding the pattern, as the author articulated it in that header comment, does not inoculate you. You still need someone to ask the question whose answer you already know.

## Related Posts

[Nothing Read It, So Nothing Failed](https://startaitools.com/posts/nothing-read-it-so-nothing-failed/) covers the same failure class at Tier 3 and broader scale.

[The Check That Only Confirmed a Name](https://startaitools.com/posts/the-check-that-only-confirmed-a-name/) and [The Ghost in the Catalog](https://startaitools.com/posts/the-ghost-in-the-catalog/) are adjacent instances in this family.
