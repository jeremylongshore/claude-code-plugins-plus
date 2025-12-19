---
description: Use when validating GitHub Actions workflows for Google Cloud and Vertex AI deployments. Trigger with phrases like "validate github actions", "setup workload identity federation", "github actions security", "deploy agent with ci/cd", or "automate vertex ai deployment". Enforces Workload Identity Federation (WIF), validates OIDC permissions, ensures least privilege IAM, and implements security best practices.
allowed-tools:
- Read
- Write
- Edit
- Grep
- Glob
- Bash(git:*)
- Bash(gcloud:*)
name: gh-actions-validator
license: MIT
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

## Prerequisites

Before using this skill, ensure:
- GitHub repository with Actions enabled
- Google Cloud project with billing enabled
- gcloud CLI authenticated with admin permissions
- Understanding of Workload Identity Federation concepts
- GitHub repository secrets configured
- Appropriate IAM roles for CI/CD automation

## Instructions

1. **Audit Existing Workflows**: Scan .github/workflows/ for security issues
2. **Validate WIF Usage**: Ensure no JSON service account keys are used
3. **Check OIDC Permissions**: Verify id-token: write is present
4. **Review IAM Roles**: Confirm least privilege (no owner/editor roles)
5. **Add Security Scans**: Include secret detection and vulnerability scanning
6. **Validate Deployments**: Add post-deployment health checks
7. **Configure Monitoring**: Set up alerts for deployment failures
8. **Document WIF Setup**: Provide one-time WIF configuration commands

## Output

**Secure Workflow Template:**
```yaml
# {baseDir}/.github/workflows/deploy-vertex-ai.yml
name: Deploy Vertex AI Agent

on:
  push:
    branches: [main]
    paths: ['agent/**']

permissions:
  contents: read
  id-token: write  # REQUIRED for WIF

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to GCP (WIF)
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Deploy to Vertex AI
        run: |
          gcloud ai agents deploy \
            --project=${{ secrets.GCP_PROJECT_ID }} \
            --region=us-central1

      - name: Validate Deployment
        run: |
          python scripts/validate-deployment.py
```

**WIF Setup Commands:**
```bash
# One-time WIF configuration
gcloud iam workload-identity-pools create github-pool \
  --location=global \
  --display-name="GitHub Actions Pool"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository"
```

**Security Validation Checks:**
```yaml
# {baseDir}/.github/workflows/security-check.yml
name: Security Validation

on: [pull_request, push]

permissions:
  contents: read
  security-events: write

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Scan for secrets
        uses: trufflesecurity/trufflehog@main

      - name: Vulnerability scan
        uses: aquasecurity/trivy-action@master

      - name: Validate no JSON keys
        run: |
          if find . -name "*service-account*.json"; then
            echo "ERROR: Service account keys detected"
            exit 1
          fi

      - name: Validate WIF usage
        run: |
          if grep -r "credentials_json" .github/workflows/; then
            echo "ERROR: Use WIF instead of JSON keys"
            exit 1
          fi
```

## Error Handling

**WIF Authentication Failed**
- Error: "Failed to generate Google Cloud access token"
- Solution: Verify WIF provider and service account email are correct

**OIDC Token Error**
- Error: "Unable to get ACTIONS_ID_TOKEN_REQUEST_URL env variable"
- Solution: Add `id-token: write` permission to workflow

**IAM Permission Denied**
- Error: "does not have required permission"
- Solution: Grant service account minimum required roles (run.admin, aiplatform.user)

**Attribute Condition Failed**
- Error: "Token does not match attribute condition"
- Solution: Update attribute mapping to include repository restriction

**Deployment Validation Failed**
- Error: "Agent not in RUNNING state"
- Solution: Check agent configuration and deployment logs

## Resources

- Workload Identity Federation: https://cloud.google.com/iam/docs/workload-identity-federation
- GitHub OIDC: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments
- Vertex AI Agent Engine: https://cloud.google.com/vertex-ai/docs/agent-engine
- google-github-actions/auth: https://github.com/google-github-actions/auth
- WIF setup guide in {baseDir}/docs/wif-setup.md
