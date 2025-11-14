# Jeremy Vertex Terraform

**🎯 VERTEX AI MODEL GARDEN & AI INFRASTRUCTURE**

Terraform infrastructure specialist for **broader Vertex AI services** including Model Garden, Gemini endpoints, vector search, ML pipelines, and enterprise AI infrastructure (NOT Agent Engine - use jeremy-adk-terraform for that).

## ⚠️ Important: What This Plugin Is For

**✅ THIS PLUGIN IS FOR:**
- **Vertex AI Model Garden** deployments (foundation models)
- **Gemini API endpoints** (gemini-pro, gemini-2.0-flash)
- **Vector Search** infrastructure (ScaNN-based similarity search)
- **Vertex AI Pipelines** (Kubeflow Pipelines for ML workflows)
- **Endpoint deployment** (model serving infrastructure)
- **Batch prediction** jobs
- **ML model training** infrastructure
- **Feature Store** for ML feature management

**❌ THIS PLUGIN IS NOT FOR:**
- Agent Engine infrastructure (use `jeremy-adk-terraform` for ADK agents)
- Cloud Run deployments (use `jeremy-genkit-terraform`)
- Self-managed ML infrastructure

## Overview

This plugin provides Terraform modules for deploying Vertex AI services including Model Garden foundation models, Gemini API endpoints, vector search for RAG applications, ML pipelines, and production model serving infrastructure.

**Key Infrastructure Components:**
- `google_vertex_ai_endpoint` for model serving
- `google_vertex_ai_deployed_model` for model versions
- `google_vertex_ai_index` for vector search
- `google_vertex_ai_index_endpoint` for similarity search
- `google_vertex_ai_feature_store` for feature management
- Cloud Storage for model artifacts
- BigQuery for ML model training

## Installation

```bash
/plugin install jeremy-vertex-terraform@claude-code-plugins-plus
```

## Prerequisites & Dependencies

### Required Tools

**1. Terraform:**
```bash
# Install Terraform 1.5+
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Verify
terraform version  # Should show 1.5.0+
```

**2. gcloud CLI:**
```bash
# Install gcloud
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Update to latest
gcloud components update

# Authenticate
gcloud auth application-default login
```

**3. Terraform Google Provider:**
```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}
```

### Required Google Cloud APIs

```bash
# Enable all required APIs
gcloud services enable \
    aiplatform.googleapis.com \
    compute.googleapis.com \
    storage.googleapis.com \
    bigquery.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    cloudtrace.googleapis.com \
    --project=YOUR_PROJECT_ID
```

### Required IAM Permissions

```yaml
# Service account for Terraform needs:
- roles/aiplatform.admin              # Deploy Vertex AI resources
- roles/storage.admin                 # Manage model artifacts
- roles/bigquery.admin                # ML training datasets
- roles/compute.networkAdmin          # VPC for private endpoints
- roles/monitoring.admin              # Observability
- roles/iam.serviceAccountAdmin       # Service account management
```

## Features

✅ **Model Garden Deployment**: Foundation models (Gemini, PaLM, Claude, Llama)
✅ **Gemini API Endpoints**: Dedicated endpoints with rate limiting
✅ **Vector Search**: ScaNN-based similarity search for RAG
✅ **ML Pipelines**: Kubeflow Pipelines for training workflows
✅ **Model Serving**: Production endpoints with auto-scaling
✅ **Batch Predictions**: Large-scale inference jobs
✅ **Feature Store**: Centralized feature management
✅ **Monitoring**: Model performance tracking and drift detection

## Quick Start

### Natural Language Activation

```
"Create Terraform for Gemini endpoint deployment"
"Deploy vector search for RAG application"
"Set up Vertex AI Pipeline for model training"
"Create Feature Store for ML features"
"Deploy custom model to Vertex AI endpoint"
```

## Terraform Module Structure

### 1. Gemini API Endpoint

```hcl
# gemini_endpoint.tf

# Gemini 2.0 Flash endpoint
resource "google_vertex_ai_endpoint" "gemini_endpoint" {
  display_name = "gemini-2-0-flash-endpoint"
  location     = var.region
  project      = var.project_id

  description = "Production Gemini 2.0 Flash endpoint"

  # Network configuration
  network = google_compute_network.vertex_vpc.id

  # Encryption
  encryption_spec {
    kms_key_name = google_kms_crypto_key.model_key.id
  }
}

# Deploy Gemini model
resource "google_vertex_ai_deployed_model" "gemini_flash" {
  endpoint = google_vertex_ai_endpoint.gemini_endpoint.id

  model = "publishers/google/models/gemini-2.0-flash-001"

  display_name = "gemini-2-0-flash-001"

  dedicated_resources {
    machine_spec {
      machine_type = "n1-standard-4"
    }

    min_replica_count = var.min_replicas
    max_replica_count = var.max_replicas

    autoscaling_metric_specs {
      metric_name = "aiplatform.googleapis.com/prediction/online/accelerator/duty_cycle"
      target      = 70
    }
  }

  # Traffic split
  traffic_split = {
    "0" = 100
  }
}

# Service account for endpoint
resource "google_service_account" "vertex_sa" {
  account_id   = "vertex-ai-endpoint-sa"
  display_name = "Vertex AI Endpoint Service Account"
}

resource "google_project_iam_member" "vertex_permissions" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/storage.objectViewer",
    "roles/logging.logWriter"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.vertex_sa.email}"
}
```

### 2. Vector Search Infrastructure

```hcl
# vector_search.tf

# Vector index for embeddings
resource "google_vertex_ai_index" "embeddings_index" {
  display_name = "${var.app_name}-embeddings-index"
  region       = var.region
  project      = var.project_id

  description = "Vector search index for RAG application"

  metadata {
    contents_delta_uri = google_storage_bucket.embeddings.url

    config {
      dimensions                  = 768  # text-embedding-gecko dimensions
      approximate_neighbors_count = 150
      distance_measure_type       = "DOT_PRODUCT_DISTANCE"

      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 1000
          leaf_nodes_to_search_percent = 7
        }
      }

      shard_size = "SHARD_SIZE_MEDIUM"
    }
  }

  index_update_method = "STREAM_UPDATE"
}

# Index endpoint for queries
resource "google_vertex_ai_index_endpoint" "embeddings_endpoint" {
  display_name = "${var.app_name}-embeddings-endpoint"
  region       = var.region
  project      = var.project_id

  description = "Vector search endpoint"

  # Private VPC
  network = "projects/${data.google_project.project.number}/global/networks/${google_compute_network.vertex_vpc.name}"

  public_endpoint_enabled = false
}

# Deploy index to endpoint
resource "google_vertex_ai_index_endpoint_deployed_index" "deployed" {
  index_endpoint = google_vertex_ai_index_endpoint.embeddings_endpoint.id
  index          = google_vertex_ai_index.embeddings_index.id

  deployed_index_id = "deployed_embeddings_index"
  display_name      = "Deployed Embeddings Index"

  dedicated_resources {
    machine_spec {
      machine_type = "n1-standard-16"
    }

    min_replica_count = 2
    max_replica_count = 10

    autoscaling_metric_specs {
      metric_name = "aiplatform.googleapis.com/prediction/online/cpu/utilization"
      target      = 70
    }
  }

  enable_access_logging = true
}

# Storage bucket for embeddings
resource "google_storage_bucket" "embeddings" {
  name     = "${var.project_id}-${var.app_name}-embeddings"
  location = var.region

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 3
    }
    action {
      type = "Delete"
    }
  }
}
```

### 3. Custom Model Deployment

```hcl
# custom_model.tf

# Upload model to Cloud Storage
resource "google_storage_bucket" "model_artifacts" {
  name     = "${var.project_id}-ml-models"
  location = var.region

  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
}

resource "google_storage_bucket_object" "model_artifact" {
  name   = "models/${var.model_name}/model.pkl"
  bucket = google_storage_bucket.model_artifacts.name
  source = var.model_path
}

# Register model
resource "google_vertex_ai_model" "custom_model" {
  display_name = var.model_name
  region       = var.region
  project      = var.project_id

  description = "Custom ML model"

  version_aliases = ["production"]

  # Model artifact location
  artifact_uri = "gs://${google_storage_bucket.model_artifacts.name}/models/${var.model_name}/"

  # Container spec for serving
  container_spec {
    image_uri = "us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest"

    env {
      name  = "MODEL_NAME"
      value = var.model_name
    }

    ports {
      container_port = 8080
    }

    predict_route = "/predict"
    health_route  = "/health"
  }

  # Encryption
  encryption_spec {
    kms_key_name = google_kms_crypto_key.model_key.id
  }
}

# Create serving endpoint
resource "google_vertex_ai_endpoint" "model_endpoint" {
  display_name = "${var.model_name}-endpoint"
  location     = var.region
  project      = var.project_id

  network = google_compute_network.vertex_vpc.id
}

# Deploy model to endpoint
resource "google_vertex_ai_deployed_model" "deployed" {
  endpoint = google_vertex_ai_endpoint.model_endpoint.id
  model    = google_vertex_ai_model.custom_model.id

  display_name = "${var.model_name}-v1"

  dedicated_resources {
    machine_spec {
      machine_type = "n1-standard-4"

      accelerator_type  = "NVIDIA_TESLA_T4"
      accelerator_count = 1
    }

    min_replica_count = 1
    max_replica_count = 5

    autoscaling_metric_specs {
      metric_name = "aiplatform.googleapis.com/prediction/online/cpu/utilization"
      target      = 60
    }
  }

  traffic_split = {
    "0" = 100
  }
}
```

### 4. Vertex AI Pipelines

```hcl
# pipelines.tf

# Pipeline storage bucket
resource "google_storage_bucket" "pipeline_root" {
  name     = "${var.project_id}-pipeline-root"
  location = var.region

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# Artifact Registry for pipeline containers
resource "google_artifact_registry_repository" "pipeline_containers" {
  repository_id = "vertex-pipelines"
  location      = var.region
  format        = "DOCKER"

  description = "Container images for Vertex AI Pipelines"
}

# Service account for pipelines
resource "google_service_account" "pipeline_sa" {
  account_id   = "vertex-pipeline-runner"
  display_name = "Vertex AI Pipeline Runner"
}

resource "google_project_iam_member" "pipeline_permissions" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/storage.admin",
    "roles/bigquery.dataEditor",
    "roles/logging.logWriter"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

# Example: Training pipeline trigger
resource "google_cloudfunctions2_function" "pipeline_trigger" {
  name     = "trigger-training-pipeline"
  location = var.region

  build_config {
    runtime     = "python312"
    entry_point = "trigger_pipeline"

    source {
      storage_source {
        bucket = google_storage_bucket.pipeline_root.name
        object = "functions/trigger.zip"
      }
    }
  }

  service_config {
    available_memory   = "256M"
    timeout_seconds    = 60
    service_account_email = google_service_account.pipeline_sa.email

    environment_variables = {
      PROJECT_ID    = var.project_id
      PIPELINE_ROOT = "gs://${google_storage_bucket.pipeline_root.name}"
      REGION        = var.region
    }
  }
}
```

### 5. Feature Store

```hcl
# feature_store.tf

resource "google_vertex_ai_featurestore" "main" {
  name   = "${var.app_name}-featurestore"
  region = var.region

  online_serving_config {
    fixed_node_count = 1
  }

  encryption_spec {
    kms_key_name = google_kms_crypto_key.feature_key.id
  }

  force_destroy = false
}

# Entity type (e.g., users, items)
resource "google_vertex_ai_featurestore_entitytype" "users" {
  name         = "users"
  featurestore = google_vertex_ai_featurestore.main.id

  monitoring_config {
    snapshot_analysis {
      disabled = false
    }
  }
}

# Features
resource "google_vertex_ai_featurestore_entitytype_feature" "user_age" {
  name       = "age"
  entitytype = google_vertex_ai_featurestore_entitytype.users.id

  value_type = "INT64"

  description = "User age in years"
}

resource "google_vertex_ai_featurestore_entitytype_feature" "user_ltv" {
  name       = "lifetime_value"
  entitytype = google_vertex_ai_featurestore_entitytype.users.id

  value_type = "DOUBLE"

  description = "User lifetime value"
}
```

### 6. Batch Prediction

```hcl
# batch_prediction.tf

# Batch prediction job
resource "google_vertex_ai_batch_prediction_job" "batch_inference" {
  display_name = "${var.model_name}-batch-prediction"
  location     = var.region

  model = google_vertex_ai_model.custom_model.id

  input_config {
    instances_format = "jsonl"

    gcs_source {
      uris = ["gs://${google_storage_bucket.model_artifacts.name}/batch-input/*.jsonl"]
    }
  }

  output_config {
    predictions_format = "jsonl"

    gcs_destination {
      output_uri_prefix = "gs://${google_storage_bucket.model_artifacts.name}/batch-output/"
    }
  }

  dedicated_resources {
    machine_spec {
      machine_type      = "n1-standard-4"
      accelerator_type  = "NVIDIA_TESLA_T4"
      accelerator_count = 1
    }

    starting_replica_count = 1
    max_replica_count      = 10
  }

  service_account = google_service_account.vertex_sa.email
}
```

### 7. Monitoring & Observability

```hcl
# monitoring.tf

# Dashboard for model endpoints
resource "google_monitoring_dashboard" "vertex_dashboard" {
  dashboard_json = jsonencode({
    displayName = "${var.app_name} Vertex AI Dashboard"

    mosaicLayout = {
      columns = 12

      tiles = [
        # Prediction requests
        {
          width  = 6
          height = 4
          widget = {
            title = "Prediction Requests"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"aiplatform.googleapis.com/prediction/online/prediction_count\" resource.type=\"aiplatform.googleapis.com/Endpoint\""
                  }
                }
              }]
            }
          }
        },

        # Prediction latency
        {
          xPos   = 6
          width  = 6
          height = 4
          widget = {
            title = "Prediction Latency (p95)"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"aiplatform.googleapis.com/prediction/online/response_latencies\" resource.type=\"aiplatform.googleapis.com/Endpoint\""

                    aggregation = {
                      alignmentPeriod     = "60s"
                      perSeriesAligner    = "ALIGN_DELTA"
                      crossSeriesReducer  = "REDUCE_PERCENTILE_95"
                    }
                  }
                }
              }]
            }
          }
        },

        # Error rate
        {
          yPos   = 4
          width  = 6
          height = 4
          widget = {
            title = "Error Rate"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"aiplatform.googleapis.com/prediction/online/error_count\" resource.type=\"aiplatform.googleapis.com/Endpoint\""
                  }
                }
              }]
            }
          }
        },

        # Replica utilization
        {
          xPos   = 6
          yPos   = 4
          width  = 6
          height = 4
          widget = {
            title = "Replica Utilization"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"aiplatform.googleapis.com/prediction/online/replicas\" resource.type=\"aiplatform.googleapis.com/Endpoint\""
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

# Alert: High latency
resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "${var.app_name} - High Prediction Latency"
  combiner     = "OR"

  conditions {
    display_name = "P95 latency > 5s"

    condition_threshold {
      filter          = "metric.type=\"aiplatform.googleapis.com/prediction/online/response_latencies\" resource.type=\"aiplatform.googleapis.com/Endpoint\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5000

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]
}

# Alert: High error rate
resource "google_monitoring_alert_policy" "high_errors" {
  display_name = "${var.app_name} - High Error Rate"
  combiner     = "OR"

  conditions {
    display_name = "Error rate > 5%"

    condition_threshold {
      filter          = "metric.type=\"aiplatform.googleapis.com/prediction/online/error_count\" resource.type=\"aiplatform.googleapis.com/Endpoint\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]
}
```

## Variables

```hcl
# variables.tf

variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "Region for Vertex AI resources"
  type        = string
  default     = "us-central1"
}

variable "app_name" {
  description = "Application name prefix"
  type        = string
}

# Endpoint configuration
variable "min_replicas" {
  description = "Minimum number of replicas"
  type        = number
  default     = 1
}

variable "max_replicas" {
  description = "Maximum number of replicas"
  type        = number
  default     = 10
}

# Model configuration
variable "model_name" {
  description = "Custom model name"
  type        = string
}

variable "model_path" {
  description = "Local path to model artifact"
  type        = string
}

# Vector search
variable "embedding_dimensions" {
  description = "Dimensions for embeddings (768 for gecko, 1536 for OpenAI)"
  type        = number
  default     = 768
}

# Alerting
variable "alert_email" {
  description = "Email for monitoring alerts"
  type        = string
}
```

## Deployment Workflow

### 1. Initialize Terraform

```bash
terraform init
```

### 2. Plan Infrastructure

```bash
terraform plan \
  -var="project_id=my-project" \
  -var="app_name=my-app" \
  -var="model_name=custom-model" \
  -var="model_path=./model.pkl" \
  -var="alert_email=alerts@example.com"
```

### 3. Apply Configuration

```bash
terraform apply \
  -var="project_id=my-project" \
  -var="app_name=my-app" \
  -var="model_name=custom-model" \
  -var="model_path=./model.pkl" \
  -var="alert_email=alerts@example.com"
```

### 4. Verify Deployment

```bash
# Check endpoints
gcloud ai endpoints list --region=us-central1

# Check deployed models
gcloud ai models list --region=us-central1

# Check vector search indexes
gcloud ai indexes list --region=us-central1

# Test prediction
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT/locations/us-central1/endpoints/ENDPOINT_ID:predict \
  -d '{"instances": [{"feature1": 1.0, "feature2": "value"}]}'
```

## Integration with Other Plugins

### jeremy-adk-terraform
- jeremy-adk-terraform: Agent Engine (ADK agents)
- jeremy-vertex-terraform: Model serving & ML infrastructure (this plugin)

### jeremy-vertex-engine
- Terraform provisions endpoints → Engine inspector validates (for Agent Engine only)

### jeremy-vertex-validator
- Terraform provisions infrastructure → Validator checks production readiness

## Use Cases

### Gemini API Deployment
```
"Create Terraform for Gemini 2.0 Flash endpoint"
"Deploy Gemini Pro with auto-scaling"
```

### Vector Search for RAG
```
"Set up vector search infrastructure for RAG application"
"Deploy embeddings index with 768 dimensions"
```

### Custom Model Serving
```
"Deploy custom scikit-learn model to Vertex AI"
"Create endpoint for TensorFlow model with GPU"
```

### Batch Predictions
```
"Set up batch prediction job for large dataset"
"Deploy batch inference with T4 GPUs"
```

### Feature Store
```
"Create Feature Store for user features"
"Deploy feature serving for real-time predictions"
```

## Best Practices

✅ **Private Endpoints**: Use VPC for production endpoints
✅ **Auto-scaling**: Configure based on traffic patterns
✅ **Monitoring**: Deploy dashboards and alerts
✅ **Encryption**: Use CMEK for sensitive models
✅ **Version Control**: Tag model versions
✅ **Cost Optimization**: Use preemptible VMs for batch jobs
✅ **Traffic Splitting**: Blue/green deployments
✅ **Model Registry**: Organize models in Vertex AI Model Registry

## Requirements

- Terraform >= 1.5.0
- Google Cloud Provider >= 5.0
- Google Cloud Project with billing enabled
- Appropriate IAM permissions
- Model artifacts prepared
- gcloud CLI

## License

MIT

## Support

- Issues: https://github.com/jeremylongshore/claude-code-plugins/issues
- Discussions: https://github.com/jeremylongshore/claude-code-plugins/discussions

## Version

1.0.1 (2025) - Comprehensive Vertex AI infrastructure (Model Garden, Vector Search, Pipelines)
