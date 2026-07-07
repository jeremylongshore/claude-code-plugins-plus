---
title: "Backlog Zero: Burning Down the Estate with a Triage Machine"
description: "How a wave-based triage machine burned an estate backlog from 973 to 531 open issues using deterministic gates and verified close manifests."
date: "2026-07-02"
tags: ["backlog", "triage", "devops", "automation", "process", "backlog-management"]
featured: false
---
A backlog becomes impossible when you treat every issue as its own transaction. The remedy isn't faster triage — it's a **wave-based triage machine**: batch → gate → manifest → verify → repeat.

## The Burn-Down

Yesterday the intent-os estate went from roughly **973 open issues → 531**. Not through a heroic all-nighter. Through three coordinated waves, each with a written close manifest and a post-close verification addendum.

Wave 0 was the big burn: **973 → 620 open**. Mostly supersession closures and resolved-by-deploy cleanup, each batch landing under a committed close manifest. Fast, deterministic, auditable.

Wave 1's first leg focused on `claude-code-plugins`. The triage machine ran the standing marketplace-tier gate errors across seven skill packs (supabase, openrouter, notion, sentry, hubspot, figma, coreweave). Each pack had to hit zero errors before closing. Result: **620 → 537 open**. Then eight governance-cleanup PRs landed in the same push, plus a renewal of cross-repo standards. Final count: **→ 531 open**.

The number itself matters less than the *method*. A backlog of 442 closed issues means nothing if you can't prove it.

## The Triage Machine

Each wave lands with two artifacts:

1. **The close manifest.** A single, committed file named `Backlog Zero Wave N` that lists every closure: issue ID, title, reason, linked PR or commit. No ambiguity. Anyone auditing the burn can read the manifest and verify every line against the git history.

2. **The post-close verification addendum.** After the manifest commits, run the deterministic gate one more time. Marketplace-tier errors at zero? Stale branches really gone? Write a second addendum documenting what was verified. This is the audit trail.

The gate itself is the machine's filter: a pack doesn't pass the wave until it has zero marketplace-tier errors. A repository doesn't land in "closed" until the verification addendum confirms it did. No fuzzy closures, no deferred mess.

## The Credibility Surface

Same day, three new repo documents went live:

- **`STANDARDS.md`** — the repo's spec posture in one page. Marketplace tier rules, required fields, error categories. A manifest reader needs to know *what* "zero errors" means.
- **`SUPPORT.md`** — the support surface. Triage SLA: 72 hours from filed issue to acknowledged state. That SLA is part of the triage machine now.
- **AI-authorship disclosure** — filed in the 000-docs as policy (doc 697). Every artifact in the repo signed and timestamped so reviewers know who/what produced the closure.

These documents are the machine's operating manual. They make the triage method repeatable by someone else.

## The Gate-Clearing Work

Seven packs cleared their standing marketplace-tier gate errors in a single push — each had to reach zero before its wave could close. Two of the fixes are representative:

- **sentry** — added the missing Overview sections (cost-tuning, load-scale).
- **hubspot** — synced catalogs, README, and tracker to the 10-skill v2.0.0 reality.

The rest — supabase, openrouter, notion, figma, coreweave — were the same shape: a validation error the gate surfaced, fixed, then re-validated to zero. The individual fixes are straightforward; what's noteworthy is the *batch*. Seven packs, all with verified closures, in one wave is a statement that the triage machine works.

Supporting quality-of-life fixes landed in the same push:

- De-flaked the production marketplace search specs. Added deterministic data-ready waits so the tests don't flake under load.
- Updated the validator to recognize kebab-case and snake-case MCP server names in the allowlist check. (Was too strict before.)

## The Lesson

Progress on a backlog is measured in **waves**, not individual closures. A wave has a manifest, a gate, and a verification addendum. The gate is deterministic (errors → zero, not "looks good"). The manifest is committed and auditable. The verification is written.

Run the machine again next week. The estate will shrink in the same predictable, verifiable way.

The backlog is not the enemy. The *absence of a repeatable triage method* is.
