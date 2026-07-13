# PRD: ADK Infra Expert

**Version:** 1.0.0
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

Provisioning production Vertex AI ADK infrastructure requires coordinating multiple GCP services: VPC networking with Private Service Connect, least-privilege IAM for Agent Engine, Code Execution Sandbox configuration, Memory Bank with Firestore, VPC Service Controls for data exfiltration protection, and Cloud Monitoring dashboards. Manually configuring these via the console or ad-hoc gcloud commands leads to inconsistent environments, security gaps, and infrastructure that can't be reproduced or audited. Teams need Terraform modules that encode enterprise security constraints as code.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| Platform Engineer | Building a production ADK agent deployment environment from scratch | Complete Terraform modules for Agent Engine with networking, IAM, and monitoring |
| Security Engineer | Enforcing VPC-SC and IAM least-privilege on AI workloads | Terraform code that encodes security constraints as infrastructure policy |
| DevOps Engineer | Automating ADK infrastructure provisioning in CI/CD | Terraform modules with remote state, plan/apply workflow, and validation steps |
| Solutions Architect | Designing enterprise ADK deployment architecture | Reference Terraform that implements all recommended production guardrails |

## Success Criteria

1. Terraform plan succeeds on first run with zero manual console configuration required
2. Agent Engine deployed with Code Execution Sandbox (14-day TTL, SECURE_ISOLATED) and Memory Bank enabled
3. IAM bindings follow least-privilege: no `roles/owner` or `roles/editor`, only purpose-specific roles
4. VPC Service Controls perimeter configured and enforced around AI resources
5. Cloud Monitoring dashboards and alerting policies created for agent health metrics
6. All resources pass `terraform validate` and `terraform fmt` checks

## Functional Requirements

1. Initialize Terraform backend for remote state storage in GCS
2. Configure variables for project ID, region, and agent-specific settings
3. Provision VPC network with Private Service Connect for Agent Engine
4. Create service accounts with least-privilege IAM roles for agent runtime and deployment
5. Deploy Agent Engine with Code Execution Sandbox defaults and Memory Bank configuration
6. Enable VPC Service Controls perimeter around Vertex AI resources
7. Configure Cloud Monitoring dashboards and alerting policies for agent health
8. Include `terraform validate` and `terraform plan` commands for pre-apply verification

## Non-Functional Requirements

- All modules must be idempotent and safe to re-apply without side effects
- State stored remotely in GCS with locking via Cloud Storage
- Terraform >= 1.0 and Google provider >= 5.0 required
- No hardcoded project IDs, regions, or credentials in Terraform code
- All variables must include descriptions documenting expected format and valid ranges
- google-beta provider required for Agent Engine and VPC-SC resources

## Dependencies

- Google Cloud project with billing enabled
- Terraform 1.0+ installed
- `gcloud` CLI authenticated with project admin permissions
- Vertex AI API enabled in the target project
- VPC Service Controls access policy created (for enterprise deployments)

## Out of Scope

- ADK agent application code (handled by adk-engineer skill)
- Agent deployment to Agent Engine (handled by adk-deployment-specialist)
- Post-deployment inspection and scoring (handled by vertex-engine-inspector)
- CI/CD pipeline setup for Terraform (handled by gh-actions-validator)
