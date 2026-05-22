# ISEDC Decision Record — Issue #710 spec-mint response (2026-05-16)

**Document type:** Adversarial Technical Decision Record (AT-DECR) — partial reconstruction
**Date deliberated:** 2026-05-16
**Date reconstructed:** 2026-05-21
**Decision type:** Partner-dynamics + architectural + brand
**Head of Board:** Jeremy Longshore
**Status:** Deferred until 2026-05-23 (bead `claude-t11v`)
**Recovery posture:** PARTIAL — see "Recovery + provenance" at end

---

## Mission

Decide how to respond to GitHub issue #710 (`jeremylongshore/claude-code-plugins-plus-skills#710`) — a four-part interop ask from latentloop07 (Luna Prompts / skillnote), which escalates from technical schema additions into a "spec-mint partnership" framing that would position Intent Solutions as the standards-author for `marketplace.json` and skillnote as the canonical consumer.

## Counterparty background (council seat findings)

| Surface               | Finding                                                            |
| --------------------- | ------------------------------------------------------------------ |
| Crunchbase            | No listing found                                                   |
| LinkedIn company page | No company page found                                              |
| GitHub                | `luna-prompts/skillnote` — MIT-licensed self-hosted skill registry |
| Named individuals     | Tyler Nash; Rudra Naik (Joist AI moonlighting situation)           |
| Prior relationship    | None — first contact via #710                                      |

**Council confidence:** medium — engineer-credible but org-thin.

**Red flags:**

- No Crunchbase / no LinkedIn company page (could be early stealth OR vapor)
- Rudra Naik / Joist AI moonlighting context surfaced in the council bg-check
- Counterparty co-mint framing positions them as peer despite scale asymmetry (one repo vs. our 425-plugin marketplace)

**Green flags:**

- MIT license on skillnote — interop-friendly
- Engineer-grade asks (specific schema fields) — competent + precise
- Independent corroboration: cited Jeremy publicly on `sickn33/antigravity-awesome-skills#596`; sickn33 implemented in Jeremy's model

## Questions adjudicated (5)

1. Accept #710 asks as-is / reject / modify / counter-frame?
2. Ship `install_source_url` in schema 3.7.0?
3. Ship per-skill `license` + `author` echo in L0?
4. Publicly accept the **spec-mint framing** — minting marketplace.json schema 3.4.0+ as "the" registry-interop spec with skillnote as canonical consumer?
5. Publicly commit to listing skillnote in ccpi within 1 week of their adapter landing?

## Vote outcomes

| Q   | Vote distribution                                           | Result                                                           |
| --- | ----------------------------------------------------------- | ---------------------------------------------------------------- |
| 1   | All 7 seats voted MODIFY                                    | **Unanimous modify** — don't take their framing as-is            |
| 4   | CTO ✗ · GC ✗ · CMO ✓ · CFO ✗ · CSO ✗ · CISO ✗ · VP DevRel ✗ | **6 of 7 REJECT co-mint framing.** CMO is lone strong dissenter. |

## Cross-cutting themes

**#1 most-costly-to-recover-from:** spec-mint partnership framing (Q4).
**Named by 6 of 7 seats** as the option whose downside is hardest to undo. Standards-author role, if it sours or attracts the wrong partner mix, is hard to walk back without ecosystem fragmentation.

## Synthesis (council recommendation — Path 1)

**Stacked-constraints response:**

- **Accept** the technical asks that strengthen the schema regardless:
  - `install_source_url` — ship in schema 3.7.0 on our own timeline
  - per-skill `license` + `author` echo — ship in same release
- **Defer** the listing-with-clock commitment — move from "1 week after adapter" to "when adapter is in main + works against our L0"; no calendar clock
- **Decline** the co-mint framing — publish schema 3.4.0+ as Intent Solutions' own spec under our name; explicitly invite ANY aggregator (Composio, VoltAgent, sickn33, alirezarezvani, ComposioHQ) to consume it as the published format; no exclusive partnership framing
- **Steel-man CMO's positioning concern** in the response prose itself — we DO want skill-aggregator ecosystem coherence; we just won't accept co-mint asymmetry as the path to it

### Binding minority protections (from CMO dissent)

CMO's positioning win is preserved by:

- Publishing schema 3.4.0+ as Intent Solutions' own spec, under our name
- Explicit invitation to any aggregator to consume — we get the spec-author role on our terms without the co-mint asymmetry
- sickn33's parallel implementation (already happening) becomes additional independent ecosystem evidence we point to

### Paths offered

| Path                                        | Summary                                                               | When to pick                                                | Downside                                                                           |
| ------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **1 — Adopt synthesis as-is** (recommended) | Post stacked-constraints response; ship schema asks; decline co-mint  | Default                                                     | Counterparty may walk; mitigated by sickn33's parallel impl                        |
| 2 — Adopt with per-question overrides       | Take synthesis, override specifics (e.g. accept 1-week listing clock) | If goodwill on a specific axis matters                      | Erodes coherent stance; minority protections harder to honor                       |
| 3 — Adjourn                                 | Don't respond; pick a named trigger                                   | If timing isn't right; want to see their adapter ship first | Counterparty's "starting this week" means 7-day shelf is OK; longer risks ghosting |

## Decision (Acting Head of Board — Jeremy Longshore)

**Path 3 (interim) — defer 1 week to think.**

Rationale: council recommended Path 1; Jeremy chose time before committing. latentloop07's "starting this week" adapter timeline means a 7-day shelf is within natural cadence — no public-facing damage from the brief silence.

**Reopen triggers:**

- 2026-05-23 (bead `claude-t11v` auto-resurfaces from defer)
- Earlier if latentloop07's adapter PR lands and forces a response
- Earlier if a competing aggregator publishes a similar spec-author claim and we need to assert priority

**Commitments made:** none.

**Commitments explicitly NOT made:**

- No public response posted on #710 yet
- No commitment to schema 3.7.0 timeline yet
- No commitment to listing skillnote in ccpi
- No co-mint framing accepted
- No "within 1 week" clock accepted

## Recovery + provenance

This document is a **partial reconstruction** dated 2026-05-21. Original session source files at `/tmp/isedc-710/isedc-710-decision-record.md` and `/tmp/competitive-bg/competitive-deepdive.md` were lost to `/tmp` cleanup. Reconstructed from:

- Gmail email body (sent 2026-05-16T20:04:39Z) summarizing the council DR — Gmail thread `19e32641506f03ac`
- Gmail email body (sent 2026-05-16T20:46:01Z) on the competitive deep-dive — Gmail thread `19e3289f4ac413bc`
- `bd show claude-t11v` (deferred bead capturing decision state at shelving)
- `bd show claude-djcb` (original respond-to-#710 task bead)

**What was lost:** verbatim per-seat positions for all Q1–Q5 × 7 seats (~35 records), per-seat Council Memos, full detail of the competitive analysis bodies (Composio · VoltAgent · Spillwave-Skillzwave including Rick Hightower + Chris Mathias).

**Path to full recovery:** save `isedc-710-decision-record.pdf` from Gmail to `inputs/`, then run pdftotext + reconstruction to populate the `seat-position` records in `session.jsonl`. The 27-page PDF (167 KB) is the canonical full deliberation.

## Source of truth

Structured data: `~/.claude/skills/exec-decision-council/sessions/2026-05-16-issue-710-spec-mint/session.jsonl`
This document: derived from that JSONL.
Filed copy: TBD — `/doc-filing` will mirror into the relevant project's `000-docs/` per the skill's mandatory final step.

---

_Session reconstructed 2026-05-21 by Claude as part of building the durability mechanism that should have existed when this council ran. Future councils will write directly to the JSONL during deliberation, eliminating this `/tmp` cleanup risk._

---

## Addendum — Final acting-head-of-board call (2026-05-21)

After re-reading the #710 thread on 2026-05-21, the acting head of board confirmed
that latentloop07 **did not ask a hard question**:

- Both `?` lines in their 2026-05-16 comment are soft "want to pin/mint?" framings
- The same comment ends with two self-commits:
  - _"starting on the adapter this week"_
  - _"will file the install_source_url schema-feature request against your repo this week"_

They are self-driving. No reply from us is required for their adapter work to proceed.

**Final decision: Path 3 EXTENDED indefinitely.** No reply posted to #710. The
2026-05-23 calendar defer is DROPPED.

### Narrowed reopen triggers (replace the original list)

| #   | Trigger                                                      | Action                                                   |
| --- | ------------------------------------------------------------ | -------------------------------------------------------- |
| 1   | Their adapter PR lands on a repo we maintain                 | Forces a response in PR review                           |
| 2   | They explicitly ping with a hard, direct question            | Re-engage with the response (council's Path 1 synthesis) |
| 3   | A competing aggregator publishes a similar spec-author claim | Re-engage to assert priority                             |

**Natural attrition:** if none of the above fires by **2026-07-01**, close bead
`claude-t11v` with reason "natural attrition" and consider this session closed
without a public response.

### Additional context surfaced during 2026-05-21 re-read

Luna Prompts' actual business per `lunaprompts.com`: _"AI-native technical screen
for hiring AI engineers."_ They sell developer-screening software; skillnote is a
3-month-old side product. This reinforces (rather than weakens) the original council's
6-of-7 reject of the co-mint framing — accepting a spec-mint partnership with a
company whose actual revenue is in adjacent hiring software increases the
asymmetry, doesn't reduce it.

### What's still unchanged from the original synthesis

If a reopen trigger fires later, the council's Path 1 stacked-constraints response
remains the right shape:

- Ship the schema asks (`install_source_url`, per-skill license/author echo) on our own timeline as schema 3.7.0
- Decline the co-mint framing — publish schema 3.4.0+ under Intent Solutions' name
- Invite ANY aggregator (Composio, VoltAgent, sickn33, alirezarezvani) to consume the published format

The "let it sit" decision is operationally Path 3 but does not foreclose Path 1.
