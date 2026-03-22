---
name: castai-ci-integration
description: |
  Integrate CAST AI policy validation and cost checks into CI/CD pipelines.
  Use when adding CAST AI savings verification to GitHub Actions,
  validating Terraform plans, or gating deployments on cost thresholds.
  Trigger with phrases like "cast ai CI", "cast ai github actions",
  "cast ai terraform CI", "cast ai pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI CI Integration

## Overview

Add CAST AI cost validation to CI/CD pipelines: verify savings thresholds, validate Terraform plans before apply, and gate deployments on autoscaler health.

## Prerequisites

- GitHub Actions enabled
- CAST AI API key stored as repository secret
- Terraform state accessible from CI (if using Terraform)

## Instructions

### Step 1: GitHub Actions -- Savings Gate

```yaml
# .github/workflows/castai-check.yml
name: CAST AI Cost Check

on:
  pull_request:
    paths: ["terraform/**", "k8s/**"]
  schedule:
    - cron: "0 8 * * 1"  # Weekly Monday report

jobs:
  cost-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check CAST AI Savings
        env:
          CASTAI_API_KEY: ${{ secrets.CASTAI_API_KEY }}
          CASTAI_CLUSTER_ID: ${{ secrets.CASTAI_CLUSTER_ID }}
        run: |
          SAVINGS=$(curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
            "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/savings")

          PERCENT=$(echo "$SAVINGS" | jq -r '.savingsPercentage')
          MONTHLY=$(echo "$SAVINGS" | jq -r '.monthlySavings')

          echo "### CAST AI Savings Report" >> $GITHUB_STEP_SUMMARY
          echo "- Monthly savings: \$${MONTHLY}" >> $GITHUB_STEP_SUMMARY
          echo "- Savings percentage: ${PERCENT}%" >> $GITHUB_STEP_SUMMARY

          # Fail if savings drop below threshold
          if (( $(echo "$PERCENT < 10" | bc -l) )); then
            echo "WARNING: Savings below 10% threshold"
            exit 1
          fi

      - name: Verify Agent Health
        env:
          CASTAI_API_KEY: ${{ secrets.CASTAI_API_KEY }}
          CASTAI_CLUSTER_ID: ${{ secrets.CASTAI_CLUSTER_ID }}
        run: |
          STATUS=$(curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
            "https://api.cast.ai/v1/kubernetes/external-clusters/${CASTAI_CLUSTER_ID}" \
            | jq -r '.agentStatus')

          if [ "$STATUS" != "online" ]; then
            echo "CAST AI agent is ${STATUS}, expected online"
            exit 1
          fi
```

### Step 2: Terraform Plan Validation

```yaml
  terraform-plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3

      - name: Terraform Init & Plan
        working-directory: terraform/
        env:
          CASTAI_API_TOKEN: ${{ secrets.CASTAI_API_KEY }}
        run: |
          terraform init
          terraform plan -var-file=environments/prod.tfvars \
            -out=plan.tfplan -no-color | tee plan-output.txt

      - name: Check for Destructive Changes
        run: |
          if grep -q "will be destroyed" terraform/plan-output.txt; then
            echo "DESTRUCTIVE CHANGES DETECTED in CAST AI resources"
            exit 1
          fi
```

### Step 3: Store Secrets

```bash
gh secret set CASTAI_API_KEY --body "your-api-key"
gh secret set CASTAI_CLUSTER_ID --body "your-cluster-id"
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing `gh secret set` | Add secrets to repo |
| Savings check fails | Cluster not onboarded | Verify cluster ID is correct |
| Terraform init fails | State backend misconfigured | Check backend config |
| Agent offline in CI | Key scope mismatch | Use production API key |

## Resources

- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [CAST AI API Reference](https://api.cast.ai/v1/spec/openapi.json)

## Next Steps

For deployment patterns, see `castai-deploy-integration`.
