---
description: Use when provisioning Vertex AI infrastructure with Terraform. Trigger with phrases like "vertex ai terraform", "deploy gemini terraform", "model garden infrastructure", "vertex ai endpoints terraform", or "vector search terraform". Provisions Model Garden models, Gemini endpoints, vector search indices, ML pipelines, and production AI services with encryption and auto-scaling.
allowed-tools:
- Read
- Write
- Edit
- Grep
- Glob
- Bash(terraform:*)
- Bash(gcloud:*)
name: vertex-infra-expert
license: MIT
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

## Prerequisites

Before using this skill, ensure:
- Google Cloud project with Vertex AI API enabled
- Terraform 1.0+ installed
- gcloud CLI authenticated with appropriate permissions
- Understanding of Vertex AI services and ML models
- KMS keys created for encryption (if required)
- GCS buckets for model artifacts and embeddings

## Instructions

1. **Define AI Services**: Identify required Vertex AI components (endpoints, vector search, pipelines)
2. **Configure Terraform**: Set up backend and define project variables
3. **Provision Endpoints**: Deploy Gemini or custom model endpoints with auto-scaling
4. **Set Up Vector Search**: Create indices for embeddings with appropriate dimensions
5. **Configure Encryption**: Apply KMS encryption to endpoints and data
6. **Implement Monitoring**: Set up Cloud Monitoring for model performance
7. **Apply IAM Policies**: Grant least privilege access to AI services
8. **Validate Deployment**: Test endpoints and verify model availability

## Output

**Gemini Model Endpoint:**
```hcl
# {baseDir}/terraform/vertex-endpoints.tf
resource "google_vertex_ai_endpoint" "gemini_endpoint" {
  name         = "gemini-25-flash-endpoint"
  display_name = "Gemini 2.5 Flash Production"
  location     = var.region

  encryption_spec {
    kms_key_name = google_kms_crypto_key.vertex_key.id
  }
}

resource "google_vertex_ai_deployed_model" "gemini_deployment" {
  endpoint = google_vertex_ai_endpoint.gemini_endpoint.id
  model    = "publishers/google/models/gemini-2.5-flash"

  automatic_resources {
    min_replica_count = 1
    max_replica_count = 5
  }
}
```

**Vector Search Index:**
```hcl
resource "google_vertex_ai_index" "embeddings_index" {
  display_name = "production-embeddings"
  location     = var.region

  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.embeddings.name}/index"
    config {
      dimensions = 768
      approximate_neighbors_count = 150
      distance_measure_type = "DOT_PRODUCT_DISTANCE"

      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count = 1000
          leaf_nodes_to_search_percent = 10
        }
      }
    }
  }
}
```

## Error Handling

**API Not Enabled**
- Error: "Vertex AI API has not been used in project"
- Solution: Enable with `gcloud services enable aiplatform.googleapis.com`

**Model Not Found**
- Error: "Model publishers/google/models/... not found"
- Solution: Verify model ID and region availability

**Quota Exceeded**
- Error: "Quota exceeded for resource"
- Solution: Request quota increase or reduce replica count

**KMS Key Access Denied**
- Error: "Permission denied on KMS key"
- Solution: Grant cloudkms.cryptoKeyEncrypterDecrypter role to Vertex AI service account

**Vector Search Build Failed**
- Error: "Index build failed"
- Solution: Check GCS bucket permissions and embedding format

## Resources

- Vertex AI Terraform: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/vertex_ai_endpoint
- Vertex AI documentation: https://cloud.google.com/vertex-ai/docs
- Model Garden: https://cloud.google.com/model-garden
- Vector Search guide: https://cloud.google.com/vertex-ai/docs/vector-search
- Terraform examples in {baseDir}/vertex-examples/
