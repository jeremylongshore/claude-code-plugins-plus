# Fondo Skill Pack

> 18 production-ready Claude Code skills for Fondo startup bookkeeping, R&D tax credits, and financial operations -- real workflows with actual provider integrations.

## What This Is

A complete skill pack for managing startup finances with Fondo. Every skill covers real Fondo workflows: connecting Gusto/QuickBooks/Plaid integrations, monthly bookkeeping close, R&D tax credit claims (Form 6765), and financial reporting. Includes code for building internal dashboards using data from shared providers (Stripe, Gusto API).

## Installation

```bash
/plugin install fondo-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `fondo-install-auth` | Connect Gusto, QuickBooks, Plaid, Stripe, and bank accounts |
| S02 | `fondo-hello-world` | Verify bank sync, review auto-categorization, check R&D eligibility |
| S03 | `fondo-local-dev-loop` | Parse Fondo CSV exports, build burn rate calculator |
| S04 | `fondo-sdk-patterns` | Gusto API, QuickBooks API, Zod-typed CSV parsers |
| S05 | `fondo-core-workflow-a` | Monthly bookkeeping close timeline, financial statements, metrics |
| S06 | `fondo-core-workflow-b` | R&D tax credit workflow, Form 6765, payroll tax offset |
| S07 | `fondo-common-errors` | Sync failures, categorization errors, R&D qualification issues |
| S08 | `fondo-debug-bundle` | Diagnostic checklist for support tickets |
| S09 | `fondo-rate-limits` | Provider API limits (Gusto, QuickBooks, Stripe, Plaid) |
| S10 | `fondo-security-basics` | OAuth management, financial data protection, access control |
| S11 | `fondo-prod-checklist` | Year-end tax filing readiness, key deadlines |
| S12 | `fondo-upgrade-migration` | Migrate from other bookkeeping services, plan upgrades |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `fondo-ci-integration` | Budget alert pipelines, burn rate monitoring |
| P14 | `fondo-deploy-integration` | Deploy internal finance dashboards |
| P15 | `fondo-webhooks-events` | Stripe/Gusto/Plaid webhooks for financial event processing |
| P16 | `fondo-performance-tuning` | Faster month-end close, auto-categorization rules |
| P17 | `fondo-cost-tuning` | Maximize R&D credits, plan selection, ROI analysis |
| P18 | `fondo-reference-architecture` | Full startup finance stack architecture |

## Key Fondo Concepts

- **TaxPass**: Bundled bookkeeping + tax filing + R&D credits
- **R&D Tax Credits**: Up to $500K/year payroll tax offset for qualifying startups
- **Monthly Close**: Fondo CPA team handles reconciliation, you answer questions
- **Integrations**: OAuth connections to Gusto, QuickBooks, Plaid, Stripe, Brex
- **Form 6765**: IRS form for claiming research and development tax credits

## License

MIT
