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

## GitHub Actions Workflow

```yaml
name: CoreWeave Deploy
on:
  push:
    branches: [main]
    paths: ["k8s/**", "Dockerfile"]

jobs:
  build-deploy:
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

      - name: Validate deployment
        run: |
          export KUBECONFIG=/tmp/kubeconfig
          kubectl get pods -l app=inference
```

```bash
# Store secrets
gh secret set COREWEAVE_KUBECONFIG --body "$(base64 -w0 ~/.kube/coreweave)"
gh secret set GHCR_TOKEN --body "$GITHUB_TOKEN"
```

## Resources

- [GitHub Actions](https://docs.github.com/en/actions)

## Next Steps

For deployment patterns, see `coreweave-deploy-integration`.
