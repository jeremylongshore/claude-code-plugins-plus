# Security Status – Automations Setup

Date: 2025-10-15

Before: 1 Dependabot alert (0 High/Critical), 33 CodeQL alerts (no High/Critical)
After: 1 Dependabot alert (awaiting bot PR), CodeQL workflows enabled and passing; no secret scanning alerts.

Actions in this PR:
- Enabled Dependabot (npm, GitHub Actions)
- Enabled CodeQL default analysis (push, PR, weekly)
- Added weekly security audit sweep workflow
- Added auto-merge for Dependabot minor updates
- Augmented PR template with security checks
- Set repository watch level to Participating/@mentions (for the current account)
- Enabled secret scanning & push protection (where available)
- Prepared branch protection to require PR + checks

Next steps:
- Approve Dependabot PRs; they will auto-merge after green checks
- Dismiss low-severity CodeQL notes with justification if noisy
- Rotate any credentials if future secret alerts appear

