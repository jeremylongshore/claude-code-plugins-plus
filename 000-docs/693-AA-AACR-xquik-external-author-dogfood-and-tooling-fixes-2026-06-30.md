<!-- doc-class: record -->

# AAR — Xquik external-author onboarding, eval dogfood, and the tooling fixes it surfaced

**Doc:** 693-AA-AACR · **Date:** 2026-06-30 · **Status:** LANDED (after-action change-record)
**Subject:** what the marketplace did when an external author (`Xquik-dev`) opened two source-link PRs — we onboarded both plugins, ran our own eval platform on them, and the run found two bugs in **our** tooling (not his skills), which we fixed and shipped.
**Companion record (IEP side, full detail):** `intent-eval-platform/intent-eval-lab/000-docs/104-RR-LAND-xquik-external-author-dogfood-initiative-2026-06-30.md`

---

## TL;DR

`Xquik-dev` (GitHub `kriptoburak`, Burak Bayır) opened two external-source PRs to this marketplace — **#924** (`hermes-tweet`) and **#865** (`x-twitter-scraper`, ⭐126). Both skills are thorough and security-conscious. We:

1. **Merged both** into the catalog (the reciprocity) — #924 cleaned of two stray codex hunks, #865 with a `sources.yaml` conflict resolved.
2. **Ran our own Intent Eval Platform on his two public skills.** Package checks were clean (`j-rig check`: **11/0** and **12/0**); the behavioral run returned `block` — but reading the rows, that block was **two bugs in our tooling**, not his skills.
3. **Fixed and shipped both bugs** (j-rig **#175**, this repo **#925**).
4. **Reached out as a peer** — two "dogfood the platform, file issues against it" requests on his repos, with tailored `eval.yaml` specs.

The headline lesson is the same as the [088 `beads-dolt`] run: a platform that runs on a real external artifact and catches a flaw in its own seams is doing its job. Here it caught two.

## What we changed (the concrete record)

| Change | Where | Status |
|---|---|---|
| Onboard `hermes-tweet` external source | this repo **#924** | MERGED (clean — dropped a `numman-ali` `verified` flip + an unrelated blog-newline strip that rode in from codex) |
| Onboard `x-twitter-scraper` external source | this repo **#865** | MERGED (resolved a `sources.yaml` conflict with the `publishing-skills` block that landed at the same spot) |
| Bump `@intentsolutions/jrig-cli` `0.1.0 → 0.1.1` | this repo **#925** | MERGED (the pinned `0.1.0` predated the per-test-case `criteria_ids` scoping fix; kernel-coupling-safe — `0.1.1` deps `core@0.9.0`, the root pin) |
| Judge verdict-parsing robustness (`extractVerdict` regex fallback + judge token-budget parity) | `j-rig-skill-binary-eval` **#175** | MERGED |

## Findings

### Finding 1 — the pinned eval CLI carried a shipped false-blocker

The repo pinned `jrig-cli@0.1.0`, which **predates jrig #162**. On `0.1.0`, `j-rig eval` applies **every criterion to every test case**, so an off-topic `should_not_trigger` control prompt (e.g. "capital of France", "Hamlet plot") fails unrelated X-safety criteria — the *false-blocker bug that inflated NO-SHIP rates*. The fix shipped in `0.1.1`; we were just behind. **Change:** pin bumped to `0.1.1` (#925). **Correction filed:** an earlier internal note wrongly said the fix was "absent from 0.1.1" — it is present; the only gap was our stale pin.

### Finding 2 — the judge mis-parsed truncated structured verdicts as "unsure"

With `--provider deepseek`, the judge returns the `{"verdict":"yes",…}` JSON it is asked for, but a long `reasoning` truncates the object at the token ceiling, `parseJsonObject` returns null, and a decisive verdict silently becomes `unsure` (a non-pass) — inflating NO-SHIP. **Change:** `extractVerdict` recovers the verdict via a regex fallback when structured parse fails, plus judge-budget parity across providers (j-rig #175). This is a **current** bug (present in published `0.1.1` + `anthropic-real`), so the fix is real, not just a pin bump.

### Finding 3 — the marketplace validator under-credits rich external skills (open)

Both skills scored **66/73** in the IS validator **only** because their section names (`## Instructions` / `## Output` / `## Error Handling`) don't match our marketplace taxonomy and their `capabilities:` security block is "unknown" to the validator — a **taxonomy mismatch on our side, not a deficiency in the work**. Calling a 126★ skill "not fleshed out" because its headings differ from ours reads as not having read it. **Follow-up (open):** credit equivalent non-IS section names + recognize the `capabilities` field, or publish the section-name convention so external authors can self-align. Tracked as bead `iel-62j`.

## What went right / what to repeat

- **Run the eval ourselves before any public claim.** The behavioral score is a property of *(skill × subject-model × judge-model × spec)*, not just "is the skill good." The honest read of a `block` is "look at the rows" — and the rows indicted our harness, not the author. Had we published the raw `block`/score, we'd have insulted a strong contributor with our own bug.
- **Clean the contribution as maintainer, don't merge the noise.** #924's stray `numman` flip would have downgraded another contributor's `verified` status; a rebase onto the updated `main` auto-resolved it to a clean hermes-only diff.
- **Reciprocity stays implicit.** We merged his PRs and made the dogfood ask peer-to-peer — no tit-for-tat language anywhere public.

## What to watch

The adoption signal: whether Xquik runs the public IEP tooling and/or files issues against the `@intentsolutions/*` packages (`Xquik-dev/hermes-tweet#577`, `Xquik-dev/x-twitter-scraper#5`). That's the real-world external-adoption evidence — qualitative, arriving via GitHub, not a data feed.

## Evidence / references

- Merged PRs: this repo **#924**, **#865**, **#925**; `j-rig-skill-binary-eval` **#175**.
- Authored issues (the ask): `Xquik-dev/hermes-tweet#577`, `Xquik-dev/x-twitter-scraper#5`.
- Beads: `iel-fta` (epic), `iel-62j` (validator fairness, open), `j-rig-binary-eval-708` / `-908` (closed).
- Full IEP-side initiative record: `intent-eval-lab/000-docs/104-RR-LAND-…-2026-06-30.md`.
