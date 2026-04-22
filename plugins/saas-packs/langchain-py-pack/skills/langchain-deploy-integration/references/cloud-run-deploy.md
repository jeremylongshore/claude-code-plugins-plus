# Cloud Run Deploy Reference

The complete flag set for a production LangChain service on Cloud Run, with
rationale for each flag and the failure mode it prevents.

## Baseline deploy command

```bash
gcloud run deploy langchain-api \
  --source=. \
  --region=us-central1 \
  --min-instances=1 \
  --max-instances=20 \
  --cpu=2 --memory=2Gi \
  --cpu-boost \
  --no-cpu-throttling \
  --timeout=3600 \
  --concurrency=80 \
  --execution-environment=gen2 \
  --port=8080 \
  --ingress=all \
  --allow-unauthenticated \
  --service-account=langchain-api@PROJECT.iam.gserviceaccount.com \
  --set-env-vars=LANGCHAIN_TRACING_V2=true \
  --set-secrets=ANTHROPIC_API_KEY=anthropic-key:latest,OPENAI_API_KEY=openai-key:latest
```

## Flag-by-flag rationale

| Flag | Value | Why it matters |
|------|-------|----------------|
| `--min-instances` | `1` | Kills cold-start p99 (P36). One always-warm replica costs ~$15/mo on 2 vCPU / 2 GiB and dominates p99 improvement over any other tuning. |
| `--max-instances` | `20` | Hard ceiling on autoscale. Set based on provider rate limits — each instance can hit the Anthropic tier-1 rate cap (50 req/min) independently. |
| `--cpu` | `2` | Import time scales with CPU. `cpu=1` doubles cold start on LangChain imports. |
| `--memory` | `2Gi` | Embedding models (even small ones) + tokenizer caches + request buffers. 1Gi OOMs on 10 concurrent embedding calls. |
| `--cpu-boost` | flag | 2x CPU during first 10 seconds. Halves import time on cold start. Free when using `gen2`. |
| `--no-cpu-throttling` | flag | CPU-always-allocated billing. Required so `astream` keeps executing between HTTP keepalive pings; without it, a long LangGraph run stalls at tool boundaries. |
| `--timeout` | `3600` | Max request duration. Cloud Run max is 3600s (1h); use full value for agent runs. Defaults to 300s — too low for real agents. |
| `--concurrency` | `80` | Per-instance concurrent request ceiling. LangChain is mostly I/O-bound (LLM calls), so 80 is typical. Drop to 10 if embedding large docs in-process. |
| `--execution-environment` | `gen2` | Required for `--cpu-boost`. Slightly slower cold start than gen1 but supports mounts and network filesystems. |
| `--ingress` | `all` | Public. Use `internal-and-cloud-load-balancing` for private APIs; requires a load balancer. |
| `--service-account` | dedicated SA | Least-privilege. The SA needs `roles/secretmanager.secretAccessor` on each secret and `roles/cloudtrace.agent` for tracing. |

## Secret mounts: env vs file

Two ways to consume Secret Manager secrets:

**Environment variables** (simplest, recommended for API keys):
```bash
--set-secrets=ANTHROPIC_API_KEY=anthropic-key:latest
```
Secret is read once at container start; not hot-reloaded on rotation.

**Mounted as files** (required for multi-line secrets like certs or JSON creds):
```bash
--set-secrets=/var/secrets/gcp-credentials=gcp-sa-key:latest
```
File appears at the mount path; set `GOOGLE_APPLICATION_CREDENTIALS=/var/secrets/gcp-credentials`.

Rotation note: Cloud Run does not auto-redeploy on Secret Manager version
changes. After `gcloud secrets versions add anthropic-key`, you must redeploy
the service to pick up the new version. The `:latest` alias is evaluated at
deploy time, not at request time.

## VPC egress for private Postgres / Redis

LangChain apps often need a private DB (pgvector, Redis cache). Cloud Run
defaults to public egress only; route internal traffic via a VPC connector.

```bash
gcloud compute networks vpc-access connectors create lc-egress \
  --region=us-central1 --network=default --range=10.8.0.0/28

gcloud run deploy langchain-api \
  --vpc-connector=projects/PROJECT/locations/us-central1/connectors/lc-egress \
  --vpc-egress=private-ranges-only   # only 10.x / 172.16.x / 192.168.x go via VPC
  # alternative: --vpc-egress=all-traffic   (everything through VPC, slower)
```

Use `private-ranges-only` unless you need all egress going through a NAT for
IP allowlisting on external APIs — that path adds 20-40ms per call.

## Revision traffic splitting

Canary deploys without full cutover:

```bash
# Deploy new revision, send 0% traffic
gcloud run deploy langchain-api --source=. --no-traffic --tag=canary

# Route 10% of traffic to canary
gcloud run services update-traffic langchain-api \
  --to-revisions=LATEST=90,canary=10

# Promote canary
gcloud run services update-traffic langchain-api --to-latest
```

## Health checks and readiness

Cloud Run pings `/` by default for startup. LangChain apps should expose a
cheap `/healthz` that does **not** hit the model:

```python
@app.get("/healthz")
async def healthz():
    return {"status": "ok", "model": settings.model_id}
```

Configure with `--startup-probe=httpGet=/healthz,initialDelaySeconds=0,periodSeconds=1,timeoutSeconds=1,failureThreshold=20`.
Do not probe model invocation — a slow model response will fail the probe and
retart the instance.

## Cost model

Per-month baseline for one always-warm replica, 2 vCPU, 2 GiB, us-central1
(2026 pricing):

| Component | Cost |
|-----------|------|
| Always-allocated CPU (2 vCPU × 720 hrs) | ~$33 |
| Always-allocated memory (2 GiB × 720 hrs) | ~$7 |
| Requests (1M) | ~$0.40 |
| Egress (10 GB) | ~$1.20 |
| **Total baseline** | **~$42/mo** |

Scaling to `--min-instances=0` drops this to ~$2/mo but you pay with 5-15s
p99 cold start on the first request after idle. For production, pay the $40.
