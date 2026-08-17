# 733-AA-AACR — Slice 2 Publisher Exclusion After-Action Review

**Date:** 2026-08-15  
**Blueprint:** document 727 §15.1, E7.2  
**Bead:** `claude-s03q.3` — Refuse to publish any plugin directory that carries an upstream source record  
**Status:** Complete after independent review and merge; no registry mutation performed

## Scope and baseline

This slice contains exactly E7.2. It does not activate E7.3, another Epic 7
bead, or another epic. The baseline was measured from current `origin/main`
`d63cb627d3ca63d2dc0ddb75477bb062b79ebc09` before editing.

Publisher entry points discovered by searching for `npm publish`, `npm pack`,
and package enumeration are:

- `.github/workflows/publish-changed-packages.yml` — changed plugin paths,
  then publish.
- `.github/workflows/publish-all-packages.yml` — manual all-package dry run,
  then publish.
- `.github/workflows/cli-publish.yml` — `packages/cli`, not a plugin directory
  and therefore outside this `.source.json` boundary.

The two plugin publishers previously filtered only `private`; a nested package
under a mirrored ancestor could therefore enter the candidate set. Baseline
commands and results:

```bash
rg -n 'npm publish|npm pack' .github/workflows scripts
node scripts/check-mirror-packages-private.mjs
node scripts/publish-candidate-report.mjs --all --scope '@intentsolutionsio/' --json \
  | jq '{first_party:(.firstPartyCandidates|length), mirror_skipped:(.mirrorSkipped|length), refused:(.refused|length)}'
```

Before the E7.2 resolver, the old private-only emulation admitted 408 scoped
candidate directories, including nested descendants beneath provenance
markers. The new dry-run report identifies 395 first-party candidates, skips
71 scoped candidates by inherited provenance, and refuses 0 malformed records.
The 71 includes 58 scoped marker roots plus 13 nested package descendants;
the machine-readable inventory remains 63 marker roots, 58 of them scoped.

The old-candidate count was reproduced without npm access using a read-only
Node walk over plugin package manifests, requiring the existing plugin marker,
the `@intentsolutionsio/` scope, and `private !== true`; it returned `408`.

## Implemented boundary

`scripts/plugin-provenance.mjs` is the sole resolver. It walks real filesystem
ancestors, rejects traversal, distinguishes sibling records, and fails closed
for malformed, contradictory, or unreadable records. Both plugin publishing
workflows consume `scripts/publish-candidate-report.mjs`; provenance exclusion
happens before build, version changes, token use, or registry contact.

Reason codes are `FIRST_PARTY_CANDIDATE`, `UPSTREAM_SOURCE_RECORD`,
`MALFORMED_SOURCE_RECORD`, `CONTRADICTORY_SOURCE_RECORD`, `PATH_TRAVERSAL`,
and `PRIVATE_PACKAGE`. No `.source.json`, mirrored skill, package content, or
existing published package was edited.

## Tests and red proof

```bash
node --test scripts/plugin-provenance.test.mjs
node scripts/publish-candidate-report.mjs --all --scope '@intentsolutionsio/' --json
pnpm run verify
```

The fixture suite covers first-party acceptance, private and non-private
mirrors, nested ancestry, sibling non-matches, malformed/unreadable/
contradictory records, traversal, dry-run reason codes, all 63 marker roots,
all 58 scoped roots, and zero mirror candidates in the first-party set. Its
red proof shows the legacy private-only selector admitting a non-private mirror
while the resolver excludes it. No test contacts npm or any other registry.

## Review, rollback, and prohibited scope

The focused PR was reviewed from a clean checkout at exact head
`dfa23e07e9bb8a895861403bca7da0b805e507d6` by a non-implementing review
process and returned **PASS**. It discovered both publishers, planted a mirror
fixture, reran the suite and dry run, and verified zero network mutation, zero
mirrored-content changes, no name-based list, no fourth status context, and an
accurate rollback. PR #1190 merged as
`85dbf9f6e8310a83c25ffa787588c45c3d6728d4` with an administrator bypass
because the independent GitHub approval topology remains unsatisfied; this is
not independent certification. Post-merge commands reported 63/63 private,
395 first-party candidates, 71 provenance-skipped paths, 0 refusals, and all
six resolver tests passed. Rollback is a revert of the resolver, workflow
filters, tests, and this record; it does not touch npm.

Prohibited: npm or registry mutation, credentials or Environment changes,
contributor/upstream contact, branch-protection changes, mirror-content edits,
E7.3 or other-bead activation, and production changes.

The unrelated npm `public-hoist-pattern` warning remains deferred maintenance;
it is not part of this ratification or containment slice.
