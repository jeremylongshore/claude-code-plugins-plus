---
name: research-to-deploy
description: |
  Researches infrastructure best practices and generates deployment-ready
  configurations, Terraform modules, Dockerfiles, and CI/CD pipelines. Use
  when the user needs to deploy services, set up infrastructure, or create
  cloud configurations based on current best practices. Trigger with phrases
  like "research and deploy", "set up Cloud Run", "create Terraform for",
  "deploy this to AWS", or "generate infrastructure configs".
allowed-tools: Read, Write, Edit, Bash(terraform:*), Bash(docker:*), Bash(kubectl:*), Bash(git:*), Bash(npm:*), Glob, Grep, WebSearch, WebFetch
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex
tags: [deployment, infrastructure, automation, devops, terraform, cloud]
---

# Research to Deploy

Research infrastructure best practices and generate deployment-ready cloud configurations.

## Overview

This skill bridges the gap between researching cloud infrastructure patterns and actually deploying them. Instead of spending hours reading documentation, comparing approaches, and manually writing configuration files, this skill automates the entire pipeline: it searches for current best practices on the target platform, synthesizes the findings into a coherent deployment strategy, and generates production-grade Infrastructure as Code (IaC) that you can review and apply directly.

The skill supports multi-cloud deployments across GCP, AWS, and Azure, as well as platform-as-a-service providers like Railway, Fly.io, and Render. It generates Terraform modules by default but can also produce Pulumi programs, Docker Compose files, Kubernetes manifests, or platform-specific CLI commands. Every generated configuration includes security hardening, monitoring hooks, and cost optimization annotations based on the latest recommendations from the cloud provider.

## Instructions

1. **Describe what you want to deploy** and where:
   - "Research GCP Cloud Run best practices and deploy my Node.js API to staging"
   - "Set up a production Kubernetes cluster on AWS with monitoring"
   - "Create Terraform configs for a serverless Python function on Azure"

2. **Specify constraints** if you have them:
   - Budget: "keep monthly costs under $50"
   - Region: "deploy to us-central1"
   - Compliance: "needs HIPAA-compliant storage"
   - Existing infra: "we already use Terraform Cloud for state management"

3. **Let the skill research.** It will search for current documentation, community best practices, and known pitfalls for the specified platform and service. The research phase produces a summary of findings before generating any code.

4. **Review the research summary** and confirm the approach. The skill presents:
   - Recommended architecture with rationale
   - Cost estimate based on expected usage
   - Security considerations and mitigations
   - Alternative approaches that were considered

5. **Apply the generated configs** after review:
   - Terraform: `terraform init && terraform plan`
   - Docker: `docker compose up -d`
   - Kubernetes: `kubectl apply -f`

## Output

The skill produces a structured set of deployment artifacts:

- **Research Summary** (Markdown): A concise document covering the best practices found, architectural decisions made, and trade-offs considered. Includes source links.
- **Infrastructure Code**: Terraform modules (`.tf` files), Dockerfiles, Kubernetes manifests, or platform-specific configs organized in a standard directory structure.
- **CI/CD Pipeline**: GitHub Actions workflow or equivalent CI config that automates testing, building, and deploying the infrastructure.
- **Monitoring Setup**: Configuration for health checks, alerting rules, and dashboards appropriate to the target platform (Cloud Monitoring, CloudWatch, or Datadog).
- **Cost Estimate**: Annotated breakdown of expected monthly costs based on the chosen resources and expected traffic.
- **Runbook** (Markdown): Step-by-step instructions for deploying, updating, rolling back, and troubleshooting the infrastructure.

## Examples

### Example 1: GCP Cloud Run Deployment

**User:** "Research Cloud Run best practices and create a deployment for my Express API."

The skill will:
1. Search for current Cloud Run documentation on container sizing, concurrency settings, min/max instances, and VPC connector patterns.
2. Generate a `Dockerfile` optimized for Cloud Run (multi-stage build, non-root user, health check endpoint).
3. Create `main.tf` with Cloud Run service, IAM bindings, custom domain mapping, and Cloud SQL connection.
4. Add a GitHub Actions workflow for automated deployment on push to `main`.
5. Include a `monitoring.tf` with uptime checks and alerting policies.

### Example 2: AWS ECS Fargate with Terraform

**User:** "Deploy a Python microservice to ECS Fargate, keep costs minimal."

The skill will:
1. Research Fargate Spot pricing, right-sizing strategies, and ALB vs API Gateway trade-offs.
2. Generate Terraform modules for VPC, ECS cluster, Fargate service, ALB, and ECR repository.
3. Configure auto-scaling based on CPU utilization with conservative thresholds for cost optimization.
4. Produce a cost estimate comparing Fargate vs Fargate Spot for the expected workload.

### Example 3: Kubernetes on Azure AKS

**User:** "Set up a production AKS cluster with monitoring and RBAC."

The skill will:
1. Research AKS best practices for node pool sizing, network policies, and Azure AD integration.
2. Generate Terraform for the AKS cluster, node pools, Azure Monitor workspace, and RBAC role assignments.
3. Create Kubernetes manifests for ingress controller, cert-manager, and Prometheus stack.
4. Include a runbook covering cluster upgrades, node pool scaling, and incident response.

## Error Handling

- **Unknown platform:** Prompts the user to specify a supported cloud provider or platform.
- **Insufficient context:** Asks clarifying questions about the application type, expected traffic, and budget before generating configs.
- **Web search unavailable:** Falls back to built-in knowledge of common deployment patterns, noting that the recommendations may not reflect the latest documentation.
- **Conflicting requirements:** Identifies trade-offs (e.g., "HIPAA compliance requires dedicated tenancy which increases costs beyond the $50 budget") and asks the user to prioritize.

## Prerequisites

- Target cloud provider CLI authenticated (`gcloud`, `aws`, or `az`)
- Terraform >= 1.5 installed (for IaC output)
- Docker installed (for container-based deployments)
- WebSearch and WebFetch tools enabled for best-practice research

## Resources

- [Terraform Registry](https://registry.terraform.io/) — official provider and module documentation
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/) — cloud architecture best practices
- [GCP Cloud Architecture Center](https://cloud.google.com/architecture) — reference architectures and patterns
