---
name: coreweave-ci-integration
description: |
  Integrate CoreWeave deployments into CI/CD pipelines with GitHub Actions.
  Use when automating container builds, deploying inference services from CI,
  or validating GPU manifests in pull requests.
  Trigger with phrases like "coreweave CI", "coreweave github actions",
  "coreweave pipeline", "automate coreweave deploy".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave CI Integration

## Overview

Set up CI/CD for CoreWeave GPU cloud workloads: run unit tests with mocked Kubernetes clients on every PR, deploy inference containers to CoreWeave namespaces on merge to main, and validate GPU resource requests against quota. CoreWeave uses standard Kubernetes APIs with GPU-specific scheduling, so CI pipelines authenticate via kubeconfig and manage deployments through `kubectl`.

## GitHub Actions Workflow

```yaml
# .github/workflows/coreweave-ci.yml
name: CoreWeave CI
on:
  pull_request:
    paths: ['src/**', 'k8s/**', 'Dockerfile']
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
      - name: Build and push container
        run: |
          echo "${{ secrets.GHCR_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker build -t ghcr.io/${{ github.repository }}/inference:${{ github.sha }} .
          docker push ghcr.io/${{ github.repository }}/inference:${{ github.sha }}
      - name: Deploy to CoreWeave
        env:
          KUBECONFIG_DATA: ${{ secrets.COREWEAVE_KUBECONFIG }}
        run: |
          echo "$KUBECONFIG_DATA" | base64 -d > /tmp/kubeconfig
          export KUBECONFIG=/tmp/kubeconfig
          kubectl set image deployment/inference \
            inference=ghcr.io/${{ github.repository }}/inference:${{ github.sha }}
          kubectl rollout status deployment/inference --timeout=300s
```

## Mock-Based Unit Tests

```typescript
// tests/coreweave-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { deployInferenceModel } from '../src/coreweave-service';

vi.mock('@kubernetes/client-node', () => ({
  KubeConfig: vi.fn().mockImplementation(() => ({
    loadFromDefault: vi.fn(),
    makeApiClient: vi.fn().mockReturnValue({
      patchNamespacedDeployment: vi.fn().mockResolvedValue({ body: { status: { readyReplicas: 1 } } }),
      listNamespacedPod: vi.fn().mockResolvedValue({
        body: { items: [{ metadata: { name: 'inference-abc' }, status: { phase: 'Running' } }] },
      }),
    }),
  })),
  AppsV1Api: vi.fn(),
}));

describe('CoreWeave Service', () => {
  it('deploys inference model with GPU requests', async () => {
    const result = await deployInferenceModel('llama-70b', { gpu: 'A100', count: 4 });
    expect(result.status).toBe('deployed');
    expect(result.gpuType).toBe('A100');
  });
});
```

## Integration Tests

```typescript
// tests/integration/coreweave.integration.test.ts
import { describe, it, expect } from 'vitest';
import { KubeConfig, CoreV1Api } from '@kubernetes/client-node';

const hasKubeconfig = !!process.env.COREWEAVE_KUBECONFIG;

describe.skipIf(!hasKubeconfig)('CoreWeave Live API', () => {
  it('lists GPU nodes in namespace', async () => {
    const kc = new KubeConfig();
    kc.loadFromString(Buffer.from(process.env.COREWEAVE_KUBECONFIG!, 'base64').toString());
    const k8sApi = kc.makeApiClient(CoreV1Api);
    const { body } = await k8sApi.listNamespacedPod('default');
    expect(Array.isArray(body.items)).toBe(true);
  });
});
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| `KUBECONFIG_DATA` empty | Secret not set | Run `gh secret set COREWEAVE_KUBECONFIG --body "$(base64 -w0 kubeconfig)"` |
| Rollout timeout | GPU nodes unavailable | Increase `--timeout` or check CoreWeave GPU availability dashboard |
| Image pull backoff | GHCR auth expired | Verify `GHCR_TOKEN` secret and image registry permissions |
| Quota exceeded | GPU request exceeds namespace limit | Check namespace quota with `kubectl describe quota` |
| Pod pending | No matching GPU node type | Verify `nodeSelector` matches available GPU SKUs (A100, H100) |

## Resources

- [CoreWeave Kubernetes Docs](https://docs.coreweave.com/coreweave-kubernetes/)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

For deployment patterns, see `coreweave-deploy-integration`.
