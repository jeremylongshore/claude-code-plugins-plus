---
title: "The Ghost in the Catalog"
description: "A pipeline wrote a published record for a post it never published, then its own self-audit article read that record as truth and printed it for readers."
date: "2026-07-31"
tags: ["automation", "ci-cd", "devops", "release-engineering", "debugging", "provenance"]
featured: false
canonical: "https://startaitools.com/posts/the-ghost-in-the-catalog/"
---
Yesterday my blog [published an article auditing itself](https://startaitools.com/posts/after-14-days-of-daily-posts-here-is-what-i-notice/). It counted its own posts, tallied its own
categories, and reported the results in a table. The table was wrong.

Not wrong in a rounding way. Wrong in a way that should not be possible: one of the rows described
an article that does not exist. The file is untracked in git. The URL returned 404. Nobody has ever
read it. And the pipeline's own append-only methodology log had a record for it, dated and
formatted exactly like every real one, asserting it had been published.

That is the whole story. An automated system fabricated a record of work it did not do, and then a
later stage of the same system read that record as ground truth and reported it to readers as fact.
The system lied to itself, in public, in an article about how well it was working.

The green checks are a footnote here. I have written that post already, more than once. This one is
about provenance: where a claim comes from, and what happens when a system's only witness to its own
behavior is a file the system writes itself.

## The screenshot

The trigger was Jeremy sending a phone screenshot of the freshly published meta post and one line of
instruction:

> /init then investiafte the following after fully understanding all cron automations scripts etc

Read only. Understand the automation first, then look at the claim. **GPT-5.6 Sol** ran that
investigation through Codex CLI: two sessions, 27 turns, 176 minutes, no repository changes.

The first finding came before anyone touched the article. The repo's own CLAUDE.md said the daily
chain runs at 07:00 and 08:30. The live crontab runs production at 04:00 and 05:00. There were no
blog specific systemd timers at all. The documentation described a schedule that had not been true
for a while.

That is a small thing on its own. It matters because every subsequent finding had the same shape:
a written description of the system that had quietly stopped matching the system.

## Falsifying the article, one check at a time

The article's headline claim was "sixteen posts between 2026-07-16 and 2026-07-29." That number is
correct. Fourteen days, sixteen posts, two days carrying two posts each. Fine.

The chronology table underneath it listed **fifteen** rows. That gap is where the whole thing
unravels, and the cheapest possible check proved it.

```bash
# The table listed 15 rows under a claim of 16 posts.
# Check the one 07-27 slug it DID list, plus the two 07-27
# posts it did not, against the live site. HTTP status is
# ground truth that lives OUTSIDE the pipeline's own bookkeeping.
for slug in the-day-the-green-checks-were-lying \
            diagnostic-engagements-q3-2026 \
            the-brand-behind-the-plugins-survivorship-story ; do
  printf '%-52s %s\n' "$slug" \
    "$(curl -o /dev/null -s -w '%{http_code}' "https://startaitools.com/posts/$slug/")"
done

the-day-the-green-checks-were-lying                  404
diagnostic-engagements-q3-2026                       200
the-brand-behind-the-plugins-survivorship-story      200
```

### The soft 404 I found while fact-checking this post

One caveat on that loop, and it is not a small one. Those status codes are from July 31, when the
domain still resolved to Netlify. Run the same loop against the site today and all three return 200,
because the Caddy config this post cuts the site over to ends in a catch-all that serves the
homepage for any unmatched path. That is a soft 404: the server says "here is your page" and hands
you a different one. I found it while fact-checking this article, which is the correct amount of
funny. It is the same disease one layer further out, the host now asserting existence for things
that do not exist, and it is filed as its own defect rather than quietly patched into this sentence.

Two facts fell out of that loop, and the arithmetic gave up a third.

The article **included** a post that returns 404. It **omitted** both actually published July 27
posts, which return 200. So the fifteen rows resolve like this:

```
15 rows listed
 -1 phantom row   (the-day-the-green-checks-were-lying, HTTP 404, untracked)
 = 14 real rows
 +2 omitted rows  (both 07-27 posts, HTTP 200, tracked and live)
 = 16 actual published posts
```

The count was right. The contents were not. The deploy branch really did have 16 published posts,
and the article really did say 16, but the set it enumerated was not that set. One row was a
phantom and two real posts were invisible to it.

That contamination propagates unevenly, which is its own lesson. The repetition count (how often the
catalog repeats a thesis) was computed over the wrong set and had to be corrected. The category
split happened to survive, because the phantom and the two omitted posts balanced out in that
particular tally. So one derived number was wrong and one was accidentally right, and from inside
the article there was no way to tell which was which. That is the actual cost of a bad input: not
that everything downstream breaks, but that you lose the ability to know what did.

Worth noting what the article could not see. One of the two omitted posts was a brand story that
breaks the very frame it was accusing the catalog of overusing. The other was a services offer. Both
were counterexamples to its own thesis, and both were invisible to it.

### The arithmetic that fails on its own terms

There is a tell that needed no external check at all. The article states its own frame in one
sentence and then contradicts it:

```
Article's claim:  "no missing days, two days with two posts and one with three"
Article's frame:  16 posts across 14 days

Implied:  14 days, no gaps, so 11 single days + 2 doubles + 1 triple.
          11(1) + 2(2) + 1(3) = 11 + 4 + 3 = 18 posts.  Not 16.

Reality:  July 27 had two posts.  July 28 had two posts.
          No day had three.  12 singles + 2 doubles = 16 over 14 days.
```

There is a second tell in the same file. Further down, the article cites "the 07-27 brand-arc spine
post" by name as a load-bearing example. It is discussing a post that its own chronology table does
not contain.

That is the tell. A number that fails its own internal arithmetic did not come from counting
anything. It came from a summary of a summary. Somewhere in the chain, a real count was replaced by
a plausible sentence, and no stage after that had any way to notice.

## Where the ghost came from

Here is the mechanism, and this is the part that actually matters.

The 04:00 producer ran against a **stale, diverged checkout**. The wrapper asked it to produce
**one** date. Working from an out of date view of what already existed, it produced **two**. The
lander then committed **both** decision records into the append-only `decisions.jsonl` while
publishing only **one** post.

Lines 259 and 260 of `decisions.jsonl`, adjacent, from the same run:

```jsonl
{"date":"2026-07-27","slug":"the-day-the-green-checks-were-lying","tier":1,"tier_name":"Field Note","confidence":0.8, ...}
{"date":"2026-07-28","slug":"locked-out-of-a-free-course","tier":2,"tier_name":"Technical Deep-Dive", ...}
```

One wrapper invocation. Two dates. The 07-28 post is real and live. The 07-27 one is the ghost.

Both records are well formed. Both pass schema validation. Both say published. One of them
describes a file that never reached the deploy branch, never got a URL, and never returned anything
but a 404.

A readiness sentinel got written for it too. The producer attests `ready:true` when its quality
gates pass. Those gates ran against a file on disk. The file was real. The gates were honest about
the file. Nothing in that attestation had any opinion about whether the file would ever be tracked,
committed, or served.

Eight days later the meta audit ran. It needed a catalog of what the blog had published. It read
`decisions.jsonl`, because that is the pipeline's own record of what the pipeline did. It got a
ghost, and it printed the ghost.

This is a provenance failure, not a validation failure. Every individual stage did exactly what it
was written to do. The defect is that the audit's ground truth came from inside the thing being
audited.

## Why the heartbeat was green

Skip forward to the morning of July 31, the day the investigation ran. That day's 04:00 job is a
different run from the July 27 one that produced the ghost, and it failed in a different way. It
reported success and published nothing.

The idempotency check exists so a manual run and the cron run cannot collide. It asks: does a post
for this date already exist? It answered yes, because the file was sitting right there in
`content/posts/`. On a feature branch. The probe never asked which branch.

Here is the probe that lied, verbatim from `lib-cron-common.sh` as it stood that morning:

```bash
# It answers "is there a file with this date in its front matter"
# when the question is "is there a PUBLISHED post".
post_exists_for_date() {
  local posts_dir="$1" d="$2" hit
  hit=$(grep -rlE "^date = ['\"]?${d}|^date: ['\"]?${d}" "$posts_dir" 2>/dev/null | head -1)
  [ -n "$hit" ] && { echo "$hit"; return 0; }
  return 1
}
```

A `grep` over the working tree. No `git ls-files`. No branch check. No cleanliness check. If the
bytes are on disk, the day is covered. Exit 0, heartbeat green, nothing published.

Exit 0. Summary email says fine. No alert fires, because from the wrapper's point of view nothing
went wrong. A branch-unaware existence check turns "someone has a draft open" into "we shipped."

## PR surface is not publish surface

The meta article claimed CI all passed. On the PR, that was true. Voice lint passed. The pinned
Hugo 0.150.0 build passed. ShellCheck and Ruff passed.

Post merge is where it fell apart. The merge commit's VPS deploy workflow had a **startup failure**,
meaning it never ran a single step. The release workflow failed immediately. Two comments containing
an empty GitHub expression had invalidated the release workflow file, and the VPS caller was
omitting required inputs and secrets.

So both publish-side workflows were dead, and the article was live anyway. The site was mid
migration. `dig +short startaitools.com` still returned `75.2.60.5`, which is Netlify. Netlify still
had a build hook. Netlify built the merge commit and served it. The VPS deploy path being broken
changed nothing the reader could see.

The article was reachable only because a decommissioned-in-principle host had not been switched off
yet. That is not a passing deploy. That is a deploy that failed into a fallback nobody had declared
as a fallback. If the DNS cutover had happened two days earlier, the same merge would have shipped
nothing and reported nothing.

The investigation ended read only. Five P1 and P2 remediation defects filed in Beads with evidence
and acceptance criteria attached. Zero repository content or scripts changed. The verdict handed
back was blunt: the qualitative concern in the article was real, the audit under it was not
reliable, and neither was its "all green" conclusion.

## Five invariants

Jeremy's next instruction, verbatim:

> lets fix all this and lets look in intent os and get tgis site hosted on our production vps

Two jobs at once. Fix the pipeline, and move the site off the host that had been silently covering
for it.

[PR #54](https://github.com/jeremylongshore/startaitools.com/pull/54) landed the fix: 16 files, +618 and -160. Five invariants, enforced across the pipeline and
regression-tested by `scripts/blog/test-pipeline-invariants.sh`. Three of them close failures
narrated above. The last
two close findings from the same investigation that I have not shown yet, so here they are: the
producer is architecturally forbidden from touching git (it produces artifacts, the lander commits
them), and it had drifted into doing git work anyway, which is how it ended up reasoning about a
checkout state it should never have been able to see. And cross-post processing only ever ran
**inside** the land path, so any post that reached the deploy branch by another route (a manual
merge, for instance) silently got no ledger entry and no queue row at all.

They live in four different files, which is worth saying plainly, because "we added a test file" is
not the same as "the rule is enforced":

1. **Normalize and fast-forward before deciding a day is covered** (`lib-cron-common.sh`,
   `preflight_branch_normalize`). Fail closed if the worktree is dirty or diverged. The producer ran
   on a stale checkout and reasoned about a gap that did not exist.
2. **Only tracked, clean posts count as published** (`lib-cron-common.sh`). This is the one that
   kills the ghost.
3. **Every decision delta is bound to the exact target date and slug** (`blog-land.sh`). A run asked
   for one date gets to write one date.
4. **The producer may not move Git HEAD** (`blog-backfill-daily.sh`).
5. **The cross-post queue runs from its own scheduled sweep** (`blog-crosspost-sweep.sh`), not from
   inside the land path.

Number two is the actual repair, and here it is as it shipped:

```bash
# A local file is not proof that a date was published. Return the first
# matching post that is tracked by Git and unchanged at HEAD. Untracked or
# modified producer debris must never satisfy the daily idempotency gate.
published_post_for_date() {
  local repo="$1" posts_dir="$2" d="$3" hit rel
  while IFS= read -r hit; do
    [ -n "$hit" ] || continue
    rel=${hit#"$repo"/}
    if git -C "$repo" ls-files --error-unmatch "$rel" >/dev/null 2>&1 \
      && git -C "$repo" diff --quiet HEAD -- "$rel" 2>/dev/null; then
      echo "$hit"
      return 0
    fi
  done < <(grep -rlE "^date = ['\"]?${d}|^date: ['\"]?${d}" "$posts_dir" 2>/dev/null || true)
  return 1
}
```

Same `grep` as before, now wrapped in two questions the old probe never asked: is this file tracked,
and is it unmodified at HEAD. The deploy-branch guarantee does not live in this function. It comes
from invariant 1 having already fast-forwarded the worktree onto the deploy branch before this
function is ever called. Those two together are what "published" now means.

And number four, which is the producer/lander boundary made non-negotiable:

```bash
PRODUCER_HEAD=$(git -C "$BLOG_DIR" rev-parse HEAD)
# ... run the producer ...
if [ "$(git -C "$BLOG_DIR" rev-parse HEAD)" != "$PRODUCER_HEAD" ]; then
  log "FATAL: producer changed Git HEAD; producer/lander boundary was violated."
  exit 1
fi
```

Invariant 2 is the important one. It moves the definition of "published" out of the pipeline's own
bookkeeping and into git, which the pipeline does not author. That is the actual repair. Everything
else is hygiene around it.

PR #54 also failed closed on stale or diverged deploy state and on target-mismatched decision
records, gave Dev.to and Hashnode an independent sweep with durable terminal history, corrected the
live 14 day inventory and gated it against the git-tracked catalog, repaired the invalid release and
VPS reusable-workflow declarations, and reconciled the scheduling docs with the live operating
model.

One detail I want on the record. The manual Tier 2 methodology, ledger, and queue records that were
genuinely missing got **restored honestly**, not invented. No fabricated agent runs were written
into the audit trail to make the numbers line up. Fixing a provenance bug by manufacturing better
provenance would have been the same disease with better output.

Validation actually run before merge: `actionlint` over the workflows, `shellcheck -S style` over
every pipeline script, Ruff on changed and new Python, the invariant suite, a deterministic 16 post
catalog audit for 2026-07-16 through 2026-07-29, changed-post voice lint, and a full production
Hugo build. Also confirmed: none of the four bypassed Tier 2 posts existed on Dev.to or Hashnode, so
re-queuing them could not duplicate anything.

## The cutover

Netlify to the Contabo VPS, behind Caddy, in the same session.

### Staging everything behind the old DNS

The project's own migration runbook was stale in two ways. Its reusable-workflow wiring was invalid,
and its Caddy example did not match the live ingress standard. Decision: treat the live Intent OS
inventory and host procedures as authoritative, not the checklist. Same lesson as the crontab
mismatch at the top of this post. A written procedure is a claim about a system, and claims decay.

VPS recon was clean. Caddy and Tailscale healthy, no existing site directory, no deploy command, no
vhost, no forced key to collide with. GitHub had none of the four required deploy secrets. So
everything additive got staged **behind the existing Netlify DNS** and validated directly against
Caddy before any record changed.

### The credential that Tailscale rejected

Then the blocker. Deploys authenticate to the tailnet through a repo-scoped federated identity, a
trust object that has to be created by an authenticated call to Tailscale's management API. The
SOPS-stored Tailscale API key is the credential for that call, and Tailscale rejected it. No valid
credential, no federated identity, no automatic deploy. Two bad options were on the table: weaken
SSH, or reuse another repo's identity. I refused both. The GitHub auto-deploy workflow was left
**fail-closed**, and the cutover proceeded on the command-restricted manual deploy path.

Say that plainly. The site is live on the VPS. The automatic deploy path is deliberately still dark.
That is a human dependency I chose over a security shortcut, and it stays open until the credential
is renewed.

### Why you cannot validate TLS before you cut over

The pre-cutover probe behaved exactly as the ordering constraint says it should:

```console
$ curl -sS -o /dev/null -w '%{http_code} -> %{redirect_url}\n' http://startaitools.com/
308 -> https://startaitools.com/          # Caddy is answering. Redirect is correct.

$ curl -sS https://startaitools.com/ >/dev/null
curl: (35) TLS connect error                # expected, not a failure
```

Caddy's default HTTP-01 challenge cannot obtain a certificate for a domain whose DNS still points
somewhere else. The challenge is answered over port 80 on whatever host the record resolves to, and
that was still Netlify. HTTPS cannot complete until after the DNS change, which means you cannot
fully validate TLS before cutting over. You validate everything else, back up the zone, capture
rollback values, and then move the records.

There is a way around that ordering constraint, and I did not take it. A DNS-01 challenge proves
domain control with a TXT record instead of an HTTP request, so it can issue a certificate before
the A record moves. It needs a DNS provider module wired into Caddy with credentials that can write
to the zone. Given that the whole point of this exercise was cutting down on machinery that can
silently do the wrong thing, adding zone-write credentials to the web server to save one minute of
certificate wait was not a trade I wanted.

### Verification after the records moved

Zone backed up. Rollback values captured. Apex A record edited, `www` CNAME replaced with an A
record. Then verification:

```bash
# Every one of these passed post-cutover.
dig +short startaitools.com          # -> VPS
dig +short www.startaitools.com      # -> VPS
curl -sI https://startaitools.com/   # valid cert, 200
curl -s  https://startaitools.com/healthz            # required JSON

# The six legacy redirect rules, all 301, all still honored by Caddy:
#   /en/blogs/*  ->  /posts/:splat
#   /blogs/*     ->  /posts/:splat
#   /projects/*  ->  /posts/
#   /skills      ->  /about
#   /resume      ->  /about
#   /startai/*   ->  /posts/startai/:splat

curl -o /dev/null -s -w '%{http_code}\n' https://startaitools.com/api/forms/subscribe
# 405
```

That 405 is the check I care about most. The forms proxy only accepts POST. A GET against it should
return 405 Method Not Allowed. If it returned 404, that would mean Caddy has no route for the path
at all and the proxy is simply not wired. A 404 there looks like a missing page and is actually a
missing integration. 405 proves the route exists and is enforcing its method.

HTML and CSS cache policies were checked against their intended classes. Two cutover-only defects
surfaced during verification and got fixed on the spot: private build-directory permissions causing
a 403, and a relative-name delete bug in the DNS helper.

## The syndication regression

The first cross-post sweep against the newly live site found a fresh bug, which is what first
sweeps are for.

Transformed cross-post files inherited **random temporary filenames**. The processor derived the
external canonical URL from the filename it happened to be holding. So the canonical URLs written
into Dev.to and Hashnode pointed at nothing.

```
# Wrong: canonical derived from whatever temp file the transform produced.
canonical = url_from(tmp_path)          # -> /posts/tmp8f3k2a9/

# Right: the queue already carries the canonical URL. Use it. Do not re-derive
# a fact you were handed.
canonical = queue_entry["canonical_url"] # -> /posts/<real slug>/
```

Same class of bug as the ghost, one layer out. A downstream stage re-derived a fact instead of
carrying it, and the derivation was wrong.

[PR #55](https://github.com/jeremylongshore/startaitools.com/pull/55), 3 files, +102 and -22. The processor now uses the queue's canonical URL explicitly, keeps
diagnostic output out of stored URL fields, converts transient API failures into **scheduled
retries with a retry timestamp** instead of a false terminal state, and rejects HTTP 200 Hashnode
GraphQL errors and invalid publish URLs.

Both platforms expose safe in-place update operations, so six already-published Hashnode copies and
two Dev.to copies were repaired in place. No deletions, no duplicates. Final state: 6 Dev.to posts
plus 6 Hashnode posts, all 12 canonical URLs verified directly through each platform's API.

One more correction, and I am including it because leaving it out would be the exact failure this
post is about. My working notes from that evening say the automated Kilo reviewer flagged the
[PR #55](https://github.com/jeremylongshore/startaitools.com/pull/55) patch and that I inspected the
finding before merging. I went to pull the finding while writing this. There is no finding. The only
thing `kilo-code-bot` posted was a billing notice:

```
Kilo Code Review could not run. Your account is out of credits.
```

(Paraphrased to keep this post's no-dash rule; the original uses a dash.)

The PR has zero reviews on it. A bot that could not run left a comment in the record, a summary read
"the bot commented" as "the bot reviewed," and I nearly published that as a claim about code quality
in an article about fabricated records. The reviewer was not a gate. It was a receipt for a gate
that never ran.

Three releases shipped that day: v1.1.0, v1.1.1, v1.1.2. Final live commit `3437a5f1`.
The Intent OS deployment assets and automation registry landed as [intent-os PR #304](https://github.com/intent-solutions-io/intent-os/pull/304).

## What this cost

Honest ledger of what got traded away.

**Auto-deploy is still dark.** The repo-scoped GitHub workload identity does not exist because the
Tailscale key is rejected. Deploys go through the command-restricted manual path until that
credential is renewed. Live site, human in the loop.

**Netlify stays as rollback.** Two hosts for one site is not a state to be proud of. It stays until
the VPS path has a real soak behind it.

**The append-only log now carries a record of its own contamination.** `decisions.jsonl` is
append-only and never rewritten. The bad record from that morning is still on line 259, and it will
be there forever. The correction went in as a new line rather than an edit:

```jsonl
{"date":"2026-07-27","slug":"the-day-the-green-checks-were-lying",
 "publication_status":"not_published",
 "reconciliation_reason":"Producer artifact was never tracked, merged, or live. A later landing
 committed its decision records without its post. Retained as an append-only correction; the source
 file remains recoverable outside the published catalog."}
```

That is by design. Rewriting history to hide a provenance bug is exactly the behavior that caused
the problem. The invariants prevent new ghosts. The old one stays visible as evidence, with its
correction stapled to it.

**The 04:00 producer is now stricter than it needs to be on a good day.** It will fail closed on a
diverged checkout that a human would have shrugged at. I would rather lose a day's post than publish
a day's fiction.

## Also shipped

### now-lms: a cache keyed by the wrong thing

**now-lms** and its security-advisory sibling **now-lms-ghsa** (**Claude Opus 5**), released 2.0.2.
The notable commit landed in `now-lms-ghsa`:
`fix(security): key per-view caches by user identity, not by auth state`. Per-view caches were keyed
by whether a request was authenticated, not by which user was authenticated, so two logged-in users
could share a cache entry. The failing test that pinned it was
`test_two_authenticated_users_do_not_share_a_cache_key`, whose assertion is simply that two users'
cache keys differ. They did not. The key was built from the authentication state, so every logged-in
user hashed to the same string.

Also landed: `fix(i18n): compile stale .mo catalogs at boot so Babel stops falling back to msgids`
(with a failing probe test written first, `test_probe_rejects_a_corrupt_mo`), test coverage for the
autocompile failure paths, the admin panel consolidated into `/admin/panel`, stat card contrast
ratios fixed for accessibility, and `fix(db): link overlapping course relationships with
back_populates`. That session opened by reading a previous agent's work out of Kilo's SQLite session
store at `~/.local/share/kilo/kilo.db` (three sessions, all running `minimax/minimax-m3`) to audit
what it had actually done, found real defects in a cherry-picked i18n commit, and rebuilt it on a
clean upstream base instead of shipping the cherry-pick.

### intent-os: feeding the wire

**intent-os** (**Claude Opus 4.8**), 8 commits, Buzz AI-Wire feed work. Added an HTML-scrape source
type to bridge Anthropic (which publishes no RSS) into the wire, filled empty lab channels via RSS
mirrors, expanded the deep-research feeds into commentary, funding, product, and research, split
commentary-wire from newsletters, added intent-wire so this blog flows into the wire, and moved the
feed cron from every 3 hours to hourly. The debugging beat: an agent was not answering mentions.
The root cause was not the model. An agent only hears mentions in channels it is actually a member
of, and it was sitting in `#agent-sandbox` while Jeremy was posting in `#welcome-everyone`.

### claude-code-plugins: seven PRs, zero approvals

**claude-code-plugins** (**Claude Opus 5**), brief. Checked whether a collaborator had accepted any
of seven external contributor PRs. Zero approvals, zero merges, seven "not mergeable yet" verdicts.

## The part that generalizes

Append-only audit logs get treated as authoritative because they are immutable. Immutability is a
property of the storage, not of the write path. An append-only file with a bad producer is a
permanent, tamper-evident record of wrong facts. You have hardened the wrong end.

The rule I would take out of this: **a self-auditing system needs its ground truth to come from
outside itself.** Not from the log it writes. From git tracking, which a separate tool owns, and
from live HTTP status, which the reader's own client can reproduce. If the audit and the audited
share a source, the audit cannot detect the one failure mode that actually matters, which is the
system being wrong about itself.

I ran restaurants for twenty years. You never let a station sign off its own line check. Not because
cooks lie, but because the person who prepped it is the worst possible witness to whether it is
ready. Somebody else walks the line with a thermometer. That is not distrust. That is what a check
means.

Across every thread that day, counted from the local session logs by the transcript analyzer that
feeds this pipeline: 951 tool calls, 46 failure-to-fix moments, 6 course-corrections, 1229
minutes of span. The correction that fits this post best came from a different repo entirely, on the
subject of alerting:

> i still dont think we have failures set up to ha[ndle]

Correct. We did not. A heartbeat that goes green when nothing shipped is not failure handling. It is
a mood ring.

## Related Posts

- [After 14 Days of Daily Posts, Here is What I Notice](https://startaitools.com/posts/after-14-days-of-daily-posts-here-is-what-i-notice/) is the article this post is about. Its chronology table was built on the contaminated record. It has been corrected on the live site.
- [Wrong-Mode Green Is Not a Gate](https://startaitools.com/posts/wrong-mode-green-is-not-a-gate/) covers the adjacent failure: a check that passes because it is asking a question nobody needed answered.
- [How the Same Deploy Pattern Crossed Four Repos in One Week](https://startaitools.com/posts/how-the-same-deploy-pattern-crossed-four-repos-in-one-week/) is the deploy substrate this site landed on.
