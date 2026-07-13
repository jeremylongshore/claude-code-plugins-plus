# Vertex AI Terraform - Implementation Details

## Configuration

### Backend and Provider Setup

```hcl
terraform {
  required_version = ">= 1.0"

  backend "gcs" {
    bucket = "my-project-tf-state"
    prefix = "vertex-ai-infrastructure"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}
```

### Required Variables

```hcl
variable "project_id" {
  description = "GCP project ID with Vertex AI enabled"
  type        = string
}

variable "region" {
  description = "Region for Vertex AI resources"
  type        = string
  default     = "us-central1"
}

variable "kms_key_id" {
  description = "KMS key for CMEK encryption (optional)"
  type        = string
  default     = null
}
```

## Module Structure

```
modules/
├── endpoints/          # Vertex AI endpoints + deployed models
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── vector-search/      # Vector Search indices + endpoints
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── pipelines/          # ML pipeline definitions + scheduling
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── iam/                # Service accounts + least-privilege roles
│   ├── main.tf
│   └── outputs.tf
├── networking/         # VPC peering for private endpoints
│   ├── main.tf
│   └── outputs.tf
└── monitoring/         # Dashboards + alerting policies
    ├── main.tf
    └── variables.tf
```

## Advanced Patterns

### CMEK Encryption for Endpoints

All production endpoints should use Customer-Managed Encryption Keys:

```hcl
resource "google_kms_key_ring" "vertex" {
  name     = "vertex-ai-keyring"
  location = var.region
}

resource "google_kms_crypto_key" "vertex_key" {
  name     = "vertex-ai-key"
  key_ring = google_kms_key_ring.vertex.id
  purpose  = "ENCRYPT_DECRYPT"

  rotation_period = "7776000s"  # 90 days

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_kms_crypto_key_iam_member" "vertex_encrypter" {
  crypto_key_id = google_kms_crypto_key.vertex_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-aiplatform.iam.gserviceaccount.com"
}
```

### Private Endpoints via VPC Peering

```hcl
resource "google_compute_global_address" "vertex_peering" {
  name          = "vertex-ai-peering-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
}

resource "google_service_networking_connection" "vertex" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.vertex_peering.name]
}

resource "google_vertex_ai_index_endpoint" "private" {
  display_name = "private-rag-endpoint"
  region       = var.region
  network      = google_compute_network.main.id

  depends_on = [google_service_networking_connection.vertex]
}
```

### Autoscaling Metric Configuration

```hcl
# Scale on GPU utilization for custom model endpoints
dedicated_resources {
  min_replica_count = 1
  max_replica_count = 10
  machine_spec {
    machine_type      = "n1-standard-8"
    accelerator_type  = "NVIDIA_TESLA_T4"
    accelerator_count = 1
  }
  autoscaling_metric_specs {
    metric_name = "aiplatform.googleapis.com/prediction/online/accelerator/duty_cycle"
    target      = 60
  }
}
```

## Troubleshooting

### Endpoint Deployment Timeout

Model deployment can take 10-30 minutes. Increase Terraform timeout:

```hcl
resource "google_vertex_ai_endpoint_deployed_model" "model" {
  timeouts {
    create = "45m"
    delete = "30m"
  }
}
```

### Vector Search Index Build Failures

Index builds fail if embedding data is malformed. Validate before creating:

```bash
# Check embedding format in GCS
gsutil cat gs://BUCKET/index-data/embeddings.json | head -1 | python3 -c "
import json, sys
doc = json.loads(sys.stdin.read())
print(f'ID: {doc[\"id\"]}, dims: {len(doc[\"embedding\"])}')
"
```

### Quota Exhaustion

Check Vertex AI quotas before scaling:

```bash
gcloud alpha quotas info list \
  --project=PROJECT_ID \
  --service=aiplatform.googleapis.com \
  --filter="metric:prediction" \
  --format="table(metric,value,limit)"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
