# Implementation Reference — podium-multi-location-router

Language-portability layer, SQLite audit-log query layer, and operator deployment patterns.

## Node.js / TypeScript port

The Python `LocationRouter` translates to TypeScript with two changes: `asyncio.Lock` becomes a per-uid single-flight promise map, and atomic credential writes go through `fs.rename` after `fs.writeFile` to a temp path.

```typescript
import { promises as fs } from "fs";
import * as path from "path";
import { PodiumAuth } from "@intentsolutions/podium-auth";
import { TokenBucket } from "@intentsolutions/podium-rate-limit";

interface LocationCredential {
  locationUid: string;
  orgSlug: string;
  clientId: string;
  clientSecret: string;
  refreshTokenFile: string;
  verifiedAt: number;   // unix ms; 0 = never
}

interface AuditRecord {
  ts: number;
  locationUid: string;
  orgSlug: string;
  endpoint: string;
  method: string;
  status: number;
  requestId: string;
  latencyMs: number;
}

export class UnknownLocationError extends Error {}
export class LocationNotInScopeError extends Error {}

export class LocationRouter {
  private creds = new Map<string, LocationCredential>();
  private auths = new Map<string, PodiumAuth>();
  private buckets = new Map<string, TokenBucket>();
  private verifyInflight = new Map<string, Promise<void>>();

  constructor(private auditLogPath: string) {}

  static async fromCredentialsFile(path: string, auditLogPath: string): Promise<LocationRouter> {
    const router = new LocationRouter(auditLogPath);
    const raw = JSON.parse(await fs.readFile(path, "utf-8"));
    for (const [uid, c] of Object.entries(raw as Record<string, any>)) {
      router.creds.set(uid, { locationUid: uid, orgSlug: c.org_slug,
        clientId: c.client_id, clientSecret: c.client_secret,
        refreshTokenFile: c.refresh_token_file, verifiedAt: 0 });
    }
    return router;
  }

  getClient(locationUid: string): PodiumLocationClient {
    const cred = this.creds.get(locationUid);
    if (!cred) throw new UnknownLocationError(`No credentials for ${locationUid}`);
    if (!this.auths.has(locationUid)) {
      this.auths.set(locationUid, new PodiumAuth({
        clientId: cred.clientId, clientSecret: cred.clientSecret,
        refreshTokenFile: cred.refreshTokenFile,
      }));
      this.buckets.set(locationUid, new TokenBucket({ capacity: 30, refillPerSecond: 5 }));
    }
    return new PodiumLocationClient(locationUid, this);
  }

  async ensureLocationVerified(locationUid: string): Promise<void> {
    const cred = this.creds.get(locationUid)!;
    const TTL_MS = 3600_000;
    if (Date.now() - cred.verifiedAt < TTL_MS) return;
    if (this.verifyInflight.has(locationUid)) return this.verifyInflight.get(locationUid)!;

    const p = (async () => {
      const auth = this.auths.get(locationUid)!;
      const token = await auth.getToken();
      const res = await fetch("https://api.podium.com/v4/locations", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Verification failed: ${res.status}`);
      const body = await res.json() as { locations: { uid: string }[] };
      const ids = new Set(body.locations.map(l => l.uid));
      if (!ids.has(locationUid)) {
        throw new LocationNotInScopeError(
          `${locationUid} not in scope; token sees ${ids.size} locations`);
      }
      cred.verifiedAt = Date.now();
    })().finally(() => this.verifyInflight.delete(locationUid));

    this.verifyInflight.set(locationUid, p);
    return p;
  }

  async emitAudit(record: AuditRecord): Promise<void> {
    await fs.mkdir(path.dirname(this.auditLogPath), { recursive: true });
    await fs.appendFile(this.auditLogPath, JSON.stringify(record) + "\n");
  }

  bucketFor(uid: string): TokenBucket { return this.buckets.get(uid)!; }
  authFor(uid: string): PodiumAuth { return this.auths.get(uid)!; }
  credFor(uid: string): LocationCredential { return this.creds.get(uid)!; }
}
```

The TypeScript port is structurally identical to the Python one. Choose whichever matches the rest of the stack — there is no performance reason to prefer one.

## SQLite audit-log query layer (for large logs)

The default JSONL audit log handles thousands of writes per second on local disk and is grep-friendly. For agencies generating > 1 million audit lines per day, query latency on the raw JSONL gets uncomfortable. The recommended approach: keep the JSONL as the source of truth (append-only, simple to back up, immutable) and periodically index it into SQLite for query speed.

```python
import json, sqlite3
from pathlib import Path

def index_audit_log(jsonl_path: Path, db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit (
            ts REAL NOT NULL,
            location_uid TEXT NOT NULL,
            org_slug TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            method TEXT NOT NULL,
            status INTEGER NOT NULL,
            request_id TEXT NOT NULL,
            latency_ms REAL NOT NULL
        );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS ix_audit_uid_ts ON audit(location_uid, ts);")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_audit_request_id ON audit(request_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_audit_ts ON audit(ts);")

    # Idempotent — re-runs only add new lines beyond the last indexed ts.
    last_ts = conn.execute("SELECT COALESCE(MAX(ts), 0) FROM audit;").fetchone()[0]

    with open(jsonl_path) as f:
        rows = []
        for line in f:
            r = json.loads(line)
            if r["ts"] > last_ts:
                rows.append((r["ts"], r["location_uid"], r["org_slug"], r["endpoint"],
                             r["method"], r["status"], r["request_id"], r["latency_ms"]))
        conn.executemany("INSERT INTO audit VALUES (?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()
```

Query examples:

```sql
-- All writes to a specific location in a date range
SELECT * FROM audit
WHERE location_uid = '{your-location-uid}'
  AND ts BETWEEN strftime('%s', '2026-05-01') AND strftime('%s', '2026-05-31')
ORDER BY ts;

-- Per-location call volume by day
SELECT location_uid, date(ts, 'unixepoch') AS day, COUNT(*) AS n
FROM audit
WHERE ts > strftime('%s', '2026-05-01')
GROUP BY location_uid, day
ORDER BY day, n DESC;

-- All 5xx errors in the last 24h
SELECT ts, location_uid, endpoint, method, status, request_id
FROM audit
WHERE status >= 500
  AND ts > strftime('%s', 'now', '-1 day')
ORDER BY ts DESC;
```

## Credentials-map secret-store integrations

### AWS Secrets Manager

```python
import boto3, json
sm = boto3.client("secretsmanager")

def load_credentials_map() -> dict:
    r = sm.get_secret_value(SecretId="podium/location-credentials-map")
    return json.loads(r["SecretString"])

def persist_credentials_map(new_map: dict) -> None:
    sm.put_secret_value(
        SecretId="podium/location-credentials-map",
        SecretString=json.dumps(new_map),
    )
```

IAM policy: `secretsmanager:GetSecretValue` + `secretsmanager:PutSecretValue` on the specific secret ARN. AWS Secrets Manager versions every update — onboarding history is recoverable for 30 days.

### GCP Secret Manager

```python
from google.cloud import secretmanager
sm = secretmanager.SecretManagerServiceClient()
NAME = "projects/{project}/secrets/podium-location-credentials-map"

def load_credentials_map() -> dict:
    r = sm.access_secret_version(name=f"{NAME}/versions/latest")
    return json.loads(r.payload.data.decode("utf-8"))

def persist_credentials_map(new_map: dict) -> None:
    sm.add_secret_version(parent=NAME, payload={"data": json.dumps(new_map).encode()})
```

GCP role: `roles/secretmanager.secretAccessor` + `roles/secretmanager.secretVersionAdder`.

### SOPS + age (Intent Solutions standard)

```python
import subprocess, yaml, json

SOPS_FILE = "secrets/podium-locations.sops.yaml"

def load_credentials_map() -> dict:
    out = subprocess.run(["sops", "-d", SOPS_FILE], check=True, capture_output=True, text=True)
    data = yaml.safe_load(out.stdout)
    return data["locations"]
```

For writes, regenerate the encrypted file via `sops encrypt` rather than `sops --set` because the credential map is nested. Easier to reason about as an opaque blob.

## Audit-log retention and rotation

The library never deletes audit lines — retention is operator-controlled. Recommended setup:

```
# /etc/logrotate.d/podium-multi-location-router
/var/log/podium/podium-router.jsonl {
    daily
    rotate 365
    compress
    delaycompress
    notifempty
    missingok
    create 0640 podium podium
    postrotate
        # Re-index the new active file into SQLite if the index layer is in use.
        /usr/local/bin/python3 /opt/podium-router/index_audit_log.py
    endscript
}
```

365 daily rotations = ~1 year of audit lines retained. Adjust to match the compliance contract for the specific deployment (GDPR + CCPA defaults typically 6+ months).

## Library packaging notes

This skill ships the library inline in `scripts/location_router.py` rather than as a separate pip package. Rationale: the library is ~400 lines, every Podium integration's credentials-map secret store binding is custom, and an extracted package would require versioning that adds maintenance overhead. If the library grows past ~800 lines or three concrete callers depend on identical behavior, promote it to `@intentsolutions/podium-multi-location-router` on npm or `intent-podium-multi-location-router` on PyPI.

## Testing matrix (what `tests/` should cover when this skill is integrated)

| Test | Type | What it proves |
|---|---|---|
| `test_unknown_uid_raises` | unit | `router.get_client("nonexistent")` raises `UnknownLocationError` immediately |
| `test_location_not_in_scope_raises` | unit | Pre-flight fails when `GET /v4/locations` does not contain the uid |
| `test_verification_ttl_cache_hit` | unit | Second call within TTL does NOT trigger a verify HTTP call |
| `test_verification_single_flight` | unit | 100 concurrent `get_client()` calls produce exactly 1 verify HTTP call |
| `test_audit_log_schema` | unit | Every audit line has all 8 required fields |
| `test_audit_log_no_secrets` | unit | Audit lines never contain token-like substrings (regex match against known patterns) |
| `test_bulk_onboarding_partial_failure_rollback` | unit | Failed location is rolled back; others remain onboarded |
| `test_bulk_onboarding_idempotent` | unit | Re-running with same input → all locations status=skipped_existing |
| `test_per_location_bucket_isolation` | unit | Draining one location's bucket does not affect another's |
| `test_credential_persistence_atomic` | unit | SIGKILL mid-write leaves the old credentials file intact |
| `test_audit_query_by_uid_and_daterange` | integration | `audit_log_query.py` returns exactly the expected lines |
| `test_wrong_org_credential_detected` | integration | A wrong-org pairing fails verification at onboarding time |
