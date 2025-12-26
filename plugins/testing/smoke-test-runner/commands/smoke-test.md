---
name: smoke-test
description: Run quick smoke tests to verify critical functionality
shortcut: st
---
# Smoke Test Runner

Fast, focused smoke tests to verify critical application functionality after deployments. Tests the most important user flows to ensure the system is operational.

## What You Do

1. **Identify Critical Paths**
   - Determine must-work functionality
   - Map critical user journeys
   - Prioritize high-value features

2. **Generate Smoke Tests**
   - Create fast, focused tests (<5min total)
   - Cover authentication, core features, integrations
   - Include health checks and basic assertions

3. **Post-Deployment Validation**
   - Run immediately after deployment
   - Verify environment configuration
   - Test external service connectivity

4. **Report Results**
   - Fast pass/fail indication
   - Clear failure diagnostics
   - Rollback recommendations if failing

## Output Format

```markdown
## Smoke Test Suite

### Critical Paths: [N]
**Total Duration:** <5 minutes
**Environment:** [production/staging]

### Test Suite

\`\`\`javascript
// smoke-tests/critical-path.test.js
describe('Smoke Tests - Critical Path', () => {
  const timeout = 30000; // 30s max per test

  describe('System Health', () => {
    it('API is responding', async () => {
      const response = await fetch('https://api.example.com/health');
      expect(response.status).toBe(200);
    }, timeout);

    it('Database is accessible', async () => {
      const result = await db.query('SELECT 1');
      expect(result).toBeDefined();
    }, timeout);

    it('Cache is working', async () => {
      await redis.set('smoke:test', 'ok');
      const value = await redis.get('smoke:test');
      expect(value).toBe('ok');
    }, timeout);
  });

  describe('Authentication', () => {
    it('User can login', async () => {
      const response = await request(app)
        .post('/api/auth/login')
        .send({ email: '[email protected]', password: 'test123' });

      expect(response.status).toBe(200);
      expect(response.body.token).toBeDefined();
    }, timeout);

    it('Protected routes require authentication', async () => {
      const response = await request(app)
        .get('/api/user/profile');

      expect(response.status).toBe(401);
    }, timeout);
  });

  describe('Core Features', () => {
    it('Homepage loads', async () => {
      const response = await fetch('https://example.com');
      expect(response.status).toBe(200);
      expect(await response.text()).toContain('<title>');
    }, timeout);

    it('Search returns results', async () => {
      const response = await request(app)
        .get('/api/search?q=test');

      expect(response.status).toBe(200);
      expect(response.body.results).toBeDefined();
    }, timeout);

    it('Create operation works', async () => {
      const response = await authenticatedRequest
        .post('/api/items')
        .send({ name: 'Smoke Test Item' });

      expect(response.status).toBe(201);
      expect(response.body.id).toBeDefined();
    }, timeout);
  });

  describe('External Integrations', () => {
    it('Payment gateway is reachable', async () => {
      const response = await stripe.paymentMethods.list({ limit: 1 });
      expect(response).toBeDefined();
    }, timeout);

    it('Email service is configured', async () => {
      // Just verify config, don't send actual email
      expect(process.env.SMTP_HOST).toBeDefined();
      expect(process.env.SMTP_PORT).toBeDefined();
    }, timeout);

    it('Storage is accessible', async () => {
      const buckets = await s3.listBuckets();
      expect(buckets.Buckets.length).toBeGreaterThan(0);
    }, timeout);
  });

  describe('Configuration', () => {
    it('Environment variables are set', () => {
      expect(process.env.NODE_ENV).toBeDefined();
      expect(process.env.DATABASE_URL).toBeDefined();
      expect(process.env.API_KEY).toBeDefined();
    });

    it('Feature flags are loaded', async () => {
      const flags = await featureFlags.getAll();
      expect(flags).toBeDefined();
      expect(flags.newFeature).toBe(false); // Verify expected state
    });
  });
});
\`\`\`

### Execution

\`\`\`bash
# Run smoke tests
npm run test:smoke

# Post-deployment hook
\`\`\`yaml
# .github/workflows/deploy.yml
- name: Run Smoke Tests
  run: npm run test:smoke
  if: success()

- name: Rollback on Failure
  run: ./scripts/rollback.sh
  if: failure()
\`\`\`

### Results

\`\`\`
Smoke Tests - Critical Path
  System Health
     API is responding (245ms)
     Database is accessible (189ms)
     Cache is working (56ms)

  Authentication
     User can login (432ms)
     Protected routes require authentication (123ms)

  Core Features
     Homepage loads (567ms)
     Search returns results (289ms)
     Create operation works (345ms)

  External Integrations
     Payment gateway is reachable (678ms)
     Email service is configured (12ms)
     Storage is accessible (234ms)

  Configuration
     Environment variables are set (8ms)
     Feature flags are loaded (91ms)

Total: 13 tests passing in 3.27s
\`\`\`

### Smoke Test Matrix

| Category | Tests | Status | Duration |
|----------|-------|--------|----------|
| System Health | 3 |  Pass | 0.49s |
| Authentication | 2 |  Pass | 0.56s |
| Core Features | 3 |  Pass | 1.20s |
| Integrations | 3 |  Pass | 0.92s |
| Configuration | 2 |  Pass | 0.10s |

**Total:** 3.27s  All critical paths operational

### Recommendations
 Deployment successful - all critical paths working
- Monitor error rates for next 30 minutes
- Watch for performance degradation
```

## Best Practices

- Keep total runtime under 5 minutes
- Test only critical, must-work functionality
- Run after every deployment
- Fail fast - stop on first critical failure
- Use real production-like data
- Test actual external services (not mocks)
