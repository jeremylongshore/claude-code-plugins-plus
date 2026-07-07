---
title: "Every Safety Gate Has a Failure Direction"
description: "Safety gates fail in opposite directions: one crashed fail-closed, another failed open. Both from a swallowed error. A shell-script control-failure case study."
date: "2026-07-06"
tags: ["debugging", "ci-cd", "automation", "observability"]
featured: false
---
A deterministic recap tool ran for the first time on a live system. Within hours, its block-event table showed seventeen consecutive BLOCK events. The natural question: what broke? The answer was worse than expected. Two gates in the same codebase were failing in opposite directions, both invisible for the identical reason.

A **fail-closed** gate blocks when it cannot evaluate its rule—it rejects uncertainty and reports the failure. A **fail-open** gate passes unless it proves a violation—it accepts uncertainty and reports nothing. Fail-closed is noisier but visible; fail-open is silent but hidden. Both fail to answer the real question: was the gate actually evaluated?

The system is `contributing-clanker`, a governance layer for AI-assisted open-source work. Fifty-one deterministic gates—shell scripts, each a safety check—run on every pull request. No LLM in the correctness path. No voting or heuristics. Each gate either passes or blocks, and the result is final. When a gate fails invisible, it's a control failure.

## The Crash That Blocked Everything

Seventeen BLOCK events sound alarming until you triage them. Sixteen were benign noise from that session's own regression runs. The seventeenth was real: gate `e02-ai-strike-track` was crashing. Strike tracking is straightforward—the gate parses `log.jsonl` to extract AI events flagged during code review—but on this box it had been reporting BLOCK on every single task transition, and nobody had noticed until the recap put the events in one table.

The gate's logic:

```bash
#!/bin/bash
set -o pipefail
set -e

# Trap ERR and report the crashed line
trap 'echo "BLOCK: crashed at line $LINENO"' ERR

jq '.ai_strike' log.jsonl | grep -c "true"
```

Simple. Deterministic. But the log carried historical debris: old hook entries with unescaped heredoc newlines that `jq` couldn't parse. When `jq` encountered a torn line, it exited with code 5. Under `pipefail`, that non-zero exit tripped the ERR trap. Result: the gate crashed, reported BLOCK, and blocked every task transition.

The fundamental problem: the gate wasn't blocking by design. It was *crashing*, and the crash was silent because the error came from data written months ago—a hook that had already been fixed. The gate never evaluated its own rule.

The fix: tolerant per-line parsing.

```bash
jq -cR 'fromjson? | objects | select(.ai_strike == true)' log.jsonl | wc -l
```

The `-R` (raw) flag reads each line as a string. The `fromjson?` (with `?`) suppresses parse errors. The `objects` filter skips anything that isn't a JSON object. Malformed lines are simply skipped. The gate evaluates what it can.

This design is safe *specifically here* because the gate doesn't hide strikes—it only counts lines *that successfully parse and contain strike data*. A torn line carries no strike, so skipping it cannot produce a false negative. The gate re-evaluated, found three legitimate strikes, and reported PASS.

Two red-first fixtures locked it in: a torn line with no strikes (previously a crash-BLOCK, now PASS) and a torn line with a real strike (a BLOCK that names the strike, not the crash).

## The Silent Pass That Let Everything Through

Fixing e02 meant auditing the other gates that parse the same logs—and that audit turned up a second failure in the opposite direction. Gate `c24-engagement-frame-leakage` was supposed to detect when review comments leaked into author engagement frames. It had two independent bugs that silenced four of its seven detection tokens.

First bug: the token list stored patterns as `regex|hint` delimiter pairs, and the gate split on the first `|`:

```bash
for entry in "${TOKEN_LIST[@]}"; do
  token_regex="${entry%%|*}"        # split on the FIRST | — here's the bug
  token_hint="${entry#*|}"
  if grep -E "$token_regex" diff.txt 2>/dev/null; then
    echo "WARN: $token_hint"
  fi
done
```

Three of the regexes *contained* `|` alternations—patterns like `(F-finding|R-phase|Intent Solutions)`. Splitting on the first `|` truncated them:

```
(F-finding|R-phase|Intent Solutions)
becomes
(F-finding
```

Under `grep -E`, `(F-finding` is an unbalanced-parenthesis pattern—a syntax error. `grep` exits with code 2 (bad regex). But that error went to stderr, and the `2>/dev/null` inside the `if` condition threw it away. A command that fails in an `if` condition is exempt from `set -e` and the ERR trap—the shell just reads it as "false" and moves on. The gate never reported WARN. It didn't fail to *find* a leak; it failed to *run its own check*, and called that a pass.

Second bug, independent: token 7 (footer verification) anchored on `^\+`:

```bash
grep "^\+" diff.txt && echo "WARN: author footer leaked"
```

But the diff extraction stripped the leading `+`:

```bash
awk '{print substr($0, 2)}' diff.txt
```

The anchor could never match. Dead for a second, unrelated reason. Four tokens failed silently. Real engagement-frame leaks passed the gate.

The fix addressed both:

```bash
declare -a TOKEN_REGEXES=(
  '(F-finding|R-phase|Intent Solutions)'
  'author attribution block'
  # ... more patterns, no delimiters
)
declare -a TOKEN_HINTS=(
  'Frame pattern found'
  'Author block detected'
)

for i in "${!TOKEN_REGEXES[@]}"; do
  if grep -E "${TOKEN_REGEXES[$i]}" diff.txt >/dev/null 2>&1; then
    echo "WARN: ${TOKEN_HINTS[$i]}"
  elif [ $? -ge 2 ]; then
    echo "BLOCK: gate logic error—cannot evaluate rule"
    exit 1
  fi
done
```

Parallel arrays eliminate the delimiter truncation entirely—no split, so the `|` alternations survive intact. The footer token re-anchors on the actual diff shape. And—the key transfer—the gate now blocks on unevaluable rules. If `grep` exits with code 2 (bad regex, bad permissions, and so on), the gate reports BLOCK with a clear reason instead of swallowing the error and reporting PASS.

Four red-first adversarial fixtures locked it in: each proven to wrongly PASS on the old code before the fix, each correctly WARN after.

## Why Not Just Make It Strict?

The obvious move: make `jq` strict and let it crash loudly. Let `grep` fail and report the failure.

The problem: you can't. In `e02`, the log carries historical data from a hook that's already been fixed. Making the parse strict means every run forever alerts on permanent history. The alert fatigue defeats the gate entirely—you'd disable it.

In `c24`, adding a regex validation check before `grep` works, but it doubles the line count and creates a new place for bugs to hide. The parallel-array design prevents the *entire class* of delimiter-truncation bugs. It's not stricter; it's *simpler to verify*.

There is a line between the two fixes worth naming, because they look contradictory. e02 *skips* torn lines silently; c24 *blocks* on a bad regex. The difference is whether the unhandled input could hide the thing the gate is looking for. A torn log line structurally carries no strike—skipping it cannot mask a violation. A `grep` that errors out never ran its check at all—so passing *would* mask a violation. Skip only when the skipped input cannot possibly carry the signal you're gating on. Otherwise, a gate that cannot evaluate its own rule must report fail-closed (BLOCK) with a clear reason.

Crashing fail-closed is bad. Silently failing open is worse. Both happened because errors were swallowed. The fix is architectural—design gates so unevaluable states are impossible, and when they occur anyway, make them loud.

## The Mirror-Image Lesson

The real insight isn't about these specific gates. It's that two independent bugs created opposite failure modes *in the same session*. One gate crashed BLOCK. One silently passed OPEN. e02 was invisible until a new deterministic observability tool—the recap email—put real block-events in front of a human on its first live morning. c24 was invisible in the *other* direction: it produced no events at all, so no dashboard could ever surface it. It came out only because fixing e02 meant auditing every gate that swallowed an error, and c24 was one of them. One tool exposed the first bug; the audit that bug triggered exposed its mirror.

The lesson: every safety gate has a failure direction. The direction you assume is rarely the one that actually occurs. Test for crash-fail-closed and silent-fail-open together. Design gates so both are impossible.

## Also Shipped

In parallel, a control-bypass after-action was filed in the `intent-os` governance layer. A signed evaluation verdict was published, then an admin-merged PR bypassed a required check on that same verdict. The fix: enforce repository protections so admin-bypass is impossible going forward. Same principle in a different domain. A safety control that *can* be bypassed will be. Design so it can't.

## Related Reading

- [The Relevance Score That Broke Our Cite-or-Refuse Gate](/posts/relevance-score-broke-cite-or-refuse-gate/)
- [Gate the Statement, Not the Tool Name](/posts/gate-the-statement-not-the-tool-name/)
- [Human-in-the-Loop Is a Delivery Guarantee, Not a UI Feature](/posts/hitl-delivery-is-a-fail-closed-exactly-once-problem/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Every Safety Gate Has a Failure Direction",
  "description": "Safety gates fail in opposite directions: one crashed fail-closed, another failed open. Both from a swallowed error. A shell-script control-failure case study.",
  "author": { "@type": "Person", "name": "Jeremy Longshore" },
  "publisher": { "@type": "Organization", "name": "Start AI Tools", "url": "https://startaitools.com/" },
  "datePublished": "2026-07-06T08:00:00-05:00",
  "mainEntityOfPage": { "@type": "WebPage", "@id": "https://startaitools.com/posts/every-safety-gate-has-a-failure-direction/" },
  "url": "https://startaitools.com/posts/every-safety-gate-has-a-failure-direction/",
  "articleSection": "Technical Deep-Dive",
  "keywords": "fail-closed, fail-open, safety gate, error handling, CI/CD, automation, observability, debugging"
}
</script>
