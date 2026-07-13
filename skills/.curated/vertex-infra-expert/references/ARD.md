# ARD: Vertex Infra Expert

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

The Vertex Infra Expert generates Terraform modules for provisioning Vertex AI services: endpoints, deployed models, vector search indices, and ML pipelines with production guardrails.

```
Infrastructure Requirements
       ↓
[Vertex Infra Expert]
  ├── Generates: Terraform modules (.tf files)
  ├── Configures: Endpoints, Vector Search, Pipelines, IAM, CMEK, Monitoring
  └── Validates: terraform init/validate/plan
       ↓
GCP Vertex AI Infrastructure
  ├── Model Endpoints (auto-scaled)
  ├── Deployed Models (traffic-split)
  ├── Vector Search Indices
  ├── ML Pipelines
  ├── CMEK Encryption
  ├── IAM (least-privilege)
  └── Cloud Monitoring
```

## Data Flow

1. **Input**: GCP project ID, region, Vertex AI service requirements (endpoint type, model artifact URI, vector dimensions, scaling config), encryption requirements (KMS key ID), and monitoring preferences from user request
2. **Processing**: Generate Terraform module files for each service layer (endpoints, vector search, pipelines, monitoring). Configure CMEK encryption references, auto-scaling parameters, traffic splitting weights, and IAM bindings. Validate with `terraform init` and `terraform plan`.
3. **Output**: Directory of `.tf` files organized by service, `terraform.tfvars.example` with documented variables, validation output, and a deployment runbook with apply commands and verification steps

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Resource-per-file organization | Separate .tf files for endpoints, models, vector search, monitoring | Clear ownership; teams can adopt individual resources without the full module |
| CMEK-ready by default | Encryption block included with optional KMS key variable | Prod environments require CMEK; easier to configure upfront than retrofit |
| Auto-scaling with scale-down delay | Default 10-minute scale-down delay | Prevents thrashing during bursty traffic; configurable via variable |
| Traffic splitting support | Percentage-based routing across model versions | Enables canary deployments and A/B testing for model updates |
| Vector search dimensions as variable | No default dimension; must be explicitly set | Prevents silently deploying with wrong dimensions that cause retrieval failures |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| Read | Inspect existing Terraform configs, model artifacts, and embedding configurations |
| Write | Create new `.tf` files for Vertex AI resources (endpoints, vector search, pipelines) |
| Edit | Update existing Terraform to add resources, adjust scaling, or fix validation errors |
| Grep | Search for existing Vertex AI resource definitions, KMS key references, and variable usage |
| Glob | Discover existing Terraform module structure and related configuration files |
| Bash(terraform:*) | Run `terraform init`, `terraform validate`, `terraform plan`, `terraform fmt` |
| Bash(gcloud:*) | Verify Vertex AI API status, list models in registry, check KMS key availability |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| Model not found in registry | `terraform plan` fails with model resource not found | Verify model URI; list available models with `gcloud ai models list --region=REGION` |
| KMS key permission denied | Plan fails with cryptoKeyEncrypterDecrypter error | Grant `roles/cloudkms.cryptoKeyEncrypterDecrypter` to the Vertex AI service agent |
| Quota exceeded for endpoints | Plan or apply fails with quota error | Request quota increase via Cloud Console; or reduce max_replicas to fit within quota |
| Vector search dimension mismatch | Apply succeeds but queries return empty results | Verify embedding model output dimension matches the index configuration |
| Region not supported | Vertex AI resource type not available in specified region | Use `us-central1` for widest Vertex AI service availability |

## Extension Points

- Multi-model endpoints: extend traffic splitting module for A/B testing across model versions
- Batch prediction pipelines: add Terraform for scheduled batch prediction jobs
- Feature Store integration: add Terraform for Vertex AI Feature Store for ML feature management
- Custom monitoring: extend dashboards with model-specific metrics (drift detection, prediction quality)
- Module composition: combine with adk-infra-expert for Agent Engine + Vertex AI unified deployments
- Cost estimation: integrate `infracost` for pre-apply cost projections based on endpoint configuration
- Drift detection: scheduled `terraform plan` to catch manual console changes that deviate from code
