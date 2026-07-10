# Drift Categories

Seven categories of documentation drift, ordered by typical severity impact.

## 1. Status Drift

**Definition:** Documentation claims a wrong project phase, version, release state, or epic status.

**Examples:**
- README says "v0.2.0" but VERSION file says "0.3.1"
- CLAUDE.md says "Phase: Scaffolding" but repo has working application code
- Docs say "pre-release" but git tags show published releases
- Beads show epic as "in_progress" but all child tasks are closed

**Severity:** Critical when version numbers mismatch; Warning for phase descriptions.

**Detection:** Compare version strings across README, CLAUDE.md, VERSION, gemspec/package.json, CHANGELOG headers. Check phase/status language against actual repo contents.

## 2. API/Interface Drift

**Definition:** Documentation references methods, function signatures, CLI arguments, config keys, or API endpoints that have changed or no longer exist.

**Examples:**
- README shows `client.query(sql)` but code signature is `client.execute(sql, params)`
- Docs reference `--verbose` flag but CLI parser only accepts `-v`
- Config example uses `database_url` but code reads `DATABASE_URI`
- API docs show `/api/v1/users` but routes define `/api/v2/users`

**Severity:** Critical — users will hit errors following stale docs.

**Detection:** Extract method/function names from doc code blocks, compare against actual source definitions. Check CLI help output against documented flags.

## 3. Capability/Behavior Drift

**Definition:** Documentation claims features that don't exist in code, or fails to document features that do exist.

**Examples:**
- README lists "CSV export" in features but no export code exists
- Code implements webhook support but README doesn't mention it
- Docs say "supports PostgreSQL and MySQL" but only PostgreSQL adapter exists
- CLAUDE.md lists 10 repos but directory only contains 7

**Severity:** Critical for overclaims (features that don't exist); Warning for underdocumented features.

**Detection:** Extract feature claims from README/docs, search codebase for corresponding implementations. List implemented modules and check for doc coverage.

## 4. CI/Validation Drift

**Definition:** README or docs describe test/build/lint commands that differ from what CI actually runs.

**Examples:**
- README says `npm test` but GitHub Actions runs `npm run test:ci`
- Docs say "run `pytest`" but CI uses `pytest --cov --strict-markers`
- README claims "100% test coverage" but CI has no coverage gate
- Makefile target differs from workflow step

**Severity:** Warning — misleading but not immediately breaking.

**Detection:** Compare commands in README "Getting Started" / "Development" / "Testing" sections against `.github/workflows/*.yml` step commands.

## 5. Planning-vs-Implementation Confusion

**Definition:** Roadmap or planning items are presented as if they're already implemented, or implemented items are still listed as planned.

**Examples:**
- Planning doc lists "Authentication system" as epic 5 (future) but auth code exists and works
- README features section includes items from planning docs that haven't been built
- Roadmap shows "Q1 2026: Add caching" but caching was shipped in December
- CLAUDE.md says "no application code should be assumed yet" but `lib/` has modules

**Severity:** Warning for stale planning; Critical if README overclaims based on plans.

**Detection:** Cross-reference planning doc items against actual file tree and code. Check for planning language ("planned", "upcoming", "future") applied to shipped features.

## 6. Cross-Doc Contradiction

**Definition:** Two or more documentation files disagree about the same fact.

**Examples:**
- README says "MIT License" but LICENSE file is Apache-2.0
- CLAUDE.md lists 8 epics but planning doc shows 10
- README says "Ruby 3.2+" but Gemfile specifies `ruby '~> 3.1'`
- docs/setup.md says "run migrations first" but README says "migrations run automatically"

**Severity:** Warning — confusing but usually one doc is obviously more current.

**Detection:** Extract key claims (license, language version, dependency versions, setup steps) from each doc and compare for conflicts.

## 7. Index/Reference Drift

**Definition:** Index files, cross-references, or file listings are out of sync with actual files on disk.

**Examples:**
- `000-docs/000-INDEX.md` lists `003-api-spec.md` but file doesn't exist
- `000-INDEX.md` is missing entries for recently added docs
- CLAUDE.md doc table references `planning/roadmap.md` but file was moved to `000-docs/`
- README links to `docs/architecture.md` which was deleted

**Severity:** Warning for missing index entries; Info for extra entries referencing deleted files.

**Detection:** Parse index files for listed paths, check each against filesystem. Scan doc directories for files not listed in any index.

## Severity Guide

| Level | Meaning | Action Required |
|-------|---------|----------------|
| **Critical** | Users will encounter errors or be materially misled | Must fix before release |
| **Warning** | Content is stale or confusing but won't cause errors | Should fix, can defer |
| **Info** | Minor inconsistency, cosmetic, or style issue | Fix if convenient |
