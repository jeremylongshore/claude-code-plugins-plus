# Error Handling Reference

## Authentication & Authorization

| Error | Cause | Solution |
|-------|-------|----------|
| `UNAUTHENTICATED: Request had invalid authentication credentials` | ADC not configured or expired token | Run `gcloud auth application-default login`; verify `GOOGLE_APPLICATION_CREDENTIALS` env var points to a valid service account key |
| `PERMISSION_DENIED: caller does not have permission` | Service account missing required IAM roles | Grant `roles/aiplatform.user` for Vertex AI, `roles/run.developer` for Cloud Run; use `gcloud projects get-iam-policy` to audit bindings |
| `PERMISSION_DENIED: VPC Service Controls` | Request originates outside the VPC-SC perimeter | Add the caller's IP or access level to the perimeter; check `gcloud access-context-manager perimeters describe` |

## API & Quota

| Error | Cause | Solution |
|-------|-------|----------|
| `API [aiplatform.googleapis.com] not enabled` | Vertex AI API disabled on the project | Run `gcloud services enable aiplatform.googleapis.com` |
| `RESOURCE_EXHAUSTED: quota exceeded` | Rate limit or daily token quota hit | Request quota increase via Cloud Console; implement exponential backoff with jitter; consider batching requests |
| `429 Too Many Requests` | Gemini API rate-limited | Back off and retry; use `google-cloud-aiplatform` client library (auto-retries); switch lower-priority tasks to Gemini Flash |

## Model & Region

| Error | Cause | Solution |
|-------|-------|----------|
| `Model not found: gemini-2.5-pro` | Model not available in the specified region | Use `us-central1` or `europe-west4` where Gemini 2.5 models are generally available; check [regional availability docs](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/locations) |
| `INVALID_ARGUMENT: unsupported model` | Using deprecated model name or wrong model ID | Verify model ID format: `gemini-2.5-pro`, `gemini-2.5-flash`; avoid legacy names like `gemini-1.0-pro` |
| `SAFETY_BLOCK` in response | Model safety filters triggered | Review prompt for policy violations; adjust safety settings if appropriate; add input sanitization layer |

## Dependency & Build

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'google.adk'` | ADK package not installed | Run `pip install google-adk`; verify virtual environment is activated |
| `Cannot find module '@genkit-ai/googleai'` | Genkit Google AI plugin not installed | Run `npm install @genkit-ai/googleai`; check `package.json` has correct version |
| `Version conflict` between AI SDK packages | Incompatible pinned versions | Pin all `@genkit-ai/*` packages to the same minor version; use lockfile (`package-lock.json` or `pnpm-lock.yaml`) |
| `ImportError: cannot import name 'Agent' from 'google.adk'` | Wrong import path for ADK Agent class | Use `from google.adk.agents import Agent` (not `from google.adk import Agent`) |

## Deployment

| Error | Cause | Solution |
|-------|-------|----------|
| `Cloud Run: Container failed to start` | Missing env vars or port misconfiguration | Ensure `PORT=8080` is set; verify `GOOGLE_GENAI_API_KEY` or credentials are passed via `--set-secrets` |
| `Cloud Run: Memory limit exceeded` | Container OOM during model inference | Increase memory with `--memory 1Gi` or higher; reduce batch sizes; use streaming responses |
| `Terraform: Error creating Agent` | Terraform provider version incompatible | Upgrade `hashicorp/google` provider to `~> 5.0`; run `terraform init -upgrade` |
| `adk deploy: timeout` | Large agent package or slow network | Increase timeout; verify `.gcloudignore` excludes `node_modules`, `venv`, and test data |

## Runtime

| Error | Cause | Solution |
|-------|-------|----------|
| `Timeout: request took longer than 300s` | Complex prompt or large context window | Reduce context size; use Gemini Flash for simple tasks; implement streaming for long generations |
| `INVALID_ARGUMENT: request payload too large` | Input exceeds model context limit | Chunk large documents; summarize before sending; use RAG to retrieve only relevant sections |
| `JSONDecodeError` when parsing structured output | Model returned non-JSON despite `response_mime_type: application/json` | Add explicit JSON schema in prompt; retry with lower temperature; validate output before parsing |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
