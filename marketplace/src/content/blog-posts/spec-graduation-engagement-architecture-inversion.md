---
title: "Spec graduation: when a partner email rewrites architecture"
description: "A partner check-in forced a contract re-read, which clarified a content boundary, which unblocked a spec graduation that had been stalled for two weeks."
date: "2026-05-09"
tags: ["methodology", "consulting", "partner-engagement", "spec", "mcp", "observability", "architecture"]
featured: false
---
The cleanest architectural moves of the last six months didn't come from a whiteboard. They came from a partner email that essentially said: hey, remember what we actually signed.

Yesterday's post was about [coherence as a deliverable](/blog/coherence-day-drift-detection-strategic-spine/) — a full audit-day where four advisor agents independently flagged the same drift in the same engagement. The drift was real, but the post stayed at the diagnostic layer. It identified the misalignment without committing to the structural change that misalignment implied. Today is the structural change.

## The drift

The `kobiton/CLAUDE.md` for the M2 milestone work said, in plain text, that the primary venue for "Blog 1" was startaitools.com. That sentence had been there since the file was first scaffolded, and nobody had questioned it. It read like settled fact.

It wasn't. It was a gloss. Somewhere during SOW negotiation a verbal "we're flexible on venue, you do what makes sense" had been transcribed into the operating doc as "primary venue: startaitools.com." Internal interpretation became internal canon, and internal canon then started shaping how I scoped everything downstream — what the post would argue, what tone it would use, who the audience was, where it would link to.

The drift was small. The drift was three months old. The drift had compounded into structural assumptions about M3 and M4 already.

## The check-in

Frank Moyer is the Kobiton stakeholder on the M-series. He replied to a thread that was nominally about WordPress publishing access. The actual content of his reply was a course correction: Kobiton's blog is the canonical home for Blog 1. Cross-publication elsewhere — startaitools.com, the personal portfolio, anywhere — needs to align on canonical strategy ahead of publication.

He was right. He didn't argue the point, he just stated the position the contract supported. My reply was "10-4." It was the only register that fit.

## The re-read

This is the part where, if I'm being honest, the temptation was to negotiate. There was a half-formed counter forming in my head about cross-promotion, about audience reach, about how methodology content benefits both parties.

I closed the email tab and pulled the actual signed SOW from `kobiton/000-docs/001-BL-CNTR-`. I'd opened that document maybe three times since signing it.

The project title — the literal first line on the document — included the word "Promotion." The M2 milestone description required positive supportive promotional tone and content reinforcing plugin value. Venue was not specified, but the framing was unambiguous. Frank's read of the contract was well-supported. My `kobiton/CLAUDE.md` gloss was not.

This is a small humiliation worth sitting with for a moment. The contract is the artifact. The CLAUDE.md is a working note. When they disagree, the working note loses every time, and the working note had been silently steering decisions for a quarter.

## The boundary

The fix was a new section in `kobiton/CLAUDE.md` titled "Content boundaries." Two columns:

**Contracted M2 deliverables** — three blogs, Frank-coordinated, canonical at kobiton.com/blog, vendor-specific framing per the SOW, positive promotional tone, plugin-value-reinforcing. This is theirs. I'm the author of record but Kobiton owns the venue, the timing, and the framing constraints.

**Independent methodology track** — anything that generalizes across engagements: the `intent-eval-lab` spec, the matcher-map template, public technical comments on GitHub, anything that lives at the "shape of the audit" layer rather than the "this specific plugin" layer. This is mine. Authoring domain, venue, timing all under my control.

The two columns aren't in tension. They're orthogonal. A finding I make while auditing the Kobiton plugin can produce both a Kobiton-specific blog (theirs) and a contribution to the vendor-neutral spec (mine), as long as I don't co-mingle the artifacts on one publication track or one CLAUDE.md row.

Writing that section took fifteen minutes. The clarity it produced is the part of this whole episode I keep returning to, because it's the part that unblocked everything else.

## The graduation

Here's the spec graduation I hadn't seen until the boundary was on paper.

Four advisor agents — business-analyst, ai-engineer, architect-reviewer, content-marketer — had each separately produced reviews over the prior week recommending some variant of the same structural move: stop being the auditor of one plugin, become the methodology layer that Kobiton is one instance of.

The business-analyst framed it as positioning: "auditor of N plugins" doesn't compound; "author of the conformance spec N plugins are graded against" does. The architect-reviewer framed it as artifact taxonomy: the matcher-map template is being reinvented for every engagement and that's a sign it wants to be a vendor-neutral artifact. The ai-engineer framed it as eval-loop reusability. The content-marketer framed it as audience: methodology content has a different reader than vendor-specific content and the two were eating each other.

Four roads, same destination. The stall was recent — two weeks — but the misalignment feeding it was three months old: the same CLAUDE.md gloss that misread the SOW's venue position was also keeping the methodology entangled with vendor-specific framing. Pushing the methodology to a public vendor-neutral spec while simultaneously delivering vendor-specific promotional content for one of the vendors-in-question is a real tension if you don't have a content boundary.

With the content boundary in place, the tension disappears. The spec lives on the independent methodology track. The Kobiton blogs live on the contracted track. Neither contaminates the other.

This is the inversion.

Until Frank's email, the engagement architecture was: **Kobiton M-series is the primary work, methodology extraction is a side effect.** After the boundary, it's: **Methodology spec is the primary structural asset, Kobiton M-series is one instance.**

The work I do for Kobiton hasn't changed. What it produces, structurally, has.

## The artifact

I executed what the architect-reviewer agent had labeled "Option B — soft spec move." Vendor-neutral spec, draft status, public artifact, no marketing announcement. The on-disk layout:

```
intent-eval-lab/
  specs/
    mcp-plugin-observability/
      v0.1.0-draft/
        SPEC.md
        matcher-map-template.md
        case-studies/
        conformance-test-suite/
    methodology/
      README.md
    validator-contract-reliability/
      README.md
    forecasting-drift-detection/
      README.md
    decentralized-crypto-evaluation/
      README.md
```

Module 1 — `mcp-plugin-observability` — ships as `v0.1.0-draft`. The other three placeholder modules live as siblings under `specs/`, not children of the first module, because the methodology umbrella is broader than any single shape. The cross-module `methodology/` directory sits alongside.

The spec has five normative requirements, R1–R5. Most anchor to a section in Anthropic's published Claude Code monitoring, hooks, or plugins documentation; the structural ones cite [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) plus the spec's own anchoring rule. The discipline is: I'm not inventing prescriptions, I'm codifying what's canonical and pointing at the source. If a requirement can't cite a canonical doc section or an upstream MCP/OTel spec section, it doesn't go in.

The matcher-map template is the structural piece. Three columns:

| finding-shape | hook matcher | OTel signal |
| --- | --- | --- |
| race | `PreToolUse` on Bash | `mcp.tool.race.detected` span event |
| shape drift | `PostToolUse` on Edit | `mcp.context.shape.drift` metric |

- **finding-shape** — a class of failure mode that recurs across plugins.
- **hook matcher** — the Claude Code hooks declaration that detects an instance.
- **OTel signal** — what the hook should emit so the failure becomes observable downstream.

The v0.1.0-draft includes six baseline shapes — race, shape drift, cooldown, side-effect verification, mandatory context, strict-mode protocol. Each one is a row that's been instantiated against at least one real engagement. The Kobiton M2 audit produced four of them. The remaining two came from earlier work.

The three module placeholders — `validator-contract-reliability` (Polygon-shape), `forecasting-drift-detection` (Nixtla-shape), `decentralized-crypto-evaluation` (Lit-shape) — are README-only. Each README names a domain-specific failure mode and reserves the structural slot. No timeline, no commitment, no marketing. They exist so the methodology umbrella is visible without the umbrella having to ship every panel at once.

The `methodology/` directory is the cross-module layer. Its README enumerates five patterns observed early — how to write findings (Toulmin's argumentation model — claim, grounds, warrant — from Stephen Toulmin's *The Uses of Argument*, 1958), why diagnostic precedes prescription, the distinction between conformance (does the plugin meet the spec?) and eval (does the plugin do its job?), the vendor-neutrality rule, and the anchoring rule that requires every normative claim to cite a canonical source. Each pattern is provisional today; the README states the promotion gate explicitly: when at least two modules ship to a release-candidate version, the patterns get promoted to properly authored documents.

## The runner decision (separate)

The same boundary discipline that partitioned content also forced a smaller separation inside the spec itself: the language the runner is written in is not the language the spec speaks. A second multi-advisor pass — architecture, Go-fit, DX, business-strategy — converged on Go for the reference runner. Reasons stack neatly:

- Single static binary distribution. No Python venv, no Node version dance. Plugin authors clone a release and run it.
- OTel ecosystem is Go-native. Collector, Tempo, `opentelemetry-go-contrib`, and Honeycomb's Refinery proxy — all Go. The runner inherits the ecosystem instead of bridging to it.
- Fast cold start matters when the runner is in a CLI eval loop being invoked dozens of times per session.
- The official MCP Go SDK (`modelcontextprotocol/go-sdk`) gives clean protocol integration without me writing glue.
- Matches the precedent set by the [j-rig-binary-eval runner](/blog/forge-dogfood-plane-plugin-grade-a-and-jrig-verified-loop/) — same operational shape, same maintenance surface for one operator.

The critical separation: **the runner-implementation decision is decoupled from the spec-implementation decision.** The spec is language-neutral. The matcher-map template is language-neutral. The conformance reports are language-neutral JSON.

A plugin author writing in Python or TypeScript or Rust can author a conformant matcher map, run their own test harness, and produce a valid conformance report without installing Go. The Go runner is one reference implementation. A `runner-py/` or `runner-ts/` contributed later is a valid contribution, not a fork.

I want to be explicit about why this matters. The cardinal sin of methodology specs is conflating "the spec" with "the tool that checks the spec." When that happens, the tool's language choice becomes a barrier to spec adoption, and the spec dies on a toolchain hill. Keeping the layers separate is not architectural purity, it's adoption strategy.

## The discipline holds the line

R3 — the M2 deliverable due May 25 — keeps the vendor-specific framing the SOW originally scoped. No reframing. No spec-aware asides. No "this is one instance of a broader pattern" gestures. Frank gets the deliverable he contracted for, in the tone he contracted for, on the schedule he contracted for.

The public announcement of the spec — a blog post, a tweet, an entry in the methodology hub on this site — is deferred until after M3 ships. At that point I'll go back to Frank, walk him through the spec, ask for consent on a co-credit announcement, and time it accordingly. Same compounding upside, lower partner-relationship risk, three or four weeks slower timeline.

The trade is correct. A clean structural reframing that risks the partner deliverable is strictly worse than a slower reframing that doesn't.

## What this changes for future engagements

Every new engagement now lands as "an instance of a shape." The intake question is: which finding-shape does this engagement's failure modes correspond to? If the shape exists in the spec, the engagement inherits the matcher-map row, the hook patterns, the OTel signal definitions, and the conformance criteria for free. The engagement-specific work is then the actual audit: do the hooks fire, do the signals show up, what's the conformance gap.

If the shape doesn't exist, the engagement produces a new module. The Polygon engagement, when it activates, produces `validator-contract-reliability` content. The Nixtla engagement produces `forecasting-drift-detection` content. The Lit engagement produces `decentralized-crypto-evaluation` content. The shape gets added to the matcher-map. The next engagement of the same shape inherits it.

The auditor-of-one model required me to rebuild the audit framework for each engagement. The methodology-layer model means each engagement either is-a (inherits) or extends (contributes). N engagements produces an asset that compounds. N engagements under the old model produced N audit reports.

## The takeaways, packaged tight

Six items I'd hand to anyone running a sole-prop AI consultancy or a small AI-engineering team:

1. **Re-read the contract before arguing it.** Internal interpretations of verbal context drift. The document doesn't. When a partner pushes back, the first move is the SOW, not the rebuttal.

2. **Partition contracted-deliverable content from methodology-track content.** Don't let them share a row in your operating doc, a publication channel, or an authorship surface. The boundary is what makes both possible.

3. **A spec is a structural artifact, not a marketing artifact.** Anchor every normative requirement to a canonical published source. If you can't cite it, don't prescribe it. The discipline protects the spec's integrity, and credibility follows.

4. **Decouple the spec language from the runner language.** Pick the runner language for the runner's reasons (distribution, ecosystem, cold start). Keep the spec language-neutral so contributors aren't blocked by toolchain. Reference implementations are references, not gates.

5. **Reserve structural slots with placeholder READMEs.** Three READMEs that name domain-specific failure modes signal "this is a methodology umbrella" without overcommitting to timelines for modules you haven't earned the right to write yet.

6. **Hold the timeline when the reframing risks the partner deliverable.** The spec is forever. The deliverable is May 25. Don't trade a fixed-date partner asset for a marketing window on something that's going to compound for years either way.

Also shipped today, in an unrelated repo: PR #707 on `claude-code-plugins` — a CSS grid overflow fix for the marketplace landing on iPhone 13 viewports. `1fr → minmax(0, 1fr)` on the pcard-hosting grids, `minmax(min(320px, 100%), 1fr)` on the multi-column auto-fill grids, and `min-width: 0; max-width: 100%` on `.pcard` itself. Defense in depth against the [nested-flex-grid overflow](https://css-tricks.com/preventing-a-grid-blowout/) that 47 px of hidden width was causing. Worth noting only because it landed the same day; it has nothing to do with the rest of this post.

The version on disk is `v0.1.0-draft`. It will move. The spec that exists now is not the spec I would have written before Frank's email — that one would have been a Kobiton-shaped artifact dressed up as methodology. Instead it's a methodology layer that Kobiton, among others, will be instances of. The shape it took on this morning, after a partner email forced a contract re-read, is the shape it kept.
