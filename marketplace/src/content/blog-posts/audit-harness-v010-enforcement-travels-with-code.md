---
title: "Enforcement Travels With the Code: Shipping @intentsolutions/audit-harness v0.1.0"
description: "Testing policy enforcement that lives in ~/.claude/ cannot travel with a fresh clone. audit-harness v0.1.0 moves the gates into each repo as a versioned dev dependency — npm, PyPI, crates, and bash install.sh."
date: "2026-04-21"
tags: ["testing", "ci-cd", "architecture", "release-engineering", "devops", "automation", "monorepo", "typescript"]
featured: false
---
Testing policy that lives in `~/.claude/` is testing policy that dies on a fresh clone.

For the last six months the Intent Solutions repos have shared a common `/audit-tests` and `/implement-tests` skill pair — seven-layer taxonomy, RTM/personas/journeys, CRAP-score gates, escape-scan, harness-hash pinning. The skills did the enforcement *from* my workstation. That's fine until someone else clones the repo. Then the pre-commit hook that references `~/.claude/skills/audit-tests/scripts/escape-scan.sh` is gone, the CI job that validates the RTM is gone, and the policy that said "tests must kill 80% of mutants" is a markdown file nobody's workflow actually consults.

April 21 was the day enforcement moved into the repo.

## The three-line thesis

The audit-harness repo ships three surfaces that together enforce the same testing policy everywhere:

1. **An npm package** — `@intentsolutions/audit-harness` — installed as a dev dependency in any Node repo: `pnpm add -D @intentsolutions/audit-harness`. Adds `pnpm exec audit-harness <subcommand>` to the repo. Hooks and CI reference that local binary.
2. **PyPI and crates.io wrappers** — `intent-audit-harness` on PyPI, `intent-audit-harness` on crates. Same scripts, same CLI surface, distributed through each language's package manager. No Node required.
3. **`install.sh`** — for polyglot or language-less repos. `curl -sSL https://raw.githubusercontent.com/jeremylongshore/audit-harness/main/install.sh | bash`. Copies the scripts into `.audit-harness/` in-repo. Committed. Versioned. Updates via re-run.

The package shipped as [v0.1.0](https://github.com/jeremylongshore/audit-harness) today. Three commits, three wrappers. The smallest possible unit of "you can now install this."

| Commit | What it is |
|--------|-----------|
| `75b19fc init: @intentsolutions/audit-harness v0.1.0` | The npm package — scripts, CLI dispatch, manifest |
| `6162cf6 feat: add install.sh for non-Node repos` | Bash installer that vendors `.audit-harness/` |
| `9b97217 feat: add PyPI and crates.io wrappers for audit-harness` | Python + Rust distribution mirrors |

## Why this is different from "share the scripts"

There's a naive version of this: commit the scripts into every repo, update them by hand. It fails on three dimensions:

1. **Versioning.** Updating escape-scan to catch a new pattern would require a PR to every repo. You'd miss some. The ones you missed would silently run an older, permissive version.
2. **Policy hash-pinning.** The whole point of the `verify` subcommand is that `tests/TESTING.md`'s policy lines are hashed and pinned. An AI-proposed edit to the policy without a matching hash re-init → REFUSE at pre-commit. That only works if the hash binary is versioned *with* the policy schema it's verifying. Copy-pasted scripts drift; package-managed ones don't.
3. **Installability.** The skill `/implement-tests` needs to install this on a fresh repo as step 0. `pnpm add -D @intentsolutions/audit-harness` is one command. "Copy the scripts from a known-good repo and update the paths" is a doc that dies when the known-good repo moves.

The enforcement *has to* travel with the code. That's the rule. The package is the mechanism — every fresh clone is a reproducible CI environment without external dependencies on anyone's workstation.

## The CLI surface

`audit-harness <command>` routes to the script for each taxonomy layer:

- `audit-harness init` — writes `.harness-hash` pinning the current `tests/TESTING.md` policy sections. Re-run after any engineer-reviewed edit.
- `audit-harness verify` — verifies the hash manifest. Used in pre-commit and CI.
- `audit-harness escape-scan` — scans diffs for REFUSE / CHALLENGE / FLAG patterns (the escape-detection-agent's job, made deterministic).
- `audit-harness crap` — Change Risk Anti-Pattern score (cyclomatic × coverage shortfall).
- `audit-harness arch` — architecture invariant checks (dependency-cruiser, cargo-modules, equivalent per language).
- `audit-harness bias-count` — counts bias markers in test fixtures (prevents asymmetric test data that masks real failures).
- `audit-harness gherkin-lint` — lints `.feature` files against a curated rule set.

The scripts themselves are deterministic — no LLM in the loop. That's the point. When a gate refuses a change, the refusal is reproducible on any clone. "The LLM decided to block this" is not an auditable gate; "the script exits 1 on this pattern" is.

## The parallel story: Biome cuts the static-analysis cost to near-zero

If audit-harness is "make enforcement travel with the code," [Epic ccsc-dz8](https://github.com/jeremylongshore/claude-code-slack-channel/pull/139) is "make the enforcement cheap enough that nobody is tempted to skip it." Enforcement that travels with the code is worthless if every engineer disables it locally to ship faster. Biome replaced ESLint + Prettier + a half-dozen plugins in `claude-code-slack-channel` as a single fast static-analysis tool — one config, one binary, sub-second feedback.

Three PRs split the migration so each diff was reviewable in isolation:

- **[PR #139](https://github.com/jeremylongshore/claude-code-slack-channel/pull/139)** — adopt Biome with a curated set of lint rules. Tuned to the codebase, not the defaults.
- **[PR #142](https://github.com/jeremylongshore/claude-code-slack-channel/pull/142)** — tighten Biome to catch 17 additional rule classes; autofix 295 violations across the codebase in one commit. One-time pain, one-time cleanup. The commit is exactly the autofix, no hand-edits mixed in.
- **[PR #143](https://github.com/jeremylongshore/claude-code-slack-channel/pull/143)** — enable the Biome formatter + one-time reformat pass. Separate from the rule-tightening so the diff stays reviewable.

[PR ccsc-rrj](https://github.com/jeremylongshore/claude-code-slack-channel/commit/ad6dc63) wired Biome into a Husky + lint-staged pre-commit gate that runs on staged files only. Fast local feedback is what keeps the enforcement from being opt-out. The expensive gates (CRAP, mutation, architecture — the ones the harness subcommands run) stay in CI where they belong.

## The NLPM audit — exactly the case audit-harness exists for

External security researcher xiaolai filed an audit against the `claude-code-plugins` NLPM (Natural Language Package Manager) validator, and [PR #540](https://github.com/jeremylongshore/claude-code-plugins/pull/540) hardened it in response. The most telling fix: **[#538](https://github.com/jeremylongshore/claude-code-plugins/pull/538)** — replace a silent global `pnpm install` with an explicit prerequisite error. Silent side-effects in install paths are exactly the shape of finding that `audit-harness escape-scan` is designed to catch. The supporting PRs tightened YAML frontmatter handling ([#535](https://github.com/jeremylongshore/claude-code-plugins/pull/535), [#536](https://github.com/jeremylongshore/claude-code-plugins/pull/536), [#537](https://github.com/jeremylongshore/claude-code-plugins/pull/537)), quoted `phase_*.md` descriptions that had been breaking the loader ([#579](https://github.com/jeremylongshore/claude-code-plugins/pull/579)), and guarded webhook `curl` calls with env-var presence checks ([#539](https://github.com/jeremylongshore/claude-code-plugins/pull/539)).

External review finding real bugs is the strongest validation that the validator itself had real gaps — and the strongest argument for a repo-local harness over a workstation-local one. The audit was reproducible because xiaolai's environment found the same failures any clone would. A gate that lives in `~/.claude/` never produces that kind of evidence.

## What this costs

A 17-rule Biome expansion autofixing 295 violations is not a small change. Neither is vendoring a harness as a dev dependency across every repo in the ecosystem. Both pay off the same way: they convert policy that lived in my head into policy that lives in CI. The point of making enforcement travel with the code is that it doesn't depend on anyone's workstation — including mine.

## Related posts

- [Four Releases in One Day — CCSC Security Sprint](/posts/ccsc-five-releases-one-day-security-sprint/) — the security work the harness was built to enforce
- [Manifest System + Mutation Testing Pyramid](/posts/manifest-system-mutation-testing-pyramid/) — yesterday's mutation baseline, which audit-harness eventually owns
- [Collaboratively Shaped Roadmap](/posts/collaboratively-shaped-roadmap/) — the planning conversation that put audit-harness on the critical path

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Enforcement Travels With the Code: Shipping @intentsolutions/audit-harness v0.1.0",
  "description": "Testing policy enforcement that lives in ~/.claude/ cannot travel with a fresh clone. audit-harness v0.1.0 moves the gates into each repo as a versioned dev dependency — npm, PyPI, crates, and bash install.sh.",
  "datePublished": "2026-04-21T08:00:00-05:00",
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
  "keywords": "testing, ci-cd, architecture, release-engineering, devops, automation, monorepo, typescript",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://startaitools.com/posts/audit-harness-v010-enforcement-travels-with-code/"
  }
}
</script>

---

Jeremy made me do it
-claude

