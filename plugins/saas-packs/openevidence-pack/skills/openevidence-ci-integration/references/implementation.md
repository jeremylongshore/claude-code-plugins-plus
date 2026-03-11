# OpenEvidence CI Integration - Implementation Details

## GitHub Actions Workflow
Full CI pipeline with lint-and-typecheck, unit-tests (with coverage), integration-tests (sandbox API), and clinical-validation jobs.

## Test Configuration
```typescript
// vitest.config.integration.ts
export default mergeConfig(baseConfig, defineConfig({
  test: {
    include: ['tests/integration/**/*.test.ts'],
    testTimeout: 60000,
    retry: 2,
    maxConcurrency: 1, // Avoid rate limits
  },
}));
```

## Unit Tests with Mocks
```typescript
vi.mock('@openevidence/sdk', () => ({
  OpenEvidenceClient: vi.fn().mockImplementation(() => ({
    query: vi.fn().mockResolvedValue({
      id: 'test-query-123',
      answer: 'Mock clinical answer.',
      citations: [{ source: 'Test Journal', title: 'Test Article', year: 2025 }],
      confidence: 0.95,
    }),
  })),
}));
```

## Integration Tests
```typescript
describe('OpenEvidence API Integration', () => {
  beforeAll(() => {
    if (!process.env.OPENEVIDENCE_BASE_URL?.includes('sandbox')) {
      throw new Error('Integration tests must use sandbox environment');
    }
  });

  it('should successfully query clinical evidence', async () => {
    const response = await client.query({ question: 'What is the half-life of aspirin?', context: { specialty: 'pharmacology', urgency: 'routine' } });
    expect(response.answer.length).toBeGreaterThan(50);
    expect(response.citations.length).toBeGreaterThan(0);
  }, 30000);
});
```

## Clinical Validation Tests
Known-answer test cases with expectedKeywords and mustNotContain patterns, generating JSON validation reports for compliance review.

## Package.json Scripts
```json
{
  "scripts": {
    "test:unit": "vitest run -c vitest.config.ts",
    "test:integration": "vitest run -c vitest.config.integration.ts",
    "test:clinical-validation": "vitest run tests/clinical-validation"
  }
}
```
