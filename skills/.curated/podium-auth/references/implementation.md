# Implementation Reference — podium-auth

Language-portability layer plus secret-store wiring plus the operator rotation runbook.

## Node.js / TypeScript port

The Python `PodiumAuth` class translates to TypeScript with two changes: `asyncio.Lock` becomes a single-flight promise, and atomic file writes go through `fs.rename` after `fs.writeFile` to a temp path.

```typescript
import { promises as fs } from "fs";
import * as path from "path";

interface Cached { value: string; expiresAt: number; }

interface PodiumAuthConfig {
  clientId: string;
  clientSecret: string;
  refreshToken: string;
  refreshTokenFile: string;
}

export class PodiumAuth {
  private cached: Cached | null = null;
  private inflight: Promise<string> | null = null;
  private cfg: PodiumAuthConfig;

  constructor(cfg: PodiumAuthConfig) { this.cfg = cfg; }

  async getToken(): Promise<string> {
    if (this.cached && Date.now() < this.cached.expiresAt - 600_000) {
      return this.cached.value;
    }
    if (this.inflight) return this.inflight;

    this.inflight = (async () => {
      try { return await this.refresh(); }
      finally { this.inflight = null; }
    })();
    return this.inflight;
  }

  private async refresh(): Promise<string> {
    const res = await fetch("https://accounts.podium.com/oauth/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "refresh_token",
        refresh_token: this.cfg.refreshToken,
        client_id: this.cfg.clientId,
        client_secret: this.cfg.clientSecret,
      }),
    });
    if (!res.ok) throw new Error(`Podium auth ${res.status}: ${await res.text()}`);
    const body = await res.json();

    this.validateScopes(body);

    if (body.refresh_token) {
      await this.persistRefreshToken(body.refresh_token);
      this.cfg.refreshToken = body.refresh_token;
    }

    this.cached = {
      value: body.access_token,
      expiresAt: Date.now() + body.expires_in * 1000,
    };
    return body.access_token;
  }

  private validateScopes(body: any): void {
    const REQUIRED = ["conversations.read", "conversations.write", "contacts.read",
                      "contacts.write", "reviews.read", "reviews.write"];
    const granted = new Set(String(body.scope || "").split(" "));
    const missing = REQUIRED.filter(s => !granted.has(s));
    if (missing.length) throw new Error(`Scope drift: missing ${missing.join(",")}`);
  }

  private async persistRefreshToken(newToken: string): Promise<void> {
    const dir = path.dirname(this.cfg.refreshTokenFile);
    const tmp = path.join(dir, `.podium_refresh.${process.pid}.${Date.now()}`);
    await fs.writeFile(tmp, JSON.stringify({
      refresh_token: newToken,
      last_used_at: Date.now() / 1000,
    }), { mode: 0o600 });
    await fs.rename(tmp, this.cfg.refreshTokenFile);
  }
}
```

## Secret-store integrations

### AWS Secrets Manager

```python
import boto3
client = boto3.client("secretsmanager")

def load_refresh_token() -> dict:
    r = client.get_secret_value(SecretId="podium/refresh-token")
    return json.loads(r["SecretString"])

def persist_refresh_token(new: str) -> None:
    # AWS Secrets Manager versions every update; the previous version is recoverable for 30d.
    client.put_secret_value(
        SecretId="podium/refresh-token",
        SecretString=json.dumps({"refresh_token": new, "last_used_at": time.time()}),
    )
```

IAM policy required: `secretsmanager:GetSecretValue`, `secretsmanager:PutSecretValue` on the specific secret ARN. **Do not** grant `*` on `secretsmanager:*`.

### GCP Secret Manager

```python
from google.cloud import secretmanager
sm = secretmanager.SecretManagerServiceClient()
NAME = "projects/{project}/secrets/podium-refresh-token"

def load_refresh_token() -> dict:
    r = sm.access_secret_version(name=f"{NAME}/versions/latest")
    return json.loads(r.payload.data.decode("utf-8"))

def persist_refresh_token(new: str) -> None:
    sm.add_secret_version(
        parent=NAME,
        payload={"data": json.dumps({"refresh_token": new, "last_used_at": time.time()}).encode()},
    )
```

GCP role required: `roles/secretmanager.secretAccessor` + `roles/secretmanager.secretVersionAdder` on the specific secret.

### SOPS + age (Intent Solutions standard)

```python
import subprocess, json, tempfile, os

SOPS_FILE = "secrets/podium.sops.yaml"

def load_refresh_token() -> dict:
    out = subprocess.run(["sops", "-d", SOPS_FILE], check=True, capture_output=True, text=True)
    import yaml
    data = yaml.safe_load(out.stdout)
    return data["podium"]

def persist_refresh_token(new: str) -> None:
    # SOPS can edit-in-place with --set:
    subprocess.run([
        "sops", "--set", f'["podium"]["refresh_token"] "{new}"', SOPS_FILE,
    ], check=True)
    subprocess.run([
        "sops", "--set", f'["podium"]["last_used_at"] {int(time.time())}', SOPS_FILE,
    ], check=True)
```

Age public key must be listed in the repo's `.sops.yaml` under `creation_rules` so encrypted files are decryptable by anyone with the corresponding age private key (typically `$HOME/.config/sops/age/keys.txt`).

## Rotation runbook (committed to repo, not a wiki link)

The committed location is `docs/runbooks/podium-credential-rotation.md`. The script `scripts/rotate_secret.py` implements steps 4–7 of this runbook.

1. **Trigger**: leaked client_secret, scheduled quarterly rotation, departure of an engineer with secret access.
2. **Generate new secret** in the Podium developer console. Do NOT revoke the old yet.
3. **Deploy the new secret** to the secret store under a versioned key. Both old and new exist simultaneously.
4. **Signal cache reload** — SIGHUP, env var change watcher, or rolling restart.
5. **Verify with health check** — `verify_creds.py` against the new credential. Must pass `N` consecutive `/v4/me` calls (default 3).
6. **Drain overlap window** — sleep `overlap_window_seconds` (default 900s = 15min) to let in-flight requests on the old secret complete.
7. **Revoke old secret** via `POST /oauth/revoke` ONLY after steps 5–6 pass.
8. **Audit** — `git log -p` over the leak window if this rotation was triggered by a leak; assess data access scope and notify customer if required by your contract.

## Library packaging notes

This skill ships the library inline in `SKILL.md` and `references/examples.md` rather than as a separate pip package. The rationale: the library is ~150 lines, every Podium integration needs a custom secret-store binding, and an extracted package would require versioning that adds maintenance overhead without enabling reuse. If the library grows past ~500 lines or three concrete callers depend on identical behavior, promote it to `@intentsolutions/podium-auth` on npm or `intent-podium-auth` on PyPI.

## Testing matrix (what `tests/` should cover when this skill is integrated)

| Test | Type | What it proves |
|---|---|---|
| `test_refresh_at_80_percent_ttl` | unit | `get_token()` does not refresh until TTL fraction passes |
| `test_single_flight_lock` | unit | 100 concurrent `get_token()` produces exactly 1 refresh call |
| `test_atomic_persistence` | unit | SIGKILL between write and rename leaves the old file intact |
| `test_scope_drift_raises` | unit | Missing scope in response raises `PodiumScopeError` with explicit list |
| `test_decay_thresholds` | unit | warn @ 60d, page @ 75d, raise @ 85d (with mocked `time.time`) |
| `test_unknown_org_raises` | unit | `PodiumOrgRouter.get("nonexistent")` raises `KeyError` |
| `test_rotation_health_check_fail_does_not_revoke` | integration | `rotate_secret.py` aborts revoke on health-check failure |
| `test_credential_leak_grep` | static | repo grep returns clean against the leak-detection regex |
