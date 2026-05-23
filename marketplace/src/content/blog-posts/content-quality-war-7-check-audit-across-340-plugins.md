---
title: "Content Quality War: 7-Check Audit Across 340 Plugins"
description: "A 7-category audit script found boilerplate openings, empty shells, reference stubs, and duplicate content across 340 plugins. Every category got its own fix batch."
date: "2026-03-17"
tags: ["claude-code", "automation", "ci-cd", "architecture", "web-development"]
featured: false
---
Every plugin had content. Most of it was junk.

Not missing. Not absent. Present but worthless. Boilerplate openings copy-pasted across 58 skills. Reference files that said `TODO: add examples`. Methodology guides that were empty markdown headers with no prose underneath. The files existed. The content didn't.

Last week's [quality blitz](/posts/marketplace-quality-blitz-130-stubs-4300-warnings/) replaced 130 stub files and crushed 4300 validator warnings. That fixed the obvious gaps. This week I went after the subtle ones — the files that passed every existing check because they weren't empty, they were just bad.

## The Audit Script

The previous round of fixes taught me something: human spot-checks don't scale. You can eyeball 20 files. You can't eyeball 340 plugins with 5-10 files each. So I built an automated content quality audit with 7 checks. Each one targets a different category of low-value content that had been accumulating across the marketplace:

1. **Boilerplate openings** — Skills starting with the same generic sentence. "This skill helps you..." appeared verbatim in 58 files across 4 plugin packs.
2. **Empty shells** — Files with headers and structure but no substantive body text. They looked like documentation in a directory listing. Open them and there's nothing there.
3. **Reference stubs** — Files in `references/` directories containing placeholder text instead of actual code examples.
4. **Duplicate content** — Multiple skills sharing identical paragraphs. Copy-paste reuse that made every skill in a pack read the same.
5. **Below-threshold prose** — Skills with body text under a minimum word count. A skill description that's two sentences long isn't a skill description.
6. **Generic examples** — Code samples using `foo`, `bar`, `example.com` instead of domain-relevant examples.
7. **Missing methodology guides** — Implementation files with section headers but no actual methodology content.

The script runs against the full marketplace and produces a categorized report. No ambiguity. Each finding includes the file path, the category, and what's wrong. The output looks like a punch list: category, file, specific violation. You can hand each category to a separate fix batch and work through them systematically.

## The Fix Batches

Each category got its own targeted fix across the entire codebase. Not a bulk find-and-replace. Each file needed content that matched its specific plugin domain.

**Boilerplate openings** were the biggest offender. Three separate PRs hit different plugin packs:

- 21 AI/ML skills — replaced generic intros with domain-specific openers
- 24 performance skills — same treatment
- 13 security and package management skills — same treatment

That's 58 skills that all started with variations of the same sentence. After the fix, each one opens with something specific to what it actually does. A Kubernetes debugging skill now opens by talking about pod failure patterns. A model fine-tuning skill opens with transfer learning tradeoffs. Context-specific, not template-driven.

**The openrouter-pack** was the worst single offender. All 30 skills in the pack had boilerplate content. Every single one. A dedicated PR replaced all 30 with unique, domain-relevant content. When your entire plugin pack reads like it was generated from the same template, users notice.

**Empty shells** got real content. The `skill-enhancers` pack had 4 skills that were pure scaffolding — headers, metadata, no body. The `gh-dash` skill was the same. Five files went from zero to functional documentation.

**Reference stubs** were the most tedious category. Reference files are supposed to contain real code examples — actual commands, API calls, configuration snippets that a user can copy and adapt. Instead, dozens of them said `[Add examples here]`.

The fix landed across multiple batches:

- 12 API development reference files filled with real REST/GraphQL examples
- 7 AI/ML reference files filled with actual model training and inference code
- 22 DevOps and SaaS pack reference files
- 12 community, crypto, and productivity plugin references
- 13 more API development references to close out the category

That's 66 reference files. Every one now has working code examples instead of placeholder text.

**Methodology guides** in the Wondelai plugin had the right structure — sections for approach, implementation steps, best practices — but no content under any of the headers. Those got filled with actual methodology documentation.

**Below-threshold prose** in the SaaS packs needed expansion. Skills that described complex integrations in two sentences got expanded to substantive descriptions. The body-substance threshold check flags anything under a minimum word count relative to the skill's complexity. A simple utility skill might pass with 200 words. A multi-step workflow integration needs more. The threshold is proportional, not absolute.

**Duplicate content** and **generic examples** were caught by the remaining two checks. Skills sharing identical paragraphs got rewritten. Code samples using `example.com` and `foo/bar` got replaced with realistic, domain-appropriate examples. Small changes individually. Meaningful in aggregate.

## The Validator Alignment

While fixing content, I also aligned the validation system with the Anthropic plugin spec. The old validator had a single tier. The new system uses two tiers:

- **Standard** — baseline checks that every plugin must pass
- **Enterprise** — stricter requirements for plugins used in production environments

This matters because not every plugin needs the same level of scrutiny. A personal productivity tool and an enterprise security scanner have different quality bars. The two-tier system lets the validator enforce both without making either tier meaningless.

The alignment also cleaned up edge cases where the old validator was flagging things the Anthropic spec explicitly allows, and missing things the spec explicitly requires. Spec compliance isn't optional when you're building on someone else's platform.

## New Plugins and Community PRs

Content quality wasn't the only thing that shipped.

**box-cloud-filesystem** (#368) is a new plugin for transparent cloud storage via the Box API. Six commits from concept to marketplace listing. It handles file operations, folder management, and search against Box's cloud storage without the user needing to think about the API. The interesting architectural choice: it exposes Box as a filesystem abstraction, so skills that already work with local files can transparently operate on cloud storage. No Box-specific code in the consuming skill.

**PM AI Partner** (#327) adds 12 project management-specific agent skills and 6 workflow commands. Sprint planning, backlog grooming, stakeholder updates, retrospective facilitation — the kind of structured PM workflows that benefit from agent automation. Each skill maps to a specific PM ceremony or artifact, not a generic "help me manage my project" prompt.

**Browser compatibility** got an upgrade with Kobiton added as a first-class cloud provider, replacing all the stub references that were there before. Real device testing on real infrastructure, not placeholder vendor names in a config file.

And then the community PRs. Two external contributors shipped plugins this week:

- **Prism Scanner** — a new plugin from an outside contributor
- **claude-memory-kit** — another community-submitted plugin

External contributions to a plugin marketplace are a milestone. It means the submission process works, the documentation is clear enough to follow, and the marketplace has enough gravity to attract builders who don't work here. You can't manufacture that. Either external developers find your ecosystem worth building for, or they don't.

**geepers and lumera-agent-memory** also landed in the catalog (#367), along with bug fixes in the PR review pipeline. The marketplace keeps growing while the quality floor keeps rising.

## oss-agent-lab v1.0.0

Separately, oss-agent-lab hit its 1.0.0 release after a test audit remediation cycle. Every test passing, every audit finding resolved, version bumped to stable. The 1.0 tag means something specific: the project has been through a complete test audit, all findings have been remediated, and the test suite runs clean. No aspirational versioning.

## The Numbers

Adding it up across the day:

- 88 skills with boilerplate openings replaced (58 across packs + 30 in openrouter-pack)
- 5 empty shells filled with real content
- 66 reference stubs replaced with working code examples
- 30 openrouter-pack skills rewritten
- Methodology guides, prose expansions, and duplicate fixes across the remaining categories
- 2 new plugins built from scratch
- 2 community-contributed plugins merged
- 1 validator architecture redesigned

Dozens of PRs. One day.

## Why This Work Matters

None of this is glamorous. Replacing boilerplate openings in 88 files is not a conference talk. Filling in 66 reference stubs is not a blog post people share. Building an audit script with 7 checks is not a product launch.

But it's the difference between a toy and a product. A marketplace where content is boilerplate, stubs, or empty shells is a directory that happens to have an install button. A marketplace where every file has substantive, domain-specific content is a platform that users can trust.

The audit script is the real deliverable. The 7 checks will run against every future PR. The categories of junk I found this week will never accumulate again because there's now a gate that catches them. Fix the problem once, prevent it forever.

v4.19.0 shipped with all of it.

---

## Related Posts

- [Marketplace Quality Blitz: 130 Stub Files, 4300 Warnings, Zero Excuses](/posts/marketplace-quality-blitz-130-stubs-4300-warnings/) — The previous wave of quality fixes that set up this audit
- [Scaling AI Batch Processing with Vertex AI Gemini](/posts/scaling-ai-batch-processing-enhancing-235-plugins-with-vertex-ai-gemini-on-the-free-tier/) — The batch infrastructure behind large-scale content generation
- [Verified Plugins Program: Building a Quality Signal for the Marketplace](/posts/verified-plugins-program-quality-signal-for-the-marketplace/) — The rubric that defines what "quality" means for plugins
