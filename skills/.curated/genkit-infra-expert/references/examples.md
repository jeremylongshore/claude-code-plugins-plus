# Genkit Terraform Examples

## Example 1: Cloud Run Deployment for a Genkit API

Deploy a Genkit flow server to Cloud Run with Secret Manager for API keys.

```hcl
# variables.tf
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Deployment region"
  type        = string
  default     = "us-central1"
}

variable "container_image" {
  description = "Genkit app container image"
  type        = string
}

# main.tf
resource "google_secret_manager_secret" "gemini_key" {
  secret_id = "genkit-gemini-api-key"
  replication {
    auto {}
  }
}

resource "google_cloud_run_v2_service" "genkit_api" {
  name     = "genkit-api"
  location = var.region

  template {
    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

    containers {
      image = var.container_image
      ports {
        container_port = 3400
      }
      resources {
        limits = {
          cpu    = "2"
          memory = "1Gi"
        }
      }
      env {
        name = "GOOGLE_GENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name  = "GENKIT_ENV"
        value = "production"
      }
      startup_probe {
        http_get {
          path = "/api/__health"
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }
    }
    service_account = google_service_account.genkit_runner.email
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

resource "google_service_account" "genkit_runner" {
  account_id   = "genkit-runner"
  display_name = "Genkit Cloud Run Runner"
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  name   = google_cloud_run_v2_service.genkit_api.name
  location = var.region
  role   = "roles/run.invoker"
  member = "allUsers"
}
```

**Smoke test:**

```bash
SERVICE_URL=$(gcloud run services describe genkit-api \
  --region=us-central1 --format='value(status.url)')
curl -s "$SERVICE_URL/api/__health" | jq .
curl -s -X POST "$SERVICE_URL/api/myFlow" \
  -H "Content-Type: application/json" \
  -d '{"data": "test input"}' | jq .
```

## Example 2: Firebase Functions Deployment

Deploy Genkit flows as Firebase Functions with Firestore triggers.

```hcl
resource "google_cloudfunctions2_function" "genkit_flow" {
  name     = "genkit-summarize"
  location = var.region

  build_config {
    runtime     = "nodejs20"
    entry_point = "summarizeFlow"
    source {
      storage_source {
        bucket = google_storage_bucket.functions_source.name
        object = google_storage_bucket_object.source_zip.name
      }
    }
  }

  service_config {
    min_instance_count    = 0
    max_instance_count    = 5
    available_memory      = "512Mi"
    timeout_seconds       = 120
    service_account_email = google_service_account.genkit_runner.email

    secret_environment_variables {
      key        = "GOOGLE_GENAI_API_KEY"
      project_id = var.project_id
      secret     = google_secret_manager_secret.gemini_key.secret_id
      version    = "latest"
    }
  }
}

resource "google_storage_bucket" "functions_source" {
  name     = "${var.project_id}-genkit-functions-source"
  location = var.region
}
```

## Example 3: GKE Deployment with GPU

Deploy Genkit on GKE for high-throughput AI workloads with GPU acceleration.

```hcl
resource "google_container_node_pool" "gpu_pool" {
  name     = "genkit-gpu-pool"
  cluster  = google_container_cluster.main.name
  location = var.region

  node_config {
    machine_type = "n1-standard-4"
    guest_accelerator {
      type  = "nvidia-tesla-t4"
      count = 1
    }
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]
  }

  autoscaling {
    min_node_count = 0
    max_node_count = 5
  }
}

# Genkit Kubernetes deployment targeting GPU pool
resource "kubernetes_deployment" "genkit" {
  metadata {
    name = "genkit-api"
  }
  spec {
    replicas = 2
    selector {
      match_labels = { app = "genkit-api" }
    }
    template {
      metadata {
        labels = { app = "genkit-api" }
      }
      spec {
        node_selector = {
          "cloud.google.com/gke-accelerator" = "nvidia-tesla-t4"
        }
        container {
          name  = "genkit-api"
          image = var.container_image
          port {
            container_port = 3400
          }
          resources {
            limits = {
              "nvidia.com/gpu" = "1"
              cpu              = "2"
              memory           = "4Gi"
            }
          }
        }
      }
    }
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
