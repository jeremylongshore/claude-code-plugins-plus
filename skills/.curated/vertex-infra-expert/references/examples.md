# Vertex AI Terraform Examples

## Example 1: Deploy a Gemini Endpoint with Autoscaling

Provision a Vertex AI endpoint with a deployed Gemini model and configure autoscaling.

```hcl
# variables.tf
variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

# main.tf
resource "google_vertex_ai_endpoint" "gemini" {
  display_name = "gemini-production"
  location     = var.region
  project      = var.project_id

  encryption_spec {
    kms_key_name = google_kms_crypto_key.vertex_key.id
  }
}

resource "google_vertex_ai_endpoint_deployed_model" "gemini_flash" {
  endpoint = google_vertex_ai_endpoint.gemini.id

  model             = "publishers/google/models/gemini-2.0-flash"
  display_name      = "gemini-flash-prod"
  dedicated_resources {
    min_replica_count = 1
    max_replica_count = 5
    machine_spec {
      machine_type = "n1-standard-4"
    }
    autoscaling_metric_specs {
      metric_name = "aiplatform.googleapis.com/prediction/online/cpu/utilization"
      target      = 70
    }
  }
}
```

**Smoke test:**

```bash
ENDPOINT_ID=$(terraform output -raw endpoint_id)
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/endpoints/${ENDPOINT_ID}:predict" \
  -d '{"instances": [{"content": "Summarize the benefits of cloud computing"}]}'
```

## Example 2: Vector Search Index for RAG

Create a Vertex AI Vector Search index for retrieval-augmented generation.

```hcl
resource "google_storage_bucket" "embeddings" {
  name     = "${var.project_id}-vector-embeddings"
  location = var.region
  uniform_bucket_level_access = true
}

resource "google_vertex_ai_index" "rag_index" {
  display_name = "rag-document-index"
  region       = var.region

  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.embeddings.name}/index-data"
    config {
      dimensions                  = 768
      approximate_neighbors_count = 50
      shard_size                  = "SHARD_SIZE_SMALL"

      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 1000
          leaf_nodes_to_search_percent = 10
        }
      }
    }
  }

  index_update_method = "STREAM_UPDATE"
}

resource "google_vertex_ai_index_endpoint" "rag_endpoint" {
  display_name = "rag-index-endpoint"
  region       = var.region
  network      = google_compute_network.main.id
}

resource "google_vertex_ai_index_endpoint_deployed_index" "rag_deployed" {
  index_endpoint   = google_vertex_ai_index_endpoint.rag_endpoint.id
  index            = google_vertex_ai_index.rag_index.id
  deployed_index_id = "rag_index_deployed"

  dedicated_resources {
    min_replica_count = 1
    max_replica_count = 3
    machine_spec {
      machine_type = "e2-standard-2"
    }
  }
}
```

**Validation:**

```bash
# Check index build status
gcloud ai indexes describe rag-document-index \
  --project=$PROJECT_ID --region=$REGION \
  --format='value(metadata.config.dimensions, indexStats)'

# Query the index
gcloud ai index-endpoints query rag-index-endpoint \
  --deployed-index-id=rag_index_deployed \
  --region=$REGION \
  --num-neighbors=5 \
  --queries-file=query_embeddings.json
```

## Example 3: ML Pipeline with Vertex AI Pipelines

Schedule recurring ML pipelines for fine-tuning and evaluation.

```hcl
resource "google_vertex_ai_pipeline_job" "weekly_eval" {
  display_name = "weekly-model-evaluation"
  location     = var.region

  pipeline_spec = jsonencode({
    pipelineInfo = { name = "model-eval" }
    root = {
      dag = {
        tasks = {
          evaluate = {
            taskInfo = { name = "evaluate-model" }
            componentRef = { name = "eval-component" }
            inputs = {
              parameters = {
                model_name    = { runtimeValue = { constant = "gemini-2.0-flash" } }
                eval_dataset  = { runtimeValue = { constant = "gs://${var.project_id}-eval/dataset.jsonl" } }
              }
            }
          }
        }
      }
    }
  })

  service_account = google_service_account.pipeline_runner.email
}

resource "google_cloud_scheduler_job" "pipeline_trigger" {
  name     = "weekly-eval-trigger"
  schedule = "0 2 * * 0"

  http_target {
    uri         = "https://${var.region}-aiplatform.googleapis.com/v1/projects/${var.project_id}/locations/${var.region}/pipelineJobs"
    http_method = "POST"
    oauth_token {
      service_account_email = google_service_account.pipeline_runner.email
    }
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
