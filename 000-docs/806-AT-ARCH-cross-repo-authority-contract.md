<!-- doc-class: canonical -->

# 806-AT-ARCH — Cross-Repository Authority Contract

**Status:** AUTHORITATIVE

**Authority:** Blueprint 727 § 4 and Epic 9 bead 9.1. This record is the executable
cross-repository expansion of the one-owner rule; it does not transfer authority
from any system named below.

**Scope:** Tons of Skills Marketplace, `@intentsolutions/core`,
`@intentsolutions/jrig-cli`, Intent Eval Lab, Intent OS, Freshie/Dolt, and Beads.

## Contract

Every fact class below has exactly one writer. A consumer may cache, render, or
cite an owner’s output, but cannot correct, synthesize, or publish a competing
version of that fact. When two surfaces disagree, the owner named in the row
wins; the non-owner must be corrected or reduced to a pointer.

| Fact class                                                                                              | Sole writer / owner                   | Authoritative surface                                                            | Consumers and prohibited competing writes                                                                                                                                                                    |
| ------------------------------------------------------------------------------------------------------- | ------------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Marketplace catalog, plugin source, repository CI/release policy, and canonical skill-contract adoption | Tons of Skills Marketplace repository | this repository’s canonical sources and Blueprint 727                            | The Lab, Intent OS, and Freshie/Dolt may consume repository facts; none may modify the catalog, source, required checks, or release policy.                                                                  |
| Machine authoring-schema semantics and schema evolution                                                 | `@intentsolutions/core` (kernel)      | kernel `authoring` schema and changelog                                          | This repository pins and shadows the kernel while its local validator remains authoritative for local validation; a pin update is not an authority flip. Intent OS and the Lab cite, never fork, the schema. |
| Behavioral-evaluation command implementation and emitted result shape                                   | `@intentsolutions/jrig-cli`           | published `j-rig` CLI contract                                                   | The Lab invokes it; this repository may parse its output only through the governed wrapper/recorder. The CLI never writes Freshie/Dolt inventory tables.                                                     |
| Evaluation execution, provider credentials, model-run artifacts, and verdict production                 | Intent Eval Lab                       | Lab-owned execution environment and retained primary artifacts                   | This repository consumes a retained, hash-matched verdict but does not mint one. Freshie/Dolt records governed evidence metadata only; Intent OS does not operate or rewrite Lab evaluations.                |
| Host, deployment, operational runbook, and organization decision facts                                  | Intent OS                             | Intent OS operations and decision records                                        | This repository may cite host facts but does not duplicate or edit them. Intent OS projects repository facts and never owns the catalog, validator, required set, or repository CI.                          |
| Inventory state, grade history, governed evidence ledger, and tracked export projections                | Freshie/Dolt                          | Freshie local runtime backed by Dolt; repository exports are one-way projections | The local Freshie writer records inventory and evidence metadata. JRig writes only its scratch/run data; this repository and the Lab do not write inventory tables directly.                                 |
| Durable task state, dependencies, claims, and completion evidence                                       | Beads/Dolt                            | Beads embedded Dolt database                                                     | GitHub Issues, Plane, Markdown task lists, and session notes are projections or context only; none gate or override Beads task state.                                                                        |

## Boundary invariants

1. The pin axis and authority axis are independent. Kernel or CLI upgrades are
   compatibility work, not permission to replace an owner.
2. `j-rig` is never pointed at `freshie/inventory.sqlite`. It evaluates through
   a scratch database; the repository-owned recorder is the only supported
   Freshie write path.
3. A public verification claim requires a retained, hash-matched primary
   artifact and the evidence class that authorizes its publication. No current
   marketplace badge is an exception.
4. Beads task state is durable project authority. GitHub and Plane projections
   must not become required merge or completion gates.
5. This document resolves boundary disputes only. It does not define a second
   schema, evaluation method, inventory store, or operational source of truth.

## Verification

The contract is checked by reading each row as a single-owner assignment against
Blueprint 727 § 4 and § 11. The repository’s executable supporting boundaries
are `scripts/check-jrig-db-boundary.mjs`, the Freshie recorder and wrapper, and
the Beads dependency graph. Their checks prove local enforcement; they do not
authorize a non-owner to mutate an external system.

## Change control

Changing an owner requires one reviewable transaction that updates this record,
the corresponding owner’s authoritative surface, and the `STANDARDS.md`
canonical-documents pointer. A consumer-only repository change must not rewrite
this contract to claim a new owner.
