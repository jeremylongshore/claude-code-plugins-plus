---
name: genkit-infra-expert
description: |
  Terraform infrastructure specialist for deploying Genkit applications to production.
  Provisions Firebase Functions, Cloud Run services, GKE clusters, monitoring, and CI/CD for Genkit AI workflows.
  Triggers: "deploy genkit terraform", "genkit infrastructure", "firebase functions terraform", "cloud run genkit"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## What This Skill Does

Expert in provisioning production infrastructure for Firebase Genkit applications using Terraform. Handles Firebase Functions, Cloud Run, GKE deployments with AI monitoring, auto-scaling, and CI/CD integration.

## When This Skill Activates

Triggers: "deploy genkit with terraform", "provision genkit infrastructure", "firebase functions terraform", "cloud run deployment terraform", "genkit production infrastructure"

## Core Terraform Modules

### Firebase Functions Deployment

```hcl
resource "google_cloudfunctions2_function" "genkit_function" {
  name     = "genkit-ai-flow"
  location = var.region

  build_config {
    runtime     = "nodejs20"
    entry_point = "genkitFlow"
    source {
      storage_source {
        bucket = google_storage_bucket.genkit_source.name
        object = google_storage_bucket_object.genkit_code.name
      }
    }
  }

  service_config {
    max_instance_count = 100
    available_memory   = "512Mi"
    timeout_seconds    = 300
    environment_variables = {
      GOOGLE_API_KEY      = var.gemini_api_key
      ENABLE_AI_MONITORING = "true"
    }
  }
}
```

### Cloud Run for Genkit

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
          cpu    = "2"
          memory = "1Gi"
        }
      }

      env {
        name  = "GOOGLE_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_key.id
            version = "latest"
          }
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}
```

### AI Monitoring Integration

```hcl
resource "google_monitoring_dashboard" "genkit_dashboard" {
  dashboard_json = jsonencode({
    displayName = "Genkit AI Monitoring"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "Token Consumption"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_function\" AND metric.type=\"genkit.ai/token_usage\""
                  }
                }
              }]
            }
          }
        },
        {
          width  = 6
          height = 4
          widget = {
            title = "Latency"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_function\" AND metric.type=\"genkit.ai/latency\""
                  }
                }
              }]
            }
          }
        }
      ]
    }
  })
}
```

## Tool Permissions

Read, Write, Edit, Grep, Glob, Bash - Full infrastructure provisioning

## References

- Genkit Deployment: https://genkit.dev/docs/deployment
- Firebase Terraform: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloudfunctions2_function
