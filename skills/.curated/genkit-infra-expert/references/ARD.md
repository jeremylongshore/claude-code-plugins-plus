# ARD: Genkit Infra Expert

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

The Genkit Infra Expert generates Terraform modules for deploying Firebase Genkit applications to one of three production targets, with secrets management and observability.

```
Genkit Application + Requirements
       ↓
[Genkit Infra Expert]
  ├── Generates: Terraform modules (.tf files)
  ├── Configures: Compute, Secret Manager, Monitoring, Auto-scaling
  └── Validates: terraform init/validate/plan
       ↓
GCP Production Infrastructure
  ├── Firebase Functions / Cloud Run / GKE
  ├── Secret Manager (API keys)
  ├── Cloud Monitoring (dashboards + alerts)
  ├── Auto-scaling (min/max instances)
  └── IAM (least-privilege)
```

## Data Flow

1. **Input**: GCP project ID, region, deployment target (Functions/Cloud Run/GKE), Genkit flow configuration (memory, timeout, scaling), and API key references from user request
2. **Processing**: Select the appropriate Terraform module set for the deployment target. Generate compute resource definitions with scaling configuration, Secret Manager resources with IAM bindings, Cloud Monitoring dashboard definitions, and auto-scaling policies. Validate with `terraform init` and `terraform plan`.
3. **Output**: Terraform module directory with target-specific `.tf` files, `terraform.tfvars.example` with documented variables, Secret Manager setup commands, monitoring dashboard JSON, and a deployment validation checklist

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Target selection via variable | Single module set with `deployment_target` variable | Reduces code duplication; common patterns (secrets, monitoring) shared across targets |
| Secret Manager for all secrets | No inline secrets or environment variable fallbacks | Centralized rotation, audit logging, and IAM-scoped access; never in Terraform state |
| Min instances > 0 for production | Default `min_instances = 1` | Eliminates cold start latency for production traffic; `0` only for dev/staging |
| Functions for simple flows | Recommend Functions when execution < 60s | Zero infrastructure management; auto-scaling included; cost-effective for short flows |
| Cloud Run for long flows | Recommend Cloud Run when execution > 60s | Configurable timeout up to 60 minutes; supports streaming and WebSocket connections |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| Read | Inspect existing Terraform files, Genkit config, firebase.json, and Cloud Run service YAML |
| Write | Create new `.tf` files for compute, secrets, monitoring, and IAM resources |
| Edit | Patch existing Terraform to change deployment target, update scaling, or add monitoring |
| Grep | Search for existing resource definitions, secret references, and variable usage |
| Glob | Discover existing Terraform structure and Genkit application layout |
| Bash(terraform:*) | Run `terraform init`, `terraform validate`, `terraform plan`, `terraform fmt` |
| Bash(gcloud:*) | Verify API enablement, list Secret Manager secrets, check Cloud Run services |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| Firebase API not enabled | `terraform plan` fails with API not activated | Provide `gcloud services enable firebase.googleapis.com cloudfunctions.googleapis.com` |
| Secret Manager permission denied | Plan fails with IAM error on secret access | Grant `roles/secretmanager.secretAccessor` to the compute service account |
| Functions timeout exceeded | Deployed function times out at 60s | Migrate to Cloud Run target; update `deployment_target` variable and re-plan |
| Container image not found | Cloud Run plan fails with image not found | Verify image URI; build and push with `gcloud builds submit` or `docker push` |
| Quota exceeded for instances | Apply fails with instance quota error | Reduce `max_instances`; request quota increase via Cloud Console |

## Extension Points

- Blue-green deployment: add traffic splitting between revisions for zero-downtime updates
- Custom domains: extend with Cloud Run domain mapping or Functions custom domain config
- Multi-region: deploy to multiple regions with Cloud Run services and load balancing
- Cost tracking: add budget alerts based on token usage and compute costs
- Pipeline integration: generate Cloud Build or GitHub Actions configs for Terraform plan/apply
- Environment promotion: add workspace or directory-per-env pattern for dev/staging/prod
- Drift detection: scheduled `terraform plan` to catch manual changes in Cloud Console
