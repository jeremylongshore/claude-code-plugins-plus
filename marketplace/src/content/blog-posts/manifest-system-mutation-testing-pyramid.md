---
title: "Manifest System + Mutation Testing: Two Ways to Find Out What Actually Works"
description: "Epic 31-B lands the publish side of the bot-manifest protocol in claude-code-slack-channel. Epic 31 closes with an audit. Mutation tests and a cyclomatic gate make the test pyramid stop lying."
date: "2026-04-20"
tags: ["typescript", "testing", "ci-cd", "architecture", "monorepo", "claude-code", "release-engineering"]
featured: false
---
You can ship a feature that looks tested and isn't. April 20 was two coordinated answers to that problem.

On one front (`claude-code-slack-channel`), the bot-manifest protocol's *publish* side landed — the second half of a protocol whose consumer side had shipped on April 19. The same repo set a Stryker mutation baseline, killed the top-5 mutation survivors on its security primitives, and added a TypeScript-aware cyclomatic-complexity gate to CI. On another (`claude-code-plugins`), mass-publish infrastructure for the npm catalog scaffolded — scaffold-every-package-json generator, mass + incremental publish workflows, a SIGPIPE fix for the enumerate step. The narrative thread is the same across both: don't trust that something works until an adversarial check tries to prove it doesn't.

## The bot-manifest publish side — Epic 31-B

Context from the day before: `claude-code-slack-channel` is an MCP server that lets Claude Code operate inside a Slack thread. In late Epic 31-A, peer bots got the ability to *read* each other's manifests — pinned JSON in a Slack channel announcing "here's what tools I expose." The read path was guarded by a 40 KB size cap, a 5-minute per-channel cache, and the hard invariant that manifest content never reaches `evaluate()` (the policy engine).

Epic 31-B ships the other side: a bot can now *publish* its own manifest.

Publishing sounds easier than reading. It isn't, because the publisher controls the payload, and everything a trusted publisher emits will eventually be consumed by someone who trusts it.

### The `publish_manifest` tool

[PR #119](https://github.com/jeremylongshore/claude-code-slack-channel/pull/119) is the headline — a new MCP tool with replace semantics. The flow:

1. **Zod-validate input.** `channel` must be a public `C...` ID, `caller_user_id` must be a `U...`, `manifest` must pass the full `ManifestV1` schema.
2. **`assertPublishAllowed(caller_user_id, access)`** — only humans in `access.allowFrom` may authorize a publish.
3. **`assertOutboundAllowed(channel)`** — the channel must be in the outbound allowlist (same gate as any other message).
4. **Size cap** — publish-side cap is 8 KB, not the read-side 40 KB. Postel's Law: be conservative in what you send.
5. **Rate limit** — one publish per channel per hour, enforced in-memory.
6. **Replace semantics** — find our prior pinned manifest (filter by magic header), remove it (best-effort; flaky `pins.list` skips the sweep), then `chat.postMessage` the new manifest, then `pins.add`, then journal the event.

Replace semantics shipped together with the base tool ([PRs #119 + #123](https://github.com/jeremylongshore/claude-code-slack-channel/pull/123)) because without them, every publish call would pile another pinned manifest in the channel. They are one correctness unit, not two features.

### Why 8 KB when the read cap is 40 KB

[PR #120](https://github.com/jeremylongshore/claude-code-slack-channel/pull/120) is the 8 KB publish-side cap. The asymmetry is deliberate. A publisher writes content *it controls*. Tightening the cap catches operator mistakes at publish time — an accidentally pasted API payload, a `toString()` of the wrong object — rather than letting oversized content travel out and get caught by every reader separately. Be conservative in what you send, liberal in what you receive.

### Rate-limiting the publisher

[PR #121](https://github.com/jeremylongshore/claude-code-slack-channel/pull/121) caps publishing to one per channel per hour. In-memory only, resets on process restart, same posture as the read cache. The factory:

```ts
createPublishRateLimiter({
  now: () => Date.now(),
  windowMs: 60 * 60 * 1000,
  maxEntries: 256,
})
```

Factory with injected time source so tests can fast-forward. Soft LRU at 256 entries so a single long-running server doesn't leak memory across thousands of channels. Rejection error includes "how long ago the last publish was" and "approximate minutes remaining" so the caller can back off instead of retry-looping.

### Round-trip testing

[PR #123](https://github.com/jeremylongshore/claude-code-slack-channel/pull/123) is the test that catches "we forgot to serialize a field":

```ts
// publisher chain: assertPublishSizeAndSerialize → JSON
// reader chain:    JSON → extractManifests
const published = assertPublishSizeAndSerialize(manifest)
const readBack = extractManifests(published)
expect(readBack).toEqual(manifest)  // byte-for-field
```

Three cases — minimal manifest, fully-populated manifest with every optional field, a 1000-char-description fixture pinning the Postel-Law safety margin (publish body fits read cap with ~5× headroom). If anyone adds a new optional field to the schema and forgets to include it in the publisher's serialization, round-trip fails immediately.

### A2A alignment

[PR #122](https://github.com/jeremylongshore/claude-code-slack-channel/pull/122) adds an optional `agentCard` field for interop with Google's Agent-to-Agent protocol's `/.well-known/agent-card.json` shape. Nothing in the Slack path consumes it. It exists so a future HTTP-transport publisher can reuse the same manifest field verbatim. Schema-level interop is cheap today and expensive to retrofit. The [PR #118](https://github.com/jeremylongshore/claude-code-slack-channel/pull/118) docs update includes a field-by-field mapping table between `ManifestV1` and the A2A agent card: `name/description/version` → vendor, `tools` → skills.

## Epic 31 closes — the audit pass

[PR #125](https://github.com/jeremylongshore/claude-code-slack-channel/pull/125) is a `/audit-tests` run that closes Epic 31. Headline: **no P0 findings**.

| Metric | Value |
|--------|-------|
| Tests passing | 594 |
| Skips / only / todo | 0 / 0 / 0 |
| Line coverage | 98.37% |
| Function coverage | 98.75% |
| Assertions per test | 2.47 |
| Negative-path `.toThrow()` assertions | 104 |

The 31-A.4 invariant — manifest never reaches `evaluate()` — is enforced three ways (architecture config, compile-time `@ts-expect-error`, runtime test) and all three are present in the audit evidence. Strict TypeScript, typecheck-required CI, CodeQL SAST, OpenSSF Scorecard. The audit produced `000-docs/TEST_AUDIT.md` which is how the next epic will know what shape the test suite was in when it started.

## Mutation testing baseline — adversarial testing on the security primitives

Coverage numbers lie. A test that calls a function but asserts nothing about its output contributes to line coverage and contributes nothing to confidence. [PR #128](https://github.com/jeremylongshore/claude-code-slack-channel/pull/128) set up Stryker mutation testing as an adversarial-testing baseline and captured the first score.

Mutation testing flips operators, deletes statements, negates conditionals, and re-runs the suite. A *surviving* mutant is a change that didn't break any test — evidence that the test suite doesn't actually exercise the mutated code. A *killed* mutant is a test earning its keep.

[PR #133](https://github.com/jeremylongshore/claude-code-slack-channel/pull/133) took the top-5 survivors on security primitives and killed them. That's the right next move after a baseline: don't try to drive the global score, drive the survivors on code you cannot afford to regress.

[PR #137](https://github.com/jeremylongshore/claude-code-slack-channel/pull/137) expanded the Stryker scope to `policy + manifest + journal` — the three subsystems from the April 19 security sprint. Mutation coverage on the code that enforces trust boundaries matters more than mutation coverage on glue code.

## TypeScript-aware cyclomatic-complexity gate

[PR #135](https://github.com/jeremylongshore/claude-code-slack-channel/pull/135) landed a cyclomatic complexity gate that understands TypeScript — union types, type guards, discriminated unions. The threshold is intentionally loose at introduction (the goal is "catch new 30+ complexity functions," not "rewrite existing code"), with the expectation that the threshold tightens over time as the codebase refactors.

Complexity gates are one of those tools that teams install and then quietly turn off. The trick is to set the threshold *above* the current worst-case and decrement it monthly. That way the gate never blocks merges on day one and never rubber-stamps regressions on day thirty.

## Gherkin runner wired

[PR #134](https://github.com/jeremylongshore/claude-code-slack-channel/pull/134) wired the Gherkin runner to actually execute `features/*.feature` files instead of just linting them. A BDD test suite that lints but never runs is worse than no BDD test suite — it creates the illusion of executable specs without any of the coverage.

## The npm catalog — mass publish + stats

`claude-code-plugins` got the other half of April 20's delivery. The plugin hub ships `cc` plugins as an npm catalog, and the mass-publish infrastructure was scaffolded across three PRs:

- **[PR A/D](https://github.com/jeremylongshore/claude-code-plugins/pull/541)** — scaffold `package.json` for every catalog plugin (hundreds of entries). One template, one generator, one PR that touches a lot of files but contains exactly zero decisions.
- **[PR B/C of D](https://github.com/jeremylongshore/claude-code-plugins/pull/542)** — mass + incremental publish workflows. Mass publishes the whole catalog on demand; incremental publishes only what changed since the last tag.
- **[PR #544](https://github.com/jeremylongshore/claude-code-plugins/pull/544)** — fix a SIGPIPE abort in the mass-publish enumerate step. Piping `npm search` output into a downstream process that closed early caused the whole publish to abort; the fix swallows SIGPIPE and continues.

On top of publishing, [the stats aggregator](https://github.com/jeremylongshore/claude-code-plugins/commit/ac28a233b) lands — daily cron collects npm download counts, posts a Slack digest, and drives a new marquee surface on the marketplace page. Turning download counts into visible social proof is a one-time investment that keeps paying off.

## Also shipped

- **braves** — per-panel error boundaries so a single broken panel can't blank the whole dashboard. Fault-isolation is the same defensive posture as process-level invariants: assume any sub-unit can fail, and make the failure contained.
- **claude-code-plugins v4.26.0** — cut after the publish infra landed. Marketplace got the agent37 partner restored in the hero marquee and an awesome-list-style TOC generated directly from the catalog.

## What the three moves have in common

The manifest publish side, the npm mass-publish infrastructure, and the Stryker baseline are the same move at different altitudes.

- **Round-trip tests** on the manifest publisher prove it serializes everything the schema declares. Adversarial check against the serializer.
- **Incremental publish + mass publish workflows** on the npm catalog diff the last-published state against the current state and only ship what changed. Adversarial check against "did I remember to bump this package."
- **Mutation tests** on the security primitives prove the test suite kills the mutants that would matter. Adversarial check against the tests themselves.
- **Cyclomatic gate** proves nobody silently dropped a 40-branch monster into the dispatcher. Adversarial check against complexity creep.

Coverage, clean builds, and passing suites are the floor. Adversarial checks are the ceiling. April 20 raised both across both repos.

## Related posts

- [Four Releases in One Day — CCSC Security Sprint](/posts/ccsc-five-releases-one-day-security-sprint/) — yesterday's security sprint that this day's 31-B work extended
- [Twelve PRs Security Sprint + Pregame Overhaul](/posts/twelve-prs-security-sprint-pregame-overhaul/) — earlier ccsc security batch with the same batching discipline
- [Collaboratively Shaped Roadmap](/posts/collaboratively-shaped-roadmap/) — where the Epic 31 plan came from

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Manifest System + Mutation Testing: Two Ways to Find Out What Actually Works",
  "description": "Epic 31-B lands the publish side of the bot-manifest protocol in claude-code-slack-channel. Mutation tests and a cyclomatic gate make the test pyramid stop lying.",
  "datePublished": "2026-04-20T09:00:00-05:00",
  "author": {
    "@type": "Person",
    "name": "Jeremy Longshore",
    "url": "https://startaitools.com/about/"
  },
  "publisher": {
    "@type": "Organization",
    "name": "StartAITools",
    "url": "https://startaitools.com"
  },
  "articleSection": "Technical Deep-Dive",
  "keywords": "typescript, testing, ci-cd, architecture, monorepo, claude-code, release-engineering",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://startaitools.com/posts/manifest-system-mutation-testing-pyramid/"
  }
}
</script>

---

Jeremy made me do it
-claude

