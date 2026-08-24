---
title: "A Duplicate Is a Relation, Not a Property"
description: "Duplicate detection needs to see multiple files at once. A check inside a per-item loop can only guess."
date: "2026-08-23"
tags: ["testing", "claude-code", "python", "automation", "ai-agents"]
featured: false
canonical: "https://startaitools.com/posts/a-duplicate-is-a-relation-not-a-property/"
---
The Intent Solutions skills validator stamps `is_stub` on SKILL.md files to flag placeholders before they reach the marketplace. The old implementation, freshie, scored each skill against four heuristics: line count, link density, word count, placeholder keyword density. Fire two or more of them, and the skill gets flagged as a stub.

The logic was an admission. Single signals produced too many false positives. A short, dense, correct skill would trip both "under 30 lines" and "under 150 words" at the same time. So the fix was to require two of them to agree. Two guesses that agree are still a guess. The threshold only raises how much smoke has to show up before you call it fire.

## Property versus relation

A property lives on a single item. You can inspect it alone: Is this file short? Is it dense? Is it sparse on links? A relation exists between items. Duplication is a relation. You cannot find a relation by looking at one item at a time.

At 11:48, commit 1bd6b6649 in claude-code-plugins shipped a replacement that detects only what can be proven as a relation:

1. Three or more skills inside one plugin pack share the same normalized body hash. Whitespace collapsed, lowercased, SHA-256.
2. A relative markdown link inside a skill points at a missing path on disk.

Absolute URLs, mailto links, and root-relative paths are skipped. Anything under `templates/` is skipped. Skills already graded A or B are protected from the flag.

## Why the loop had to move

The old check ran inside the per-skill loop. It was inspecting properties, so being inside the loop made sense:

```python
if _db_lines < 30:
    _db_stub_reasons.append(f"body < 30 lines ({_db_lines})")
if _db_word_count < 150:
    _db_stub_reasons.append(f"word count < 150 ({_db_word_count})")
is_stub_val = 1 if len(_db_stub_reasons) >= 2 else 0
```

The new check cannot live there. It needs to see the entire run before deciding anything. Build the complete run snapshot first:

```python
stub_records = []
for result in skill_results:
    # ... resolve skill_file, pack and body for this result ...
    stub_records.append({"path": skill_file, "pack": pack, "body": body,
                         "grade": result.get("grade", "F")})
deterministic_stubs = deterministic_stub_flags(stub_records)
```

Then inside the loop, the logic collapses to two lines:

```python
_db_stub_reasons = deterministic_stubs.get(str(skill_file), [])
is_stub_val = 1 if _db_stub_reasons else 0
```

The regression test (new file, 35 lines) protects the exemption that matters. Three skills have identical normalized bodies. Two get flagged. The one graded A does not:

```python
rows = [record(path, pack, "# Same\n\nbody", "A" if i == 0 else "F")
        for i, path in enumerate(paths)]
flags = validator.deterministic_stub_flags(rows)
assert str(paths[0]) not in flags
assert str(paths[1]) in flags
```

## The tension I did not resolve

Two earlier commits the same morning (b649059c0 and fcda0a289) mass-produced near-identical Prerequisites and Output blocks across 19 SKILL.md files in the Attio pack. Each skill got a variant of the same boilerplate paragraph. The new detector does not flag these as stubs.

It hashes the whole normalized body, not sections. Nineteen skills that share three paragraphs but differ everywhere else do not collide. That threshold is the only thing separating "shared house structure" from "copy-paste stub". It was picked, not derived. I do not have a principled reason for three rather than two, and the boilerplate commit is the case that would decide it.

## Elsewhere that day

Claude Opus 5 ran `/teamkb-compile` at 09:30 over 2026-08-22. The distiller returned 17 memory candidates. First search pass with long queries yielded 8 empty results. The model noted: "My queries were too restrictive." Retry with tight keywords found 3 candidates already covered (a proc/cmdline leak, QML elide semantics, and a vendored-lane hash manifest). Fourteen new memories captured. The brain went from 17,634 memories to 17,648, active from 10,441 to 10,455. The audit chain verified clean: 24,895 events, 0 tamper signatures, 761 anchors, 0 breaks.

That empty first search is the same failure as the old stub heuristic. An empty result from a query that was too narrow looks identical, at the call site, to a corpus that has never seen the thing. Trusting it would have written 17 memories where 14 belonged.

At 09:37 `/teamkb-review` read the quarantine queue and reported reviewed 0, promoted 0, held 0, rejected 0. No writes, no receipts. That row of zeros is only worth anything because the queue was actually read.

At 13:00, `content-seo` pulled Umami analytics and ranked next-topic candidates for the week. claude-code-plugins cut a release (patch and display minor across 2 plugins), synced the marketplace projection files, and dual-published the previous day's post to tonsofskills.com. omarchy-wait-state-entry prepared v1.0.0. x-bug-triage-plugin added kernel-floor metadata to agent definitions.

## Related Posts

- [The Lane That Reviewed Nothing](https://startaitools.com/posts/the-lane-that-reviewed-nothing/)
- [When Green CI Proves Nothing](https://startaitools.com/posts/when-green-ci-proves-nothing/)
- [We Told the Auditors to Refute Us](https://startaitools.com/posts/we-told-the-auditors-to-refute-us/)
