<!-- doc-class: record -->

# Epic 3 Kernel Proposal and Ownership Boundary — After-Action Review

- **Date:** 2026-08-19
- **Authority:** Blueprint 727, Epic 3 bead 3.13
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-t9s9.11`
- **Implementation PR:** [#1276](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1276)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E3.13 controls implemented; merge fields are recorded in Beads/Dolt after review

## Outcome

1. **The kernel proposal is filed**:
   [`intent-eval-core#90`](https://github.com/jeremylongshore/intent-eval-core/issues/90)
   proposes `skill-contract`, `capability`, and `eval-spec` as kernel authoring schemas, citing
   `schemas/canonical/v0/` as the draft with its invariants (closed schema, abstract
   capabilities, `model_class` tiers, registry-enum adapters, fail-closed `unsupported[]`, SPDX
   vocabulary, resolved-SHA mirror pins) and the evidence chain (baseline 778, the five live
   gates, AARs 779–786). The issue names the ask: authoring-family fit review, adoption vehicle
   decision, and the vendored-copy transition on adoption.
2. **The boundary statement is on the record in 727**: this repository is never its own schema
   authority; the v0 directory is `DRAFT · UPSTREAM-PENDING`; on adoption the local draft
   becomes a cited vendored copy with the kernel changelog canonical; until then the draft
   evolves only through reviewed PRs with #90 linked.
3. **The UPSTREAM-PENDING promise is discharged**: the schema `$comment` and the companion
   README both said the issue number would be recorded when filed — both now cite #90 with the
   filing date.

## Verification

- Issue live at intent-eval-core#90 (estate-internal repo; footer-signed per the authoring
  standard).
- Schema still compiles under Ajv 2020 strict with all 11 contract tests passing after the
  `$comment` edit; hosted CI final.

## Scope discipline

No schema semantics changed — only the recorded filing status. No corpus, catalog, or gate
change.

## Follow-up

- The kernel's review on #90 drives the adoption vehicle; the CCPI-side pin-and-vendor step
  lands when the kernel publishes.
