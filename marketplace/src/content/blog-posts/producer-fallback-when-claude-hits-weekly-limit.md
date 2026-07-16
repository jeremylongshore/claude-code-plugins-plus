---
title: "Producer Fallback: When Claude Hits the Weekly Limit, the Pipeline Still Ships"
description: "A weekly LLM limit is a producer outage, not a reason to miss the daily post. Grok fallback + land path kept startaitools shipping."
date: "2026-07-15"
tags: ["automation", "devops", "claude-code", "blogging", "reliability"]
featured: false
---
A daily content pipeline that dies because one model returns a rate-limit error is measuring the wrong success criterion. The job is not "Claude ran." The job is "yesterday has a post on the live site."

On 2026-07-15 that distinction stopped being theoretical.

## What broke at 04:00

Two failures, one after the other:

1. **Dirty tree preflight.** Closing a bead the night before left one uncommitted line in `.beads/interactions.jsonl`. `preflight_branch_normalize` correctly refused to run on a dirty `master`. No produce step. No post for 2026-07-14.
2. **Claude weekly limit.** After the tree was cleaned and the run re-fired, `claude -p /blog-backfill` exited in three seconds with: weekly limit, resets Jul 19. Land saw no post file and reported `NO-POST (rc=20)`.

That is the same shape as automation assurance on Intent-OS: exit codes and "the scheduled job ran" are not outcome verification. The outcome is a live URL.

## Fix one: do not brick the cron on beads interaction noise

`.beads/interactions.jsonl` is an append-only session audit log. Any `bd close` dirties it without committing. Treating that as "human has uncommitted feature work" is wrong; treating real content dirt the same as always is right.

`preflight_branch_normalize` now:

- Still **FATAL** on any tracked dirt that is not interactions-only.
- If the **only** dirty path is `.beads/interactions.jsonl`, auto-commit it with a mechanical message and continue.

That keeps the clean-tree invariant for posts and methodology files without letting a late-night bead close silence the morning publish.

## Fix two: hard voice lint (already on master)

Separately, the produce path now fails closed on AI voice fingerprints: em dash / en dash hard ban, expanded slop phrase list, deterministic `lint-post-voice.py` in the skill and again in `blog-land.sh`. Phrase checks mask fenced code and URLs so repo names do not false-positive. Historical posts are not bulk-rewritten; only the post being landed is gated.

That gate is what made the recovered 2026-07-14 post ship without the em-dash density that had become the house default.

## Fix three: Grok as producer fallback

Claude remains the primary producer. It is not the only producer.

`blog-backfill-daily.sh` now:

1. Tries `claude -p /blog-backfill` (same as before).
2. If Claude fails **and** no post exists for the target date, runs a **Grok headless** producer with the same contract: write the post, append `decisions.jsonl`, write `.blog-staging/DATE.intent.json` with `ready:true` only after gates (including voice lint). No git.
3. Always runs `blog-land.sh` afterward (verify → commit → push → dual-publish → queue, or quarantine).

Env knobs:

| Variable | Values | Meaning |
|----------|--------|---------|
| `BLOG_PRODUCER` | `auto` (default), `claude`, `grok` | Which producer(s) to run |
| `GROK_BIN` | path | Defaults to `~/.grok/bin/grok` |
| `BLOG_GROK_MAX_TURNS` | int | Headless turn cap (default 120) |

`auto` is the production setting until Claude is healthy again, and it stays useful after: a weekly limit or API blip should not equal a missed day.

## What actually shipped for 2026-07-14

While Claude was dark, the 2026-07-14 post was produced manually under the same land contract:

- [Exit 0 Is Not Success: Automation Assurance That Verifies Outcomes](/posts/exit-0-is-not-success/)
- Voice lint PASS, Hugo PASS, dual-publish to tonsofskills + field-notes, live liveness OK
- Ezekiel packet re-sent with real social copy after the first send degraded (voice-gen still hits Claude)

The content thesis of that post and the ops lesson of this one are the same sentence: **exit 0 is not success; verify the outcome.**

## Also on the board today

- Release bumps and README/changelog sync after the voice-lint and preflight commits landed on `master`.
- IAM Bob packaging release noise (`v2.1.6`) from the overnight auto-release path: docs-only, not the story of the day.

## Takeaway

Producer outages will happen. Rate limits, model downtime, auth glitches. The pipeline should treat them like any other dependency failure:

1. Do not fail open (publish half-baked).
2. Do not fail silent (alert + log).
3. Do not single-home the produce step on one vendor when a second local producer can honor the same artifact contract.
4. Keep land deterministic and dumb: it does not care which model wrote the markdown.

Tomorrow's 04:00 run can try Claude, fall back to Grok, and still land. That is the bar.

## Related Posts

- [Exit 0 Is Not Success: Automation Assurance That Verifies Outcomes](/posts/exit-0-is-not-success/)
- [Liveness Without Health Is Theater](/posts/liveness-without-health-is-theater/)
- [Empty Is Not Clean: Five Fail-Open Bugs in an AI Agent](/posts/empty-is-not-clean/)
