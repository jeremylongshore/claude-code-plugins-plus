<!-- doc-class: canonical -->

# 808-DR-STND — Certification Standard

**Status:** AUTHORITATIVE

**Authority:** Blueprint 727 § 2 and Epic 10 bead 10.1. This record is the
repository's only definition of a certified marketplace artifact. It preserves
the criteria verbatim; implementation beads may add enforcement, but may not
weaken, reinterpret, or self-declare a certification tier.

## Certification rule

**A-GRADE ⇔ (all of G1–G10) ∧ (all of E1–E6).** Every row terminates in an exit code, a hash comparison, or a filesystem/schema fact. The words _documented_, _reviewed_, _intended_, and _best-practice_ appear in no criterion. The 100-point Freshie score is retained as an **advisory quality hint only** and is explicitly **not** a certification input — 962 A/B artifacts that fail the gate prove why (§ 3.1).

### Gate G — structural prerequisites (any failure ⇒ not A; no partial credit)

| #   | Criterion                                                                                              | Verifier                                         | Why it cannot be satisfied by assertion                                                                                                                                      |
| --- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| G1  | Zero errors at marketplace tier                                                                        | `validate-skills-schema.py --marketplace`        | exit code                                                                                                                                                                    |
| G2  | Zero REFUSE, zero unwaived CHALLENGE                                                                   | `scripts/scan-synced-content.mjs`                | exit code; a waiver requires a **named reviewer, written reason, and expiry** in `scripts/scan-allowlist.txt`, read from the **base** branch (a PR may not allowlist itself) |
| G3  | Unicode hygiene clean                                                                                  | `validate-unicode-hygiene.py --strict`           | exit code                                                                                                                                                                    |
| G4  | `allowed-tools` least-privilege **and** accurate                                                       | tier-2 accuracy check                            | declared-but-unused **and** used-but-undeclared both fail; over-declaring cannot buy a pass                                                                                  |
| G5  | No unscoped `Bash` alongside `Write`/`WebFetch` absent a Safety Justification **naming the operation** | tier-2 tool-safety                               | free text alone does not clear it; the named operation is matched                                                                                                            |
| G6  | Every referenced path resolves inside the skill directory                                              | relative-link check                              | filesystem resolution                                                                                                                                                        |
| G7  | Every declared asset matches its extension                                                             | magic-byte sniff (**not** a NUL sniff)           | 12 artifacts fail this today                                                                                                                                                 |
| G8  | License declared and equal to `.source.json` when mirrored                                             | cross-file compare                               | 9 mirrors contradict upstream today                                                                                                                                          |
| G9  | No vendor-literal model id in the canonical layer                                                      | role-aware model-id classifier, bead-ID-excluded | ~131 true source files fail today                                                                                                                                            |
| G10 | Declared harness requirements satisfiable by ≥2 adapters, **or** explicitly marked single-harness      | adapter matrix                                   | 1,454 skills fail today                                                                                                                                                      |

### Gate E — evidence (class carried in-band; see § 10)

| #   | Criterion                                                                                     | Minimum class |
| --- | --------------------------------------------------------------------------------------------- | ------------- |
| E1  | Deterministic conformance reproducible offline from committed inputs                          | E1            |
| E2  | Committed `eval-spec.yaml`; `j-rig eval` passes under pinned tool + kernel + provider + model | E2            |
| E3  | **Primary `--json` artifact retained and hash-matched to the ledger**                         | E2            |
| E4  | Recorded `baseline_delta`: a deliberately-broken variant of the skill FAILS the same spec     | E3            |
| E5  | Ledger row written by an **independent CI identity**, never the producing agent               | —             |
| E6  | Provenance chain hash-links source → catalog → build → published artifact                     | —             |

## Tier mapping

Certification tier is computed by the validator from observed, passing facts and
is written to Freshie before projection. It is never self-declared.

| Tier   | Name      | Asserts                                                                           | Expected population               |
| ------ | --------- | --------------------------------------------------------------------------------- | --------------------------------- |
| **T0** | Listed    | parses; frontmatter valid; unicode-clean; not malicious                           | all 3,179                         |
| **T1** | Cataloged | T0 + registry entry + license + provenance resolved + generated artifacts in sync | in-repo + all 63 mirrors          |
| **T2** | Carded    | T1 + `skill-card.yaml` (capabilities, side effects, harness support, limitations) | curated set (~1,881)              |
| **T3** | Evaluated | T2 + `eval-spec.yaml` + a passing evidence bundle referenced by run id            | flagship packs, anything marketed |
| **T4** | Certified | T3 + G1–G10 ∧ E1–E6 + integrity digest + negative fixtures                        | small, deliberate, hand-counted   |

`CERTIFY-PENDING-EVIDENCE` is the honest name for T2-clean artifacts that cannot
yet reach T3/T4. Anything short of the full G1–G10 and E1–E6 conjunction is
never certified.

## Binding behavior

- A failed G or E criterion is `NOT-CERTIFIED`; no quality score offsets a
  legal, safety, provenance, or evidence failure.
- An E2/E3 record whose primary artifact cannot be retrieved and hash-matched
  auto-demotes to E0.
- Rendered strength is the minimum evidence class of a plugin's components;
  aggregation never raises a class.
- A producing identity may not record its own final verdict. E5 is enforced by
  the independent-identity ledger boundary, not a reviewer assertion.

## Change control

Any change to a G or E criterion, tier mapping, or its machine verifier must
update Blueprint 727, this standard, its `STANDARDS.md` authority pointer, and
the corresponding automated check in one reviewable transaction.
