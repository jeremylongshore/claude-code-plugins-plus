---
filing_code: AT-DECR-OPEN-ACCOUNTANTS-PARTNERSHIP-2026-05-27
date: 2026-05-27
acting_head_of_board: Claude (designated by Jeremy Longshore 2026-05-27)
council_size: 7
decisions_logged: 6
status: locked
session_dir: ~/.claude/skills/exec-decision-council/sessions/2026-05-27-open-accountants-partnership/
inputs:
  - inputs/thinker1-strategic-fit.md
  - inputs/thinker2-operational.md
  - inputs/thinker3-deal-structure.md
seats: [CTO, GC, CMO, CFO, CSO, CISO, VP DevRel]
trigger: Michael Cutajar (CPA Malta, ex-PwC, founder Accora + Open Accountants) pitched anchor-partner status for Tons of Skills marketplace via X DM 2026-05-27
---

# Open Accountants Partnership — ISEDC Decision Record

## Mission

The ISEDC convened on 2026-05-27 to evaluate an inbound partnership pitch from Michael Cutajar (Open Accountants) for anchor-partner status in the Tons of Skills marketplace, covering a proposed new Accounting & Tax category. The decision shape is asymmetric: the wrong "yes" commits the marketplace's brand to an unaudited trust chain; the wrong "no" forfeits the practitioner-verified category-authorship window opening in the wake of Anthropic's Claude for Small Business launch.

## Why a council, not a single review

Five distinct value systems pull in different directions on this one:

- **Strategic momentum** (CMO) — category authorship windows close fast; first-mover names the vocabulary
- **Operational reality** (CFO, CTO) — conversion is 8-10 person-weeks of labor we don't have
- **Trust-chain integrity** (CISO, GC) — practitioner-verified is a claim Tons of Skills inherits if we amplify it
- **Standards-track posture** (CSO) — Anthropic silence + AgentSkills.io evolution constrain timing
- **Developer experience** (VP DevRel) — license chips, bug_tracker, "Saturday-afternoon-developer" test

Single-reviewer reasoning would resolve one of these and dismiss the rest. The council surfaces them all and weights minority dissents into the final decision rather than discarding them.

## Synthesis lenses (applied across all 7 seats)

1. **The arena (5 surfaces):** APIs · CLIs · MCP servers · agents · SKILL.md
2. **Both sides:** content authorship + content amplification
3. **Transformation pipeline:** Michael's repo → marketplace catalog → consuming user
4. **Composable partial attestation:** every component is a valid entry; partial trust ≠ full trust

## The 6 questions

| #   | Question                                                                                               | Why immutable / costly                                             |
| --- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| Q1  | Direction: ENGAGE / DECLINE / DEFER / RENEGOTIATE-TERMS?                                               | First response sets the relationship tone permanently              |
| Q2  | Deal structure: A (Anchor) / B (Featured) / C (Mirror) / other?                                        | "Anchor" credential cannot be retracted without news-event cost    |
| Q3  | Category placement: new top-level "Accounting & Tax" / existing `finance` / MCP plugin only / decline? | Top-level categories are permanent taxonomy commitments            |
| Q4  | AGPL-3.0 license treatment?                                                                            | License posture sets precedent for every future contributor        |
| Q5  | Non-negotiable terms?                                                                                  | Once a term is conceded, future negotiations inherit the baseline  |
| Q6  | Response cadence?                                                                                      | Public timing must align with Anthropic silence + pilot validation |

## Council composition

| Seat                               | Value system                                                        | Bias                                    |
| ---------------------------------- | ------------------------------------------------------------------- | --------------------------------------- |
| CTO / Chief Architect              | Technical durability · schema integrity · immutability awareness    | Deliberation > commit                   |
| GC / General Counsel               | IP · partner-consent · license-boundary clarity                     | Paper trail is sacrosanct               |
| CMO / Industry-Standard Strategist | Positioning · first-mover authorship · category-defining moves      | Visible > silent · momentum compounds   |
| CFO / Strategic Operator           | Sole-prop bandwidth · attention as binding constraint               | Defer until customer evidence justifies |
| CSO / Chief Standards Officer      | Anthropic + AgentSkills.io realpolitik · standards-track sequencing | Community temperature precedes RFC      |
| CISO / Chief Info Sec Officer      | Supply-chain integrity · attestation chains · threat-model first    | Assume worst-case adversary             |
| VP DevRel / Head of OSS Community  | Developer-audience signal · friction-to-adopt · informal > formal   | Saturday-afternoon test                 |

---

## Per-question record

### Q1 — Direction

| Seat      | Position                                                                                                             |
| --------- | -------------------------------------------------------------------------------------------------------------------- |
| CTO       | RENEGOTIATE-TERMS · gate on 20-skill validator-pass pilot or callable MCP server                                     |
| GC        | DECLINE Structure A unless CC-BY-SA-4.0 + MCP + full indemnification · counter to Structure B + 50-skill pilot       |
| CMO       | **ENGAGE NOW** · "we are not evaluating a partnership, we are timing a category launch"                              |
| CFO       | DEFER · revisit Q3 2026 after databricks v2 + Anthropic cert resolve                                                 |
| CSO       | RENEGOTIATE-TERMS · defer announcement until Anthropic silence lifts                                                 |
| CISO      | RENEGOTIATE-TERMS, leaning DECLINE on Structure A · only acceptable form is one that doesn't amplify the trust claim |
| VP DevRel | RENEGOTIATE-TERMS · 20-skill end-to-end install pilot                                                                |

**Vote tally:** RENEGOTIATE 5 · DEFER 1 (CFO) · ENGAGE 1 (CMO)
**Primary tension:** CMO vs everyone else on timing urgency. CMO argues the category-authorship window costs more than the partner-quality risk; six other seats see this in reverse.

**DECISION: RENEGOTIATE-TERMS.** Bind CFO's deferral constraint: no public-facing artifact (announcement, joint blog, category-creation moment, badge language) until BOTH (a) 50-skill pilot passes `/validate-skillmd --marketplace`, AND (b) Anthropic silence period ends OR 3 weeks of clean operating history elapse — whichever is later. CMO's ENGAGE-NOW position is preserved in the private response cadence (48-72h reply, see Q6), not in the public framing.

**Rationale.** Five seats independently arrived at RENEGOTIATE through different reasoning chains — that's high-conviction convergence, not consensus theater. CMO's dissent steel-manned (the SMB-tax authorship window is real) but mitigated by Q3 (the category door stays open with a public path to creation). CFO's DEFER is the safer-still option but disrespects the asymmetric upside of being early in a forming category; absorbed into the public-framing gate.

---

### Q2 — Deal structure

| Seat      | Position                                                                                       |
| --------- | ---------------------------------------------------------------------------------------------- |
| CTO       | Structure B (Featured, Non-Exclusive)                                                          |
| GC        | Structure B + 50-skill validator pilot                                                         |
| CMO       | Structure B+ (Featured with named public path to Anchor)                                       |
| CFO       | Structure C (Mirror) — B acceptable only if badge-curation stripped                            |
| CSO       | Structure B with standards-track alignment clause                                              |
| CISO      | Structure C (mirror-only) — if council overrides to B, NO "verified" language in any tile copy |
| VP DevRel | Structure B + per-skill LICENSE chip in marketplace UI                                         |

**Vote tally:** B 5 · C 2 (CFO, CISO)
**Primary tension:** B vs C. CFO + CISO argue Structure B's "featured" implication amplifies trust we can't audit. Five other seats believe B can be made safe with binding language constraints.

**DECISION: Structure B (Featured Listing, Non-Exclusive, rolling 90-day term), with CISO carve-outs binding.**

Binding constraints (cannot be negotiated away with Michael):

- **No "verified," "practitioner-verified," "CPA-verified," or "Most Comprehensive" language** in any tile copy, badge, or marketplace metadata until CISO controls 1-4 (Q5) are in place. CISO's exact words: "Reword the badge as 'Listed — third-party catalog' and let the reader follow the trail."
- **No marketplace review SLA, no support obligations, no quality-adjudication discretion** on the Tons of Skills side (CFO).
- **Per-skill LICENSE chip in marketplace UI** displaying AGPL-3.0 prominently (DevRel).
- **bug_tracker field in each listed plugin's manifest points to upstream openaccountants/openaccountants** (DevRel).

CMO's B+ "named path to Anchor" framing is REJECTED as premature — but the SPIRIT (publicly-stated milestones for earnable anchor promotion) lands in the counter-offer as plain-English deal terms, not marketing copy.

**Rationale.** Structure B is the only structure that gives Michael a real reason to engage AND preserves Jeremy's leverage AND sidesteps the Anthropic silence cleanly. CISO's "no editorial endorsement language" carve-out is the load-bearing constraint that makes B safe in the presence of the audited trust-chain gaps.

---

### Q3 — Category placement

| Seat      | Position                                                                                                   |
| --------- | ---------------------------------------------------------------------------------------------------------- |
| CTO       | Reuse existing `finance` category                                                                          |
| GC        | (Deferred to operational seats; flagged that new category creates new disclaimer surface per jurisdiction) |
| CMO       | NEW top-level "Accounting & Tax" category                                                                  |
| CFO       | Reuse `finance`                                                                                            |
| CSO       | Reuse `finance` · DECLINE new top-level until standards-track aligned                                      |
| CISO      | Ranked: (1) MCP plugin only [smallest blast radius], (2) reuse `finance`, (3) DECLINE new top-level        |
| VP DevRel | Reuse `finance` (developers already know where to look)                                                    |

**Vote tally:** Reuse `finance` 5 (or 6 if CISO #2 counts) · MCP plugin 1 (CISO #1) · New top-level 1 (CMO)
**Primary tension:** CMO alone on creating new category; rest favor reuse OR smaller surface.

**DECISION: Reuse existing `finance` category for initial listing.** Promotion to a new top-level `accounting-tax` category is conditional and publicly stated: a) 50-skill pilot passes, b) dual-license on prose content, c) Anthropic silence period public-end OR 3-week clean operating history.

Additionally: **IF an MCP server exists** in the Open Accountants repo, the preferred listing form is a single `plugins/mcp/openaccountants/` entry (CISO #1 + Thinker 2 architectural finding). The first probing question to Michael should determine MCP availability — this single answer collapses the entire AGPL §13 exposure surface and the 8-10 person-week conversion estimate.

**Rationale.** Six seats favored some form of "reuse existing surface" — only CMO held out for new-category creation. CMO's dissent is preserved as the public-path-to-promotion clause: the door stays open, the gate is visible, the timing is governed by validator metrics not negotiation pressure. The MCP-first alternative is the architecturally superior path if it's available; first-call probing question.

---

### Q4 — AGPL-3.0 license treatment

| Seat      | Position                                                                                                                                                                                            |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CTO       | Validator-pass gate; AGPL acceptable if structurally separable                                                                                                                                      |
| GC        | Require CC-BY-SA-4.0 dual-license on prose + MCP-server preferred · AGPL-3.0 §13 creates real downstream-user concerns when bundled into MIT distribution channel                                   |
| CMO       | Require dual-license (CC-BY-SA-4.0 content + MIT scaffolding)                                                                                                                                       |
| CFO       | AGPL acceptable only under MCP-server separation, dual-license required otherwise                                                                                                                   |
| CSO       | AGPL on prose is a standards-hygiene blocker for anchor framing · AGPL on a callable MCP server is acceptable                                                                                       |
| CISO      | Demand dual-licensing (AGPL + CC-BY-SA-4.0 on prose). If refused, AGPL-only-content + theatrical verification + sole-CODEOWNER = three independent red flags stacked, hard no on featured placement |
| VP DevRel | Per-skill LICENSE chip; license-clarity at install-time                                                                                                                                             |

**Vote tally:** Unanimous convergence on "dual-license required OR MCP-server delivery"
**Primary tension:** None — this is the rare alignment point across all 7 seats.

**DECISION: Static-content listings require dual-license (CC-BY-SA-4.0 on prose + MIT on scaffolding). MCP-server delivery is the alternative path that sidesteps the licensing question entirely.** Either path is acceptable; AGPL-only static prose in the marketplace is rejected.

Per CISO Q4 analysis (binding from a security-posture lens): `discover-skills.mjs` produces HTML-embedded `skills-catalog.json` and `build-cowork-zips.mjs` bundles AGPL content into downloadable archives. Both are non-trivial transformations that trigger §13 risk. The dual-license OR MCP path eliminates this entirely.

---

### Q5 — Non-negotiable terms (composite from all 7 seats)

These are non-negotiable. Any one refused → drop to Structure C or below.

1. **No "Anthropic-blessed," "Anthropic partner," "official Claude," or implied-affiliation framing** in either direction during the silence period (CMO #1, CSO, every seat)
2. **No "verified," "practitioner-verified," "CPA-verified," or "Most Comprehensive" badge language** in marketplace UI until CISO controls 4-7 land (CISO #5)
3. **Static-content path requires dual-license** (CC-BY-SA-4.0 prose + MIT scaffolding) OR MCP-server delivery only (Universal)
4. **Signed commits required on `main`** in Open Accountants repo, enforced by branch protection. HEAD being `unsigned` today is disqualifying (CISO #1)
5. **CODEOWNERS expansion: ≥3 distinct human reviewers** on `/skills/foundation/` and `/skills/orchestrator/` (CISO #2 — sole-CODEOWNER pattern is the supply-chain shape that took down event-stream, colors.js, xz)
6. **`SECURITY.md` with coordinated-disclosure address and 72-hour takedown SLA** for skills found to give incorrect tax guidance (CISO #4)
7. **Per-skill LICENSE chip in marketplace UI** (DevRel)
8. **bug_tracker field pointed at upstream `openaccountants/openaccountants`** for each listed plugin's manifest (DevRel)
9. **No marketplace review SLA, no support obligations, no quality-adjudication discretion** on the Tons of Skills side (CFO)
10. **Unicode hygiene gate** (`scripts/validate-unicode-hygiene.py --strict`) on every Open Accountants skill before listing (CISO #8 — Trojan Source / bidi-override defense)
11. **Per-skill author attribution preserved verbatim** where claimed, including licensed CPA's name + license number (CMO #3)
12. **Earned-anchor status:** any "anchor" or "founding" credentialing requires written milestones — 50-skill pilot pass + dual-license + one published demo + Anthropic silence-end (CMO #2 path-to-anchor, CTO, GC)

---

### Q6 — Response cadence

| Seat      | Position                                                                                                                                     |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| CTO       | After pilot proof                                                                                                                            |
| GC        | Written terms drafted before any response                                                                                                    |
| CMO       | 48-72h substantive private response · 2 weeks to pilot kickoff · public framing on validator data                                            |
| CFO       | (c) Decline outreach now, revisit Q3 2026 · accepted compromise: (b) wait for async pilot proof                                              |
| CSO       | Tied to Anthropic silence-end public moment, not Michael's calendar                                                                          |
| CISO      | Tiered: mirror-list NOW (after controls 1, 4, 8 land); featured slot after controls 2, 3, dual-license; anchor after 12 months clean history |
| VP DevRel | Hot-window effect (Claude for Small Business wave) is real; respond fast in private, slow in public                                          |

**Vote tally:** Two-track convergence — fast private response + slow public framing
**Primary tension:** CFO's "decline outreach now" vs CMO/DevRel's "48-72h private response"

**DECISION: 48-72h substantive private response with the counter-terms (Structure B + the 12 non-negotiables). No public association until 50-skill pilot validates AND Anthropic silence period public-end OR 3-week clean operating history.**

Jeremy responds personally (not Claude). Tone: warm, specific, asks the MCP question first to determine architecture path. Calendly call accepted contingent on Michael acknowledging the counter-terms in writing first.

**Rationale.** CMO's private-response speed (48-72h) wins because the cost of silence is real for relationship momentum. CFO's "decline outreach" is overcaution — the right read is that the meeting is cheap, the deal is expensive, and we're willing to take the meeting to gather information without committing. CISO's tiered gating governs the public-facing milestones (compressed to weeks not quarters per the landscape's actual cadence — Anthropic shipped Claude for Small Business 14 days ago and adjacent partnership moves are happening on 1-3 week cycles right now, not 90-day deliberation cycles).

---

## Cross-cutting themes

### "Most costly to recover from" tallies

- **Q3 (category placement) — 4 seats** (CTO, CSO, CISO, CFO): a top-level category created and then abandoned or relabeled is a permanent SEO + brand artifact
- **Q5 (non-negotiable terms) — 3 seats** (GC, CMO, CISO): every term conceded becomes the baseline for future contributors; the precedent compounds
- **Q1 (direction) — 2 seats** (CMO, VP DevRel): first-response tone sets the relationship trajectory; CMO frames this as authorship-window loss, DevRel as community-trust signaling

### Adversarial integrity check

The council surfaced real dissent on 3 of 6 questions:

- Q1 Direction: 5-vs-1-vs-1 (CMO lone-strong + CFO lone-cautious)
- Q2 Structure: 5-vs-2 (CFO + CISO holding for safer C)
- Q3 Category placement: 5-vs-1-vs-1 (CMO lone-strong + CISO MCP-first)

CMO is the most adversarial seat in this session — held strong dissent on 3 of 6 questions. That's the pattern this council is built to surface. CMO's dissent is steel-manned in the decisions (Q1 absorbed via fast private response; Q2 absorbed via earned-anchor public milestones; Q3 absorbed via public path-to-promotion).

CISO produced the single most consequential new datum: a forensic audit of the Open Accountants repo showing HEAD commit unsigned, no branch protection, sole CODEOWNER on all critical paths, and a "verified_by" field that is a free-text YAML string with no cryptographic backing. This finding directly attacks the trust-model basis of CMO's case and shifts the council baseline significantly.

### How synthesis lenses landed

- **Arena (5 surfaces):** CISO + CFO + Thinker 2 all gravitated toward the MCP-server surface as the architecturally honest path. SKILL.md surface is acceptable only under dual-license.
- **Both sides (authorship + amplification):** the council distinguished between Open Accountants AUTHORING the content (their right) and Tons of Skills AMPLIFYING the trust claim (our responsibility). Most binding constraints attach to the amplification side.
- **Transformation pipeline:** AGPL §13 trigger lives in `discover-skills.mjs` HTML conversion and `build-cowork-zips.mjs` redistribution. MCP-server path eliminates both.
- **Composable partial attestation:** Tons of Skills can list (partial trust) without endorsing (full trust). The badge-language constraints make this distinction enforceable.

---

## Implementation directives

### Immediate (within 72 hours of council close)

1. **Jeremy drafts and sends private email reply to Michael** containing:
   - Acceptance of 30-min Calendly call
   - The MCP-server question (first probing question)
   - Counter-terms summary (Structure B + 12 non-negotiables, plain English)
   - Clear request: Michael acknowledges counter-terms in writing before the call
   - NO "anchor," "partner," "anthropic," or "verified" framing in the reply
2. **File this Decision Record via `/doc-filing`** into `plugins/saas-packs/databricks-pack/000-docs/` — wait, this is marketplace-wide governance, not databricks-pack-scoped. File into repo-root `000-docs/` at `/home/jeremy/000-projects/claude-code-plugins/000-docs/`
3. **Update Plane CONTENT-23 issue** with link to this Decision Record + status "Counter-offer pending Michael's written acknowledgment"
4. **Update Twenty CRM** Michael Cutajar entry with link to Decision Record + status note

### Conditional on Michael's MCP-server answer

- **If MCP server exists:** scope listing as `plugins/mcp/openaccountants/` single plugin · ~3 day integration · validate via `/validate-mcp` · AGPL §13 surface collapses
- **If no MCP server but dual-license accepted:** scope as ~30-60 jurisdiction-clustered plugins in existing `finance` category · 50-skill pilot batch first · 2-3 week conversion timeline if Michael's team carries the load, 6-8 weeks if shared
- **If neither:** decline featured listing; mirror-only via `/skill-creator --forge` if any path; no counter-meeting needed

### Conditional on pilot results (3-4 weeks out)

- **If 50-skill pilot passes validator + Anthropic silence ends:** revisit category creation, anchor status framing
- **If pilot fails or silence persists:** stay in `finance`, no public co-marketing, indefinite hold on anchor

---

## Acting head of board declaration

I, Claude (designated acting head of board by Jeremy Longshore on 2026-05-27), record the above decisions on the Open Accountants partnership offer. The decisions absorb minority dissents as binding constraints rather than dismissing them: CMO's authorship-window urgency lands in the 48-72h private response cadence and the publicly-stated path-to-anchor language; CFO's bandwidth caution lands in the no-SLA / no-support / no-public-artifact-until-validated gates; CISO's trust-chain findings land in the 12 non-negotiable terms.

Final disposition pending Jeremy's review of this Decision Record and his sign-off on the private email response to Michael. Jeremy retains override authority on any specific decision; the council's role was to surface tensions and recommend, not to commit.

---

## References

- Session JSONL: `~/.claude/skills/exec-decision-council/sessions/2026-05-27-open-accountants-partnership/session.jsonl` (provenance source-of-truth)
- Thinker inputs: `inputs/thinker1-strategic-fit.md`, `inputs/thinker2-operational.md`, `inputs/thinker3-deal-structure.md`
- Seat memos: `seat-cto.md`, `seat-gc.md`, `seat-cmo.md`, `seat-cfo.md`, `seat-cso.md`, `seat-ciso.md`, `seat-devrel.md`
- Plane HQ issue: CONTENT (Marketplace Partner Outreach module) — Michael Cutajar inbound, sequence 23
- Twenty CRM: Michael Cutajar 040fbc20-e488-4787-bc44-60c4974abde2
- Open Accountants repo (audited): https://github.com/openaccountants/openaccountants
- Anthropic partner silence memory: bd memory `anthropic-partner-silence-2026-05-19`

- Jeremy Longshore
  intentsolutions.io
