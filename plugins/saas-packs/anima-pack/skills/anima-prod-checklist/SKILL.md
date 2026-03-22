---
name: anima-prod-checklist
description: |
  Production readiness checklist for Anima design-to-code pipelines.
  Use when deploying automated design-to-code services, preparing CI/CD
  Figma-to-code automation, or validating output quality before production.
  Trigger: "anima production", "anima go-live", "anima prod checklist".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, production]
compatible-with: claude-code
---

# Anima Production Checklist

## Pre-Launch Checklist

### Credentials & Access
- [ ] Anima API token stored in secret manager
- [ ] Figma PAT has read-only scope with expiration
- [ ] Separate tokens for dev/staging/prod environments
- [ ] Token rotation schedule documented

### Code Quality
- [ ] Generated code passes ESLint/Prettier
- [ ] Generated components render correctly in target framework
- [ ] Design tokens mapped to project design system
- [ ] Output normalization rules configured and tested

### Pipeline
- [ ] Rate limiting configured (10 gen/min standard tier)
- [ ] Error handling with retry for transient failures
- [ ] Generation cache to avoid redundant API calls
- [ ] Figma change detection working (version polling)

### Validation Script

```typescript
// scripts/anima-readiness.ts
async function checkReadiness() {
  const checks = [];

  // Figma access
  try {
    const res = await fetch('https://api.figma.com/v1/me', {
      headers: { 'X-Figma-Token': process.env.FIGMA_TOKEN! },
    });
    checks.push({ name: 'Figma Access', pass: res.ok, detail: res.ok ? 'Authenticated' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Figma Access', pass: false, detail: e.message }); }

  // Anima SDK
  try {
    const { Anima } = await import('@animaapp/anima-sdk');
    new Anima({ auth: { token: process.env.ANIMA_TOKEN! } });
    checks.push({ name: 'Anima SDK', pass: true, detail: 'Initialized' });
  } catch (e: any) { checks.push({ name: 'Anima SDK', pass: false, detail: e.message }); }

  // Token not in build
  const buildFiles = require('fs').existsSync('./dist');
  if (buildFiles) {
    const content = require('fs').readFileSync('./dist', 'utf8');
    const leaked = content.includes(process.env.ANIMA_TOKEN || '');
    checks.push({ name: 'Token Safety', pass: !leaked, detail: leaked ? 'TOKEN IN BUILD!' : 'Safe' });
  }

  for (const c of checks) {
    console.log(`[${c.pass ? 'PASS' : 'FAIL'}] ${c.name}: ${c.detail}`);
  }
}

checkReadiness();
```

## Output

- Readiness validation script
- All checklist items verified
- Token safety confirmed

## Resources

- [Anima API](https://docs.animaapp.com/docs/anima-api)

## Next Steps

For version upgrades, see `anima-upgrade-migration`.
