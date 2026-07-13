# PRD: Genkit Infra Expert

**Version:** 1.0.0
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

Deploying Firebase Genkit applications to production requires choosing between Firebase Functions, Cloud Run, and GKE, then configuring secrets management, auto-scaling, monitoring dashboards, and CI/CD pipelines for each target. Manual configuration leads to inconsistent environments, exposed API keys, missing monitoring, and deployment targets that don't match the application's requirements (e.g., using Functions for long-running flows that exceed the 60-second timeout). Teams need Terraform modules that encode deployment best practices per target.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| Backend Developer | Deploying a Genkit flow to production for the first time | Terraform for the right deployment target with secrets and monitoring configured |
| DevOps Engineer | Standardizing Genkit deployment infrastructure across teams | Reusable Terraform modules for Functions, Cloud Run, and GKE with consistent patterns |
| Platform Engineer | Building a shared AI platform with Genkit flows | Multi-environment Terraform with dev/staging/prod configurations |
| SRE | Setting up monitoring and alerting for Genkit flows in production | Terraform for Cloud Monitoring dashboards, alert policies, and log-based metrics |

## Success Criteria

1. Terraform plan succeeds for the chosen deployment target on first run
2. All API keys and secrets stored in Secret Manager with proper IAM bindings
3. Auto-scaling configured: min instances > 0 for production, max instances capped for cost control
4. Monitoring dashboards track token usage, latency, error rate, and cost per flow
5. Cloud Run services include readiness probes for health checking
6. Functions deployments specify appropriate memory and timeout limits for the flow

## Functional Requirements

1. Choose deployment target: Firebase Functions, Cloud Run, or GKE based on flow requirements
2. Configure Terraform backend with GCS remote state
3. Define project variables: project ID, region, Genkit application configuration
4. Provision compute resources for the chosen target with appropriate scaling
5. Configure Secret Manager for API keys with IAM bindings to the compute service account
6. Set up Cloud Monitoring dashboards for token usage, latency, and error metrics
7. Enable auto-scaling with configurable min/max instances
8. Validate deployment by testing Genkit flow HTTP endpoints

## Non-Functional Requirements

- Terraform modules must support all three deployment targets (Functions, Cloud Run, GKE) via variable selection
- Secrets must never appear in Terraform state or plan output (use `sensitive = true`)
- Cloud Run services must have a readiness probe configured for health checking
- Functions deployments must specify memory and timeout limits appropriate for the flow
- All modules must be idempotent and safe to re-apply
- Variable descriptions must document valid deployment targets and their trade-offs

## Dependencies

- Google Cloud project with Firebase enabled
- Terraform 1.0+ installed
- `gcloud` and `firebase` CLI authenticated
- Genkit application built and containerized (for Cloud Run/GKE)
- API keys for Gemini or other AI model providers

## Out of Scope

- Genkit application code implementation (handled by genkit-production-expert)
- Model fine-tuning or training infrastructure
- Frontend hosting configuration
- Custom domain and SSL certificate management
- GKE cluster creation (assumes existing cluster for GKE target)
- Database provisioning (Firestore, Cloud SQL) for flow state storage
