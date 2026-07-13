# Genkit Terraform - Implementation Details

## Configuration

### Backend and Provider Setup

```hcl
terraform {
  required_version = ">= 1.0"

  backend "gcs" {
    bucket = "my-project-tf-state"
    prefix = "genkit-infrastructure"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
```

### Required Variables

```hcl
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Primary deployment region"
  type        = string
  default     = "us-central1"
}

variable "deploy_target" {
  description = "Deployment target: cloud_run, firebase_functions, or gke"
  type        = string
  default     = "cloud_run"
  validation {
    condition     = contains(["cloud_run", "firebase_functions", "gke"], var.deploy_target)
    error_message = "deploy_target must be cloud_run, firebase_functions, or gke."
  }
}
```

## Module Structure

```
modules/
├── cloud-run/          # Cloud Run service + IAM + domain mapping
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── firebase-functions/ # Cloud Functions 2nd gen + triggers
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── gke/                # GKE cluster + node pools + workload identity
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── secrets/            # Secret Manager for API keys
│   ├── main.tf
│   └── outputs.tf
└── monitoring/         # Cloud Monitoring dashboards + alerts
    ├── main.tf
    └── variables.tf
```

## Advanced Patterns

### Secret Manager Integration

All Genkit flows that call Gemini or external APIs need secrets. Use Secret Manager with IAM bindings rather than environment variable injection:

```hcl
resource "google_secret_manager_secret" "api_keys" {
  for_each  = toset(["GOOGLE_GENAI_API_KEY", "OPENAI_API_KEY"])
  secret_id = lower(replace(each.key, "_", "-"))
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_iam_member" "access" {
  for_each  = google_secret_manager_secret.api_keys
  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.genkit_runner.email}"
}
```

### Cloud Run Traffic Splitting for Canary Deployments

```hcl
resource "google_cloud_run_v2_service" "genkit_api" {
  name     = "genkit-api"
  location = var.region

  traffic {
    percent  = 90
    revision = "genkit-api-stable"
  }
  traffic {
    percent  = 10
    revision = "genkit-api-canary"
    tag      = "canary"
  }
}
```

### Monitoring Dashboard for Token Usage

```hcl
resource "google_monitoring_dashboard" "genkit" {
  dashboard_json = jsonencode({
    displayName = "Genkit Flows Dashboard"
    mosaicLayout = {
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "Request Latency (p50/p95/p99)"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_latencies\""
                  }
                }
              }]
            }
          }
        },
        {
          xPos   = 6
          width  = 6
          height = 4
          widget = {
            title = "Instance Count"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/container/instance_count\""
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

## Troubleshooting

### Cold Start Latency

Cloud Run cold starts are slow for Genkit because it loads model configs at startup. Mitigate with:

```hcl
# Set min instances to avoid cold starts
scaling {
  min_instance_count = 1
}

# Use startup CPU boost
annotations = {
  "run.googleapis.com/startup-cpu-boost" = "true"
}
```

### Firebase Functions Timeout

Default Cloud Functions timeout is 60s, which is insufficient for LLM calls. Increase to 300s:

```hcl
service_config {
  timeout_seconds = 300
}
```

### Container Image Size

Genkit images can be large (1GB+) due to Node.js dependencies. Use multi-stage builds:

```dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3400
CMD ["node", "dist/index.js"]
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
