# Secrets Lifecycle — Dev to Prod

A secret that reaches `os.environ` can be read by anyone with `docker exec`,
`kubectl exec`, or a crashed-process dump (P37). This reference walks the
full secret lifecycle: where it lives per environment, how it's loaded into
the app, and how `pydantic.SecretStr` keeps it from leaking through logs.

## Environment matrix

| Environment | Secret source | Loaded via | Exported to `os.environ`? |
|-------------|---------------|------------|---------------------------|
| Local dev | `.env` (gitignored) | `python-dotenv` | Yes (accepted risk — no PII, dev keys only) |
| CI | GitHub secrets / CI vault | Action injects env var | Yes (job-scoped, rotated on each run) |
| Staging | Secret Manager | In-process fetch → `SecretStr` | **No** |
| Production | Secret Manager + scheduled rotation | In-process fetch → `SecretStr` | **No** |

The critical rule: **in staging and production, secrets never touch
`os.environ`**. They are fetched into memory and wrapped immediately.

## `.env` in dev — the rules that keep it safe

1. `.env` in `.gitignore`, always. Verify with `git check-ignore .env`.
2. `.env.example` committed with placeholder values so new devs know which keys are required.
3. Use dev-tier provider keys (separate from prod) — rotate if a dev machine is lost.
4. Never `COPY .env` in a Dockerfile. Use build args or runtime injection.

```python
# dev_config.py — only imported when APP_ENV=dev
from dotenv import load_dotenv
import os

load_dotenv(".env")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
```

## Staging and production — secret manager flow

Three common providers. Pick one per infra.

### GCP Secret Manager

```python
from google.cloud import secretmanager
from pydantic import SecretStr

def fetch_secret(project: str, name: str, version: str = "latest") -> SecretStr:
    client = secretmanager.SecretManagerServiceClient()
    path = f"projects/{project}/secrets/{name}/versions/{version}"
    resp = client.access_secret_version(name=path)
    return SecretStr(resp.payload.data.decode("utf-8"))

anthropic_key = fetch_secret("my-project", "anthropic-api-key")
```

IAM: grant `roles/secretmanager.secretAccessor` to the service account the
app runs as. Do not grant to humans unless they're debugging a specific
incident — use break-glass access logs.

### AWS Secrets Manager

```python
import boto3
from pydantic import SecretStr

def fetch_secret(name: str, region: str = "us-east-1") -> SecretStr:
    client = boto3.client("secretsmanager", region_name=region)
    resp = client.get_secret_value(SecretId=name)
    return SecretStr(resp["SecretString"])

openai_key = fetch_secret("prod/openai-api-key")
```

IAM: least-privilege policy granting `secretsmanager:GetSecretValue` on the
specific secret ARN, not `*`.

### HashiCorp Vault

```python
import hvac
from pydantic import SecretStr

def fetch_secret(path: str, field: str) -> SecretStr:
    client = hvac.Client(url="https://vault.corp.example.com", token=VAULT_TOKEN)
    resp = client.secrets.kv.v2.read_secret_version(path=path)
    return SecretStr(resp["data"]["data"][field])

gemini_key = fetch_secret("langchain-prod", "gemini_api_key")
```

Vault: prefer AppRole or Kubernetes auth over static tokens. Rotate tokens
on every deploy.

## `pydantic.SecretStr` end to end

`SecretStr` exists to defeat accidental `print()` / `repr()` / JSON serialization:

```python
>>> from pydantic import BaseModel, SecretStr
>>> class Settings(BaseModel):
...     api_key: SecretStr
...
>>> s = Settings(api_key=SecretStr("sk-super-secret"))
>>> print(s)
api_key=SecretStr('**********')
>>> s.model_dump_json()
'{"api_key":"**********"}'
>>> s.api_key.get_secret_value()  # explicit opt-in to read
'sk-super-secret'
```

LangChain 1.0 provider integrations accept `SecretStr` directly:

```python
from langchain_anthropic import ChatAnthropic
model = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=settings.api_key,  # SecretStr — no .get_secret_value() needed
)
```

Never `.get_secret_value()` except when passing to a provider that requires
a string, and never log the return value.

## Rotation

| Secret type | Rotation cadence | Method |
|-------------|------------------|--------|
| Provider API key (Anthropic/OpenAI/Gemini) | 90 days | Generate new key → deploy → revoke old |
| Database password | 30 days | Secret Manager auto-rotation where supported |
| Vault token | Per deploy | New token on each pod start |
| Webhook signing secret | 90 days or on compromise | Accept both old + new for grace period |

Rotation implementation: the fetch helper re-reads the secret on each process
start. For long-lived processes, add a scheduled background refresh every
15 minutes so a rotated secret propagates without a redeploy.

## Leakage scenarios and mitigations

| Scenario | Mitigation |
|----------|-----------|
| `docker exec <pod> env` shows `ANTHROPIC_API_KEY=...` (P37) | Don't export to env. Fetch into `SecretStr` in-process only. |
| Crash dump uploaded to Sentry contains the secret | `SecretStr` masks in `repr`; set Sentry's `before_send` to strip any string matching `sk-...` |
| Git history includes `.env` from early commit | `git filter-repo` to rewrite history; rotate every leaked secret |
| CI logs echo secret | Use `::add-mask::` in GitHub Actions, or CI-vault-provided masking |
| `kubectl describe pod` shows env | Use Kubernetes `Secret` resource mounted as file, not env var; read into `SecretStr` |

## What a reviewer will check

- `.env` in `.gitignore`
- No `COPY .env` in Dockerfiles
- Process env in prod pod does not contain API keys (`kubectl exec <pod> env | grep -iE 'key|secret|token'` returns nothing)
- Secret Manager IAM grants least privilege to the service account
- Rotation schedule documented and audit-logged
- Settings classes use `SecretStr`, not `str`, for every credential field
- Sentry / error-tracker has a scrubber for provider key patterns

## Resources

- [Pydantic `SecretStr`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.SecretStr)
- [GCP Secret Manager best practices](https://cloud.google.com/secret-manager/docs/best-practices)
- [AWS Secrets Manager rotation](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html)
- [HashiCorp Vault AppRole auth](https://developer.hashicorp.com/vault/docs/auth/approle)
- Pack pain catalog: P37
