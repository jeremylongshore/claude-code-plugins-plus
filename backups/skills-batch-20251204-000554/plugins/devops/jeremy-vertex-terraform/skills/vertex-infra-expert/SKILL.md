---
name: vertex-infra-expert
description: |
  Terraform infrastructure specialist for Vertex AI services and Gemini deployments.
  Provisions Model Garden, endpoints, vector search, pipelines, and enterprise AI infrastructure.
  Triggers: "vertex ai terraform", "gemini deployment terraform", "model garden infrastructure", "vertex ai endpoints"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## What This Skill Does

Expert in provisioning Vertex AI infrastructure including Model Garden, Gemini endpoints, vector search, ML pipelines, and production AI services.

## When This Skill Activates

Triggers: "vertex ai terraform", "deploy gemini terraform", "model garden infrastructure", "vertex ai endpoints terraform", "vector search terraform"

## Core Terraform Modules

### Gemini Model Endpoint

```hcl
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

  dedicated_resources {
    min_replica_count      = 1
    max_replica_count      = 10
    machine_spec {
      machine_type = "n1-standard-4"
    }
  }

  automatic_resources {
    min_replica_count = 1
    max_replica_count = 5
  }
}
```

### Vector Search Index

```hcl
resource "google_vertex_ai_index" "embeddings_index" {
  display_name = "production-embeddings"
  location     = var.region

  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.embeddings.name}/index"
    config {
      dimensions                  = 768
      approximate_neighbors_count = 150
      distance_measure_type       = "DOT_PRODUCT_DISTANCE"

      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 1000
          leaf_nodes_to_search_percent = 10
        }
      }
    }
  }
}
```

## Tool Permissions

Read, Write, Edit, Grep, Glob, Bash - AI infrastructure provisioning

## References

- Vertex AI Terraform: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/vertex_ai_endpoint
