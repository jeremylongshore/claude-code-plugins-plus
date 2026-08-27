---
name: anima-prod-checklist
description: 'Production readiness checklist for Anima design-to-code pipelines.

  Use when deploying automated design-to-code services, preparing CI/CD

  Figma-to-code automation, or validating output quality before production.

  Trigger: "anima production", "anima go-live", "anima prod checklist".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.4.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- design
- figma
- anima
- production
compatibility: Designed for Claude Code
---
# Anima Production Checklist

## Overview

Anima converts Figma designs into production-ready code for React, Vue, and HTML. A failed design-to-code pipeline means engineers receive broken components, mismatched tokens, or stale screens that drift from the source of truth. This checklist ensures your Anima integration produces reliable, framework-compliant output before it reaches CI/CD.

## Prerequisites

- Named design, engineering, security, and operations owners who can make a
  go/no-go decision and own the rollback path.
- A staging environment using separate managed Anima/Figma credentials, an
  allowlisted design registry, and a reproducible generated-code fixture.
- Defined output quality gates: source-version traceability, lint/type/build,
  visual/accessibility review, and no secrets in artifacts or logs.

## Instructions

1. Assign an owner and evidence link to every required checklist item.
2. Run the readiness script with the deployment identity in staging and retain
   only its redacted result.
3. Exercise a generation and rollback/disable path with an approved design
   component, then verify downstream code-quality and visual gates.
4. Approve progressive release only when all required checks pass; any failed
   security, credential, output, or fallback control is a no-go condition.

## Authentication & Secrets

- [ ] `ANIMA_API_KEY` stored in secrets manager (never in source)
- [ ] Figma personal access token scoped to read-only with expiration
- [ ] Separate API keys for dev/staging/prod environments
- [ ] Key rotation schedule documented (90-day cycle recommended)
- [ ] Tokens excluded from client bundles and build artifacts

## API Integration

- [ ] Production base URL configured (`https://api.animaapp.com`)
- [ ] Rate limit handling for standard tier (10 generations/min)
- [ ] Generation cache prevents redundant API calls for unchanged screens
- [ ] Figma file version polling detects design changes automatically
- [ ] Webhook or polling configured for async generation completion
- [ ] Component mapping rules tested for target framework (React/Vue/HTML)

## Error Handling & Resilience

- [ ] Circuit breaker configured for Anima API outages
- [ ] Retry with exponential backoff for 429/5xx responses
- [ ] Graceful fallback when Figma PAT expires mid-pipeline
- [ ] Generated code validated against ESLint/Prettier before merge
- [ ] Design token mismatches flagged before component output
- [ ] Empty generation results handled (missing layers, unsupported elements)

## Monitoring & Alerting

- [ ] API latency tracked per generation request
- [ ] Error rate alerts set (threshold: >5% over 5 minutes)
- [ ] Generation quality score monitored (component render pass rate)
- [ ] Figma sync failures trigger immediate notification
- [ ] Daily digest of generation counts and token usage

## Validation Script

```typescript
async function checkAnimaReadiness(): Promise<void> {
  const checks: { name: string; pass: boolean; detail: string }[] = [];
  // Verify Anima API connectivity
  try {
    const res = await fetch('https://api.animaapp.com/v1/projects', {
      headers: { Authorization: `Bearer ${process.env.ANIMA_API_KEY}` },
    });
    checks.push({ name: 'Anima API', pass: res.ok, detail: res.ok ? 'Connected' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Anima API', pass: false, detail: e.message }); }
  // Verify Figma access
  try {
    const res = await fetch('https://api.figma.com/v1/me', {
      headers: { 'X-Figma-Token': process.env.FIGMA_TOKEN! },
    });
    checks.push({ name: 'Figma Access', pass: res.ok, detail: res.ok ? 'Authenticated' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Figma Access', pass: false, detail: e.message }); }
  // Token leak check
  const fs = await import('fs');
  if (fs.existsSync('./dist')) {
    const content = fs.readdirSync('./dist').map(f => fs.readFileSync(`./dist/${f}`, 'utf8')).join('');
    const leaked = content.includes(process.env.ANIMA_API_KEY || '');
    checks.push({ name: 'Token Safety', pass: !leaked, detail: leaked ? 'KEY IN BUILD!' : 'Clean' });
  }
  for (const c of checks) console.log(`[${c.pass ? 'PASS' : 'FAIL'}] ${c.name}: ${c.detail}`);
}
checkAnimaReadiness();
```

## Error Handling

| Check | Risk if Skipped | Priority |
|-------|----------------|----------|
| API key rotation | Expired keys break entire pipeline | P1 |
| Figma token expiry | Silent sync failure, stale designs | P1 |
| Generation rate limits | 429 errors drop design updates | P2 |
| Component render validation | Broken UI shipped to production | P2 |
| Design token mapping | Visual inconsistencies across app | P3 |

## Output

- Signed-off go/no-go record with owners and redacted readiness evidence
- Verified secret, provider, and Figma access boundaries
- Generated-component validation and source-version traceability receipts
- Tested rollback or generation-disable path for production incidents

## Examples

For a production rehearsal, generate one allowlisted staging component using
the production-shaped secret binding, run the readiness script, and send the
result through lint, type checking, visual review, and the release approval
workflow. Record the Figma version, generated artifact digest, deploy revision,
and rollback owner. If token safety fails, a quality gate is red, or the design
source cannot be traced, declare a no-go, disable generation, and correct the
failed control before rerunning the full checklist.

## Resources

- [Anima API Docs](https://docs.animaapp.com/docs/anima-api)
- [Anima Status](https://status.animaapp.com)

## Next Steps

See `anima-security-basics` for secret management and access control patterns.
