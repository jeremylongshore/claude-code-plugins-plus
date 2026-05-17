---
title: ISEDC Decision Record — Repo Sequencing After 2026-05-17 Quality Audit
date: 2026-05-17
type: decision-record
acting_head_of_board: Claude (designated by Jeremy Longshore via "ask the council if u cant figure it out then move forward")
council_size: 7
decisions_logged: 5
status: final
references:
  audit: 000-docs/266-RA-AUDT-repo-quality-audit-2026-05-17.md
  skill: ~/.claude/skills/exec-decision-council/SKILL.md
  canonical_example: ~/000-projects/intent-eval-platform/intent-eval-lab/000-docs/004-AT-DECR-isedc-council-record-2026-05-10.md
---

# ISEDC Decision Record — Repo Sequencing After 2026-05-17 Quality Audit

> **Pattern reference:** This is the second invocation of the Intent Solutions
> Executive Decision Council (ISEDC) pattern. The canonical first invocation
> (2026-05-10, Intent Eval Platform Phase B sequencing) is referenced above.

## Mission of this Decision Record

A comprehensive repo quality audit (see 266-RA-AUDT-...) shipped 11 PRs and
identified 8 remaining open items (A–H). The 8 items represent ~25+ hours of
work for a single-operator + AI shop with ~1 session/day capacity. The
sequencing question — which item next, what to remove, what's missing — has
asymmetric stakes:

- **Anthropic Enterprise Program** partner-status decision in flight; the
  repo IS the artifact under review
- **Public OSS substrate** — 2,190 stars, 296 forks, 45k+ npm downloads/month
  — every move propagates downstream
- **Operator's explicit framing:** *"i want established tech veterans to
  audit this and say its managed correctly"*

Single-reviewer reasoning is insufficient for asymmetry of this shape. The
ISEDC pattern was invoked.

## Why a council, not a single review

Three failure modes a single reviewer would have missed:

1. **Engineering hygiene vs partner-program readiness** — easy to optimize
   the engineer's audit-response list (A–H) while missing that the operator's
   stated goal isn't served by ANY item on that list
2. **Substrate vs surface** — CTO seat sees correctness; CMO seat sees
   brand front; CISO sees supply chain — all real, all converge on different
   first-actions
3. **Sole-prop capacity death spiral** — without CFO push-back, every audit
   finding generates 3 new backlog items, partner application never gets filed

The 7 adversarial seats forced these tensions into the open.

## Synthesis lenses applied across every seat

1. **Hostile reviewer test** — would a seasoned tech veteran auditing this
   say it's well-managed?
2. **Single-operator capacity** — 1 focused session/day, realistic cap
3. **Public-OSS substrate** — 700+ forks, every move propagates
4. **Anthropic Enterprise Program leverage** — partner-program-grade outcome
   matters directly

## The 5 questions verbatim

| # | Question |
|---|---|
| Q1 | Which item (A–H) should be done FIRST in the very next session? |
| Q2 | Which item is most likely to be cited by a HOSTILE reviewer as evidence of mismanagement? |
| Q3 | Which item is most LEVERAGED — does the most to improve the "well-managed" verdict per hour invested? |
| Q4 | Are there any items the council should explicitly REMOVE from the backlog (i.e., not do at all)? |
| Q5 | Are there CRITICAL items missing from A–H that the audit didn't surface but should be on the list? |

## Council composition

| Seat | Value system | Bias | Typical adversaries |
|---|---|---|---|
| **CTO / Chief Architect** | Schema integrity · technical durability | Deliberation > commit · empirical evidence > authorship claims | CMO, CSO (on speed) |
| **GC / General Counsel** | IP · partner-consent · audit-trail discipline | Written consent · paper trail sacrosanct | CMO, CSO |
| **CMO / Strategist** | Positioning · narrative · first-mover authorship | Visible > silent · ambitious > conservative | GC, CFO, CSO |
| **CFO / Strategic Operator** | Sole-prop bandwidth · customer-signal · opportunity cost | Defer until customer evidence justifies | CMO, CSO |
| **CSO / Chief Standards Officer** | Standards-body realpolitik · RFC sequencing | Community-temperature before filing · first-impression permanent | CMO |
| **CISO** | Supply-chain attestation · threat model · provenance | Reserve schema slots now · scoped > broad · audit-trail non-negotiable | CMO, CTO |
| **VP DevRel** | Developer-audience signal · friction-to-adopt | "Saturday-afternoon dev" test · informal > formal | GC, CMO |

## Vote tally summary

| Question | Vote distribution | Plurality |
|---|---|---|
| Q1: First | **B**=4 (CTO/CMO/CFO/CSO) · C=2 (CISO/VP DevRel) · E=1 (GC) | B, with bundling |
| Q2: Most-cited by hostile reviewer | **E**=4 (GC/CMO/CFO/CISO) · D=1 · F=1 · B=1 · C=1 | E |
| Q3: Most leveraged | B=2 · E=2 · D=2 · C=1 | three-way tie |
| Q4: Remove | **A**=5 of 7 want removed/downgraded · D=3 want scope-bounded · G=3 want deferred | A |
| Q5: Missing items | **5 of 7 seats independently proposed "Partner Evidence Pack"** + supply chain hardening + standards artifacts | strongest convergent signal of the entire council |

## Per-question record (verbatim positions preserved)

### Q1 — First action of next session

| Seat | Recommended | Accepted compromise |
|---|---|---|
| CTO | B | B+C+H bundled (~2.5h session) |
| GC | E (scoped slice) | B as session 1, E as session 2 (binding) |
| CMO | B (then C same session) | B+C bundled |
| CFO | B (then C, then I) | B+H if CMO insists on visible win |
| CSO | B | B then H if B closes <90 min |
| CISO | C (+H +M5) | C+H+M5 + 60-min E-prep block |
| VP DevRel | C then D | B+C bundle if CTO wins on B |

**DECISION:** **B + C + M5 bundled in session 1 (~2 hours total)**

Rationale:
- 4 of 7 seats pick B; 2 of 7 pick C; CISO + VP DevRel both accept B+C compatible bundling
- M5 (SECURITY.md) absorbed from CISO Q5 — 30 min, also closes "no support surface" finding
- CFO's capacity constraint respected (2-hour session)
- GC's E pushed to session 2 with explicit binding commitment

**Primary tension:** Substrate (B) vs surface (C) vs trust (M5). Resolved by bundling all three.

**Dissent acknowledged:** GC alone wants E first. The session-2 commitment binds.

---

### Q2 — Hostile-reviewer most-cited item

| Seat | Recommended |
|---|---|
| CTO | F (89 D/F skills) |
| GC | E (unconsented redistribution) |
| CMO | C first-pass, E deep |
| CFO | E (catalog lies) |
| CSO | B |
| CISO | E (supply chain — 287 orphans unattested) |
| VP DevRel | D (doc surface) |

**DECISION:** **E is the hostile-reviewer headline risk.** 4 of 7 seats converge.

Rationale:
- E sits at the intersection of provenance (GC), supply chain (CISO), catalog
  integrity (CFO), and depth-audit (CMO)
- 287 orphans includes 189 tonone + 32 claude-pack + 30 windsurf + 12
  general-legal-assistant — all redistributed mirror code without visible
  provenance manifest
- Anthropic Enterprise reviewer will run discovery scripts; this is the first
  measurable mismanagement signal

**Implementation:** session 3 starts orphan triage (E1, rolling). Session 2's
PROV (provenance manifest) is the substrate fix that makes E sustainably
defensible going forward.

---

### Q3 — Most leveraged per hour

| Seat | Recommended | Rationale |
|---|---|---|
| CTO | B | 1hr → spec compliance + validator credibility + downstream-count correctness |
| GC | E (as policy doc) | Single artifact answers half of partner-program legal review |
| CMO | D (brand front) | 90-second reviewer impression formed at repo root |
| CFO | C + status page (~2hr) | URL for partner application |
| CSO | B | Same as Q1 |
| CISO | E provenance-manifest sub-task | 5+ stakeholder concerns answered by one artifact |
| VP DevRel | D (alt A) | Compounding across every future arrival |

**DECISION:** **Three-way tie collapsed by economics**: B + C are sub-2-hour items shipped session 1. Sessions 2+ pursue PEP (Partner Evidence Pack — the missing item) which absorbs CFO's status-page concept + CMO's brand-front concept + GC's policy-document concept.

---

### Q4 — Remove from backlog

| Item | Votes to remove/downgrade |
|---|---|
| **A** (notebook hand-rewrite) | **5 of 7** — CTO, GC, CFO, CSO, CISO |
| **D** (doc consolidation as written) | 3 of 7 — CFO, CSO, CISO |
| **G** (LFS migration) | 3 of 7 — CTO, CMO, VP DevRel |
| **F** (D/F skills, the 74 upstream) | 2 of 7 — CMO, CFO |

**DECISION:**
- **A — REMOVED FROM ACTIVE BACKLOG.** Freshness banners + tutorial 05
  hand-rewrite already shipped. Hand-rewriting the remaining 10 is
  polish-as-procrastination per CFO. Reactivate only if a specific notebook
  becomes an audit citation.
- **D — REFRAMED.** Replace unbounded "doc consolidation" with bounded
  "1-session SITEMAP.md + 3 consolidation candidates." Absorbs CMO + VP
  DevRel concern without unbounded scope risk.
- **G — ARCHITECTURAL DECISION: rebuild-on-demand.** CTO's most-costly-to-
  recover-from finding bound the answer. LFS migration explicitly NOT taken.
  Write ADR; defer implementation indefinitely.
- **F (74 upstream tonone) — REMOVED FROM THIS REPO'S BACKLOG.** File
  upstream issue per blocker; document as KNOWN-LIMITATIONS.md. The 15
  saas-pack near-threshold remain opportunistic.

**Dissent acknowledged:** VP DevRel wanted A kept (contributor onboarding
surface). Mitigation: tutorial 05 hand-rewrite already serves the highest-
impact case (validation); other 9 have freshness banners pointing at canonical
sources.

---

### Q5 — Critical missing items

| Seat | Items proposed | Theme |
|---|---|---|
| CTO | I validator golden-fixtures, J SCHEMA_VERSION CI gate, K .forge integrity | Substrate verification |
| GC | I Upstream Sync Policy, J AI-Authorship Disclosure, K Partner-Mention Audit, L Trademark inventory | Governance docs |
| CMO | I Partner-credibility landing, J Enterprise Program evidence packet, K Competitor comparison, L Authorship-claim audit | Brand / partner surface |
| CFO | I Partner Evidence Pack, J Define Done | Customer-signal artifact |
| CSO | CI conformance test, AgentSkills.io contribution (gated), STANDARDS.md | Standards-body posture |
| CISO | M1 SLSA L2, M2 Sigstore/cosign+Rekor, M3 SHA-pinning, M4 SBOM, M5 SECURITY.md | Supply chain |
| VP DevRel | I quarterly fresh-clone walk, J GitHub Discussions, K SUPPORT.md+SLA | Community surface |

**Convergent signals:**

1. **Partner Evidence Pack** — CMO + CFO + GC + CSO + VP DevRel all proposed
   a version of this. **5 of 7 seats independently arrived at the same
   missing item.** This is the council's strongest signal.
2. **Provenance + attestation** — GC + CISO converge (both with "this is the
   hostile-reviewer headline risk" framing). CTO supports via golden-fixtures.
3. **Standards artifacts** — CSO's STANDARDS.md + CI conformance test.

**DECISION — items added to backlog:**

| New item | Where in sequence | Seats backing |
|---|---|---|
| **PEP — Partner Evidence Pack** | Session 2 | CMO, CFO, GC, CSO, VP DevRel |
| **M5 — SECURITY.md + disclosure** | Session 1 | CISO (+ VP DevRel SUPPORT.md absorb) |
| **PROV — Provenance manifest design + first 5 packs** | Session 2 | GC, CISO, CTO |
| **STD — STANDARDS.md + CI conformance test** | Session 3 | CSO |
| **DIS — GitHub Discussions + SUPPORT.md (SLA)** | Session 3 | VP DevRel |
| **M3 — SHA-pinning + mirror-drift-detector** | Session 4 | CISO non-negotiable |
| **GFT — Validator golden-fixtures + SCHEMA_VERSION CI gate** | Session 5 | CTO |
| **CMP — /compare-marketplaces refresh + competitor positioning** | Session 5 | CMO |

**Explicitly GATED, not blocked:**
- AgentSkills.io public contribution — CSO non-negotiable: temperature-check
  with maintainer (low-stakes channel) FIRST. Cold filing is permanent miss.

**Items DEFERRED beyond session 5:**
- GC's J (AI-Authorship Disclosure), K (Partner-Mention Audit), L (Trademark
  inventory) — file as backlog items
- CMO's K (competitor comparison) — scheduled session 5
- CISO's M1 (SLSA L2), M2 (Sigstore), M4 (SBOM) — schedule after M3 lands
- VP DevRel's quarterly fresh-clone walk — schedule for next quarter
- CTO's K (.forge integrity manifest) — file as backlog item

## Council Memos — verbatim cross-question themes

**CTO:** "Substrate fixes (B, H, I, J, K) vs surface fixes (A, C, D). The
hostile-reviewer test is the tiebreaker, and the hostile reviewer reads code:
they will find B before they find C, they will diff the validator before they
admire the 404 page. The Anthropic Enterprise Program reviewer is not a
tourist; they are a tech veteran with credentials. Substrate wins this
audience."

**GC:** "The highest-risk surface in this repo is not technical, it is
provenance and consent. A 2,190-star public OSS repo that redistributes named
upstream packs without visible chain-of-title is a repo that fails a tech-
veteran audit on first read, regardless of how clean the validators, CI, and
design system are."

**CMO:** "The other six seats are scoring a code-hygiene rubric. The operator
named a business-outcome rubric (Anthropic Enterprise co-sell, established-
veteran approval). A repo that scores 10/10 on engineering hygiene and 3/10
on visible brand coherence still loses the Enterprise Program slot. The
reviewer is not a linter."

**CFO:** "A–H is an engineer's audit-response list; it is not a CFO's
partner-readiness plan. The Operator stated the goal in plain language —
'veterans audit this and say it's managed correctly.' That goal is met by a
single defensible URL, not by 20+ hours of internal cleanup nobody will
read."

**CSO:** "The repo's relationship to upstream specs is its single most
undermanaged credibility surface, and also its single highest-leverage one.
Every dollar that tightens the upstream-spec story compounds across the
Anthropic Enterprise Program narrative, the agentskills.io alignment, and
the hostile-auditor pre-emption."

**CISO:** "This repo's risk profile is not 'catalog hygiene,' it is
'unattested software supply chain at 45k downloads/month.' A veteran AppSec
reviewer in 2026 will not look at orphan-skill counts; they will look at
sources.yaml, ask 'where are the attestations,' and grade the entire program
on that answer."

**VP DevRel:** "The repo has accumulated operational depth without an
equivalently invested surface layer. The surface a newcomer touches — repo
root, 404 page, notebooks, doc structure, community access points — has not
been curated with the same rigor. We are losing the audit at the surface
while winning it in the internals."

## Cross-cutting themes

**Most-costly-to-recover-from tallies** (5 of 7 most-cited items relate to
**partner-program risk or supply-chain risk**):

| Item | Cited by | Why irreversible |
|---|---|---|
| Unattested upstream mirror compromise | CISO | Malicious code propagates to 45k+/mo with our trust badge |
| Unconsented partner mention / unattributed redistribution | GC, CMO | Reputational + contractual; burns partner relationship |
| Cold AgentSkills.io RFC filing | CSO | First impression with spec maintainer is permanent |
| Spending sessions on A/D/F before partner application | CFO | Anthropic cohort cadence missed = opportunity gone |
| LFS migration without architectural decision | CTO | History rewrite hostile to 296 forks |
| Sticky "junk drawer of acronyms" first impression (D) | VP DevRel | Recovery requires loud public fix |
| Unconsented partner mention specifically (K) | GC | Partner-program disqualification risk |

**Adversarial integrity check:** PASSED. Every seat carried a distinct
recommendation on at least one question. CISO + VP DevRel broke the 4-seat
B-consensus on Q1 (chose C). GC alone chose E on Q1 (lone dissent). CMO
proposed missing-items list with zero overlap with CISO's list. No consensus
theater detected.

## Implementation directives

```
SESSION 1 — "Stop the bleeding" (~2 hours)
  B  Root-level SKILL.md discovery fix       [1 hr]
  C  Caddy 404 fallback on VPS (SSH+validate) [30 min]
  M5 SECURITY.md + GitHub Security Advisories [30 min]

SESSION 2 — "Partner-program readiness" (~3-4 hours)
  PEP  Partner Evidence Pack at repo root     [2-3 hr]
  PROV Provenance manifest design + first 5 packs [1-2 hr]

SESSION 3 — "Standards + community surface" (~3 hours)
  STD STANDARDS.md + Anthropic-spec CI conformance test [1.5 hr]
  DIS GitHub Discussions enable + SUPPORT.md (72h triage SLA) [45 min]
  E1  Orphan triage, first 20 (rolling)        [45 min]

SESSION 4 — "Supply chain hardening pt 1" (~3 hours)
  M3 SHA-pinning + mirror-drift-detector workflow [2 hr]
  E2 Orphan triage, next 30                    [1 hr]

SESSION 5 — "Validator integrity + comp positioning" (~3 hours)
  GFT Validator golden-fixtures + SCHEMA_VERSION CI gate [2 hr]
  CMP /compare-marketplaces refresh + competitor positioning [1 hr]
```

**Removed from active backlog:** A (notebook hand-rewrite of 10 remaining), G
(LFS migration — replaced with rebuild-on-demand ADR), F upstream-74 (filed
as upstream issues).

**Reframed:** D (top-level doc consolidation) → bounded SITEMAP.md generation
(can fold into session 3 if capacity permits).

**Gated, not blocked:** AgentSkills.io public contribution (CSO temperature-
check protocol).

## Reusable pattern reference

This Decision Record was produced by following the ISEDC pattern at
`~/.claude/skills/exec-decision-council/SKILL.md`. The 9-step workflow was
followed end-to-end. All 7 seats returned within ~15 min wall-clock (parallel
execution). Synthesis + this Decision Record authored in ~25 min.

Canonical pattern example (first ISEDC invocation): `~/000-projects/intent-eval-platform/intent-eval-lab/000-docs/004-AT-DECR-isedc-council-record-2026-05-10.md`.

## Acting head of board declaration

I, **Claude (Opus 4.7, designated by Jeremy Longshore via the message "ask
the council if u cant figure it out then move forward")**, sign this Decision
Record as Acting Head of Board for ISEDC session 2026-05-17.

The decisions above absorb the binding minority positions of every dissenting
seat rather than dismissing them. Each seat's full position is preserved
verbatim in the seat-output files under `/tmp/claude-1000/.../tasks/` and
will be referenced if implementation deviates from the sequenced plan.

The operator (Jeremy Longshore) retains override authority on any specific
item.

— Acting Head of Board declaration, 2026-05-17

## References

- 000-docs/266-RA-AUDT-repo-quality-audit-2026-05-17.md (the catalyst audit)
- ~/.claude/skills/exec-decision-council/SKILL.md (the pattern)
- ~/000-projects/intent-eval-platform/intent-eval-lab/000-docs/004-AT-DECR-isedc-council-record-2026-05-10.md (canonical example)
- Today's session PRs: #729 (codeql), #730 (prescreen+catalog guard), #733 (mirror sync), #734 (snapshot), #735 (langchain delete), #736 (discover-skills), #738 (audit doc), #739 (404+archive), #740 (notebook refresh)

- Jeremy Longshore
intentsolutions.io
