# Changelog — databricks-pack

All notable changes to this pack. Format loosely follows [Keep a Changelog](https://keepachangelog.com/);
versioning is SemVer on the `databricks-pack` marketplace slug.

## [1.1.0] — 2026-06-21 — Deprecation release

**This is a signposting release. No skill behavior changes.** It starts the auto-update clock
on the v2 rebuild so users on auto-update see what's coming before `2.0.0` deletes the v1 skills.

### Added

- Deprecation banner at the top of all **24** v1 `SKILL.md` files. Each banner states the skill
  is removed in `2.0.0` and points to its v2 replacement (or marks it cut, with reason).
- README **Migration: v1 → v2** section — full v1-skill → v2-destination map + the 5 v2 skills
  and the `1.1.0 → 2.0.0 → 2.1.0` timeline.
- README top-of-file deprecation warning.

### Changed

- Nothing functional. Skill bodies are unchanged below the banner.

### Why

Per [`000-docs/007-AT-ADEC-databricks-v2-cto-decision.md`](000-docs/007-AT-ADEC-databricks-v2-cto-decision.md)
§ Decision 1: Claude Code marketplace auto-update **deletes files** on upgrade. Jumping straight
from v1 to a `2.0.0` that removes every v1 skill would break any `CLAUDE.md` referencing them with
no in-product warning. The `1.1.0` deprecation lane (2–4 weeks) + `2.0.0` tombstones close that
404 cliff.

## [Unreleased] — v2.0.0 (in progress)

- 5 live-detection skills (`cost-leak-hunter` pilot, `cluster-forensics`, `streaming-guardian`,
  `uc-migration-pilot`, `bundle-medic`) + shared `databricks-workspace-mcp` server.
- Tombstone stubs in the 24 removed v1 skill directories.
- Rewritten catalog description (operational depth, not surface breadth).

## [1.0.x] — through 2026-06

- The original 24-skill documentation pack (Standard / Pro / Flagship tiers). Superseded by the
  v2 rebuild; see the migration map.
