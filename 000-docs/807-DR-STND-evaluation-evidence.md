<!-- doc-class: canonical -->

# 807-DR-STND — Evaluation and Evidence Standard

**Status:** AUTHORITATIVE

**Authority:** Blueprint 727 § 9. Epic 5 owns this standard; Epics 9 and 10 consume it.

## Evidence classes

| Class                      | Definition                                                                                                          | Supports                |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| E0 Assertion               | An author states it.                                                                                                | Nothing.                |
| E1 Deterministic           | A validator, j-rig check, or harness exit code reproducible offline from committed inputs.                          | Structural conformance. |
| E2 Behavioral-reproducible | j-rig eval with committed eval-spec.yaml; exact CLI, kernel, provider, and model; retained and hashed primary JSON. | Capability claims.      |
| E3 Adversarial             | E2 plus red-team cases and a baseline_delta showing the evaluation discriminates.                                   | Safety claims.          |

## Validity and claim ceiling

Evidence carries its class in-band with `spec_sha256`, `artifact_sha256`, `artifact_uri`, tool and kernel versions, provider, model, recording identity, and timestamp. No class means no verification claim. Renderers read the class, never a boolean.

If an E2 or E3 primary artifact cannot be retrieved and matched to `artifact_sha256`, the record auto-demotes to E0. E3 requires a non-null baseline_delta. Rendered strength is the minimum class across a plugin’s components; aggregation never raises a class.

## Determinism, storage, and independence

E2/E3 records require exact jrig-cli and core pins, a committed specification, pinned provider/model/temperature, recorded seed, and adapter ID. A nondeterministic provider requires at least three runs and a recorded variance bound; a single sample is E1.

Freshie/Dolt stores the append-only ledger: verdict, class, hashes, pins, and timestamps. A separate artifact store retains raw evaluation payloads addressed by ledger hash; payloads never enter the CMDB or public Dolt export. The producing identity may not record its own final verdict; independent CI records a re-executed evaluation. `jrig_run_id` and `discovery_run_id` remain separate namespaces, with only discovery_run_id a discovery-run FK.

## Change control

Consumers may implement enforcement but may not weaken the class, retention, claim-ceiling, storage-split, or no-self-approval rules.
