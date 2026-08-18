---
title: "Seventeen Spellings of the Same Number"
description: "A checker that governs published skill counts must discover them without hardcoding variable names. Every commit found a new legal spelling to handle."
date: "2026-08-17"
tags: ["ci-cd", "testing", "automation", "claude-code", "architecture"]
featured: false
canonical: "https://startaitools.com/posts/seventeen-spellings-of-the-same-number/"
---
The Tons of Skills marketplace renders skill-count numbers on its public pages. Those counts were bare. A number like "3,068 skills" does not say which population it counted. Different pages could legitimately count different things and a reader could not tell.

The rule went in: every published count must declare its cohort and expose a reproducible resolver command beside it. I built a registry at `scripts/published-count-cohorts.json` and a CI gate that discovers counts in Astro source and binds each one to a registered cohort.

Then the night began. One feature commit at 20:31, then seventeen fixes landing through 03:43.

Here is the full chain, with the checker's line count and its test file's line count after each commit. The checker grew about two and a half times, from 473 lines to 1,241, while the tests went from 331 to 827. The two biggest single jumps were at 21:52 (binding every expression, plus 157 lines of checker) and 23:17 (closing independent count bypasses, plus 220 lines of checker). Net for the entire chain, from the commit before the feature through the last fix: 30 files, plus 2,986 lines, minus 157. Commit subjects below are abbreviated; the real ones carry a `marketplace-site` scope.

```
20:31 1296df609 feat: label published count cohorts              checker= 473L  tests=331L
20:55 33803b51a fix: broaden published count discovery           checker= 536L  tests=418L
21:29 412a615fa fix: reject trailing comment provenance          checker= 536L  tests=450L
21:31 9ed3c33fc fix: cover compact line comments                 checker= 536L  tests=462L
21:52 c9c4015d5 fix: bind every published count expression       checker= 693L  tests=558L
21:59 2443cf54f fix: require rendered count provenance           checker= 716L  tests=613L
22:07 8e976f0d2 fix: enforce rendered count labels               checker= 723L  tests=639L
22:17 b513d7b4c fix: require exact count expressions             checker= 721L  tests=672L
22:24 d538e6b2e fix: reject compound count wrappers              checker= 721L  tests=672L
22:35 0eba12625 fix: parse rendered provenance tags              checker= 784L  tests=690L
22:47 a62f6f946 fix: mask quoted markup attributes               checker= 795L  tests=706L
23:17 6166a7f19 fix: close independent count bypasses            checker=1015L  tests=747L
23:37 ad0dee2bd fix: detect cross-line count expressions         checker=1048L  tests=752L
23:56 79701c643 fix: align count discovery with rendered structure checker=1107L tests=777L
00:11 7ae7f9028 fix: bind counts to heading containers           checker=1132L  tests=779L
00:19 1680d7df6 fix: preserve external heading counts            checker=1169L  tests=781L
00:55 e2f759cc6 fix: harden count discovery exclusions           checker=1193L  tests=783L
03:43 145c8725a fix: govern query-local skill counts             checker=1241L  tests=827L
```

Each commit closed a spelling the previous checker had missed.

## Why Not the Obvious Approaches

A grep for a known variable name fails the moment someone renames it. The failure is silent.

Rendering the site and checking HTML would sidestep most parsing entirely. But it checks output, not the source a reviewer reads in a diff. A reviewer still cannot see the violation at review time.

Manual review is what this replaced. It let unlabeled counts accumulate across five pages.

I chose source parsing with fixtures. The cost is 1,241 lines of checker and 827 lines of tests.

## How the Gate Works

The gate has three parts. A registry lists every cohort alongside a command that re-derives its number. A CI check discovers count expressions in Astro source and refuses any that is not bound to a registered cohort. A component renders the label and that command beside the number. It fails closed.

The registry lives at `scripts/published-count-cohorts.json`. The component is `CountProvenance.astro`, 48 lines. The check runs as a step inside the existing `validate` job in `.github/workflows/validate-plugins.yml`, deliberately, so that it adds no fourth required status context.

Here is the cohort half of the registry, with `marketplace-visible` spelled out. The real file also carries `discovery`, `surfaces`, and `deferredGroups` sections:

```json
{
  "schemaVersion": 1,
  "cohorts": {
    "marketplace-visible": {
      "label": "marketplace-visible",
      "description": "Tracked plugin skills reachable from canonical marketplace catalog source roots; hidden adapter trees, the root curriculum, and the curated mirror are excluded.",
      "command": "node scripts/corpus-resolver.mjs --cohort marketplace-visible --json",
      "resolver": "scripts/corpus-resolver.mjs"
    }
  }
}
```

The other four cohorts are `graded`, `first-party`, `curated-mirror`, and `curriculum`. A reader looking at any public page can now see which population a count covers and run the command themselves to verify the number.

Calibrate the rest of this against one number before reading on: the enforced surface is five pages (homepage, explore, compare-marketplaces, sponsor, and the skills directory) out of 51 inventoried Astro files. Everything below is what it cost to govern those five honestly. The section near the end on what is enforced and what is deferred says what the other forty-six are and why.

## The Spellings the Checker Missed

Each fix was parser hardening: teaching the discovery pass one more legal form it had not seen.

Fake provenance in comments. A trailing comment or compact line comment mentioning a cohort satisfied the naive "is a label nearby" check. Comments now get masked while preserving line geometry:

```js
function stripComments(source) {
  return source
    .replace(/<!--[\s\S]*?-->/g, (comment) => comment.replace(/[^\n]/g, ' '))
    .replace(/\/\*[\s\S]*?\*\//g, (comment) => comment.replace(/[^\n]/g, ' '))
    .replace(/(?<!:)\/\/.*$/gm, maskText);
}

function maskText(value) {
  return value.replace(/[^\r\n]/g, ' ');
}
```

Every branch replaces characters with spaces rather than deleting them. That is what keeps line and column numbers valid for the passes that run afterward, which matters because the error messages point at a file and a position a human has to open.

The `(?<!:)` is critical. Without it, `https://` gets masked as a comment.

Provenance not actually rendered. A cohort string in Astro frontmatter, in `<script>` or `<style>` body, or inside markup attributes is invisible to a reader. All those regions get masked for the rendered contract.

Expression rewrapping. A registered count gets no inheritance from compound outer expressions. Wrapping it in arithmetic or adding a second count next to it cannot ride the first one's registration through the gate.

Multiline identifiers. Collection `.length`. Catalog counts. Nested object syntax. Cross-line expressions. Each was a new parser case the previous build had not seen.

Parser bugs producing false evidence. A quoted `/>` inside an attribute could terminate a raw-text element early and expose `<script>` content as if it were visible page text. That needed quote-aware and brace-aware raw-text scanning, and malformed raw-text elements now refuse rather than guess.

False positives that had to be taught apart from real counts. The discovery pass had to learn `/skills/` in a URL path is not a count. Prose durations and adjacent time units. Star counts. Notebook and agent populations. Narrative heading shapes. All of it without relying on identifier names that look count-like.

Real constants from the shipped checker:

```js
const REGISTRY_PATH = 'scripts/published-count-cohorts.json';
const DISCOVERY_ROOTS = Object.freeze(['marketplace/src/pages', 'marketplace/src/components']);
const DISCOVERY_DYNAMIC_EXPRESSION_POLICY = 'any-braced-expression';
const DISCOVERY_IGNORED_PHRASES = Object.freeze(['Tons of Skills']);
const LABEL_LINE_WINDOW = 4;
const CANONICAL_COHORTS = Object.freeze([
  'marketplace-visible', 'graded', 'first-party', 'curated-mirror', 'curriculum'
]);

class CohortCheckError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'CohortCheckError';
    this.code = code;
  }
}

function refuse(code, message) {
  throw new CohortCheckError(code, message);
}
```

`DISCOVERY_IGNORED_PHRASES` exists because the brand name contains the noun the discovery pass keys on. "Tons of Skills" is not a count of skills. Every refusal carries a code, so a failing build says `INVALID_REGISTRY` or `MALFORMED_ASTRO_FRONTMATTER` rather than just failing.

## The Same Rule in intent-os

The same rule arrived in a different place on the same day, about nineteen hours before the marketplace chain started. An operator receipt must not cite a qualification that is not bound to the evidence that produced it. The commits are literally that sentence:

```
00:07 ff49f6e4 fix(agent-ops): bind canonical B6 attempts and invalidate fired queue
00:11 5eb83fe3 fix(agent-ops): enforce canonical B6 receipt semantics
01:21 3c0ca90b feat(agent-ops): bind J-Rig qualification and package operator
01:24 abd8ccea fix(agent-ops): deny unbound qualifications in receipts
01:28 630349f1 fix(agent-ops): verify J-Rig sources in receipt path
01:31 c6660e59 test(agent-ops): reject uncertified J-Rig sources
01:34 16594bc4 fix(agent-ops): bind qualification row to evaluation
01:47 1b6bf562 feat(agent-ops): expose read-only escalation queue (B6.5) (#523)
```

Different system, different day-part, same thesis. A claim that cannot name its source fails closed.

## Five Pages Enforced, Forty-Six Deferred

The first inventory found 51 public Astro source files. Five are the enforced core, and they are the five pages that were showing bare global totals in the first place. Forty-six files plus the generated social image are path-level deferrals, because their counts are local or point-in-time rather than global claims about the marketplace. Three local or query-scoped expressions sitting on otherwise enforced pages are expression-level deferrals, owned separately.

That is the honest shape of it. A gate covering five files cost 1,241 lines of checker and 827 lines of tests, and it does not yet govern the other forty-six. What it does govern, it governs fail-closed. It also did not add another required CI status context, which was deliberate. It runs inside the existing `validate` job rather than growing the check list.

## The Collaboration

The night ran in Codex with GPT-5.6 Sol. Across the whole day's Codex work, not just the count chain, the transcript analyzer counted four sessions, 3,630 turns, a 1,074 minute span, and sixty-eight operator course-corrections. Two steers repeated all night: stop asking for approval, I own this platform, and check the free Greptile reviews as part of the merge process and keep going. The model kept stopping to ask for a human sign-off. The answer each time was that the merge gate is the review bot and the CI, not a person.

The blog pipeline work ran with Claude Opus 5, Claude Sonnet 5, and Claude Fable 5. An append to `decisions.jsonl` landed concatenated onto the previous line because that line had no trailing newline. The first repair re-serialized all 306 existing records, which violated the file's append-only contract. It got restored from backup and redone as a surgical byte-level fix because `blog-land.sh` enforces additions-only diffs on that file and would have quarantined the post otherwise. (Also lost to the same session: a heredoc that failed because `cat` is aliased to `bat` on this box.)

The day's third instance of the rule came from the brain pipeline. A `/teamkb-compile` run distilled 17 memory candidates (16 new, 1 already covered) and then found `brain_govern` blocked on `~/.teamkb/.write.lock`. The holder was the nightly cron, PID 4166431, running the identical command on the identical window. The agent identified the duplicate run, declined to race it, and waited, since `brain_govern` drains the whole spool and the cron's pass would dispose of its candidates too. The system refused to act on something it could not bind to a single owner.

## Also Shipped

Epic 1.8 closed four deterministic projection drift gates in claude-code-plugins: skill index, skill catalog, plugin catalog, unified search. Each implementation PR was followed by an after-action review filed into `000-docs/` with base and head SHAs and gate evidence. PR #1237 replaced a self-referential, timestamp-varying plugin catalog renderer with one strict source-derived renderer. Projected plugins went from 450 to 467. Distinct projected skills went from 3,022 to 3,068. Commands went from 81 to 80. PR #1235 enforced unique plugin names and collapsed four excess canonical rows (three redundant `claudebase`, one duplicate `geepers-agents`). Duplicate, empty, non-string, or non-object catalog names now fail closed.

Unrelated to any of the above, and worth recording only for the cost: a numbered list in a blog post was missing its preceding blank line. Markdownlint flagged [MD032](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md#md032) in run 32045714543 and blocked every subsequent PR that day until the blank line was added. A whitespace fix sat in the critical path of everything else shipping.

In diagnostic-pro, `robots.txt` had lived at `02-src/frontend/public/public/robots.txt`. A doubled `public/` segment. The file was in the repo and never served. The fix moved it to `public/robots.txt`, added `public/sitemap.xml`, and wired route metadata into a `RouteSeo.tsx` component covering 15 equipment categories with canonical, title, and description per route. Something present is not the same as something reachable.

## Related Posts

[The Check That Only Confirmed a Name](https://startaitools.com/posts/the-check-that-only-confirmed-a-name/)

[Three Commits Between the Rule and the Violation](https://startaitools.com/posts/three-commits-between-the-rule-and-the-violation/)

[Every Fix Failed in the Shape of the Bug](https://startaitools.com/posts/every-fix-failed-in-the-shape-of-the-bug/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Seventeen Spellings of the Same Number",
  "description": "A checker that governs published skill counts must discover them without hardcoding variable names. Every commit found a new legal spelling to handle.",
  "author": { "@type": "Person", "name": "Jeremy Longshore" },
  "publisher": { "@type": "Organization", "name": "Start AI Tools", "url": "https://startaitools.com/" },
  "datePublished": "2026-08-17T09:00:00-05:00",
  "mainEntityOfPage": { "@type": "WebPage", "@id": "https://startaitools.com/posts/seventeen-spellings-of-the-same-number/" },
  "url": "https://startaitools.com/posts/seventeen-spellings-of-the-same-number/",
  "articleSection": "Technical Deep-Dive",
  "keywords": "count provenance, fail-closed CI gate, Astro source parsing, cohort labeling, parser hardening, CI/CD, automation"
}
</script>
