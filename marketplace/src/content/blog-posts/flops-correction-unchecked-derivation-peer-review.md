---
title: "The 35x FLOPs Error That Peer Review Predicted"
description: "A 35x FLOPs correction in pre-filing patent artifacts validated the reviewers' unchecked-derivation warning. The day's other shipments show what systematizing against named failure classes looks like."
date: "2026-04-15"
tags: ["architecture", "release-engineering", "code-quality", "ai-agents", "claude-code", "automation", "supply-chain-security"]
featured: false
---
Peer review is not paperwork. When a reviewer tells you "unchecked derivations are your highest-risk failure class," they are handing you the exact failure that will bite you if you skip the checklist.

On April 15 a FLOPs figure in pre-filing patent artifacts for QCSS quietly moved from 19M to 679M — a 35x underestimate — exactly the class the reviewers flagged. Elsewhere in the portfolio that same day, cosign and SLSA provenance shipped for a daemon image, an 11-dimension code-cleanup plugin landed, a 5-agent research chain got recoverable failure states, and a marketplace shed 24,884 lines of obsolete scripts. Different projects, same pattern: systematize against the failure classes you can name.

This post is about that pattern.

## The unchecked derivation

Commit `6c07680` on semantic-flux reads:

```
fix: correct Architecture C FLOPs figure (19M → 679M) across paper, patent, design
```

Architecture C is the production profile of Query-Compiled Semantic Scan (QCSS) — a retrieval architecture that compiles a natural-language query into a lightweight scoring operator, then scans raw, never-embedded text with that operator. The operator is applied many times per query. That "many times" is the entire story.

The FLOPs figure in §4.1 of the paper had been computed for a single operator application. It was never multiplied by the number of applications per query. The error was not subtle; it was a missing loop.

Five files changed in the same commit:

- `paper/QCSS-paper-draft.md` §4.1 — replaces 19M with 679M and spells out the throughput implication
- `attorney-package/04-formal-specification.md` — claims a range of 33K to 679M FLOPs rather than a point value, giving the patent a stronger posture against reduction-to-practice attacks
- `paper/README.md` — marks gap G2 closed with a reference to `DESIGN.md` §7.2
- `DESIGN.md` — 82 lines changed, including the derivation that should have been there in the first place
- `DECISIONS.md` — 18 new lines, a permanent record of what went wrong and what it costs us

The commit body is the interesting part:

```
Downstream impact: throughput gate (50K passages/sec) is now on
the edge, not comfortably above. Phase 1 must preregister a d=96
fallback. This is exactly the unchecked-derivation failure mode
peer review warned about — better found now than in examiner review.
```

A 35x FLOPs increase does not leave the throughput budget alone. The headline claim — 50,000 passages per second on the reference hardware — used to have comfortable headroom. Now it sits on the edge. The mitigation is [preregistration](https://www.cos.io/initiatives/prereg): Phase 1 of the experiment commits, in advance, to a d=96 embedding-dimension fallback if the d=128 configuration misses the throughput gate. Preregistering the fallback before running the experiment is how you avoid the "we moved the goalposts after seeing the data" failure mode that kills empirical claims in patent review.

The Phase 0 conditional-go review two days earlier (April 13) had named three failure classes: unchecked derivations, untested claims, unpegged hardware. FLOPs was in bucket one. The reviewers did not tell us the FLOPs figure was wrong — they did not do the arithmetic. They told us the *class* of error we were most likely to make. Then we made it.

## Believing the reviewer

There is a version of peer review where the reviewer finds specific bugs and you fix them. That version is less useful than it sounds. Specific findings are a sample. The reviewer read some of your document carefully and some of it quickly. The bugs they found correlate with where they looked, not with where the worst bugs are.

The more valuable output of a careful review is a named failure class. "Your highest risk is unchecked derivations." That is a statement about the whole document, not about a paragraph. It tells you where to look with a checklist, not where the reviewer already looked.

The April 13 Phase 0 conditional-go review delivered three such classes. By April 15, one of them had paid out at 35x. The question is not "did the reviewer catch it" — they did not, and they were not supposed to. The question is "did we run the checklist." We did, and we found it, and we documented it before filing.

Patent provisional deadline is June 12. Finding a 35x error in examiner review after filing is a different kind of day than finding it now.

## Meanwhile in another repo: supply-chain provenance

The same morning, qmd-team-intent-kb cut v0.4.0. The headline PR is #82: cosign keyless signing and SLSA provenance for the edge-daemon Docker image.

The release workflow gains a tag-gated `build-and-push-image` job:

```yaml
build-and-push-image:
  runs-on: ubuntu-latest
  if: startsWith(github.ref, 'refs/tags/v')
  permissions:
    contents: read
    packages: write
    id-token: write
  steps:
    - uses: docker/build-push-action@v6
      id: build
      with:
        push: true
        tags: ghcr.io/jeremylongshore/qmd-team-intent-kb-edge-daemon:${{ github.ref_name }}
    - uses: sigstore/cosign-installer@v4
    - run: |
        cosign sign --yes \
          ghcr.io/jeremylongshore/qmd-team-intent-kb-edge-daemon@${{ steps.build.outputs.digest }}
```

Then a `provenance` job chains to [`slsa-framework/slsa-github-generator`](https://github.com/slsa-framework/slsa-github-generator) to produce a [SLSA Build Level 3](https://slsa.dev/spec/v1.0/levels) provenance attestation bound to the same digest.

Consumers verify the image before they run it:

```bash
cosign verify \
  ghcr.io/jeremylongshore/qmd-team-intent-kb-edge-daemon:v0.4.0 \
  --certificate-identity-regexp "https://github.com/jeremylongshore/qmd-team-intent-kb" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com"

cosign verify-attestation \
  ghcr.io/jeremylongshore/qmd-team-intent-kb-edge-daemon:v0.4.0 \
  --type slsaprovenance \
  --certificate-identity-regexp "https://github.com/jeremylongshore/qmd-team-intent-kb" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

Keyless is the substantive change. The old pattern is a signing key stored in a secrets manager, rotated on a schedule, revoked when someone guesses wrong about who had access. The new pattern: the GitHub Actions runner mints a short-lived OIDC token, exchanges it with [Fulcio](https://docs.sigstore.dev/certificate_authority/overview/) (Sigstore's certificate authority) for an ephemeral certificate bound to the identity, uses the certificate to sign the digest once, and writes the certificate plus signature to the [Rekor transparency log](https://docs.sigstore.dev/logging/overview/). There is no long-lived signing key to rotate or leak — trust is shifted to the Sigstore CA and transparency log infrastructure.

The failure class being systematized here is "supply chain compromise." The name is not new. What is new, for this repo, is that the verify command gives a consumer a cryptographic answer to "did this image come from the CI job in the repo I think it came from." That is what PR #82 buys.

PR #84 shipped the same week and targets a different failure class: "contract drift between code and docs." Wiring `@fastify/swagger` plus Swagger UI at `GET /docs` makes the control plane publish its own OpenAPI contract at `GET /openapi.json`, generated from the route metadata itself. Every route declares minimal schema — tags, summary, description — without any handler logic changing. Route registration got wrapped in an inner `app.register()` so the swagger `onRoute` hook fires at registration time. The contract is generated from the routes, not maintained next to them, so the class of error "docs said one thing, the API did another" stops being a class.

PR #83 targets the class "internal packages copy-pasted as folders instead of published as libraries." Adding `publishConfig` so internal packages can publish to a private registry means libraries become libraries, with versioning and consumers and a changelog, instead of snapshots in a sibling directory.

Then a 20-PR quality sweep in the same day. A sample:

- **#58** — DRY sweep on fixture factories and the spool JSONL writer
- **#54** — Removed AI slop: `// Check if the item is valid before processing` above `if (!isValid(item)) return`
- **#53** — Deleted `ConsoleDaemonLogger`, `NullLogger`, and vestigial public re-exports (pino was standardized weeks earlier)
- **#56** — Removed unused code flagged by knip
- **#57** — Replaced `Record<string, unknown>` with a typed interface and `any` with proper types
- **#73** — Replaced repository type casts with Zod-on-read validation
- **#78** — Replaced the `as Record<string, unknown>` delete pattern with rest-destructure in schema tests
- **#55** — Broke a peer-level `mcp-server` → `edge-daemon` import through a shared interface package
- **#51** — Consolidated `SensitivityLevel` into the schema `Sensitivity` type
- **#52** — Deleted defensive `try/catch` hiding fast-glob errors in `importFiles`; error propagates, caller decides
- **#48** — Fixture-based test suite covering 9 repo-resolver edge cases
- **#49** — HTTP `/healthz` and `/last-cycle` endpoints
- **#45** — Replaced `ConsoleDaemonLogger` with structured pino logging
- **#47** — Exponential-backoff-with-jitter retry for transient failures
- **#46** — Deployment artifacts (systemd, launchd, docker) plus an ops runbook

Compare #52 specifically. Before:

```ts
export async function importFiles(pattern: string): Promise<string[]> {
  try {
    const results = await fg(pattern);
    if (!results || results.length === 0) {
      return [];
    }
    return results;
  } catch (err) {
    return [];
  }
}
```

After:

```ts
export async function importFiles(pattern: string): Promise<string[]> {
  return fg(pattern);
}
```

The ten-line version swallowed errors and returned an empty array. The three-line version propagates the error and lets the caller decide. The caller now has the information to make that decision. That is a failure class — "defensive code that hides failures" — being removed from the codebase one call site at a time.

## Meanwhile in another repo: 11 failure classes, 11 agents

Commit `2ca7720e0` on claude-code-plugins reads:

```
feat: add Ultimate Code Cleanup plugin — 11 dimensions, 11 agents, 98/100 A+
```

Twenty-five new files. Four thousand eighty-one lines added. One skill (`cleanup-code`) orchestrates the work. Eleven agents, one per failure class, ordered by the plugin's risk model:

| # | Agent | Risk | Default |
|---|-------|------|---------|
| 1 | dead-code-hunter | LOW | auto-apply |
| 2 | slop-remover | LOW | auto-apply, comments only |
| 3 | weak-type-eliminator | MED | auto-apply |
| 4 | security-scanner | MED | flag only |
| 5 | legacy-code-remover | MED | confirm |
| 6 | type-consolidator | MED | auto-apply |
| 7 | defensive-code-cleaner | MED | auto-apply |
| 8 | performance-optimizer | MED | auto-apply |
| 9 | dry-deduplicator | HIGH | flag only, ≥10 lines |
| 10 | async-pattern-fixer | HIGH | flag only |
| 11 | circular-dep-untangler | HIGH | flag only |

The ordering is load-bearing. Dead code goes first because deletion is the safest transformation: if a function has zero callers, removing it cannot break anything. Type consolidation comes before dead code only if you are doing full-repo refactoring — otherwise you waste cycles consolidating a type you are about to delete. DRY deduplication is last and flag-only because "this looks duplicated" is frequently wrong at the semantic level.

Build verification runs between dimensions. If dimension 4 breaks the build, dimensions 5 through 11 do not execute. Confidence scoring rides along — the agent reports how sure it is about each change, and anything below the threshold gets flagged instead of applied.

Four reference docs ship with the plugin: dimensions, tools, patterns, safety protocol. Enterprise validator scores it 98/100 (A+). Invocations look like:

```
/cleanup-code
/cleanup-code --dimensions dead,types,security
/cleanup-code src/api/ --changed
```

The plugin is a systematization of the quality sweep you just read about in qmd. Instead of a human spotting a `ConsoleDaemonLogger` that pino replaced weeks ago, the dead-code-hunter finds it. Instead of a human deleting the `// Check if valid` comment above `if (!isValid)`, the slop-remover does. The qmd quality sweep *is* this plugin, executed by hand.

Meanwhile in the same claude-code-plugins repo: commit `f61853026` — "refactor: comprehensive codebase cleanup — 8 parallel agents" — changed 126 files at 423 insertions and 25,307 deletions. The deletions were scripts that had been used once and never cleaned up: `overnight-skill-fix.py` at 978 lines, `skills-generate-vertex-safe.py` at 740, `skill-gap-report.py` at 577, `skills-enhancer-batch.py` at 651, `validate-plugin.js` at 807. Eight parallel agents did the work. A human confirmed the deletions. A 24,884-line net reduction in a single commit is the kind of thing that happens when you have named the failure class — "one-shot scripts that accreted" — and pointed a system at it.

Four more cleanup commits landed the same week, each one a named failure class caught by tooling rather than by hand:

- `4e07649fe` — resolved 27 validation errors across 3,874 files (schema drift between skill definitions and the validator)
- `11f7b5b94` — split 13 SKILL.md files that exceeded the 500-line limit (notion-pack 4, supabase-pack 8, sentry-pack 1)
- `b2debbdf8` — removed XML tags from 4 skill descriptions
- `fa1977410` — fixed an unused `tableHeaderDone` variable flagged by CodeQL

## Meanwhile in another repo: failure state has a home now

Intentional Cognition OS shipped v0.9.1, v0.9.2, and v0.9.3 back to back. The headline is v0.9.1, commit `87794f4`:

```
feat(compiler): research orchestrator with recoverable failure states (E9-B06)
```

E9-B06 caps Epic 9's 5-agent episodic research chain:

- **B02** collector — pulls raw sources
- **B03** summarizer — compresses per source
- **B04** skeptic — red-teams each summary
- **B05** integrator — merges into a research artifact
- **B06** orchestrator — shipped April 15

Without the orchestrator, a failure at any stage killed the whole cycle. A malformed JSON response from the LLM at the summarizer step meant the skeptic never ran, the integrator never ran, and the cycle burned its budget on nothing. Rate limits, schema drift, and transient network errors all had the same failure mode: the pipeline died, mid-flight, with partial results and no way to resume.

With B06, failures get classified. Transient failures — network timeouts, rate limits, malformed JSON from a model that usually returns valid JSON — go into bounded retry with exponential backoff. Permanent failures — schema mismatches after a model upgrade, auth errors that will not resolve by retrying — fail fast. The orchestrator owns retry policy, the circuit breaker, and the dead-letter path. The agents own their output. The split matters: an agent that tries to own its own retry policy turns into a retry-policy library with a model call in the middle, and then every agent has its own subtly different version of the same policy.

That split is the pattern. A named failure class — "transient LLM errors kill multi-stage pipelines" — gets handled in one place by one component. The components above and below get simpler because they no longer have to reason about it.

## The permanent correction record

Back to semantic-flux. The 18-line addition to `DECISIONS.md` is worth reading carefully because the pattern is portable:

```markdown
## 2026-04-15 — Architecture C FLOPs Correction

**Correction**: §4.1 FLOPs figure revised from 19M to 679M.

**Root cause**: Prior derivation computed FLOPs for a single
operator application without multiplying by application count
per query. 35x underestimate.

**Downstream impact**: Throughput gate (50K passages/sec on
reference hardware) moves from comfortable headroom to edge-of-
budget. d=128 configuration is no longer robustly above gate.

**Mitigation**: Phase 1 experiment plan preregisters d=96
fallback configuration. Preregistration is filed before Phase 1
execution begins.

**Forward check**: Checklist item C-4 added to pre-filing review:
"For every FLOPs, throughput, and latency figure, confirm the
derivation includes the loop bound."
```

Four sections: correction, root cause, downstream impact, mitigation. Plus a forward check — a new line on the pre-filing checklist that will catch this specific shape of error next time. The checklist grows. The review gets longer. That is the point.

The alternative — fix the bug, move on, don't write it down — is how you ship the same bug again six months later under a different disguise. `DECISIONS.md` is a write-ahead log for judgment. If the patent examiner asks "when did you know" and "what did you do about it," the answer has a timestamp.

## Tradeoffs

Every systematization on this list costs something.

**Cosign and SLSA cost Sigstore trust.** Keyless signing means you are trusting the Sigstore transparency log and the GitHub OIDC issuer. Those are not infinitely trustworthy. They are more trustworthy than a secret in a CI variable, and they avoid the key-rotation failure mode, but they move the trust, they do not eliminate it. The cost is a dependency on an external service run by other humans.

**The 11-dimension cleanup plugin costs auto-apply risk.** Three of the dimensions default to auto-apply. The plugin gates on confidence scores and build verification between dimensions, but a weak-type-elimination change that compiles and passes tests can still be wrong semantically. The cost is that a regression introduced by the plugin looks exactly like a regression introduced by the author, and `git blame` will point at the commit that ran the skill. The mitigation is that flag-only is an option and commit boundaries are per-dimension.

**The orchestrator costs a failure taxonomy upfront.** B06 works because "transient" and "permanent" are defined in advance. A failure the taxonomy does not cover goes down the default path, which is almost always wrong. Every new kind of failure — a new model's new error surface, a new provider's new rate-limit semantics — is a taxonomy migration. The cost is ongoing curation.

**The DECISIONS.md pattern costs discipline.** The entry only exists if someone writes it. A correction that ships without the 18-line record is a correction that will get re-made next year by someone who never heard about this one. The cost is that the process depends on the author not being in a hurry, which is a fragile assumption.

**Preregistration costs optionality.** The d=96 fallback ties our hands. If Phase 1 misses the throughput gate at d=128, we fall back to d=96 even if post-hoc analysis would suggest d=112 is better. The cost is that "post-hoc analysis would suggest" is exactly the optionality that makes empirical claims unfalsifiable. We bought rigor by paying optionality.

## Where this fits

AI-assisted development produces more code, faster, than human review alone catches. That is not a complaint — it is an observation about throughput. A single reviewer can read a 200-line diff carefully. A single reviewer cannot read the twenty 200-line diffs that land on a productive day with an AI pair. The math does not work.

Systematization is how you scale review past what any one reviewer can hold in their head. It has three moves:

1. **Name the failure class.** "Unchecked derivations." "Supply chain compromise." "Defensive code that hides failures." "Transient LLM errors that kill pipelines." "One-shot scripts that accreted." Names are cheap; the discipline is making them specific enough to be actionable.
2. **Point a system at the class.** A checklist item. A verify command. An agent. An orchestrator. A `DECISIONS.md` entry. The system does not have to be sophisticated — it has to run every time.
3. **Log when it fires.** The system that catches failures silently is a system you will stop trusting. The system that catches failures loudly and writes them to a permanent record is a system that earns its keep.

The FLOPs correction fired the checklist that a careful reviewer handed us two days earlier. The cosign workflow fires every time a tag gets pushed. The cleanup plugin fires when a human runs `/cleanup-code`. The research orchestrator fires on every cycle. The `DECISIONS.md` pattern fires whenever someone writes the four-section entry.

None of this replaces careful human judgment. It makes careful human judgment scale to a throughput that would otherwise drown it. That is the whole game now.

## Related Posts

- [QCSS Research Corpus: Twenty-One Documents and a Weak Reject](/blog/qcss-research-corpus-twenty-one-documents/)
- [Twelve PRs, a Security Sprint, and a Pregame Overhaul](/blog/twelve-prs-security-sprint-pregame-overhaul/)
- [Wild Deep Dive #4: Tech Lead](/blog/wild-deep-dive-4-tech-lead/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "The 35x FLOPs Error That Peer Review Predicted",
  "description": "A 35x FLOPs correction in pre-filing patent artifacts validated the reviewers' unchecked-derivation warning. The day's other shipments show what systematizing against named failure classes looks like.",
  "datePublished": "2026-04-15T10:00:00-05:00",
  "dateModified": "2026-04-15T10:00:00-05:00",
  "author": {"@type": "Person", "name": "Jeremy Longshore", "url": "https://startaitools.com/about/"},
  "publisher": {"@type": "Organization", "name": "Intent Solutions", "url": "https://startaitools.com"},
  "mainEntityOfPage": {"@type": "WebPage", "@id": "https://startaitools.com/posts/flops-correction-unchecked-derivation-peer-review/"},
  "keywords": "peer review, failure class, cosign SLSA, unchecked derivation, code cleanup, supply-chain-security"
}
</script>
