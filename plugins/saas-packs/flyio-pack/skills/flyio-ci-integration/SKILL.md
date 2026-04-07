---
name: flyio-ci-integration
description: |
  Configure CI/CD pipelines for Fly.io with GitHub Actions, Docker builds,
  deploy tokens, and automated deployment workflows.
  Trigger: "fly.io CI", "fly.io GitHub Actions", "fly deploy CI/CD".
allowed-tools: Read, Write, Edit, Bash(fly:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io CI Integration

## Overview

Set up CI/CD for Fly.io edge deployments: run unit tests on every PR, deploy to staging on pull requests, and promote to production on merge to main. Fly.io uses Machines API for app management and deploy tokens for scoped CI authentication. CI pipelines build Docker images, deploy via `flyctl`, and run post-deploy health checks against the edge endpoints.

## GitHub Actions Workflow

```yaml
# .github/workflows/fly-ci.yml
name: Fly.io CI
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm test -- --reporter=verbose

  deploy:
    if: github.ref == 'refs/heads/main'
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: fly deploy --ha=false
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
      - name: Health check
        run: |
          sleep 10
          curl -sf https://my-app.fly.dev/health || exit 1
```

## Mock-Based Unit Tests

```typescript
// tests/fly-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { scaleApp } from '../src/fly-service';

vi.mock('../src/fly-client', () => ({
  FlyClient: vi.fn().mockImplementation(() => ({
    listMachines: vi.fn().mockResolvedValue([
      { id: 'mch_abc', state: 'started', region: 'iad', config: { size: 'shared-cpu-1x' } },
      { id: 'mch_def', state: 'started', region: 'lhr', config: { size: 'shared-cpu-1x' } },
    ]),
    scaleMachine: vi.fn().mockResolvedValue({ id: 'mch_abc', state: 'started' }),
    getApp: vi.fn().mockResolvedValue({ name: 'my-app', status: 'deployed', hostname: 'my-app.fly.dev' }),
  })),
}));

describe('Fly.io Service', () => {
  it('scales app machines across regions', async () => {
    const result = await scaleApp('my-app', { count: 3 });
    expect(result.machines).toBeDefined();
    expect(result.status).toBe('scaled');
  });
});
```

## Integration Tests

```typescript
// tests/integration/fly.integration.test.ts
import { describe, it, expect } from 'vitest';

const hasToken = !!process.env.FLY_API_TOKEN;

describe.skipIf(!hasToken)('Fly.io Live API', () => {
  it('lists apps via Machines API', async () => {
    const res = await fetch('https://api.machines.dev/v1/apps', {
      headers: { Authorization: `Bearer ${process.env.FLY_API_TOKEN}` },
    });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty('apps');
  });
});
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| `FLY_API_TOKEN` invalid | Token expired or revoked | Regenerate with `fly tokens create deploy -a my-app` |
| Deploy timeout | Image build too slow | Add Docker layer caching with `--build-cache` |
| Health check fails | App not ready after deploy | Increase sleep or use `fly status --wait` |
| Machine stuck in `replacing` | Rolling deploy conflict | Run `fly machines list` and destroy orphaned machines |
| Region unavailable | Edge region at capacity | Set `primary_region` in `fly.toml` to a different region |

## Resources

- [Fly.io GitHub Actions](https://fly.io/docs/launch/continuous-deployment/github-actions/)
- [Fly.io Machines API](https://fly.io/docs/machines/api/)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

For deployment strategies, see `flyio-deploy-integration`.
