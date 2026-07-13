# ARD: ADK Infra Expert

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

The ADK Infra Expert generates and validates Terraform modules for provisioning Vertex AI Agent Engine infrastructure. It interacts with the local filesystem for Terraform code and GCP APIs for validation.

```
Infrastructure Requirements
       ↓
[ADK Infra Expert]
  ├── Generates: Terraform modules (.tf files)
  ├── Configures: VPC, IAM, Agent Engine, VPC-SC, Monitoring
  └── Validates: terraform init/validate/plan
       ↓
GCP Infrastructure
  ├── VPC + Private Service Connect
  ├── Agent Engine Runtime
  ├── Code Execution Sandbox
  ├── Memory Bank (Firestore)
  ├── IAM (least-privilege)
  ├── VPC Service Controls
  └── Cloud Monitoring
```

## Data Flow

1. **Input**: GCP project ID, region, agent configuration requirements (sandbox TTL, memory bank settings, scaling), and security requirements (VPC-SC, encryption) from user request
2. **Processing**: Generate Terraform module files for each infrastructure layer (networking, IAM, compute, monitoring), configure variables with sensible defaults, set up remote state backend, then validate with `terraform init` and `terraform plan`
3. **Output**: Directory of `.tf` files (main.tf, variables.tf, outputs.tf, backend.tf), a `terraform.tfvars.example` template, validation output from `terraform plan`, and a deployment checklist with commands

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| GCS backend for state | `backend "gcs"` with locking | Standard GCP pattern; prevents concurrent modifications; auditable state history |
| Module-per-concern | Separate files for network, IAM, compute, monitoring | Clean separation; teams can adopt modules independently |
| Variables with defaults | All settings configurable, production defaults pre-set | Works out of the box; customizable without forking |
| google-beta provider | Required for Agent Engine and VPC-SC resources | Several Agent Engine Terraform resources are only in the beta provider |
| Code Execution Sandbox defaults | 14-day TTL, SECURE_ISOLATED | Matches Google's recommended production configuration; balances retention with security |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| Read | Inspect existing Terraform files, state configuration, and variable definitions |
| Write | Create new `.tf` files for each infrastructure module |
| Edit | Patch existing Terraform configs to add resources, update variables, or fix validation errors |
| Grep | Search for existing resource definitions, provider versions, and variable usage |
| Glob | Discover existing Terraform files and module structure in the project |
| Bash(terraform:*) | Run `terraform init`, `terraform validate`, `terraform plan`, `terraform fmt` |
| Bash(gcloud:*) | Verify API enablement, IAM policies, and VPC-SC configuration |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| Provider initialization failure | `terraform init` fails with provider download errors | Check network access; verify provider version constraints; use `terraform providers lock` |
| Invalid resource configuration | `terraform validate` returns errors | Parse error messages; fix the specific field/block; re-validate |
| Permission denied on plan | `terraform plan` returns 403 errors | Verify gcloud auth; check that the authenticated identity has `roles/resourcemanager.projectIamAdmin` |
| API not enabled | Plan fails with "API not activated" | Provide `gcloud services enable` command for each required API |
| State lock conflict | State locked by another process | Identify the lock holder; use `terraform force-unlock` as last resort |

## Extension Points

- Multi-environment support: add workspaces or directory-per-env for dev/staging/prod
- Custom monitoring dashboards: extend the monitoring module with project-specific alert policies
- Multi-region deployment: duplicate compute modules across regions with traffic management
- Policy-as-code: integrate with Terraform Sentinel or OPA for org-level policy enforcement
- Module registry: publish modules to a private Terraform registry for cross-team reuse
- Cost estimation: integrate `infracost` for pre-apply cost projections
- Drift detection: add scheduled `terraform plan` to detect configuration drift in production
