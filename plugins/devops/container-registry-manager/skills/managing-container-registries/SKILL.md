---
name: managing-container-registries
description: |
  Execute use when you need to work with containerization.
  This skill provides container management and orchestration with comprehensive guidance and automation.
  Trigger with phrases like "containerize app", "manage containers",
  or "orchestrate deployment".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(docker:*), Bash(kubectl:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Managing Container Registries

## Overview

Manage container registries across Docker Hub, AWS ECR, GCP Artifact Registry, Azure ACR, and self-hosted registries (Harbor, Nexus). Automate image tagging, lifecycle policies, cross-region replication, vulnerability scanning integration, and access control for container image storage and distribution.

## Prerequisites

- Docker CLI installed and authenticated to the target registry
- Cloud provider CLI (`aws`, `gcloud`, `az`) for managed registries
- Registry credentials configured (`docker login` or credential helpers)
- Understanding of image naming conventions (registry/namespace/image:tag)
- IAM permissions for registry operations (push, pull, delete, admin)

## Instructions

1. Identify the target registry type: ECR, Artifact Registry, ACR, Docker Hub, or self-hosted
2. Configure authentication: set up credential helpers for automated access (`docker-credential-ecr-login`, `gcloud auth configure-docker`)
3. Define image naming and tagging strategy: use semantic versioning for releases, git SHA for CI builds, `latest` only for development
4. Create repository/namespace structure organized by team, application, or environment
5. Configure lifecycle policies to auto-delete untagged images and images older than retention threshold (e.g., keep last 10 tagged images, delete untagged after 7 days)
6. Set up vulnerability scanning: enable automatic scanning on push (ECR scan-on-push, GCP Container Analysis)
7. Configure cross-region replication for disaster recovery and latency reduction
8. Implement access control: read-only for CI pull, push access for CI build agents, admin for operators
9. Generate Terraform/IaC for registry infrastructure and policies

## Output

- Terraform/CloudFormation for registry creation with lifecycle and replication policies
- Docker credential helper configuration scripts
- CI/CD pipeline steps for building, tagging, and pushing images
- Lifecycle policy JSON (ECR) or cleanup scripts (Docker Hub, Harbor)
- RBAC configurations for registry access control

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `denied: requested access to the resource is denied` | Missing push/pull permissions or expired token | Re-authenticate with `docker login` or refresh credential helper; verify IAM policies |
| `manifest unknown: manifest unknown` | Image tag does not exist in the registry | Verify image name and tag; check if lifecycle policy deleted the image |
| `no space left on device` during push | Registry storage quota exceeded | Increase quota, run lifecycle cleanup, or delete unused images |
| `unauthorized: authentication required` | Credential helper not configured or token expired | Set up credential helper (`aws ecr get-login-password`, `gcloud auth configure-docker`) |
| `toomanyrequests: rate limit exceeded` | Docker Hub pull rate limit hit | Use authenticated pulls, mirror images to private registry, or upgrade Docker Hub plan |

## Examples

- "Set up an AWS ECR repository with scan-on-push enabled, lifecycle policy to keep last 20 tagged images, and cross-region replication to us-west-2."
- "Configure GCP Artifact Registry with Docker credential helper and a cleanup policy for images not pulled in 90 days."
- "Create a CI pipeline step that builds a Docker image, tags it with the git SHA and `latest`, pushes to ECR, and fails if Critical vulnerabilities are found."

## Resources

- AWS ECR: https://docs.aws.amazon.com/AmazonECR/latest/userguide/
- GCP Artifact Registry: https://cloud.google.com/artifact-registry/docs
- Azure ACR: https://learn.microsoft.com/en-us/azure/container-registry/
- Harbor registry: https://goharbor.io/docs/
- Docker Hub: https://docs.docker.com/docker-hub/
