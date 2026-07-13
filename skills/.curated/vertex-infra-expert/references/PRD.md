# PRD: Vertex Infra Expert

**Version:** 1.0.0
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

Deploying Vertex AI services (model endpoints, vector search indices, ML pipelines) to production requires configuring encryption (CMEK), auto-scaling, IAM least-privilege, and monitoring across multiple interdependent resources. Console-based setup produces undocumented infrastructure that drifts between environments and can't be audited. Teams need Terraform modules that encode Vertex AI best practices as reproducible, version-controlled infrastructure.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| ML Engineer | Deploying trained models to Vertex AI endpoints with auto-scaling | Terraform for endpoint + deployed model with CMEK encryption and scaling config |
| Data Engineer | Setting up vector search for embedding-based retrieval | Terraform for vector search index + endpoint with appropriate dimensions and distance metric |
| Platform Engineer | Standardizing Vertex AI infrastructure across teams | Reusable Terraform modules with consistent IAM, encryption, and monitoring |
| Security Engineer | Enforcing encryption and access controls on AI resources | Terraform that encodes CMEK, VPC-SC, and least-privilege IAM as policy |

## Success Criteria

1. Terraform plan succeeds for endpoint, vector search, and pipeline resources on first run
2. All deployed resources use CMEK encryption when KMS keys are provided
3. Auto-scaling configured with appropriate min/max replicas for production traffic
4. Monitoring dashboards track model latency, prediction count, and error rate
5. Traffic splitting configured for canary deployments between model versions
6. Vector search indices created with correct dimensions matching the embedding model

## Functional Requirements

1. Define AI services required: endpoints, deployed models, vector search indices, ML pipelines
2. Configure Terraform backend and provider with project variables
3. Provision Vertex AI endpoints with auto-scaling (min/max replicas, scale-down delay)
4. Deploy models to endpoints with traffic splitting configuration
5. Create vector search indices with configurable dimensions, distance metric, and shard size
6. Configure CMEK encryption for endpoints and stored data
7. Implement Cloud Monitoring dashboards for model performance metrics
8. Apply least-privilege IAM policies for Vertex AI resource access

## Non-Functional Requirements

- Modules must support both single-model and multi-model endpoint configurations
- All CMEK key references must use full resource paths, not short names
- Terraform code must pass `terraform fmt` and `terraform validate` without errors
- Variable descriptions must document the expected format and valid ranges
- Auto-scaling must include a scale-down delay to prevent thrashing during bursty traffic
- All resources must be taggable with environment and owner labels for cost attribution

## Dependencies

- Google Cloud project with Vertex AI API enabled
- Terraform 1.0+ installed
- `gcloud` CLI authenticated with appropriate permissions
- KMS keys created for CMEK encryption (if required)
- GCS buckets for model artifacts and embeddings
- Trained models uploaded to Vertex AI Model Registry

## Out of Scope

- Model training, fine-tuning, or hyperparameter tuning
- Application code that calls Vertex AI prediction endpoints
- Agent Engine infrastructure (handled by adk-infra-expert)
- CI/CD pipeline setup for Terraform operations
- Custom container image building for model serving
- Feature Store provisioning (future extension)
