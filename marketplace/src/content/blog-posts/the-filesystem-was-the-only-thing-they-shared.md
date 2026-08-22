---
title: "The Filesystem Was the Only Thing They Shared"
description: "Four models, nine threads, one disk. Two missed nights with two unrelated root causes, and a bug filed against a file another session already fixed."
date: "2026-08-04"
tags: ["ai-agents", "claude-code", "automation", "debugging", "devops"]
featured: false
canonical: "https://startaitools.com/posts/the-filesystem-was-the-only-thing-they-shared/"
---
Nine AI coding threads ran on this box on August 4, across four models. They shared nothing by design. Separate processes, separate contexts, separate in-memory state. One session cannot read another's variables or see another's open files. The only surface they hold in common is the disk.

When two of them disagree about what is on that disk, the failure does not announce itself as a concurrency problem. It shows up as a scheduled job that quietly declines to run, a bug filed against a file somebody else already fixed, and a morning of permission denied on paths another session moved.

The day's best evidence for that is also, inconveniently, the day's best evidence against over-applying it. Two nights of blog posts went missing. Exactly one of them was this problem.

## The threads

Claude Opus 5 and Claude Fable 5 ran intent-os: 251 turns, 643 tool calls, 27 errors. The blog pipeline thread ran Claude Sonnet 5, Claude Fable 5, and Claude Opus 5: 162 turns, 342 tool calls, 11 errors. Claude Fable 5 ran intent-eval-platform: 84 turns, 213 calls, 15 errors. Claude Opus 5 ran the now-lms email session and the claude-code-plugins thread. Claude Sonnet 5 ran claude-partner-network. Claude Fable 5 also ran bobs-big-brain-umbrella. Grok 4.5 ran the claude-code-slack-channel thread. A ninth ran at the home-directory level for a team-brain review.

Nine threads on one filesystem. That is the collision surface. The three with the heaviest tool traffic account for 53 of the day's errors.

## Two nights, two root causes

The day opened with a question about the blog's social-posting packet, which goes to Ezekiel, who posts the syndication by hand. Was he still getting it?

He was. The 5am packet job had fired every day and reported "nothing to send" on August 2 and August 3. That is its correct behavior when no post landed.

This pipeline has gone quiet before. In June it published nothing for nine days while its monitoring reported success, and that one was also opened by someone noticing the absence rather than by an alert ([Nine Days Silent](https://startaitools.com/posts/the-automation-that-stopped-publishing-itself/)). The failure below is a different mechanism with the same tell.

Two turns later, the real question:

> why'd nothing land Aug 2 and 3 thats impossible we been doing work

Correct. Work had shipped. The problem was upstream of the packet, in the 4am producer.

`blog-backfill-daily.sh` runs a dirty-tree guard before it does anything:

```bash
git status --porcelain --untracked-files=no
```

Non-empty output means tracked files are uncommitted, and the script refuses. Untracked files do not trip it. Only tracked edits.

The first hypothesis was that this guard explained everything. It explained half of it.

### The night the guard fired

The second of the two. On the evening of August 2, a different session on this box rewrote 12 of the 13 scripts under `scripts/blog/` in a single bulk edit, migrating them off the retired Slack notifier onto the governed Buzz alert runtime at `~/bin/lib/intent-runtime.sh`. The work was legitimate and complete. It was never committed. The guard found a dirty tree and refused, exactly as designed:

```text
working tree has uncommitted changes on 'master'
```

### The night it never got that far

The first was self-inflicted, and had nothing to do with any other session. It never reached the guard at all. The preflight deliberately tolerates a dirty `.beads/interactions.jsonl` and commits it after the fast-forward. But this repo carried `pull.rebase=true` in local config, which routes `git pull --ff-only` through the rebase path. Rebase refuses any unstaged change. So the file the pipeline was designed to tolerate aborted the pipeline:

```text
cannot pull with rebase: You have unstaged changes
```

That is a real bug, in our own tooling, and it had been sitting there waiting for the tolerated-dirty file to show up.

## The fix did not take minutes

The tempting version of this story is that the cause was found and the thing was fixed. The commit log says otherwise.

`aef7b908` landed the stranded script refactor at 21:47 on August 3. Two backfills followed at 22:58 and 22:59, recovering the August 1 and August 2 posts. Then, still inside the same recovery session, the rebase failure reproduced. `f5a6358c` fixed it at 00:24 on August 4 by pinning the pull inside the code rather than trusting repo config:

```bash
git -c pull.rebase=false pull --ff-only origin "$default_branch"
```

One minute later the August 3 post landed at 01:03, about three hours before its own cron would have fired. When 04:00 came, that run found the post already published and correctly no-opped.

Even that was not clean. The land step first reported `FAILED (orphaned local commit)`, which was misleading, because nothing was orphaned and no commit had happened. The recovery session had inherited the producer's git guard shim on its `PATH`, a wrapper that exists specifically to stop the model from committing, so `git add` was rejected. The daily wrapper deletes that shim immediately before invoking the lander. Running the lander by hand from inside a producer session does not get that cleanup. Re-running with the shim off `PATH` worked first try, and then the wrapper noticed the producer had moved git HEAD and refused to push anything further:

```text
FATAL: producer changed Git HEAD; producer/lander boundary was violated.
```

That refusal was also correct. It is also, exactly, the day's subject: a session acting on state it inherited from a context it could not see.

Three hours and sixteen minutes from first fix to last post, across two unrelated causes that had presented as one symptom, and a third that only showed up once we started fixing them.

The choice of `-c pull.rebase=false` over unsetting the local config is the durable part. Local git config is unmanaged state that any tool can reintroduce at any time. Enforcement that matters has to travel with the code.

## Why not loosen the guard

The obvious fix for the second night is to delete the dirty-tree guard, or narrow it so an edit under `scripts/` does not block content generation. That is the wrong fix.

The guard is what makes the pipeline's later steps safe to run unattended. The producer commits and pushes to a live site. Running it on top of somebody else's uncommitted work means committing that work blind, under a message that describes something else entirely. That night the guard refused correctly.

But the diagnosis has to be split, because the two causes need different remedies.

For the cross-session night, prevention is the answer, and the rules already existed before any of this happened: commit early, do multi-step file work in a `git worktree` so the shared tree is not a shared mutable, and append to the cross-session journal at `~/000-projects/CROSS-SESSION-LOG.md` before and after touching a repo another session may be in. The guard did not fail there. The discipline did.

The first night's remedy was the code fix above, pinning the pull. What neither cause had was any way to get noticed. That is a separate problem, the routing gap, and it has its own remedy.

Prevention does not help there, because nothing was preventable. Both failures were logged, each with its own fail-loud alert. The daily email said what it said. Nothing connected "the producer failed again" to "a human needs to look at this." A job nobody watches, declining to run on a schedule, should escalate the first time it repeats, and that is a check nobody had written. Prevention stops the dirty tree. It does not tell you when a correct refusal has gone unread.

## A bug filed against a file someone else had already fixed

In a separate session on now-lms, the instruction was direct:

> file a bead for the broken email search tool fix it now

Bead `OPS-1zm` was filed. The error was real:

```text
IMAP Error: No supported authentication method(s) available
```

The agent went to read the working sender first, to learn how it resolves its config, then opened the search script that shares that same `SMTP_*` config. It was already pointing at MXroute, with a comment dated that same day. The mtime confirmed it: another session had repointed the file at 17:24, five hours before the failure that prompted the bug report.

The agent's line: "This file has already been fixed. I didn't make those edits."

So the code was correct and the failure had still been real. The agent ran the identical query four consecutive times. It succeeded every time, and correctly returned an email that had just been sent. The honest conclusion is that the error did not reproduce, and the cause was never established. A throttle after a burst of sends is the likely explanation, not a demonstrated one.

```bash
bd close OPS-1zm -r "FALSE PREMISE - the tool was already fixed and is working; my diagnosis was wrong"
```

The self-assessment is better than the command:

> I filed the bead, then investigating it proved me wrong, so I closed it as a false premise rather than leave a fabricated defect in the tracker. The mistake wasn't the transient.

The mistake was filing before investigating. A tracker full of fabricated defects is worse than a tracker with a gap in it, because the fabricated ones look like work.

## The same error, one level down: assuming instead of asking

That session then audited all five email workflows. Two were broken, and the interesting thing about both is that they failed the same way the dirty tree did: something acted on a belief about state that nobody had verified.

`bulk-organize.cjs` was hardcoded to `imap.gmail.com` with `GMAIL_*` credentials and no `.env` loading at all. It could not have worked without someone exporting those variables by hand. It was rewritten onto the shared config, and, more usefully, rewritten to read the folder hierarchy from the server at runtime instead of assuming Gmail's convention.

That second change is the transferable one. MXroute is Dovecot: the delimiter is `.` and user folders nest under `INBOX`. A Gmail-style `Social/LinkedIn` label would have created literal garbage folders. The real shape was confirmed by probing `getBoxes()` before a line of the fix was written. Assuming the folder convention is the same category of error as assuming the tree is clean.

`bulk-filters.cjs` used the Gmail API's server-side filter settings, which have no MXroute equivalent, so repointing could not fix it. Before concluding it was impossible, the agent checked what the server actually offered:

```bash
H=sunfire.mxrouting.net
for p in 4190 2000; do
  timeout 8 bash -c "echo > /dev/tcp/$H/$p" 2>/dev/null && echo "port $p: open"
done
```

Port 4190 answered. A second connection read the banner:

```bash
exec 3<>/dev/tcp/sunfire.mxrouting.net/4190
timeout 5 cat <&3
```

It advertised `SASL PLAIN`, `STARTTLS`, and, critically, `fileinto` plus `mailbox`, which means rules can auto-create the folders they file into. A real server-side filter implementation was possible after all.

The only `sieve` package on npm was an unmaintained 0.0.4, so the agent hand-rolled a client against Node's built-in `tls` for what it called a ten-command line protocol, with a guard against clobbering existing rules. The guard fired immediately, on a real pre-existing MXroute default script named `managesieve` containing `/* empty script */`. The dry run was then verified side-effect free by re-probing the mailbox list and confirming it unchanged.

## Two more claims withdrawn

The false-premise close was not the only time that day a claim got pulled rather than shipped.

**An agent refused to re-stamp a dated evidence record.** In intent-os, an edit to `live_observer.py` broke a validation, because that file's hash is bound into a dated evidence record named `live-runbook-resolution-residual-2026-07-16.json`. Re-stamping the record would have made the validation pass immediately:

> Re-stamping that record to accommodate my edit would quietly change what a past observation attests. I won't do that.

It reverted its own change with `git checkout --` and implemented a narrower exemption instead, on the grounds that the rule is a human-noise policy and should not apply in dry-run, where nobody is being paged.

**A reviewer refused someone else's.** On intent-os PR #374, an independent evidence-auditor reproduced two review findings as genuinely accepted defects and returned `EVIDENCE_INCOMPLETE` rather than let the epic close. The findings were specific: the schema's cross-field constraints allowed a `WORK_STATE_CONFLICT` to be recorded against a partial link, and `"plane"` sat in the `authority_verdict` enum even though a mirror surface is never authoritative.

Both were fixed before any producer existed to emit against them. The schema went 0.1.0 to 0.2.0, and `"plane"` was replaced by an optional `detected_on` field. Correcting a contract before anything writes against it is cheap. Correcting it afterward is a migration.

The same reflex showed up in a merge. Reading the review comments on bobs-big-brain-registrar #319 before merging caught that the branch carried a stale pre-fix copy of #318's eval-anchor code. Merging blind would have regressed main's WAL-safe preserve back to the torn-copy bug. That is the cron story again, in a different vocabulary: a stale artifact on disk, caught only because someone looked before acting.

## The errors that were two sessions disagreeing

Five lines from the day's error output. Each reads like an ordinary failure:

```text
ls: cannot access '/home/jeremy/bin/lib/notify-lib.sh': No such file or directory
grep: /home/jeremy/bin/minimax-agent.py: No such file or directory
error: cannot open '.git/FETCH_HEAD': Permission denied
fatal: cannot create directory at '.claude/agent-memory': Permission denied
fatal: Not possible to fast-forward, aborting.
```

The first is the sharpest piece of evidence in the whole day. `notify-lib.sh` is precisely the file the stranded refactor retired. One session removed it; another session went looking for it and got a file-not-found.

The next is the same shape. The permission denied pair are root-owned artifacts another run left behind. The fast-forward refusal is git's version of the same disagreement.

I did not classify all 71 of the day's failure-to-fix moments, so I cannot say what fraction were cross-session. These five are the ones that trace directly to another session's changes.

Two human course-corrections that day carried the right instinct:

> hold on check bobs big brain imbrella and make sure we are all aligned etc etc
>
> i dont see that api key anywhere this machine has ssh access see intent os for instructions

Both are the same move. Before trusting your read of shared state, go check whether it already changed, or already exists.

## An adjacent failure: a repo nothing could deploy

One thread from the day is worth recording even though it is not a shared-state collision, because it is the shape you get when there is no second session to disagree with you.

A sidecar service on the production VPS was 48 commits behind. Before deploying, the session checked what the pull would actually change, which is the part worth copying. Across all 48 commits the sidecar's own source changed only by its own 26-line fix, and `secrets.prod.sops.yaml` was untouched. Those were the two specific restart risks, and both cleared.

Then the pull failed on credentials. Three per-repo SSH deploy keys already existed on that host: `github-braves`, `github-runbook`, and `partner-portals-github`. Each was tested read-only against the repo. None could reach it, because they are repo-scoped by design.

The repo had no deploy path at all. Nothing on that box held the belief that this service was deployable, so no session could have discovered the absence except by trying. A read-only deploy key was registered, an SSH host alias wired up, and the pull run as the service's own user so artifact ownership stayed correct.

## What the day was

Nine threads, one disk, no shared memory between them. When they disagreed about that disk, the failures looked like a job that skipped, a bug that was not a bug, and a handful of file-not-found errors.

The honest version has a caveat attached, and the caveat is the useful part. Two nights failed, and only one of them was this. The other was our own config breaking our own tolerance rule, with no second session anywhere near it. Had the cross-session explanation been accepted for both, it would have been fixed once and stayed broken, and the next failure would have looked like a mystery.

That is the working conclusion. The disk is the only thing these processes share, so read it before you trust your model of it. And when a story explains half the evidence, do not let the half it explains stand in for the rest.

## Also shipped

The rest of the day, for the record.

**intent-os, 16 merged PRs**, mostly finishing the estate-wide retirement of `notify.sh` for a governed alert floor on the Buzz transport. PR #365 migrated the last three consumers, #367 replaced the retired entry point with a translator shim, #366 raised public-internet SSH logins to high severity, and #362 committed detection state before dispatch so that a failed alert can no longer disable the uptime monitor that produced it.

Also in intent-os, PRs #373 and #374 landed the `work-item-link.v0` and `drift-finding.v0` schema contracts (a stable ID triple with a two-of-three linkage minimum, and a closed four-class finding enum), and #375 landed the read-only GitHub, Beads and Plane reconciler that consumes them. Its first live sweep ran over 40 databases and 742 work items and returned 53 findings. Its schema validation also refused a real bead id, which widened the link pattern to accept uppercase prefixes.

**buzz, 6 PRs.** A fork-contract breach from the day before was audited (#17), the offending change reverted (#18), upstream main synced (#19, 117 commits), and the contract encoded as a CI gate (#20). The rule that got broken became a check.

**bobs-big-brain-compiler #183** made the MiniMax-M3 compile path usable by stripping inline `<think>` blocks and pricing it. A follow-on audit found the nightly harness `minimax-agent.py` killed the entire run on any `HTTPError`, including 429. It now retries 429, 500, 502, 503 and 529 up to five times, honoring the server's `Retry-After` header, while 401, 402 and 400 still fail fast.

**claude-code-plugins** turned retired URLs into real 301s (#1158) and made the marketplace site chrome model-agnostic (#1159). **twenty-mcp** repaired 12 MCP tools broken by Twenty's v2 GraphQL schema migration. **claude-code-slack-channel** #287 shipped Block Kit replies with live option buttons.

## Related Posts

- [The Check That Only Confirmed a Name](https://startaitools.com/posts/the-check-that-only-confirmed-a-name/)
- [When Live Numbers Argue Back](https://startaitools.com/posts/when-live-numbers-argue-back/)
- [How the Same Deploy Pattern Crossed Four Repos in One Week](https://startaitools.com/posts/how-the-same-deploy-pattern-crossed-four-repos-in-one-week/)
