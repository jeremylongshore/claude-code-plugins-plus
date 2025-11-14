# Jeremy ADK Terraform

**🎯 VERTEX AI AGENT ENGINE INFRASTRUCTURE ONLY**

Terraform infrastructure-as-code specialist for deploying **ADK agents to Vertex AI Agent Engine** with complete observability, security, and production-ready configurations.

## ⚠️ Important: What This Plugin Is For

**✅ THIS PLUGIN IS FOR:**
- **Vertex AI Agent Engine** infrastructure (fully-managed runtime)
- **ADK agents** Terraform deployment (`google_vertex_ai_reasoning_engine`)
- **Agent Engine features**: Code Execution Sandbox, Memory Bank, VPC-SC, IAM
- **Observability infrastructure**: Cloud Monitoring dashboards, alert policies, BigQuery connectors
- **Production ADK deployments** with security hardening

**❌ THIS PLUGIN IS NOT FOR:**
- Cloud Run deployments (use `jeremy-genkit-terraform`)
- LangChain/LlamaIndex on other platforms
- Self-hosted agent infrastructure
- Non-Agent Engine Terraform

## Overview

This plugin provides Terraform modules and configurations for deploying ADK agents to Vertex AI Agent Engine with production-ready infrastructure including VPC Service Controls, IAM least privilege, Code Execution Sandbox configuration, Memory Bank setup, observability dashboards, and BigQuery analytics connectors.

**Key Infrastructure Components:**
- `google_vertex_ai_reasoning_engine` resource for Agent Engine
- VPC Service Controls perimeter
- IAM roles and service accounts
- Cloud Monitoring dashboards and alerts
- BigQuery datasets for agent analytics
- Cloud Storage buckets for artifacts
- Secret Manager for credentials

## Installation

```bash
/plugin install jeremy-adk-terraform@claude-code-plugins-plus
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

# Install alpha commands (for Agent Engine)
gcloud components install alpha

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
    discoveryengine.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    cloudtrace.googleapis.com \
    bigquery.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com \
    compute.googleapis.com \
    servicenetworking.googleapis.com \
    --project=YOUR_PROJECT_ID
```

### Required IAM Permissions

```yaml
# Service account for Terraform needs:
- roles/aiplatform.admin              # Deploy Agent Engine resources
- roles/iam.serviceAccountAdmin       # Create service accounts
- roles/resourcemanager.projectIamAdmin  # Manage IAM bindings
- roles/compute.networkAdmin          # VPC configuration
- roles/monitoring.admin              # Create dashboards/alerts
- roles/bigquery.admin                # Create datasets
- roles/storage.admin                 # Create buckets
```

## Features

✅ **Agent Engine Deployment**: `google_vertex_ai_reasoning_engine` with ADK framework
✅ **Code Execution Sandbox**: Secure isolation, state persistence (1-14 days TTL)
✅ **Memory Bank**: Firestore-backed persistent memory with retention policies
✅ **VPC Service Controls**: Perimeter security for Agent Engine
✅ **IAM Least Privilege**: Service accounts with minimal permissions
✅ **Observability Infrastructure**: Dashboards, alerts, SLOs, token tracking
✅ **BigQuery Analytics**: Automated log export and analytics datasets
✅ **Cloud Storage**: Artifact storage with lifecycle policies
✅ **Secret Management**: API keys and credentials in Secret Manager
✅ **Multi-Region**: Agent Engine deployments in multiple regions

## Quick Start

### Natural Language Activation

Simply mention what you need:

```
"Create Terraform for ADK agent deployment to Agent Engine"
"Provision Agent Engine infrastructure with VPC-SC"
"Deploy ADK agent with Code Execution and Memory Bank"
"Set up observability infrastructure for Agent Engine"
"Create multi-region Agent Engine deployment"
```

The skill auto-activates and generates production-ready Terraform.

## Terraform Module Structure

### Core Agent Engine Resource

```hcl
# main.tf
resource "google_vertex_ai_reasoning_engine" "adk_agent" {
  display_name = var.agent_name
  region       = var.region
  project      = var.project_id

  spec {
    # REQUIRED: Specify ADK framework
    agent_framework = "google-adk"

    # Agent package (ADK agent code)
    package_spec {
      pickle_object_gcs_uri    = google_storage_bucket_object.agent_package.self_link
      python_version           = "3.12"
      requirements_gcs_uri     = google_storage_bucket_object.requirements.self_link
    }

    # Runtime configuration
    runtime_config {
      # Code Execution Sandbox
      code_execution_config {
        enabled                  = true
        state_persistence_ttl_days = var.code_exec_ttl_days  # 1-14 days
      }

      # Memory Bank
      memory_bank_config {
        enabled       = true
        max_memories  = var.memory_bank_max_memories
        retention_days = var.memory_bank_retention_days
      }

      # Auto-scaling
      auto_scaling_config {
        min_replica_count = var.min_replicas
        max_replica_count = var.max_replicas
      }

      # VPC configuration
      vpc_config {
        network    = google_compute_network.agent_vpc.id
        subnetwork = google_compute_subnetwork.agent_subnet.id
      }
    }

    # Security
    encryption_config {
      kms_key_name = google_kms_crypto_key.agent_key.id
    }
  }

  # Service account
  service_account = google_service_account.agent_sa.email

  # Model Armor (prompt injection protection)
  model_armor_enabled = true

  depends_on = [
    google_project_service.aiplatform,
    google_storage_bucket_object.agent_package
  ]
}
```

### IAM Configuration

```hcl
# iam.tf
resource "google_service_account" "agent_sa" {
  account_id   = "${var.agent_name}-sa"
  display_name = "Service Account for ${var.agent_name}"
  project      = var.project_id
}

# Least privilege permissions
resource "google_project_iam_member" "agent_permissions" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
    "roles/discoveryengine.editor"  # For Memory Bank
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Code Execution Sandbox permissions (minimal)
resource "google_service_account" "code_exec_sa" {
  account_id   = "${var.agent_name}-code-exec-sa"
  display_name = "Code Execution SA for ${var.agent_name}"
}

resource "google_project_iam_member" "code_exec_permissions" {
  for_each = toset([
    "roles/storage.objectViewer",  # Read artifacts only
    "roles/logging.logWriter"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.code_exec_sa.email}"
}
```

### VPC Service Controls

```hcl
# vpc_sc.tf
resource "google_access_context_manager_service_perimeter" "agent_perimeter" {
  parent = "accessPolicies/${var.access_policy_id}"
  name   = "accessPolicies/${var.access_policy_id}/servicePerimeters/${var.agent_name}_perimeter"
  title  = "${var.agent_name} Agent Engine Perimeter"

  status {
    restricted_services = [
      "aiplatform.googleapis.com",
      "discoveryengine.googleapis.com",
      "storage.googleapis.com"
    ]

    resources = [
      "projects/${data.google_project.project.number}"
    ]

    vpc_accessible_services {
      enable_restriction = true
      allowed_services = [
        "aiplatform.googleapis.com",
        "discoveryengine.googleapis.com"
      ]
    }
  }
}
```

### Observability Infrastructure (2025 Features)

```hcl
# monitoring.tf

# Cloud Monitoring Dashboard
resource "google_monitoring_dashboard" "agent_dashboard" {
  dashboard_json = jsonencode({
    displayName = "${var.agent_name} Agent Engine Dashboard"

    mosaicLayout = {
      columns = 12

      tiles = [
        # Request Volume
        {
          width  = 6
          height = 4
          widget = {
            title = "Request Volume"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"aiplatform.googleapis.com/agent/request_count\" resource.type=\"aiplatform.googleapis.com/Agent\""
                  }
                }
              }]
            }
          }
        },

        # Error Rate
        {
          xPos   = 6
          width  = 6
          height = 4
          widget = {
            title = "Error Rate"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"aiplatform.googleapis.com/agent/error_count\" resource.type=\"aiplatform.googleapis.com/Agent\""
                  }
                }
              }]
            }
          }
        },

        # Latency Distribution
        {
          yPos   = 4
          width  = 6
          height = 4
          widget = {
            title = "Latency (p50, p95, p99)"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"aiplatform.googleapis.com/agent/prediction_latencies\" resource.type=\"aiplatform.googleapis.com/Agent\""
                  }
                }
              }]
            }
          }
        },

        # Token Usage
        {
          xPos   = 6
          yPos   = 4
          width  = 6
          height = 4
          widget = {
            title = "Token Usage"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"aiplatform.googleapis.com/agent/token_count\" resource.type=\"aiplatform.googleapis.com/Agent\""
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

# Alert Policy: High Error Rate
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "${var.agent_name} - High Error Rate"
  combiner     = "OR"

  conditions {
    display_name = "Error rate > 5% for 5 minutes"

    condition_threshold {
      filter          = "metric.type=\"aiplatform.googleapis.com/agent/error_count\" resource.type=\"aiplatform.googleapis.com/Agent\""
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

  alert_strategy {
    auto_close = "86400s"
  }
}

# Alert Policy: High Latency
resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "${var.agent_name} - High Latency"
  combiner     = "OR"

  conditions {
    display_name = "P95 latency > 10s"

    condition_threshold {
      filter          = "metric.type=\"aiplatform.googleapis.com/agent/prediction_latencies\" resource.type=\"aiplatform.googleapis.com/Agent\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10000  # milliseconds

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]
}

# Notification Channel
resource "google_monitoring_notification_channel" "email" {
  display_name = "${var.agent_name} Alerts"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }
}
```

### BigQuery Analytics (2025 Feature)

```hcl
# bigquery.tf

# Dataset for agent analytics
resource "google_bigquery_dataset" "agent_analytics" {
  dataset_id = "${replace(var.agent_name, "-", "_")}_analytics"
  location   = var.region
  project    = var.project_id

  description = "Analytics dataset for ${var.agent_name}"

  delete_contents_on_destroy = false
}

# Table for agent logs
resource "google_bigquery_table" "agent_logs" {
  dataset_id = google_bigquery_dataset.agent_analytics.dataset_id
  table_id   = "agent_logs"
  project    = var.project_id

  deletion_protection = true

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  schema = jsonencode([
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "agent_id"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "task_id"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "session_id"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "latency_ms"
      type = "FLOAT"
      mode = "NULLABLE"
    },
    {
      name = "input_tokens"
      type = "INTEGER"
      mode = "NULLABLE"
    },
    {
      name = "output_tokens"
      type = "INTEGER"
      mode = "NULLABLE"
    },
    {
      name = "error_count"
      type = "INTEGER"
      mode = "NULLABLE"
    },
    {
      name = "error_message"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "component"
      type = "STRING"
      mode = "NULLABLE"
      description = "AGENT_QUERIES, MEMORY_BANK_OPERATIONS, CODE_EXECUTION_EVENTS, A2A_PROTOCOL_CALLS"
    }
  ])
}

# Log sink to BigQuery
resource "google_logging_project_sink" "agent_to_bigquery" {
  name        = "${var.agent_name}-to-bigquery"
  destination = "bigquery.googleapis.com/projects/${var.project_id}/datasets/${google_bigquery_dataset.agent_analytics.dataset_id}"

  filter = "resource.type=\"aiplatform.googleapis.com/Agent\" resource.labels.agent_id=\"${google_vertex_ai_reasoning_engine.adk_agent.name}\""

  unique_writer_identity = true

  bigquery_options {
    use_partitioned_tables = true
  }
}

# Grant sink permission to write to BigQuery
resource "google_bigquery_dataset_iam_member" "sink_writer" {
  dataset_id = google_bigquery_dataset.agent_analytics.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = google_logging_project_sink.agent_to_bigquery.writer_identity
}
```

### Cloud Storage for Artifacts

```hcl
# storage.tf

# Bucket for agent artifacts
resource "google_storage_bucket" "agent_artifacts" {
  name     = "${var.project_id}-${var.agent_name}-artifacts"
  location = var.region
  project  = var.project_id

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
      matches_prefix = ["executions/", "logs/"]
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age                = 30
      matches_prefix     = ["executions/"]
      num_newer_versions = 3
    }
    action {
      type = "Delete"
    }
  }
}

# Grant agent access to artifacts
resource "google_storage_bucket_iam_member" "agent_artifacts_viewer" {
  bucket = google_storage_bucket.agent_artifacts.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Upload agent package
resource "google_storage_bucket_object" "agent_package" {
  name   = "agent-packages/${var.agent_name}/agent.pkl"
  bucket = google_storage_bucket.agent_artifacts.name
  source = var.agent_package_path
}

# Upload requirements
resource "google_storage_bucket_object" "requirements" {
  name    = "agent-packages/${var.agent_name}/requirements.txt"
  bucket  = google_storage_bucket.agent_artifacts.name
  content = file(var.requirements_path)
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
  description = "Region for Agent Engine deployment"
  type        = string
  default     = "us-central1"
}

variable "agent_name" {
  description = "Name of the ADK agent"
  type        = string
}

variable "agent_package_path" {
  description = "Local path to agent.pkl file"
  type        = string
}

variable "requirements_path" {
  description = "Local path to requirements.txt"
  type        = string
}

# Code Execution Sandbox
variable "code_exec_ttl_days" {
  description = "State persistence TTL for Code Execution Sandbox (1-14 days)"
  type        = number
  default     = 7

  validation {
    condition     = var.code_exec_ttl_days >= 1 && var.code_exec_ttl_days <= 14
    error_message = "TTL must be between 1 and 14 days"
  }
}

# Memory Bank
variable "memory_bank_max_memories" {
  description = "Maximum number of memories to retain"
  type        = number
  default     = 100
}

variable "memory_bank_retention_days" {
  description = "Memory retention period in days"
  type        = number
  default     = 90
}

# Auto-scaling
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
  -var="agent_name=my-adk-agent" \
  -var="agent_package_path=./agent.pkl" \
  -var="requirements_path=./requirements.txt" \
  -var="alert_email=alerts@example.com"
```

### 3. Apply Configuration

```bash
terraform apply \
  -var="project_id=my-project" \
  -var="agent_name=my-adk-agent" \
  -var="agent_package_path=./agent.pkl" \
  -var="requirements_path=./requirements.txt" \
  -var="alert_email=alerts@example.com"
```

### 4. Verify Deployment

```bash
# Check Agent Engine status
gcloud alpha ai agent-engines describe \
  projects/my-project/locations/us-central1/reasoningEngines/my-adk-agent

# Check monitoring dashboard
gcloud monitoring dashboards list --filter="displayName:my-adk-agent"

# Query BigQuery logs
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) as total_queries FROM `my-project.my_adk_agent_analytics.agent_logs`'
```

## Multi-Region Deployment

```hcl
# Multi-region deployment
module "agent_us_central1" {
  source = "./modules/agent-engine"

  project_id   = var.project_id
  region       = "us-central1"
  agent_name   = "${var.agent_name}-us-central1"
  agent_package_path = var.agent_package_path
  requirements_path  = var.requirements_path
}

module "agent_europe_west1" {
  source = "./modules/agent-engine"

  project_id   = var.project_id
  region       = "europe-west1"
  agent_name   = "${var.agent_name}-europe-west1"
  agent_package_path = var.agent_package_path
  requirements_path  = var.requirements_path
}

# Global load balancer for multi-region
resource "google_compute_global_forwarding_rule" "agent_lb" {
  name       = "${var.agent_name}-global-lb"
  target     = google_compute_target_http_proxy.agent_proxy.id
  port_range = "80"
}
```

## Integration with Other Plugins

### jeremy-vertex-engine
- Terraform provisions → Engine inspector validates
- Infrastructure deployment → Runtime inspection

### jeremy-adk-orchestrator
- Terraform creates Agent Engine resources → Orchestrator manages A2A communication
- Infrastructure layer → Communication layer

### jeremy-vertex-validator
- Terraform generates configs → Validator checks production readiness
- Infrastructure code → Validation checks

## Use Cases

### Basic ADK Agent Deployment
```
"Create Terraform for ADK agent with Code Execution and Memory Bank"
"Deploy ADK agent to Agent Engine in us-central1"
```

### Production Infrastructure
```
"Create production-ready Agent Engine infrastructure with VPC-SC"
"Deploy ADK agent with observability dashboards and alerts"
```

### Multi-Region Deployment
```
"Deploy ADK agent to multiple regions with global load balancer"
"Create multi-region Agent Engine infrastructure"
```

### Observability Setup
```
"Add monitoring dashboard and alerts to Agent Engine deployment"
"Configure BigQuery analytics for agent logs"
```

## Best Practices

✅ **State Management**: Use remote backend (GCS or Terraform Cloud)
✅ **Secret Management**: Store API keys in Secret Manager, never in code
✅ **IAM Least Privilege**: Grant minimal permissions to service accounts
✅ **VPC Service Controls**: Always enable for production
✅ **Encryption**: Use CMEK keys for data at rest
✅ **Monitoring**: Deploy dashboards and alerts with every agent
✅ **Multi-Region**: Deploy to 2+ regions for high availability
✅ **Lifecycle Policies**: Configure auto-cleanup for old artifacts
✅ **Code Execution TTL**: Set to 7-14 days for production
✅ **Memory Bank**: Configure appropriate retention (90+ days recommended)

## Requirements

- Terraform >= 1.5.0
- Google Cloud Provider >= 5.0
- Google Cloud Project with billing enabled
- Appropriate IAM permissions for Terraform service account
- ADK agent package (agent.pkl) and requirements.txt
- gcloud CLI with alpha components

## License

MIT

## Support

- Issues: https://github.com/jeremylongshore/claude-code-plugins/issues
- Discussions: https://github.com/jeremylongshore/claude-code-plugins/discussions

## Version

1.0.1 (2025) - Agent Engine Terraform with 2025 observability and storage features
