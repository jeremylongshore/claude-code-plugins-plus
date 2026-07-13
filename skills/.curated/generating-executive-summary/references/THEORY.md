# THEORY — Executive Summary as a Technical-Communication Discipline

## What an exec summary actually is

An executive summary is not a shorter vulnerability report. It's
a different document for a different reader. The vulnerability
report says "here is every finding we identified." The exec
summary says "here is what the board / CEO / CISO needs to decide
on, and how big the decision is."

The summary's job is to compress without losing decision-relevant
information. Compressed too far, it becomes content-free chrome
("the engagement found several issues; please refer to the full
report"). Compressed too little, it becomes a redundant technical
document.

The middle ground:

1. A single number that establishes the engagement's bottom line
   (risk score).
2. Counts that contextualize the number (severity breakdown).
3. Specific named priorities the reader can act on.
4. Just enough scope/authz framing that the reader can validate
   the summary against their own expectations.
5. A clear pointer to the deep document.

## Why a single risk score

The single-number summary is controversial in security circles —
it loses information, it can be gamed, it doesn't capture
exploitation likelihood. All true.

It's still the right primitive for the exec audience because:

- Execs are accustomed to making decisions on single numbers
  (NPS, MAU, ARR, Lighthouse score). A pentest result without a
  number doesn't fit the decision frame.
- The number's interpretation band ("Low / Moderate / Elevated /
  High / Critical") is more decision-relevant than the precise
  number anyway.
- Score-to-decision mapping is consistent across engagements;
  the customer can compare year-over-year and customer-to-customer.

Critical caveats the summary writer should NOT lose:

- The score is HEURISTIC. A 65 isn't twice as bad as a 32.
- The score's composition formula is documented; the reader can
  audit how it was computed.
- The score isn't a substitute for reading the finding list.

## Risk score composition — design rationale

The chosen weights:

- 20 per CRITICAL — each critical finding has potential to be a
  full-organization-impact event. Two criticals already pushes
  the score into the elevated band.
- 10 per HIGH — high findings are material but typically scoped
  to specific systems.
- 3 per MEDIUM — mediums accumulate to meaning; one isn't a
  big deal, but ten is.
- 1 per LOW — low findings are noise individually; in bulk they
  signal hygiene problems.
- 0 per INFO — informational findings don't move the score.

The OWASP-coverage breadth term adds points for engagements that
land findings in many categories. Reasoning: an engagement that
finds problems in 8 OWASP categories has surfaced a broader risk
surface than one that finds problems in 2. The breadth term
captures that.

The governance bonus (-10 when ROE is clean) is a deliberate
adjustment. A clean engagement with the same findings represents
LESS organizational risk than a chaotic engagement with the same
findings, because the customer has the operational rigor to
remediate effectively.

## Score band interpretation

The 0-100 score maps to qualitative bands:

| Range | Band | Decision implication |
|---|---|---|
| 0-25 | Low | Continue current cadence; no special action |
| 26-50 | Moderate | Standard remediation planning |
| 51-75 | Elevated | Surface to security leadership; quarter-by-quarter tracking |
| 76-90 | High | Executive attention; structured remediation plan |
| 91-100 | Critical | Treat as incident; urgent remediation |

The bands were chosen to match how exec stakeholders naturally
discretize risk. Five bands beats three (too coarse) or ten (too
fine).

## Deterministic priority selection — why not human-curated

The top-3 priorities are picked algorithmically by severity +
reachability + alphabetical tie-break. Reproducibility wins over
nuance:

- Same findings → same top-3, always.
- The skill can be re-run after remediation to confirm priorities
  changed.
- Auditors and customers can verify the prioritization wasn't
  selectively edited to match a narrative.

The `--priority-overrides` flag exists for legitimate operator
intervention (e.g. "this hardcoded AWS key is the single biggest
risk regardless of count") but the default is algorithmic.

## CVSS vs DREAD vs STRIDE risk frameworks

Several risk-scoring frameworks compete:

| Framework | Used for | Strengths | Why not here |
|---|---|---|---|
| CVSS | Per-vulnerability scoring | Industry-standard, NVD-blessed | Per-vuln, not aggregate; no exec-summary primitive |
| DREAD | Threat-modeling risk | Captures Damage/Reproducibility/Exploitability/Affected users/Discoverability | Not pentest-natural; weights are subjective |
| STRIDE | Threat categorization | Maps to threat types | Categorical, not numeric |
| EPSS | Real-world exploitation likelihood | Predictive, data-driven | Per-CVE, not per-engagement |
| FAIR | Quantitative risk in dollars | Most precise | Expensive to compute; requires asset-value modeling |

The skill's risk score is a custom aggregate optimized for the
exec-summary use case. It's not a substitute for any of the
above; it composes with them.

## Effort + impact estimates

Each priority gets a rough effort (Hours / Days / Weeks) and
impact (Limited / Significant / Material) tag. These are
HEURISTIC and based on the source skill + reach. The skill
deliberately doesn't try to predict dollar impact or hour count —
those are owned by the customer's engineering team, not the
pentester.

Effort heuristics:

- Dependency upgrade — Hours to Days
- Hardcoded secret rotation — Hours
- Config / header fix — Days
- Injection / deserialization fix — Weeks (requires code changes)
- License compliance — Weeks (requires legal + dep swap)

Impact heuristics:

- CRITICAL severity → Material
- HIGH severity + reach ≥ 3 → Material
- HIGH severity + reach < 3 → Significant
- MEDIUM severity + reach ≥ 5 → Significant
- Otherwise → Limited

The customer's engineering team will refine these; the skill
provides starting estimates.

## Document length

Target: 1-2 pages when rendered as PDF. The skill's output is
typically 60-100 lines of markdown, which fits cleanly on 1-2
US Letter pages.

Longer = unread. Shorter = content-free. The sections (Risk
score, Engagement scope, Top priorities, OWASP coverage, Next
steps) are non-negotiable; everything else is compression
optimization.

## Stable rendering

Same findings + same ROE + same coverage → same exec summary
except for the generation date. This is important because the
exec summary may go to the board, to insurers, to auditors —
parties who will compare the document against any
re-rendered version.

If the summary changes between renderings without a finding
change, something is wrong. Sources of non-stability to avoid:

- Random tie-breaks (use alphabetical sort)
- LLM-based phrasing
- Time-stamped section content beyond the header date
- Counts that depend on the iteration order of dicts

The current implementation is stable. Future modifications must
preserve this.

## Format choices

- Markdown for portability and version-control friendliness.
- Numeric tables for severity counts (machine-parseable).
- Per-priority subsections rather than a single bullet list
  (gives each priority enough room to be acted on).
- Pointer to vulnerability-report.md anchors so the reader can
  jump to the deep detail when needed.

PDF rendering is downstream; the skill's output is the source
markdown that a separate pdf-generator (e.g. `/whiteglove-pdf`)
can render for handoff.
