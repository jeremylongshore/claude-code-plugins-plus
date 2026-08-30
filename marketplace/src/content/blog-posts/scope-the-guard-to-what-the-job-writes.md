---
title: "Scope the Guard to What the Job Actually Writes"
description: "Scope a guard to the paths its job actually writes. How a nightly producer kept aborting on edits it would never have touched."
date: "2026-08-29"
tags: ["automation", "devops", "debugging", "ci-cd", "claude-code"]
featured: false
canonical: "https://startaitools.com/posts/scope-the-guard-to-what-the-job-writes/"
---
Two systems mismeasured what was in front of them. One aborted loudly on dirt that could not touch it. One returned a 200 and assigned the card to nobody. Both fixes narrowed what a piece of code claimed authority over.

## The 04:00 producer that aborted on dirt it would never touch

The blog pipeline runs unattended every morning at 04:00, on the same working tree that every interactive Claude Code session uses. One bash function, `preflight_branch_normalize()` in `scripts/blog/lib-cron-common.sh`, is the guard that decides whether the run may proceed at all.

It refused to run on ANY uncommitted tracked file. Full stop. A legitimate edit left unsaved overnight took down the entire cron job.

This happened three times:
- 2026-08-13: persona files
- 2026-08-18: a lost image-push race condition that left the tree diverged
- 2026-08-29: uncommitted 68-insertion doc update to `000-docs/002-REF-omarchy-plugin-promotion-reference.md`

Two of the three were the same cascade: the dirty-tree check FATAL'd, no post got produced, and the 05:00 posting packet had nothing to send to Ezekiel. The 08-18 abort came one step later in the same function, where an ff-only pull correctly refused a tree that a lost image-push race had diverged. That one was fixed at the push, not here, and the scoping change would not have saved it. The morning of the 29th the recovery was manual: commit the legitimate content, push, re-run backfill for the 28th by hand.

The issue is mechanical: a human editor can legitimately leave work uncommitted while a nightly job wants to proceed. These are not in conflict. The job writes to four specific paths. Uncommitted changes anywhere else do not touch what the job produces.

### The fix

Commit `605835ec`: `scripts/blog/lib-cron-common.sh` (+28/-12). The preflight now FATALs only on uncommitted changes to the pipeline's own write-set:

- `content/posts/`
- `.blog-staging/`
- `.claude/skills/blog-backfill/methodology/decisions.jsonl`
- `static/images/posts/`

Uncommitted changes anywhere else are logged and left exactly where they are. The run proceeds.

### Why not the obvious approaches

Two alternatives were considered and rejected.

**Auto-stash:** A band-aid. It moves someone's active mid-edit work out from under them, and then pops the change back to uncommitted. The same file re-triggers the abort the next night. Auto-stash also touches work that is not the pipeline's business to touch.

**A retry loop or nightly re-run:** The wrong tool for this shape of failure. A dirty tree is a standing condition, not a transient one. It stays dirty at 04:15, 04:30, any time you retry. Retries just multiply the failure alerts instead of fixing anything.

Scoping is the real fix. The producer genuinely cannot collide with dirt outside its write-set, so it should stop caring about it. The hazard is preserved: a half-written post in `content/posts/` or a mid-edit `decisions.jsonl` still aborts, because building on top of those is genuinely unsafe. That distinction is the whole reason this works.

```bash
# Abridged from preflight_branch_normalize(); log strings shortened.
# Dirt inside the write-set still aborts. Dirt outside it is logged and left alone.
_porcelain=$(git status --porcelain --untracked-files=no 2>/dev/null || true)
if [ -n "$_porcelain" ]; then
  _dangerous=$(printf '%s\n' "$_porcelain" | grep -E '^.. (content/posts/|\.blog-staging/|static/images/posts/|\.claude/skills/blog-backfill/methodology/decisions\.jsonl)' || true)
  if [ -n "$_dangerous" ]; then
    _log "$log_file" "FATAL: uncommitted changes to the pipeline's own files on '$current_branch', refusing to proceed"
    _log "$log_file" "       These paths are what the producer writes; a half-finished post or edit here is unsafe to build on. Resolve and re-run:"
    printf '%s\n' "$_dangerous" >> "$log_file" 2>&1
    exit 1
  fi
  _benign=$(printf '%s\n' "$_porcelain" | grep -c . || true)
  _log "$log_file" "Pre-flight: $_benign uncommitted file(s) outside the pipeline write-set, ignoring, they will not be touched"
fi
```

The verification: a harness over four cases on a throwaway repo. It exercises two of the four write-set paths directly; the other two share the same match arm.
- Benign `000-docs` edit: passes the dirty check, logged as "ignoring, will not be touched"
- `content/posts/` edit: FATAL
- `decisions.jsonl` edit: FATAL
- Clean tree: passes

That morning's exact failure would now proceed untouched.

## The alarm working is not the system working

One more thing about how the morning started. The failure did not surface because someone noticed a missing post. It surfaced because a gap detector built ten days earlier caught the gap and paged with a loud "no post landed" subject instead of reporting healthy.

That detector only existed for the third failure, and the reason it exists is the second one. On 2026-08-18 the producer aborted at 04:00 and the 05:00 heartbeat still called the pipeline healthy an hour later. The detector was built on 2026-08-19 precisely because detection had failed. So on 2026-08-29 it fired correctly, which is the system improving.

It is still worth saying plainly that it could have gone on firing correctly indefinitely without anything getting better. Three runs failed inside seventeen days. The alarm got fixed after the second. The guard behind it stayed wrong through all three. An alarm that fires reliably on a recurring failure is a reason to go fix the cause, not evidence that the cause is handled.

## The task board that returned HTTP 200 and assigned nobody

Ezekiel gets the posting packet as an email at 05:00. For weeks, "done" meant "reply to the email with the URLs," and a 07:30 ingest job read those replies. But the ingest kept coming back empty.

The problem with reply-as-completion: a missing reply is indistinguishable from a missing post.

The fix (commit `add88e64`): after the packet email sends and marks `packet_sent`, the sweep also creates or updates one Plane card per post, assigned to Ezekiel. He drags it To Do to Done as he posts. A card has a state on a board. Email is the delivery; the card is the record.

The failure direction matters: the card call runs after the email send and after `mark_sent`, and it swallows every error. A Plane outage can never turn a delivered packet into a failed run.

### The root cause

Plane silently drops an assignee who is not a member of the destination project, as opposed to the workspace. The PATCH returns HTTP 200 even when the assignment fails. Ezekiel was a workspace member but had never been added to the CONTENT project, so every assign returned 200 and assigned nobody.

```python
def ensure_project_member(key: str, uid: str) -> bool:
    """Plane silently drops an assignee who is not a member of the PROJECT (not
    just the workspace). Idempotently add him so the assignment can actually
    stick. Returns True if he is (now) a member."""
    def member_id(r):
        m = r.get("member")
        if isinstance(m, dict):
            return m.get("id")
        return m or r.get("id")
    try:
        _, page = call(key, "GET", f"/projects/{CONTENT_PROJECT}/members/")
        rows = page.get("results", page) if isinstance(page, dict) else page
        if uid in [member_id(r) for r in (rows or [])]:
            return True
        st, _ = call(key, "POST", f"/projects/{CONTENT_PROJECT}/members/", {"member": uid, "role": 15})
        # 200/201 = added; 400 typically means "already a member", also fine.
        return st in (200, 201, 400)
    except Exception:
        return False
```

That is why nine Omarchy showcase cards created on 2026-08-25 all read `assignees: []` even though the assign job logged "assigned 9". That is why his Plane board showed no work to do.

I isolated it by assigning a known-good member instead: Jeremy, a workspace admin. That worked instantly. Assign Ezekiel and it silently no-ops. Same code path, same 200. The difference was project membership.

I fixed it two ways. Added Ezekiel to the CONTENT project and back-assigned all 10 existing cards, the nine broken Omarchy cards plus the one for that day's post. Then `blog-plane-card.py` now calls `ensure_project_member` idempotent on every run, so this cannot silently recur.

One more Plane API quirk: assignees must be set in their own dedicated PATCH. Plane ignores an `assignees` field mixed into a create or update payload.

Verification: card created for the live post (HTTP 201). Re-run updates instead of duplicates (still exactly 1 card). Assignment confirmed by read-back. All 10 content cards now read `assignees=[ezekiel]`. Clean end-to-end run prints "updated card ... (HTTP 200)" with no error note.

## The correction that shrank the design

The Plane card did not start out as one line in an existing job. The first pass at it was a tracking subsystem: a new state file, an ingest reconciler, its own cron entry.

The correction came in voice dictation, so the transcript caught it garbled: "please dont make it comicates alproach it with simixty also." Cleaned up, that is "don't make it complicated, approach it with simplicity."

What survived the correction was one sentence: add one step to the 05:00 packet job, so when Ezekiel gets his email he also gets a Plane card. Nothing else changes. The email stays. No new cron entry, no reconciler, no new state file.

That is what shipped. Commit `add88e64` is 17 changed lines in `blog-posting-packet.sh` plus a 194-line `blog-plane-card.py`. The rejected design would have added a fourth moving part to a pipeline whose whole problem that morning was that its existing parts were too entangled with each other.

Worth being precise about what the models did here, because it was four of them across one long day. `Claude Opus 4.8` and `Claude Opus 5` carried the blog pipeline thread, including the preflight diagnosis and the scoping fix. `Claude Sonnet 5` picked up shorter turns in the same tree. `Claude Fable 5` ran the parallel Buzz investigation, which is where most of the day's errors landed: 34 of them across 847 minutes, against production Postgres auth logs over SSH. Across every session the day logged 474 tool calls, 40 failure-to-fix arcs, and 3 course-corrections in a 1112 minute span.

The three corrections are the part worth keeping. None of them were "that code is wrong." All three were scope corrections: fold this into what already exists, go verify the thing actually ran, make it smaller. The elaborate version got built competently on the first pass. What it did not get was a check on whether the problem deserved that much machinery, and on this day that check is the only thing that kept a task board from becoming a subsystem.

## The through-line

Both fixes narrow what a piece of code claims authority over. The preflight claimed authority over the whole working tree when it only writes four paths. The assign call treated a 200 as proof the assignment happened, when all the 200 actually confirmed was that the request had been accepted.

The Plane fix did not literally remove code. It added a membership check and a second PATCH. What it narrowed was the claim: the assign call stopped treating an accepted request as a completed one. In both cases the code asserted something it did not govern, and the fix was to make the claim match the control.

## Also shipped

**Omarchy marketplace submission sweep.** Eleven widget entry repos plus the shared template: Capture Conveyor, Desk Transition, Docket, Flow Boundary, Crew Chief, Foundry, Workspace Storyboard, Wait State, Quiet Queue, Listening Post, Loose Ends. The commit subjects run to "marketplace-ready" and "production certified", which is the repos' own shorthand and worth deflating here: what was actually established is that each widget loaded in a fresh Omarchy shell on the Buzz rig, with render receipts bound to the raw shell logs and runtime evidence kept separate from visual evidence. Submission is a filing, not an approval. That was breadth rather than depth, and it is not what made the day interesting.

**Gate C43, the Omarchy marketplace presentation guard.** Landed at 16:38 as 163 lines plus a 119-line bats suite, wired into CI, then tightened four more times the same day: 16:45, 17:41, 18:08, and 20:36. Each tightening closed something the previous version had let through. It checks that a manifest description uses the full 500-character allowance the catalog schema permits, that a bar widget description matches it rather than telling a different product story, and that the copy names the product, says what the user can see or do, and states a trust boundary. Requiring the full allowance is an unusual rule, and the reason given in the gate is blunt: every short description that escaped was generic. Five revisions in four hours is its own small lesson about writing gates, and it deserves its own post rather than a paragraph here.

**Hermes trust boundaries hardened in `claude-code-plugins` (PR 1383).** Split the contribute skill into read-only, prepare, and publish surfaces, dropped the automatic install-persistence hooks, and required explicit state and workspace paths. Merged.

**Buzz forensics, unresolved.** A separate thread that started as "save my automations and plan a clean reinstall" turned into reading production Postgres auth logs over SSH, per-pubkey auth successes and full connection lifecycles. It did not resolve into a shipped fix that day.

## Related Posts

- [Every Safety Gate Has a Failure Direction](https://startaitools.com/posts/every-safety-gate-has-a-failure-direction/)
- [A Green Result Only Covers What It Ran](https://startaitools.com/posts/a-green-result-only-covers-what-it-ran/)
- [Gate the Statement, Not the Tool Name](https://startaitools.com/posts/gate-the-statement-not-the-tool-name/)
