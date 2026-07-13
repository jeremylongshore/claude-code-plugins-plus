# PLAYBOOK — Audience Customizations and Delivery

## Per-audience customizations

### Board summary (default — quarterly board pack)

Risk score + top 3 priorities + OWASP coverage. The board reader
wants to know "should we be worried?" The exec summary as
emitted answers that.

```bash
python3 ./scripts/exec_summary.py engagements/acme-2026-q2/
```

### C-suite (CISO / CTO) summary

Same content as the board summary, but the C-suite reader may
want lengthier remediation discussion. After running the default
summary, the operator can edit the markdown directly to expand
specific sections. The skill's output is intentionally treated as
a draft for editorial expansion.

### Customer's security leadership summary

For the customer's own security leadership (Director of Security,
VP Engineering's security lead, etc.), the most useful expansion
is per-priority detail with cross-references to the vulnerability
report. The default output already includes the
`vulnerability-report.md#finding-XXX` cross-references — these
are clickable in most markdown viewers.

### External auditor / insurer summary

For external parties (SOC2 auditor, cyber-insurance carrier),
extend the default with engagement-archive integrity statement:

```markdown
## Archive integrity

The engagement's findings, evidence, and configuration are
archived at <path> with a SHA-256 manifest signed by <key id>.
Verification command:

`sha256sum -c manifest.sha256 && gpg --verify manifest.sha256.asc manifest.sha256`
```

Add this manually to the rendered summary before delivery.

## Summary length guidelines

| Use | Target length |
|---|---|
| Board summary | 1 page (~60 lines markdown) |
| C-suite summary | 1.5 pages (~80 lines markdown) |
| Customer security leadership | 2 pages (~120 lines markdown) |
| External auditor (with archive section) | 2 pages |

The skill emits ~80-100 lines by default. Pad or trim by editing
the rendered markdown.

## Common rewrite patterns

### "Soften the risk-score band wording"

Some customers find "Critical" / "High" risk-band language
alarming when the underlying findings are routine. The
risk-band labels are documented in THEORY.md; if your customer
relationship makes the words land badly, rewrite the band
description without changing the numeric score.

Don't change the score itself to fit the rewrite — the score
remains the canonical number; the descriptive band is the
audience-facing label.

### "Add a CFO-readable financial-impact section"

The skill doesn't compute financial impact (out of scope; too
many assumptions about asset value). For engagements that warrant
a CFO-readable section:

1. Work with the customer's finance lead to assign rough cost
   ranges to each top priority.
2. Append a "Financial impact estimates" section to the rendered
   summary with the agreed numbers.
3. Annotate clearly: "Cost estimates provided by customer; not
   computed from finding data."

### "Add a regulatory-impact narrative"

For engagements in regulated industries (HIPAA, PCI, SOC2), the
exec audience cares about regulatory exposure. Append a
"Regulatory impact" section that cross-references the top
findings against specific regulations:

```markdown
## Regulatory impact

The top finding "Hardcoded AWS key in source" triggers HIPAA
§164.308(a)(1)(ii)(B) (Risk Management) reporting obligation.
Remediation timing should align with the breach-notification
window if data has been exposed.
```

Don't include this section by default; add it when the engagement
has specific regulatory framing.

## Integration with the composing + mapping skills

The exec-summary skill consumes:

1. **Unified findings JSONL** (from `composing-vulnerability-report`
   OR `mapping-findings-to-owasp-top10`)
2. **OWASP coverage report** (from `mapping-findings-to-owasp-top10`)
3. **ROE YAML** (from the engagement repository)

Run order:

```bash
# 1. (Optional) Compose to produce the main vulnerability report first
python3 plugins/security/penetration-tester/skills/composing-vulnerability-report/scripts/compose_report.py \
    engagements/acme-2026-q2/

# 2. Map to OWASP, producing the enriched JSONL and coverage report
python3 plugins/security/penetration-tester/skills/mapping-findings-to-owasp-top10/scripts/map_owasp.py \
    engagements/acme-2026-q2/

# 3. Generate the exec summary
python3 ./scripts/exec_summary.py engagements/acme-2026-q2/
```

## Post-delivery follow-up cadence

The exec summary's "Suggested next steps" section starts a
remediation cadence. The pentester's role typically:

1. **End-of-engagement** (week 0): deliver the summary + report.
2. **Week 2**: optional check-in with the customer's security
   lead to confirm remediation has been prioritized.
3. **Week 6**: confirm the top priorities have been addressed.
4. **Week 12**: re-test the top priorities to verify the fixes
   hold. The re-test produces a follow-up summary using the same
   skill against the same engagement directory.

Re-tests should produce a LOWER risk score after remediation. If
the score doesn't drop, either the fixes didn't take effect or
new findings emerged in the re-test scan.

## Sample delivery package

The standard engagement closeout package contains:

```
engagements/archives/acme-2026-q2.tar.gz
├── engagement directory contents
├── manifest.sha256                  # SHA-256 of every file
├── manifest.sha256.asc              # GPG signature
└── reports/
    ├── vulnerability-report.md      # full technical detail
    ├── owasp-coverage.md            # OWASP Top 10 breakdown
    └── executive-summary.md         # this skill's output
```

Plus separately:

- The exec summary as a standalone PDF (via `/whiteglove-pdf`).
- A receipt-signed copy of the archive's manifest.

## Risk-score auditability

If a customer or third party questions the risk score, the
auditable response:

1. Show the score-composition formula from THEORY.md.
2. Show the severity counts that fed the formula.
3. Show the OWASP-breadth count.
4. Show the governance-bonus determination.
5. Demonstrate that re-running the skill produces the same score.

The skill is deterministic by design so this audit is always
possible.

## When the score and the findings disagree intuitively

Occasionally the algorithmic score doesn't match the operator's
gut feeling — usually because:

- A single very high-impact finding doesn't dominate enough
  (the formula adds rather than maxing).
- Numerous low-severity findings produce a higher score than the
  operator expected.
- The OWASP-breadth bonus elevates an otherwise-modest engagement.

Operator can:

- Document the divergence in the summary's "Suggested next steps"
  section.
- Use `--priority-overrides` to set top-3 priorities that match
  intuition.
- Refrain from re-engineering the formula for one engagement;
  consistency across engagements is the formula's value
  proposition.
