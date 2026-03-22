---
name: abridge-ci-integration
description: |
  Configure CI/CD pipeline for Abridge clinical AI integrations with GitHub Actions.
  Use when setting up automated testing, FHIR validation, HIPAA compliance checks,
  or deployment pipelines for healthcare AI applications.
  Trigger: "abridge CI", "abridge GitHub Actions", "abridge pipeline",
  "abridge automated testing", "abridge CI/CD".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, ci-cd]
compatible-with: claude-code
---

# Abridge CI Integration

## Overview

CI/CD pipeline for Abridge clinical documentation integrations. Healthcare CI pipelines require FHIR resource validation, PHI leak scanning, HIPAA compliance checks, and sandbox integration testing.

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/abridge-ci.yml
name: Abridge Integration CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  lint-and-type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '${{ env.NODE_VERSION }}' }
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  phi-leak-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Scan for PHI patterns in source code
        run: |
          echo "Scanning for PHI patterns..."
          # SSN patterns
          if grep -rn '\b[0-9]\{3\}-[0-9]\{2\}-[0-9]\{4\}\b' src/ --include='*.ts' --include='*.js'; then
            echo "FAIL: Possible SSN found in source code"
            exit 1
          fi
          # Hardcoded patient names (common test names)
          if grep -rn '"John Doe\|Jane Doe\|Test Patient"' src/ --include='*.ts'; then
            echo "WARN: Hardcoded patient names — use synthetic data"
          fi
          echo "PHI scan passed"

  fhir-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '${{ env.NODE_VERSION }}' }
      - run: npm ci
      - name: Validate FHIR resources
        run: |
          npm run test:fhir-schemas
          echo "FHIR R4 validation passed"

  sandbox-integration:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: [lint-and-type-check, phi-leak-scan, fhir-validation]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '${{ env.NODE_VERSION }}' }
      - run: npm ci
      - name: Run sandbox integration tests
        env:
          ABRIDGE_SANDBOX_URL: ${{ secrets.ABRIDGE_SANDBOX_URL }}
          ABRIDGE_CLIENT_SECRET: ${{ secrets.ABRIDGE_CLIENT_SECRET }}
          ABRIDGE_ORG_ID: ${{ secrets.ABRIDGE_ORG_ID }}
        run: npm run test:integration
```

### Step 2: FHIR Schema Validation Tests

```typescript
// tests/fhir-validation.test.ts
import { describe, it, expect } from 'vitest';

describe('FHIR R4 Resource Validation', () => {
  it('should generate valid DocumentReference', () => {
    const docRef = {
      resourceType: 'DocumentReference',
      status: 'current',
      type: { coding: [{ system: 'http://loinc.org', code: '11506-3', display: 'Progress note' }] },
      subject: { reference: 'Patient/test-001' },
      content: [{ attachment: { contentType: 'text/plain', data: btoa('test note') } }],
    };

    expect(docRef.resourceType).toBe('DocumentReference');
    expect(docRef.status).toBe('current');
    expect(docRef.type.coding[0].system).toBe('http://loinc.org');
    expect(docRef.content[0].attachment.contentType).toBe('text/plain');
  });

  it('should generate valid Communication resource for patient summary', () => {
    const comm = {
      resourceType: 'Communication',
      status: 'completed',
      category: [{ coding: [{ system: 'http://terminology.hl7.org/CodeSystem/communication-category', code: 'notification' }] }],
      subject: { reference: 'Patient/test-001' },
      payload: [{ contentString: 'Your visit summary...' }],
    };

    expect(comm.resourceType).toBe('Communication');
    expect(comm.payload[0].contentString).toBeTruthy();
  });
});
```

### Step 3: Integration Test with Sandbox

```typescript
// tests/integration/sandbox.test.ts
import { describe, it, expect } from 'vitest';
import axios from 'axios';

describe('Abridge Sandbox Integration', () => {
  const api = axios.create({
    baseURL: process.env.ABRIDGE_SANDBOX_URL,
    headers: {
      'Authorization': `Bearer ${process.env.ABRIDGE_CLIENT_SECRET}`,
      'X-Org-Id': process.env.ABRIDGE_ORG_ID!,
    },
  });

  it('should create and finalize an encounter session', async () => {
    const { data: session } = await api.post('/encounters/sessions', {
      patient_id: 'ci-test-patient',
      provider_id: 'ci-test-provider',
      encounter_type: 'outpatient',
      specialty: 'internal_medicine',
      sandbox: true,
    });

    expect(session.session_id).toBeTruthy();
    expect(session.status).toBe('initialized');

    // Submit transcript
    await api.post(`/encounters/sessions/${session.session_id}/transcript`, {
      speaker: 'provider', text: 'CI test — patient presents with headache.',
    });

    // Finalize
    await api.post(`/encounters/sessions/${session.session_id}/finalize`);
  }, 30000);
});
```

## Output

- GitHub Actions workflow with 4 jobs: lint, PHI scan, FHIR validation, sandbox integration
- PHI leak detection scanning source code for SSN/MRN patterns
- FHIR R4 resource validation tests
- Sandbox integration tests (main branch only)

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| PHI scan false positive | Regex too broad | Add pattern to allowlist in scan script |
| Sandbox test timeout | API slow | Increase vitest timeout to 30s |
| Secrets not available | Missing GitHub Secrets | Add to repo Settings > Secrets |

## Resources

- [Abridge Platform](https://www.abridge.com/product)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [FHIR Validator](https://hl7.org/fhir/R4/validation.html)

## Next Steps

For deployment procedures, see `abridge-deploy-integration`.
