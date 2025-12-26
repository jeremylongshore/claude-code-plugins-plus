---
name: genkit-infra-expert
description: |
  Use when deploying Genkit applications to production with Terraform. Trigger with phrases like "deploy genkit terraform", "provision genkit infrastructure", "firebase functions terraform", "cloud run deployment", or "genkit production infrastructure". Provisions Firebase Functions, Cloud Run services, GKE clusters, monitoring dashboards, and CI/CD for AI workflows.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(terraform:*), Bash(gcloud:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## Prerequisites

Before using this skill, ensure:
- Google Cloud project with Firebase enabled
- Terraform 1.0+ installed
- gcloud and firebase CLI authenticated
- Genkit application built and containerized
- API keys for Gemini or other AI models
- Understanding of Genkit flows and deployment options

## Instructions

1. **Choose Deployment Target**: Firebase Functions, Cloud Run, or GKE
2. **Configure Terraform Backend**: Set up remote state in GCS
3. **Define Variables**: Project ID, region, Genkit app configuration
4. **Provision Compute**: Deploy functions or containers
5. **Configure Secrets**: Store API keys in Secret Manager
6. **Set Up Monitoring**: Create dashboards for token usage and latency
7. **Enable Auto-scaling**: Configure min/max instances
8. **Validate Deployment**: Test Genkit flows via HTTP endpoints

## Output

**Firebase Functions:**
```hcl
# {baseDir}/terraform/functions.tf


## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.
resource "google_cloudfunctions2_function" "genkit_function" {
  name     = "genkit-ai-flow"
  location = var.region

  build_config {
    runtime     = "nodejs20"
    entry_point = "genkitFlow"
  }

  service_config {
    max_instance_count = 100
    available_memory   = "512Mi"
    timeout_seconds    = 300
  }
}
```

**Cloud Run Service:**
```hcl
resource "google_cloud_run_v2_service" "genkit_service" {
  name     = "genkit-api"
  location = var.region

  template {
    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }
    containers {
      image = "gcr.io/${var.project_id}/genkit-app:latest"
      resources {
        limits = {
          cpu = "2"
          memory = "1Gi"
        }
      }
    }
  }
}
```

## Error Handling

**Build Failures**
- Error: "Cloud Function build failed"
- Solution: Check package.json dependencies and Node.js runtime version

**Cold Start Latency**
- Warning: "High latency on first request"
- Solution: Set min_instance_count >= 1 to keep warm instances

**Secret Access Denied**
- Error: "Permission denied accessing secret"
- Solution: Grant secretAccessor role to Cloud Run/Functions service account

**Memory Exceeded**
- Error: "Container killed: out of memory"
- Solution: Increase available_memory or optimize Genkit flow memory usage

## Resources

- Genkit Deployment: https://genkit.dev/docs/deployment
- Firebase Terraform: https://registry.terraform.io/providers/hashicorp/google/latest
- Genkit examples in {baseDir}/genkit-examples/
