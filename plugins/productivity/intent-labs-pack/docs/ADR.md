# ADR: intent-labs-pack — marketplace publish over a dedicated skills repo

**Author:** Jeremy Longshore
**Date:** 2026-07-23
**Status:** Accepted

## Context

Bead `bd_000-projects-184o.7` required a public sourcing decision so three labs skills can join the nightly roster. Options were: (a) publish into `claude-code-plugins-plus-skills`, (b) a dedicated public skills repo, (c) accept marketplace-only roster coverage without labs skills.

## Decision

We use **option (a)**: publish `audit-tests` and `validate-skillmd` as `plugins/productivity/intent-labs-pack`, registered in the existing marketplace catalog. The nightly roster continues to pin a single `claude-code-plugins-plus-skills` SHA.

## Alternatives considered

| Alternative | Why rejected |
| --- | --- |
| Dedicated public skills repo | Second pin, second CI surface, no product distribution benefit |
| Marketplace-only roster (skip labs skills) | Leaves the highest-signal IS skills unevaluated on the signed dogfood path |

## Consequences

- Pack must pass CCPI intake docs + marketplace validation gates.
- Founder `~/.claude` copies remain authoritative for day-to-day edits until a sync path is defined.
- `skill-creator` stays in its existing skill-enhancers home.
