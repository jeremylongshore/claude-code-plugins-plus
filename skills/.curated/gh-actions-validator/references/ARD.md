# ARD: GH Actions Validator

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

The GH Actions Validator inspects GitHub Actions workflow files and their associated GCP IAM configuration to ensure secure deployment patterns using Workload Identity Federation.

```
.github/workflows/*.yml
       ↓
[GH Actions Validator]
  ├── Reads: workflow YAML files, IAM policies
  ├── Scans: auth patterns, permissions, IAM roles
  └── Generates: WIF setup commands, hardened workflows
       ↓
Validation Report + WIF Setup
  ├── Security findings (JSON keys, missing OIDC)
  ├── IAM role recommendations
  ├── WIF setup gcloud commands
  └── Hardened workflow templates
```

## Data Flow

1. **Input**: Repository path containing `.github/workflows/` directory. Optionally a specific workflow file to validate. GCP project ID for IAM audit.
2. **Processing**: Parse all workflow YAML files. For each workflow: check for JSON key usage patterns, validate `google-github-actions/auth` action configuration, verify `id-token: write` permission, audit IAM roles on the authenticated service account via `gcloud`, check for post-deployment health steps. Generate WIF setup commands if not yet configured.
3. **Output**: Validation report listing security findings per workflow, IAM role audit results, WIF setup commands (if needed), and optionally a hardened workflow template with WIF auth and security scanning steps.

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| WIF over JSON keys | Require OIDC authentication for all GCP deployments | JSON keys are a security liability: they leak, never expire, and can't be scoped to repo/branch |
| `google-github-actions/auth@v2` | Standardize on Google's official auth action | Maintained by Google; handles token exchange correctly; supports audience and provider config |
| Least-privilege IAM audit | Flag owner/editor roles; suggest specific alternatives | Broad roles are the most common security misconfiguration in CI/CD pipelines |
| YAML-level validation | Parse workflow YAML rather than running workflows | Safe, fast, deterministic; no need for GitHub API tokens or workflow triggers |
| Idempotent WIF setup | All gcloud commands safe to re-run | Prevents errors when running setup on already-configured projects |
| Role-to-target mapping | Map deployment targets to minimum IAM roles | Cloud Run needs `roles/run.developer`, Agent Engine needs `roles/aiplatform.user`; prevents over-granting |
| Auth action version pinning | Require `@v2` not `@v1` or `@main` | Pinned versions are reproducible and auditable; `@main` can introduce breaking changes |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| Read | Parse workflow YAML files, IAM policy exports, and WIF configuration files |
| Write | Generate hardened workflow templates and WIF setup scripts |
| Edit | Patch existing workflows to add OIDC permissions, update auth actions, add health checks |
| Grep | Search for JSON key patterns (`credentials_json`, `GOOGLE_APPLICATION_CREDENTIALS`), IAM role references |
| Glob | Discover all workflow files in `.github/workflows/` |
| Bash(git:*) | Check git history for committed credentials or key files |
| Bash(gcloud:*) | Query IAM policies, list service accounts, check WIF pool/provider configuration |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| Invalid workflow YAML | YAML parse failure on workflow file | Report syntax error location; suggest `yamllint` for detailed diagnostics |
| Missing OIDC permission | `id-token: write` not in job permissions | Provide the exact `permissions:` block to add to the workflow |
| WIF pool not configured | `gcloud iam workload-identity-pools describe` returns not found | Generate the complete set of `gcloud` commands to create pool, provider, and IAM binding |
| Overprivileged IAM role | Service account has `roles/owner` or `roles/editor` | Suggest the minimum required roles for the specific deployment target (e.g., `roles/run.developer`) |
| Auth action outdated | `google-github-actions/auth@v1` in workflow | Recommend upgrading to `@v2` with the updated parameter names |

## Extension Points

- Multi-cloud support: extend patterns to validate AWS OIDC or Azure federated credentials
- Branch-scoped WIF: configure attribute conditions that restrict authentication to specific branches
- Reusable workflow validation: audit called workflows and composite actions for the same security patterns
- Policy-as-code: define organization-level security policies that all workflows must satisfy
- Automated remediation: apply fixes to workflow files with user confirmation
- Compliance reports: generate audit reports showing WIF adoption percentage across all workflows
- Team templates: generate organization-level reusable workflows with pre-configured WIF
