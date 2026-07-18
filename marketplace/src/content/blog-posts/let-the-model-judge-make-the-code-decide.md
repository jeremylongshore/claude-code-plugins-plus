---
title: "Let the Model Judge. Make the Code Decide."
description: "A production writing pipeline rebuilt around one rule: the language model owns judgment, deterministic code owns the gates and the audit trail."
date: "2026-07-17"
tags: ["ai-agents", "claude-code", "pipeline", "llm", "architecture", "automation"]
featured: false
---
This post was written by the pipeline it describes. The transcript analyzer that runs on every build day looked at the work that produced this system and reported the receipts: four different models did the building (Claude Opus 4.8, Claude Fable 5, Grok 4.5, and GPT-5.6 Sol), across 459 minutes, with 91 moments where something failed and got fixed, and 5 places a human stepped in to change direction. That is not a brag. It is the point. No single model built this, no model committed a line of it, and the record of who did what is machine-readable because deterministic code wrote it down, not a model's memory.

The rule the whole day came down to is short. When you put a language model in a production pipeline, split the work. The model owns judgment: writing, scoring, proposing. Code owns the decisions: what ships, what gets enforced, what gets recorded. Keep them strictly apart. Call it produce then land. Yesterday it got applied across an entire writing system in one pass, and every fix was the same fix wearing a different shirt.

## The pipeline had let the model creep

This blog publishes a post most days with no human in the loop. A cron job wakes up, a Claude Code skill writes the day's post, classifies it into a tier, and it goes live. That part worked. What had rotted was everywhere the model had quietly taken over a job that code should own.

Five symptoms, one disease:

- The model was in the git-commit path. It wrote the post and it also decided the post was good enough to ship, then pushed. A model having a bad morning could push a bad morning straight to production.
- The voice rules lived in four files. The deny-list of banned phrases was restated in the skill, in a doc, in an agent prompt, and in a checklist. Four copies means four truths, and they had already started to disagree.
- A "learned patterns" file that nothing read. Every tier misclassification was supposed to teach the system. The lessons got written to a file. The file was never loaded. `times_applied` sat at zero.
- The persona's own facts had drifted. The star count for the open-source project showed up as 1,300 in one place, 2,000-plus in another, 2,100-plus in a third, and 2,519 in a fourth. Same day. Four homes, four numbers.
- The transcript scanner threw away the actual work. It was supposed to measure how each day got built. Instead it dumped truncated chat and called it analysis.

Every one of those is the same mistake. A model was trusted to be the source of truth for something that has an exact, checkable answer. Judgment is the model's job. Facts, gates, and records are not judgment. They are code's job. The rest of the day was moving each thing back to the side of the line it belonged on.

I ran restaurants for twenty years before I wrote production code. A line cook has enormous judgment: seasoning, timing, when a plate is wrong and goes back. The line cook does not decide whether the kitchen passes the health inspection. That is a checklist somebody else signs. You do not let the person cooking the food also be the person who certifies the kitchen is clean. Same rule here.

## Produce then land: the model can write junk, but it can never ship it

The first and biggest fix was pulling the model out of the git-commit path entirely.

Before, the skill did everything: wrote the post, judged it, committed, pushed. After, the skill writes two things and stops. It writes the post. It writes a small readiness sentinel, a JSON file that says "I believe this is ready, and here is why." Then it does no git at all.

```json
{
  "date": "2026-07-16",
  "ready": true,
  "tier": 3,
  "gates_passed": ["hugo_build", "consistency_audit", "fact_check"],
  "post_path": "content/posts/let-the-model-judge-make-the-code-decide.md"
}
```

A separate script, `blog-land.sh`, does the landing. It is pure bash. No model runs inside it. It reads the sentinel, then it re-checks every precondition itself, from scratch, because a model claiming a gate passed is a claim, not a fact:

```bash
# blog-land.sh (shape, trimmed)
sentinel="$STAGING/$DATE.intent.json"

ready=$(jq -r '.ready' "$sentinel")
[ "$ready" = "true" ] || quarantine "sentinel not ready"

classifier_record_exists "$DATE"        || quarantine "no classifier record"
audit_addendum_present "$DATE"          || quarantine "no step-8 audit addendum"
hugo --buildFuture --gc --minify        || quarantine "hugo build failed"

# only now does anything touch git
git add "$post_path" && git commit -m "$msg" && git push
publish_to_tonsofskills "$post_path"
queue_crosspost "$post_path"
```

If any check fails, the post gets quarantined. The script moves the file aside, restores a clean working tree, and fires an alert. It does not publish something half-baked, and it does not leave a wrecked repo for tomorrow's run to trip over.

That last part matters more than it sounds. The old failure mode was a stuck run. A gate would hang, a model would time out mid-commit, and the tree would be left dirty. The next day's job would start in a broken state and fail too. One bad morning became a bad week. Now a bad produce step just means one quarantined post and a clean tree. Tomorrow runs like nothing happened.

The model can write a bad file. It cannot ship one. The commit path has no model in it. That is the entire idea, and it is worth saying plainly because it is the thing most agent pipelines get wrong: they let the smart component also be the trusted component. Smart and trusted are different properties. Code is dumb and trustworthy. Use it for the part where trust is the requirement.

## Single source of truth, applied twice

Two of the five symptoms were the same bug: a fact copied into many places instead of referenced from one. Both got the same fix, and the fix has a name. Reference, do not copy.

### The voice deny-list

The list of banned phrases (the AI-slop tells: `delve`, `seamless`, `game-changer`, and two dozen more) had been pasted into four files. When I added a phrase to the linter, the doc still had the old list. The agent prompt had a third version. Nothing was wrong exactly, but nothing agreed either, and drift is just being wrong on a delay.

It collapsed to one file:

```json
// voice-denylist.json (26 phrases, the one true copy)
{
  "banned_phrases": ["delve", "dive into", "seamless", "supercharge",
    "leverage", "game-changer", "revolutionize", "comprehensive",
    "it's worth noting", "at its core", "in conclusion", "..."],
  "banned_chars": ["em-dash", "en-dash"]
}
```

The linter reads it. The docs reference it by path instead of restating it. Add a phrase in one place and every consumer sees it on the next run. There is exactly one answer to "is this phrase banned," and it lives in one file.

### The persona star count

The other copy-drift was uglier because it was public. The open-source project's star count was quoted in the writing persona, in the site's own about copy, in a partner doc, and in the blog's byline material. Four numbers: 1,300, 2,000-plus, 2,100-plus, 2,519. All stale except by accident, because a hand-typed number is stale the moment the counter ticks.

The fix was a canonical persona source of truth in the intent-os repo (`persona/master.md`), with the number stated once and a live-verify command sitting right next to it so nobody ever guesses again:

```bash
# live-verify the OSS numbers instead of quoting from memory
gh api repos/jeremylongshore/claude-code-plugins \
  --jq '"stars=\(.stargazers_count) forks=\(.forks_count)"'
# stars=2519 forks=362
```

The canonical text now reads "2,500-plus stars, 360-plus forks, 45,000-plus npm downloads." Rounded down, honest, and every other file points at that one instead of carrying its own copy. Two merged pull requests did the cleanup: one stood up the canonical persona (`master.md` and `voices.md`), one corrected the star count on the personal site. A model does not own a fact that a command can check. That is not a judgment call. It is a lookup, and lookups belong to code.

## Deterministic enforcement of learned judgment

Here is the one that was quietly the most broken, because it looked like it worked.

The tier classifier scores each post and assigns a tier: field note, deep-dive, case study, distinguished paper. When it got a tier wrong, a feedback step recorded the correction as a "learned pattern" in `patterns.jsonl`. The intent was a system that gets sharper over time. A pattern looks like this:

```json
{
  "id": "tch-anchor-cap",
  "condition": {"tier_claimed": ">=2", "named_artifact_count": 0},
  "action": {"cap_tier": 1},
  "evidence": "Tier 2+ requires a named artifact; 0 present downgrades to 1",
  "times_applied": 0
}
```

See the `times_applied: 0`. That was the tell. The patterns were being written and never read. The "learning loop" was a human hand-copying each learned rule back into the prompt by hand, which nobody had done in a while. The file was a diary, not a control.

The fix was a deterministic engine, `apply-patterns.py`, that loads the rules and evaluates each one against the actual scores, then caps the tier when a rule matches. The model still scores the post. It reads the artifacts, weighs the evidence, proposes a tier. That is judgment, and it stays with the model. But the enforcement (does this proposed tier survive the learned rules) is code now:

```python
def enforce(scores, patterns):
    tier = scores["proposed_tier"]
    for p in patterns:
        if matches(p["condition"], scores):
            tier = min(tier, p["action"]["cap_tier"])
            p["times_applied"] += 1
    return tier
```

The model scores. The code enforces. And the moment I ran the engine against history, it earned its keep: one active rule matched 7 of 238 historical decisions, and 4 of those were real downgrades, exactly matching the evidence the rule had recorded about itself. The system had been right about its own blind spot the whole time. It just had no hands.

Wiring it up also surfaced two silent import bugs. The analytics index that was supposed to hold every feedback entry and every pattern had zero rows in both tables. Zero. Two `import` paths had been quietly failing, so the loop had been writing to a void for who knows how long. This is the tax you pay for a "learning" component nobody checks: it can be fully disconnected and still look alive, because the diary still fills up. Only when code started reading the diary did the disconnection show.

## Measure how the work actually happened

The transcript analyzer got a full rewrite, and it is the clearest example of the split, so it is worth walking.

The old scanner grabbed chat logs, truncated them, and pasted them into a summary. Useless. It threw away the one thing worth keeping, which is what actually happened during the build, and kept the one thing worth throwing away, which is raw model chatter.

The new `scan-session-transcripts.py` reads every AI-coding CLI used on a given day: Claude Code, Grok, Codex. It names each model exactly, because "an AI helped" is not a fact and "Claude Opus 4.8, Claude Fable 5, Grok 4.5, and GPT-5.6 Sol" is. Exact model names are also just good SEO; people search the model, not the vibe. Then it extracts the collaboration deterministically:

- Tool activity: how many edits, reads, bash runs, which files.
- Failure-to-fix arcs: a command failed, then a later command succeeded on the same target. That is a debugging loop, and counting them is arithmetic, not opinion.
- Human course-corrections: the human redirected the work. Counting them is arithmetic too.

Run on its own build day, the analyzer reported the numbers this post opened with: four models, 91 failure-to-fix arcs, 5 course-corrections, 459 minutes. The model in this pipeline does exactly one thing with all that: it narrates it into a paragraph. Every number is extracted by code. The model writes the sentence around the numbers. It never invents one.

The rewrite also does secret redaction on any code it quotes, and that guard caught a live one. A real API token had leaked into a "command not found" error string in a transcript. The redactor scrubbed it before it could reach the summary. If the model had been trusted to "just summarize the logs," that token ships in a blog post. Deterministic redaction on the extraction path is the difference between a near miss and an incident.

There is a second loop in the same family worth naming: `next-topics.py`. It reads Umami content-performance data (which posts actually got read) and turns it into a ranked queue of what to write next. Real reader behavior in, ranked topics out. The model writes the posts; the data decides the order. Same split, different surface.

## The honest calibration call

Not every decision resolved cleanly into "code decides." One was a genuine judgment tradeoff, and pretending otherwise would be dishonest.

The transcript analyzer produces a "session signal" that feeds tier classification. The idea: a day with heavy, hard engineering probably produced a meatier post. Reasonable. But the raw signal is volume, and the volume is almost always "strong," because a normal day here runs 1,600 to 2,500 tool calls. If I wired a mechanical floor ("strong signal equals bump the tier"), every post would inflate to case study on day one. The tripwire that guards against tier creep would scream every week, correctly, because I would have built the creep myself.

So the call was: set the signal from real data, but do not let it mechanically set the tier. The signal is an input the model weighs against the specific arcs of the day (did something genuinely break and get solved, was there a real design decision), not a volume threshold that auto-promotes. Code owns the measurement. The judgment about what the measurement means stays judgment. That is the honest version. The split is a principle, not a religion, and the one place it bent was the one place the quantity was real but the meaning was not.

## The silence bug

One more, because it is the operator lesson in miniature.

There is a morning packet that emails the day's syndication material out for a human to post. One morning it did not send. And here is the thing: silence looked exactly like a working pipeline. No error. No alert. Nothing in the inbox is what "all quiet, nothing to post today" looks like, and it is also what "the whole thing is broken" looks like. The two states were identical from the outside.

The fix was a positive heartbeat. Now, when there is genuinely nothing to send, the pipeline sends a one-line "NO PACKET TODAY" note on purpose. An expected message. The absence of that message is now itself an alarm, because the only way to get silence is a real failure.

I checked kitchens the same way. An empty prep list is not "we are ready." An empty prep list means nobody did prep. You do not get to assume the quiet means good. You make good produce a signal, so the quiet can only mean bad. Silence was the actual defect. The missing email was not the bug's symptom; the missing email was the bug, and the fix was to make silence impossible.

## Why deterministic-owns-the-gates beats letting the model do it all

Step back from the five fixes and the shape is one design decision made five times. The gate, the fact, the enforcement, the measurement, the record: all pulled out of the model and given to code. Here is why that is not just tidiness.

**Reliability.** A model is a probabilistic component. It has good mornings and bad mornings, and you cannot schedule which. Code is deterministic. When the trustworthy part of your pipeline is the deterministic part, the model's bad morning costs you one quarantined post, not a corrupted repo.

**Auditability.** "Four models, 91 failure-to-fix, 5 course-corrections, 459 minutes" is a fact I can stand behind because code counted it. If a model had summarized the day from memory, I would have a vibe, not a receipt. Receipts are what let this post open with real numbers instead of a hand-wave.

**Reproducibility.** The learned patterns went from a diary nobody read to a rule engine that produces the same downgrade every time the same condition appears. 7 of 238 matches, 4 real, repeatable on the next run. A model re-judging from scratch each time is not reproducible. A rule is.

**It survives a flaky model.** This is not hypothetical. During the build, one model hit its weekly usage limit mid-stream. A fallback model took over. The pipeline still shipped, because the model was never the thing that ships. The commit path is bash. It does not care which model wrote the file, or whether the model that started the post is the model that finished it. When code owns the commit, the model layer can fail over, rate-limit, or swap entirely, and the output does not corrupt. You cannot get that property if the model is holding the git handle.

Across two days this was 34 commits on the blog repo, two merged pull requests on the persona and voice system, and one on the personal site to kill the star-count drift. Every one of them was the same move: find a place a model was trusted with a decision, and give the decision to code.

## The lesson

If you ship agents in production, the model is the worker on the line, not the manager who signs off. It has real skill and real judgment, and you should use all of it: let it write, let it score, let it propose. Then take its work to a gate it does not control. Let the model judge. Make the code decide.

The tell that you have it backwards is comfort. If your pipeline feels clean because the model "handles everything end to end," you have handed the trust property to the component that has bad mornings. Find the git handle, the fact, the gate, the record. Move each one to code. What is left for the model is the part it is actually good at, and the part where a mistake costs one quarantined file instead of a shipped incident.

---

**Related posts:**

- [Exit 0 Is Not Success](/posts/exit-0-is-not-success/)
- [Copying Files Is Not Installing](/posts/copying-files-is-not-installing/)
- [Producer Fallback: When Claude Hits the Weekly Limit](/posts/producer-fallback-when-claude-hits-weekly-limit/)
