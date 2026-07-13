# Vertex AI Agent Builder -- Common Errors

## Model & API Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `404 NOT_FOUND: Model gemini-2.5-pro is not found` | Model not available in selected region | Switch to `us-central1` (broadest availability) or use `gemini-2.0-flash` |
| `400 INVALID_ARGUMENT: Request contains an invalid argument` | Malformed `GenerationConfig` (e.g., `temperature` > 2.0 or negative `max_output_tokens`) | Validate config: temperature 0.0-2.0, max_output_tokens > 0, top_k >= 1 |
| `429 RESOURCE_EXHAUSTED: Quota exceeded for GenerateContent` | Per-minute or per-day token quota hit | Reduce request rate, switch to flash model (higher quota), or request quota increase in GCP console |
| `500 INTERNAL: An internal error has occurred` | Transient Vertex AI backend issue | Retry with exponential backoff; if persistent, check [Vertex AI status](https://status.cloud.google.com/) |
| `ModuleNotFoundError: No module named 'vertexai'` | SDK not installed | `pip install google-cloud-aiplatform` (vertexai is included) |

## Authentication & IAM Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `google.auth.exceptions.DefaultCredentialsError` | No application default credentials configured | `gcloud auth application-default login` or set `GOOGLE_APPLICATION_CREDENTIALS` |
| `403 PERMISSION_DENIED: Vertex AI API has not been used in project` | API not enabled | `gcloud services enable aiplatform.googleapis.com --project=PROJECT_ID` |
| `403 PERMISSION_DENIED: The caller does not have permission` | Service account missing `aiplatform.user` role | `gcloud projects add-iam-policy-binding PROJECT_ID --member=serviceAccount:SA_EMAIL --role=roles/aiplatform.user` |
| `403 on Discovery Engine API` | Missing role for Vertex AI Search operations | Grant `roles/discoveryengine.editor` for RAG corpus management |
| `403 on GCS bucket access` | Agent Engine service account cannot read document source | Grant `roles/storage.objectViewer` on the source bucket to the Agent Engine SA |

## Agent Engine Deployment Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Agent Engine not available in region` | Agent Engine has limited regional availability | Use `us-central1` or `europe-west1` (GA regions) |
| `Deployment timed out` | Large dependencies or slow container build | Reduce dependency count, use slim base image, increase `--timeout` |
| `Health check failed after deployment` | Agent crashes on startup (import error, missing env var) | Check logs: `gcloud logging read 'resource.type="aiplatform.googleapis.com/Endpoint"' --limit=50` |
| `ReasoningEngine create failed: requirements.txt missing` | Agent Engine expects dependency manifest | Ensure `requirements.txt` in project root alongside agent code |
| `Version conflict: google-cloud-aiplatform` | Agent Engine runtime has different SDK version than local | Pin SDK version in `requirements.txt` to match Agent Engine runtime |

## RAG / Retrieval Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Retrieval returns empty results despite matching documents | Embedding dimension mismatch between query and index | Verify embedding model matches index config: `text-embedding-005` = 768 dims |
| `FAILED_PRECONDITION: Corpus is not ready` | Index still building after document import | Wait for indexing to complete; check status: `rag.get_corpus(name=CORPUS_NAME)` |
| Stale results after document update | Index not refreshed after new documents added | Trigger re-import: `rag.import_files(corpus_name=NAME, paths=[GCS_URI])` |
| Citations point to wrong chunks | Chunk size too large, overlapping content | Reduce chunk size (try 512 tokens), increase overlap to 10-20% |
| `400: Embedding dimension mismatch` | Index created with one embedding model, querying with another | Recreate index with correct model or switch query embedding to match |
| `Document too large for ingestion` | Single document exceeds 10MB limit | Split document before upload, or use GCS-based chunking |

## Function Calling Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Model ignores available tools | Function descriptions too vague or overlapping | Improve `FunctionDeclaration` descriptions; make each tool's purpose distinct |
| `INVALID_ARGUMENT: function_declarations schema error` | Schema uses unsupported type (e.g., `tuple`, `set`) | Use only JSON-compatible types: `string`, `number`, `integer`, `boolean`, `array`, `object` |
| Model calls function with wrong parameter types | Schema `type` does not match description | Add `enum` constraints, tighten `description` field, add `required` field list |
| Tool returns error but model retries infinitely | No retry limit configured | Set `tool_config` with `function_calling_config.mode = "AUTO"` and handle errors in system prompt |

## Cost & Billing Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Unexpected high bill from Vertex AI | Pro model used for high-volume, low-complexity tasks | Switch to `gemini-2.0-flash` (10-20x cheaper); reserve pro for complex reasoning |
| `BILLING_DISABLED: This project has billing disabled` | Billing not linked to GCP project | Link billing account: GCP Console > Billing > Link a billing account |
| Token usage spike after RAG integration | Large retrieved context inflating input tokens | Reduce `top_k` results (3-5 chunks), set `max_output_tokens`, truncate long chunks |
| Agent Engine idle charges | Deployed agent incurring minimum instance costs | Set `min_replica_count=0` for auto-scale-to-zero, or undeploy unused agents |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
