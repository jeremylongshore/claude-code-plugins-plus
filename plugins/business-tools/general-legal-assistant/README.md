# General Legal Assistant

AI-powered contract review, risk analysis, document generation, and compliance auditing. 12 skills, 5 parallel agents.

## Skills

### Contract Analysis

| Skill | What It Does |
|-------|-------------|
| `contract-review` | **Flagship** — Full review with 5 parallel agents. Contract Safety Score (0-100), clause-by-clause analysis, prioritized recommendations. |
| `risk-analysis` | Clause-by-clause risk scoring (1-10) with financial exposure estimates and poison pill detection. |
| `contract-compare` | Side-by-side version comparison. Flags additions, removals, and dangerous changes. |
| `plain-english` | Translates legalese into plain English at an 8th-grade reading level. Flags deliberately confusing language. |
| `missing-protections` | Finds protections that should be in the contract but aren't. Ready-to-insert clause language. |
| `freelancer-review` | Reviews contracts from the freelancer's perspective. IRS 20-Factor Test for misclassification. |
| `negotiate` | Generates counter-proposals with replacement language and a negotiation email template. |

### Document Generation

| Skill | What It Does |
|-------|-------------|
| `nda-generator` | Generates custom NDAs — mutual, one-way, employee, or vendor. |
| `terms-generator` | Generates Terms of Service by analyzing what a website actually does. |
| `privacy-generator` | Generates a privacy policy by detecting data collection practices. GDPR/CCPA compliant. |
| `agreement-generator` | Generates business agreements — freelancer contracts, partnerships, SOWs, MSAs, and more. |

### Compliance

| Skill | What It Does |
|-------|-------------|
| `compliance-audit` | Gap analysis across GDPR, CCPA, ADA/WCAG, PCI-DSS, CAN-SPAM, COPPA, SOC 2. |

## Agents

The `contract-review` skill spawns 5 specialized agents in parallel:

| Agent | Role | Weight |
|-------|------|--------|
| `legal-clauses` | Clause extraction and categorization | 20% |
| `legal-risks` | Risk scoring and threat identification | 25% |
| `legal-compliance` | Regulatory compliance verification | 20% |
| `legal-obligations` | Obligation mapping and financial exposure | 15% |
| `legal-recommendations` | Recommendations and negotiation strategy | 20% |

## Install

```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
```

Or via CLI:

```bash
ccpi install legal-assistant
```

## Authoritative Sources Referenced

| Source | Authority | License |
|--------|-----------|---------|
| [CommonPaper](https://commonpaper.com/standards/) | 40+ attorneys, standard commercial contracts | CC BY 4.0 |
| [Bonterms](https://github.com/Bonterms/Cloud-Terms) | Enterprise cloud terms by practicing attorneys | CC BY 4.0 |
| [ICO Privacy Generator](https://ico.org.uk/create-your-own-privacy-notice) | UK statutory regulator (GDPR) | Crown copyright |
| [CA Attorney General](https://oag.ca.gov/privacy/ccpa) | CCPA enforcement body | Public domain |
| [FTC Compliance Guides](https://www.ftc.gov/business-guidance) | US federal regulator | Public domain |
| [SCORE / SBA](https://www.score.org) | US government-backed NDA templates | Free |
| [IRS 20-Factor Test](https://www.irs.gov/businesses/small-businesses-self-employed) | Contractor classification | Public domain |
| [W3C WCAG 2.1](https://www.w3.org/WAI/standards-guidelines/wcag/) | Accessibility standards | W3C |
| [PCI Security Standards](https://www.pcisecuritystandards.org/) | Payment security | Free reference |

## Disclaimer

This plugin provides AI-assisted legal analysis and document drafting. It does not constitute legal advice. Generated documents are drafts that should be reviewed by a qualified attorney before use. No attorney-client relationship is created by using this tool.

## License

MIT
