# PRD: GH Actions Validator

**Version:** 1.0.0
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

GitHub Actions workflows that deploy to Google Cloud commonly use long-lived service account JSON keys stored as repository secrets. This practice violates security best practices: keys can leak, never expire, and grant broad permissions. Migrating to Workload Identity Federation (WIF) with OIDC requires coordinating multiple GCP resources (workload identity pool, provider, IAM bindings) and GitHub workflow changes (id-token permissions, auth action). Developers misconfigure these steps, resulting in authentication failures and insecure fallbacks to JSON keys.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| DevOps Engineer | Setting up CI/CD for GCP deployments from GitHub Actions | Secure WIF configuration with validated OIDC permissions |
| Security Engineer | Auditing existing workflows for credential hygiene | Detection of JSON key usage and insecure IAM patterns |
| Platform Engineer | Standardizing deployment pipelines across teams | Reusable, validated workflow templates with least-privilege IAM |
| Developer | Deploying Vertex AI agents or Cloud Run services via GitHub Actions | Working workflow with WIF auth and post-deployment health checks |

## Success Criteria

1. Detect 100% of JSON service account key usage in workflow files (secrets or files)
2. Validate OIDC `id-token: write` permission is present in all deployment workflows
3. Confirm no `roles/owner` or `roles/editor` IAM bindings in deployment service accounts
4. Provide complete WIF setup commands that work on first execution
5. Hardened workflow template includes secret scanning and dependency vulnerability checks
6. Post-deployment health checks validate endpoint availability before marking success

## Functional Requirements

1. Scan `.github/workflows/` for all YAML workflow files
2. Detect JSON service account key usage: `GOOGLE_APPLICATION_CREDENTIALS`, key file references, `credentials_json` inputs
3. Validate WIF authentication: `google-github-actions/auth@v2` action with `workload_identity_provider` parameter
4. Check OIDC permissions: `id-token: write` in the `permissions` block of deployment jobs
5. Review IAM roles on deployment service accounts: flag `roles/owner`, `roles/editor`, and recommend least-privilege alternatives
6. Add security scanning steps: secret detection, dependency vulnerability scanning
7. Validate post-deployment health checks exist for each deploy step
8. Generate WIF one-time setup commands for the GCP project

## Non-Functional Requirements

- Validation must work on any GitHub Actions YAML regardless of deployment target (Cloud Run, Agent Engine, Functions)
- WIF setup commands must be idempotent (safe to re-run without side effects)
- Must handle matrix builds and reusable workflow patterns
- No modifications to workflows without explicit user consent
- YAML parsing must handle all GitHub Actions syntax including anchors, aliases, and expressions
- Validation must complete offline (no GitHub API calls required for YAML analysis)

## Dependencies

- GitHub repository with Actions enabled and workflow files in `.github/workflows/`
- Google Cloud project with billing enabled
- `gcloud` CLI authenticated with admin permissions (for WIF setup)
- `google-github-actions/auth@v2` action available on GitHub

## Out of Scope

- Non-GCP deployment targets (AWS, Azure)
- GitHub Actions runner self-hosting configuration
- Application-level testing within workflows (unit tests, integration tests)
- Cost optimization of GitHub Actions minutes
- GitHub App or OAuth token management
- Workflow performance optimization (caching, parallelism)
