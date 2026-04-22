# Secret Manager Integration

Three backend patterns — GCP Secret Manager, AWS Secrets Manager, HashiCorp
Vault. All three pull secrets into the `Settings` object only. None of them
write to `os.environ`. That is the P37 fix.

## Shared loader contract

```python
def build_settings() -> Settings:
    env = os.environ.get("LANGCHAIN_ENV")
    if env == "prod":
        values = pull_from_secret_manager()   # backend-specific
        return Settings(**values)
    # dev / staging: see SKILL.md Step 2
```

The prod path is the only one that touches a secret backend. `Settings(**values)`
populates the fields; `values` is thrown away when the function returns.
Nothing writes `os.environ[k] = v`.

## GCP Secret Manager

```python
from google.cloud import secretmanager

def pull_from_secret_manager() -> dict[str, str]:
    client = secretmanager.SecretManagerServiceClient()
    project = os.environ["GCP_PROJECT_ID"]

    secret_names = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "LANGSMITH_API_KEY",
    ]
    out: dict[str, str] = {}
    for name in secret_names:
        resource = f"projects/{project}/secrets/{name}/versions/latest"
        response = client.access_secret_version(request={"name": resource})
        out[name] = response.payload.data.decode("utf-8")

    # Non-secret passthrough (model id, prompt hash, endpoint URLs)
    for key in [
        "LANGCHAIN_ENV", "LANGCHAIN_MODEL_ID", "LANGCHAIN_PROMPT_COMMIT",
        "LANGCHAIN_VECTOR_INDEX", "LANGCHAIN_CHECKPOINTER_URL",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
    ]:
        if key in os.environ:
            out[key] = os.environ[key]
    return out
```

**Auth:** Cloud Run and GKE workloads use the pod's service account
automatically (workload identity). Grant
`roles/secretmanager.secretAccessor` on each secret to the SA — not on the
project. Audit trail lives in Cloud Audit Logs (`secretmanager.secrets.access`).

**Rotation:** Post a new version to the secret. The app re-reads at next
restart because `pull_from_secret_manager` fetches `versions/latest`. For
zero-downtime rotation, pin a specific version in `LANGCHAIN_SECRET_VERSION`
and roll it via deploy — makes the rotation atomic with the deploy.

**Cost:** Secret Manager charges per access after the first 10k/month free.
At one access per pod per start, this is effectively free.

## AWS Secrets Manager

```python
import boto3, json

def pull_from_secret_manager() -> dict[str, str]:
    client = boto3.client("secretsmanager", region_name=os.environ["AWS_REGION"])
    secret_id = os.environ["LANGCHAIN_SECRET_ID"]  # e.g. "prod/langchain/keys"
    response = client.get_secret_value(SecretId=secret_id)

    # Convention: one JSON blob containing all keys
    payload: dict[str, str] = json.loads(response["SecretString"])

    # Non-secret passthrough
    for key in [
        "LANGCHAIN_ENV", "LANGCHAIN_MODEL_ID", "LANGCHAIN_PROMPT_COMMIT",
        "LANGCHAIN_VECTOR_INDEX", "LANGCHAIN_CHECKPOINTER_URL",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
    ]:
        if key in os.environ:
            payload[key] = os.environ[key]
    return payload
```

**Auth:** IAM role attached to the ECS task / EKS pod. Policy grants
`secretsmanager:GetSecretValue` on the specific ARN.

**Layout:** One JSON blob per env (`prod/langchain/keys`, `staging/langchain/keys`)
keeps the API calls low and the rotation story simple. Per-secret layout
(`prod/langchain/anthropic-key`, `prod/langchain/openai-key`) is more
IAM-granular but triples the startup latency. Most services prefer the blob.

**Rotation:** Use Secrets Manager's rotation Lambda for automatic rotation
against Anthropic / OpenAI (they do not support it natively, so rotation is
a human-in-the-loop action — the Lambda just schedules reminders).

## HashiCorp Vault

```python
import hvac

def pull_from_secret_manager() -> dict[str, str]:
    client = hvac.Client(url=os.environ["VAULT_ADDR"])
    # AppRole auth: role_id + secret_id from k8s-mounted files
    client.auth.approle.login(
        role_id=Path("/vault/role_id").read_text().strip(),
        secret_id=Path("/vault/secret_id").read_text().strip(),
    )

    response = client.secrets.kv.v2.read_secret_version(
        path=f"{os.environ['LANGCHAIN_ENV']}/langchain",
        mount_point="kv",
    )
    payload: dict[str, str] = response["data"]["data"]

    # Non-secret passthrough (same as GCP/AWS)
    for key in ["LANGCHAIN_ENV", "LANGCHAIN_MODEL_ID", ...]:
        if key in os.environ:
            payload[key] = os.environ[key]
    return payload
```

**Auth:** AppRole is the default for workloads. Kubernetes auth method works
too — mount a service-account token and let Vault verify it via the k8s API.

**Leases:** The KV v2 secrets engine has no lease; values are static. For
short-lived credentials (database users, cloud IAM), use dynamic secrets
engines — out of scope for LangChain key material.

## What NOT to do

| Anti-pattern | Why it is broken |
|---|---|
| `os.environ[k] = v` after pulling from Secret Manager | Re-introduces P37 — `docker exec env` can read it back |
| Writing the secret to a tmpfs file and reading it on each request | Extra IO per request; file still visible to sidecars; no value over SecretStr |
| Storing the plaintext in a class attribute (`Settings.anthropic_api_key: str`) | Loses `SecretStr` masking — `repr(settings)` leaks it |
| Hard-coding the secret resource path | Makes rotation a code change instead of a config change |
| Pulling on every request | Rate limits the Secret Manager backend; adds 50-200ms to every call; pull once at startup |
| Caching the dict globally with the plaintext values | Defeats `SecretStr` — keep plaintext only inside the `Settings` field |

## Observability note

The Secret Manager access is worth logging at INFO level with the resource
name (not the value). One line at startup is enough:

```python
logger.info("pulled %d secrets from %s", len(out), "gcp_secret_manager")
```

If the log line never appears, something is wrong with the loader branch —
the service started in dev or staging mode when ops thought it was prod.
Cheap signal, catches a real class of misconfiguration.
