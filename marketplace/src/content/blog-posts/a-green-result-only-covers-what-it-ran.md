---
title: "Every Verdict Carries the Scope It Actually Ran"
description: "A verdict covers only what it ran. Four same-day cases, including a request-forgery class closed by deleting the feature it lived in."
date: "2026-08-25"
tags: ["security", "testing", "ci-cd", "devops", "architecture", "automation"]
featured: false
canonical: "https://startaitools.com/posts/a-green-result-only-covers-what-it-ran/"
---
The third review comment on the marketplace submission did not name a bypass. It named the class.

Two rounds before it, a human reviewer had handed me two working payloads and I had fixed both. Round three said the fixes were beside the point: the policy validates a hostname string, and a hostname string is not an address. An ordinary attacker-controlled name can resolve to 127.0.0.1, to an RFC1918 range, or to link-local. DNS rebinding can change what it resolves to after any check I perform separately from the fetch. Nothing I could write into that validator would change the fact that it was answering a question about spelling while the request was making a decision about routing.

The offline test suite was green at exactly the commit the reviewer's comment named. Local HEAD was `d26746cbbfdcd4282ef1a3faa9b303f14b3f3a3e`, 83 tests, all passing. That green means the spellings the suite knows about get rejected. It says nothing at all about the resolution step, because the resolution step belongs to curl and the suite never runs curl.

That is the same defect the `/omarchy-ship` lane exists to refuse. That lane is the checklist every Omarchy plugin goes through before it is submitted, and its whole job is to reject a receipt that claims more than the run behind it covers. A component had reported a conclusion whose scope it never established.

It happened four times that day. Once in the security fix. Once in a metrics gate that had never been observed failing. Once in a set of analytics tags that would have looked like measurement without being measurement. Once in nine pieces of social copy that read well and could not be found. The fixes had nothing in common mechanically. One deleted code, one deliberately broke a file to watch a check fire, one declined to build a thing at all, one added a lint. What they share is a direction: in each case the claim got cut back to what had actually been established, rather than propped up with more machinery.

## The submission was never the obstacle

`omarchy-listening-post-entry` is a bar plugin for Omarchy that reads RSS and news feeds. It shipped with 29 curated sources plus a field where a user could paste their own feed URL. The marketplace submission is [`HANCORE-linux/omarchy-plugin-marketplace#1229`](https://github.com/HANCORE-linux/omarchy-plugin-marketplace/issues/1229), opened 2026-08-21, carrying the labels `submission`, `validated`, `needs-fixes`.

Automated validation passed on the first pass. Public and reachable. One valid manifest. README and license present. Quattro compatibility green at `3759cfe`. The automated security baseline passed too.

So the listing pipeline had nothing to say. A human review thread on the custom-feed field had three things to say, in three rounds, and the escalation is the whole story.

### Round one: the hostname was not the hostname

Reviewer `ryanrhughes` sent the first payload:

```
https://user@127.0.0.1/feed
```

The private-host check read URL userinfo as part of the hostname. `user@127.0.0.1` is not in any private range, because as a string it is not an address at all. The check said public. curl parsed the same URL correctly, discarded the userinfo, and dialled loopback.

Fixed in `e8d00af`. Two things changed, and the second one mattered more than the first. The check moved out of `Service.qml` and into `Model.js` so the offline suite could actually cover it, and the reported payload got pinned as a regression test. A validator living in a QML file that only runs on a live bar is a validator nobody can test.

### Round two: the address had more than one spelling

Reviewer `HANCORE-linux` sent two more:

```
https://127.1/feed
https://0177.0.0.1/feed
```

Both reach loopback. The cause is [`inet_aton`](https://man7.org/linux/man-pages/man3/inet_addr.3.html), which accepts one to four parts and reads each part in decimal, octal, or hex. `127.1` is a two-part form where the second part fills the remaining 24 bits. `0177` is octal for 127. Neither string starts with the text `127.0.0.` that a naive range check looks for.

The fix rejected every form the parser recognizes as an address, rather than trying to enumerate the notations. That felt like progress. It was progress on the same axis: I had gone from handling one spelling to handling all spellings, and the axis itself was wrong.

### Round three: the class, server-side request forgery

On 2026-08-24 the same reviewer stopped supplying payloads. The comment observed that the policy validates a hostname string, and that hostname strings do not carry the property being checked. An attacker does not need a clever spelling. They need a domain they control with an A record pointing at 127.0.0.1. If I resolve the name to check it and then hand the name to curl, curl resolves it again, and the second answer does not have to match the first.

The comment named two options.

**Option one, resolve and pin.** Resolve the host myself. Reject every non-public result. Bind the validated address to the request so the name is never resolved twice. In curl terms that is an explicit [`--resolve host:port:addr`](https://curl.se/libcurl/c/CURLOPT_RESOLVE.html) pin, plus `--proto =https`, plus `--max-redirs 0`, with every redirect hop re-validated in `Model.js` rather than followed by curl. This is the only option that keeps arbitrary custom feeds working.

Sketched out, the safe fetch looks roughly like this, and the sketch is the argument against it:

```bash
# option one, in outline. every line here is a thing that can be
# subtly wrong, and the whole point is that a subtle wrong is
# indistinguishable from correct until somebody exploits it.
addr="$(resolve_a_record "$host")"          # my resolver, not curl's
is_public "$addr" || exit 1                 # reject loopback, rfc1918, link-local
curl --resolve "$host:443:$addr" \
     --proto '=https' \
     --max-redirs 0 \
     "https://$host/$path"
# and then: parse the Location header myself, re-run the whole
# block for every hop, and get the hop budget right too.
```

Four moving parts, and the redirect loop means the first three run again per hop. Every one of them has to hold under an attacker who controls the DNS answer and the redirect chain.

**Option two, remove arbitrary custom-feed hosts.** Ship the 29 curated sources. Drop user-supplied feed URLs entirely.

I asked Jeremy which way to go. The steer came back in one line:

```
fix listening post drop the custom feeds
```

## Why the smaller fix won

I wanted to build option one. It is the interesting one. It is also four separate pieces of security machinery (resolution, rejection, address pinning, per-hop redirect revalidation) each of which is its own opportunity to be subtly wrong, protecting a field that is not why anyone installs this plugin.

The pitch is 29 curated sources in your bar. The custom-feed box was a convenience nobody asked for. And there is a working escape hatch for the case it served: a missing feed gets added to the curated list, where it is reviewed like everything else in the list.

The tradeoff is real and worth stating rather than hiding.

| | Resolve and pin | Remove the surface |
| --- | --- | --- |
| Arbitrary user feeds | Kept | Gone |
| New code paths to get right | Four | Zero |
| Failure mode if I get it wrong | Silent forgery from a shipped plugin | None, the code does not exist |
| Testable offline | Partially, the resolution step is not | Fully |
| Reviewer can verify by reading | No, needs runtime reasoning | Yes, the constants are visible |

The bottom row is what decided it. A reviewer approving option one has to reason about runtime behavior they cannot observe from the diff. A reviewer approving option two reads a list of `https://` string constants and is done.

Commit `30ac415` at 15:14: `fix(security): remove custom feed hosts, closing the request-forgery surface for good`. Version 1.1.0.

Removed:

- `extra-sources.json`
- `Service.extraSources()`
- the `extrasFile` reader
- the `extrasPath` property
- `Model.isPublicHost()`

Every source the plugin fetches is now a compile-time constant in `Model.SOURCES`. Seven files changed, 83 insertions and 211 deletions, which is the honest summary of the change: `CHANGELOG.md`, `Model.js`, `tests/model.test.js`, `README.md`, `Service.qml`, `manifest.json`, `package.json`. The two files carrying most of the churn are `Model.js` and its test file, at 91 changed lines each.

## The deletion had to be provable

Deleting code is easy. Keeping it deleted is the actual engineering, because the next person to want a custom feed field will write `isPublicHost` again, in good faith, and the suite will not care.

So the eleven `isPublicHost` tests were replaced with two tests that assert the absence.

```js
test("the custom-feed host allowlist is gone and must not come back by name", () => {
  assert.equal(Model.isPublicHost, undefined)
})

test("every fetched source is a compile-time constant, none is user supplied", () => {
  assert.ok(Array.isArray(Model.SOURCES))
  assert.ok(Model.SOURCES.length > 0)
  for (const s of Model.SOURCES) {
    assert.ok(typeof s.url === "string" && s.url.startsWith("https://"), s.url)
  }
})
```

Plain `node:test` with `assert`, no framework. The first test name is doing work that the assertion cannot: `assert.equal(Model.isPublicHost, undefined)` on its own tells a future reader that something is absent, and nothing about why. The name tells them the absence is the point and that reintroducing the function by name is the failure being guarded against. A test name is the only part of a test that shows up in the failure output, so it is the cheapest place to put the reason.

Note the shape of the result. The suite got smaller and the guarantee got stronger. Eleven tests were each pinning one spelling of one address, which is eleven assertions about the same wrong axis. Two tests pin the class: there is no host-validation function, and no fetched URL is a runtime value.

Here is the shape of what the suite lost and what it gained, because the raw number moving down is the confusing part:

| | Before | After |
| --- | --- | --- |
| Tests about host validation | 11 | 2 |
| What they assert | this spelling is rejected | the function does not exist |
| Fails when a new notation appears | only if someone adds a twelfth test | not applicable, nothing parses hosts |
| Fails when the surface comes back | no | yes, immediately |
| Total suite | 83 | 74 |

`Model.js` also carries a comment where the old call site used to be. It names the finding and states the two conditions any future user-supplied URL would have to meet before it could be fetched. That is not decoration. The comment is where the next author looks, and a comment that says why the code is missing is more useful than any amount of code that is present.

### The deletion was scoped, not indiscriminate

`Model.safeUrl` stayed. It validates URLs parsed out of feed bodies before they are displayed or clicked through. That is a different job. Choosing a host to fetch from is a request the plugin originates; rendering a link that came back inside a feed is content handling. Both need checking. Only one of them was the forgery surface.

Deleting everything with `url` in the name would have been the same failure in the other direction: an action whose scope was wider than the finding that motivated it.

### What was actually verified, and what was not

Verified:

- Offline suite: 74 tests, 74 pass, 0 fail. That is 83, minus the 11 `isPublicHost` tests, plus the 2 absence guards.
- Vendored gate lane: PASS, 9 gates enforced, including `c38` and `c31`.
- Zero em dashes and zero en dashes across the tree.
- No non-comment reference to extras or `isPublicHost` remains in `Service.qml` or `Model.js`.

The finding closed too. Issue `#1229` went to CLOSED at 23:23 UTC on 2026-08-25, carrying the labels `submission`, `validated`, `listed`, and `approved-and-verified`. The removal shipped at 15:14 local and the plugin was listed a few hours later the same night. Two rounds of validator patches never moved that label. Deleting the field did.

Not verified, and this is the post's own instance of its thesis: the change was never re-verified on an Omarchy rig. Rig render and `omarchy-plugin-validate` are unproven rather than passing.

The reason written into the commit body at 15:14 is that the `omarchy-rig` container was not present on this box, and at 15:14 that was true. It stopped being true about six hours later. The rig was up that evening and handed out receipts to everything else: loose-ends at 21:32 and 21:33, quiet-queue at 21:58, flow-boundary at 22:01, desk-transition at 22:06. Listening Post never got back in the queue, because by the time the rig was running, the attention had moved to a new plugin.

So the plugin's newest rig receipt is still the one from 2026-08-22 at 10:29, three days older than the change it is supposed to cover. The argument that the change is safe is decent, since it removes code and touches no QML rendering path. An argument is not a run, and a receipt whose scope stops three days short of the change is the same defect as a green suite that never ran curl, this time with my name on it.

## Sibling one: corrupting the CI gate to see it fire

The same morning, a new `omarchy` umbrella repo went up (`60e3fff` at 12:16, 821 insertions) with an org landing page whose README carries a generated metrics table. `scripts/refresh-metrics.sh` regenerates it, `refresh-metrics.yml` runs it, and a `--check` lane on pull requests is supposed to fail when the committed block has drifted from what the script would produce.

Supposed to. Nobody had watched it fail.

Commit `c8bf8be` at 12:32: `test(ci): hand-edit the generated metrics table to prove the staleness gate fires`. The corruption was one table row, renamed from `**Bazaar**` to `**Bazaar (hand edited)**`. The commit body says the branch is not for merge, that it exists to verify the gate is real rather than assumed, and that it gets deleted once the check reports failure.

A gate that has never failed has not been observed working. It has been observed being quiet, and quiet is what a broken gate and a satisfied gate look like from the outside.

The gate's first observable state is the detail worth keeping. The workflow was created already broken in `60e3fff` at 12:16: the continuation lines sat at column 0 from the start, so GitHub parsed the file into zero jobs and ran nothing (run `32882805663`). `1395866` at 12:18 repaired the block scalar. For those two minutes the gate could not have fired even if every line of its logic had been right, and the pull-request view looked exactly the same as it would have if the gate were working.

## Sibling two: the UTM tags that were refused

Nine outbound social packets were dispatched that day. Seven point at individual marketplace listings, one at the widget template, and one at the umbrella portfolio page. None of the marketplace links carry a UTM parameter, and that was a decision rather than an oversight. It is written up in `000-docs/003-RP-BASE-showcase-campaign-baseline.md`, with the lane built in `89afdfa` at 12:27 and `fe425f7` at 12:29.

The reasoning: analytics for `omarchyplugins.com` belong to the marketplace. A `utm_source` attached to a link into someone else's property is a parameter nobody on this side can ever read back. Adding it produces the appearance of measurement without measurement, which is worse than nothing, because a dashboard with tagged links on it implies somebody is reading them.

Two signals are genuinely readable, and both were captured on the day.

1. **The marketplace's own public stats endpoint.** Views, copies, and hearts per plugin. `copies` is the closest thing exposed to an install, so that is the conversion metric.
2. **GitHub traffic on repos we own.** GitHub reports referrer hostnames natively, so `x.com` and `linkedin.com` arrive already separated with no tagging needed. That is also why the GitHub links in the packets are untagged: the tag would add nothing the platform does not already report.

The timing constraint is the part worth copying. GitHub traffic is a rolling 14-day window and cannot be backfilled. Miss the day and the pre-campaign number is gone permanently, so a same-day capture was the last chance at a number that predates the campaign. It was taken at 13:12 local, which is after the packets were dispatched to Ezekiel but before any of them were posted publicly. Dispatched and posted are different events here, and next to a discussion of referral windows the difference is the whole point.

Marketplace snapshot `2026-08-25T18:12:41.735Z`, across 1,366 listed plugins:

| Plugin | Views | Copies | Hearts | GitHub views 14d | Uniques |
| --- | --- | --- | --- | --- | --- |
| Bazaar | 199 | 20 | 0 | 8 | 6 |
| Pit Wall | 113 | 19 | 3 | 15 | 7 |
| Wait State | 100 | 9 | 0 | 2 | 2 |
| MLB Booth | 92 | 2 | 1 | 16 | 5 |
| X Files | 90 | 1 | 1 | 5 | 2 |
| Docket | 89 | 3 | 1 | 1 | 1 |
| Crew Chief | 66 | 8 | 1 | 4 | 2 |
| Listening Post | none yet | none yet | none yet | 5 | 2 |
| Widget Template | none | none | none | 1 | 1 |

The two blank rows mean different things. Listening Post had no marketplace row because its submission was still open at 13:12 local, and that changed the same evening when the listing went live. The widget template has no marketplace row because it is not a marketplace entry at all. Which is a small instance of the same subject: the table is accurate for the moment it was taken and for no moment after.

The baseline exists to answer two questions.

**Why are the two most-viewed listings the two with zero hearts?** Hearts do move: Pit Wall has 3, and four other listings have 1. But Bazaar sits at 0 on 199 views and Wait State at 0 on 100, which are the two highest view counts in the table. Nothing in either product asks anybody for a heart. If a campaign cannot move those two numbers, the fix is on the listing page rather than in the posting.

**Does X or LinkedIn send more traffic here?** The audience is Arch and Hyprland users, which argues for X. The LinkedIn copy carries the engineering argument, which argues the other way. GitHub's referrer hostnames answer that, and they answer it for every campaign after this one, which is the actual return on doing the boring baseline.

What they do not answer is which platform converts, because conversion is `copies` and `copies` lives on the marketplace, which exposes no referrer dimension at all. The instrument is narrower than the question. Writing that down is the difference between a measurement and the appearance of one, which is the subject of this entire piece, and it took a review pass to catch me doing it.

Listening Post got no packet at all. There was no listing page for a packet to link to, and pushing a plugin publicly while a marketplace reviewer has a documented open security finding on it costs more than one fewer post is worth. The builder handles this case by construction: given a plugin absent from the catalog it emits a HOLD banner instead of a link. Fail-closed, so the human never has to remember the rule.

## Sibling three: copy that read well and could not be found

Nine showcase packets (an X post plus two LinkedIn variants each) had already been generated and emailed to Ezekiel earlier that day. Then somebody read them.

Four of the nine X posts never said the word Omarchy anywhere: wait-state, x-files, docket, crew-chief. None of the nine carried a single hashtag. Omarchy was trending on X at the time.

A post about an Omarchy plugin that never names Omarchy is invisible to every single person searching for one. The commit body puts it better than I can paraphrase it: the copy was written to read well, which it did, and to be found, which it did not.

Commit `d37bc55` at 13:58: `fix(packets): name Omarchy in every post and add the discovery terms the first pass threw away`.

The fix front-loads the term instead of appending a "for Omarchy" tag line at the end. Two reasons. The first line is what shows in a truncated timeline preview, and the first line is what the search index weights hardest. A term in the last line is a term nobody sees and nothing indexes strongly.

The guard is a lint at the render step. The builder now refuses to render a packet when:

```
- the X post does not name Omarchy
- the X post carries fewer than three hashtags
- the LinkedIn copy does not name Omarchy
```

From the commit body: this class of miss is exactly what a lint is for, invisible on a read-through and obvious to a checker. Nobody proofreading nine packets for quality would flag "excellent post, does not contain a required keyword," because that is not what reading for quality does.

Verified after the fix: all nine X posts name Omarchy, all carry four hashtags, all land between 457 and 620 characters. The X opener and both LinkedIn openers still differ in all nine, so the lint did not flatten them into one voice. Zero em or en dashes, no URL in any authored field, clean against the voice deny-list. The nine corrected packets were re-sent to Ezekiel with the subject prefixed `CORRECTED, use this one`, and the nine Plane issues were re-synced in place, updated rather than duplicated.

## Where the packets go, and why they go into Plane

Ezekiel does the actual social posting, remote, from emailed packets. The lane that builds them went in at `89afdfa` (12:27): `scripts/build-showcase-packet.py` at 180 lines, `scripts/campaign-baseline.py` at 158, `showcase-packets.json` at 106, plus the baseline doc.

Then `87b04a8` at 12:57: `feat(plane): mirror the showcase packets into Plane so done is a state, not a report`. That is `plane-sync-packets.py` at 200 lines and `plane-assign-when-accepted.sh` at 48. Jeremy's steer that drove it:

```
is there a way ezekiel can get into plane and we track all his work
in plane so we know it is done ?
```

That mirror is the back half of the packet lane rather than a separate story. The lane produces the copy; Plane holds the state, so completion is a queryable field instead of a claim sitting in somebody's inbox. The nine packets went to `ezekiel@intentsolutions.io`, CC Jeremy, ordered individual plugins first, then the widget template, then the portfolio page last, because a summary lands better once a few of the parts have already gone out.

## The model collaboration beat, and what it actually taught

Claude Opus 5 ran the Omarchy thread that day: 1,112 transcript records in the main session, 116 in a second one, and 263 in this blog session. Claude Fable 5 ran wild at 1,878 records and claude-partner-network at 87, with Claude Sonnet 5 and Claude Haiku 4.5 in smaller volumes. Records are not conversational turns, and the only roster fact the argument needs is that Claude Opus 5 wrote the nine packets.

The packet failure is a model-collaboration failure and an instructive one. Claude Opus 5 generated nine sets of social copy that were good prose and bad distribution. The brief asked for copy that read well. It never stated that the copy had to be findable. The model optimized precisely the thing it was asked for, and got it right.

The fix is not a better prompt. A better prompt is a thing that has to be remembered every time by whoever writes the next brief. The fix is a lint at the render step, which is the same shape as the absence-guard tests in the security fix: encode the requirement in a checker rather than trusting it to be recalled. Both cases replace an instruction with a refusal.

There is a human beat in the middle of this too. While the marketplace thread was open, Jeremy hit the session with:

```
what did u fuck something up wiht that maintainer whatsww the link
omg did u screw it up
```

That is what an open security finding on a public submission feels like from outside the terminal. The `needs-fixes` label sat on a public issue for days, on a repo with the maintainer's name on the thread. No amount of "the fix is straightforward" makes that read as calm.

## Also shipped

Breadth, not depth. None of this carries the argument above.

- **omarchy-loose-ends-entry**: a new plugin built end to end the same day, a Git work queue. Initial commit 19:13, feat 20:28 (build the Loose Ends Git work queue), test 21:32 (harden shipping evidence), fix 21:32 (bound scanner output and report truncation), test 21:33 (refresh rig evidence for the bounded scanner), chore 22:07 (refresh the canonical plugin gate lane). Jeremy's steer was `build loose ends next`. The output-bounding fix is a small echo of the day: a scanner that reported without bounding what it reported.
- **Other Omarchy entries**: quiet-queue got an owner-aware quiet queue plus a rig render receipt, flow-boundary a local flow boundary ledger plus rig render, desk-transition safe desk transition scenes plus rig render, and workspace-storyboard and capture-conveyor both took work.
- **cad-dxf-agent** (renamed cad-ai-agent): a full 7-layer testing SOP retrofit. audit-harness v0.1.0 installed with L1 enforcement hooks, L7 traceability docs retrofitted (TESTING, RTM, PERSONAS, JOURNEYS, 570 insertions), L2 CodeQL plus Trivy plus import-linter plus ESLint and L4/L5 contract plus a11y gates added (275 insertions across 9 files), then the SOP rebased on the current harness (3,382 insertions, 166 deletions). That was followed by five successive CI repair commits: update contract and Trivy actions, harden contract and container gates (183 deletions), resolve frontend production vulnerabilities, install the contract service runtime, scope the initial API contract gate. Adding five gates cost five repair commits to get green. That is the ordinary price and it is worth naming out loud, because the version of this story where gates install cleanly is the version nobody has ever shipped. Also relicensed MIT to Apache-2.0, added a `cad-analyze` CLI and a Claude Code plugin, and merged 7 dependabot updates.
- **claude-code-plugins**: governance editor and dependency policies (#1322), external-sync quarantine of the walkie-talkie mirror (#1320), modernization catalog and freshness blocker repairs (#1319).
- **contributing-clanker**: three gate-scoping fixes, excluding developer scripts from the runtime gate, batching ignored-file gate filtering, and excluding ignored dependencies from gate scans.
- Ko-fi added alongside existing funding sources across about fourteen repos. intent-os regenerated its mission-control status pages.

## The rule: compare what it asserts against what it ran

Four times in one day, something was set to report a conclusion whose scope it had never established. A test suite that said the host check was safe while never running the resolver. A staleness gate that said the metrics were fresh while having never once been seen to fail, and which for its first two minutes parsed to zero jobs. Nine posts that claimed a subject they never contained the word for. And a tag scheme that would have implied a campaign was attributed, pointing at a property whose analytics nobody on this side can read.

The diagnostic that held across all four is a pair of lists. What does the thing assert, and what did it actually run? The suite asserted safety and ran string comparison. The gate asserted freshness and ran nothing observable. The copy asserted a subject and contained no instance of the word. The tags never got that far, and that is the useful one in the set, because the mismatch was caught while the lane was still being written. Nothing was dropped, because nothing was ever attached. A near miss reads as less of a story than a bug, and it is the cheapest of the four by a wide margin.

The fixes shared no mechanism at all. One removed a feature. One broke a generated table on purpose and watched the check fail. One declined to build the tagging. One added a word, four hashtags, and a lint at the render step. What they share is direction. The bigger version of each was available and it was always the one I reached for first: fortify the validator, trust the gate because the YAML looks right, tag everything because tagging is what you do, write a better brief. Every one of those leaves the unearned claim standing, with more scaffolding around it.

Fixing the spelling is not fixing the class. The honest fix is usually smaller than the one I wanted to build, and it usually removes something.

Which brings it back to the rig. The security change is good, the suite is green at 74 of 74, the gate lane passes 9 enforced checks, and the marketplace listed the plugin that night. None of that covers rig render, because none of it ran a rig, and the newest rig receipt on the plugin is three days older than the change it is filed against. That is the whole finding, sitting in my own repo, on the day I wrote it up.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Every Verdict Carries the Scope It Actually Ran",
  "description": "A verdict covers only what it ran. Four same-day cases, including a request-forgery class closed by deleting the feature it lived in.",
  "datePublished": "2026-08-25T08:00:00-05:00",
  "author": { "@type": "Person", "name": "Jeremy Longshore" },
  "url": "https://startaitools.com/posts/a-green-result-only-covers-what-it-ran/",
  "isPartOf": { "@type": "Blog", "name": "Start AI Tools", "url": "https://startaitools.com" }
}
</script>

## Related posts

- [Make the Guard Prove It Can Fail](https://startaitools.com/posts/the-gate-that-could-not-fail/): four gates in one day whose verdicts were decoupled from the thing they claimed to measure, which is the direct ancestor of corrupting the metrics table on purpose.
- [Every Check Should Report What It Did Not Look At](https://startaitools.com/posts/the-lane-that-reviewed-nothing/): the lane-level version of the same finding, where the scope of a review is part of its output.
- [Refusing to Classify Beats Matching Harder](https://startaitools.com/posts/the-green-badge-came-back-through-a-hyphen/): a status classifier that refuses wording it cannot positively recognize, and the hyphen that walked past a negation guard.
