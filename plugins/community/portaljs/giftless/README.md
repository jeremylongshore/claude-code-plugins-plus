# Giftless on Cloudflare R2 — staging deployment

A deployable [Giftless](https://github.com/datopian/giftless) (Datopian's pluggable
Git LFS server) configured to stream LFS objects to a **Cloudflare R2** bucket over
its S3-compatible API, authenticated with **JWT**. This is the LFS endpoint behind
the PortalJS data-scaling epic (po-g9y): large files are tracked by Git LFS, the
bytes land in R2, and only a tiny pointer stays in git.

The S3⇄R2 round-trip was de-risked in spike **po-e24** (119 MB CSV, byte-exact).
This phase swaps the spike's anonymous auth for the bundled JWT provider and
packages everything as deployable artifacts.

## What's here

| File | Purpose |
|------|---------|
| `Dockerfile` | Extends `datopian/giftless:latest`, bakes in the R2 backend + config. |
| `r2storage.py` | 3-line `AmazonS3Storage` subclass that points boto3 at the R2 endpoint (the stock 0.5.0 adapter can't take a custom endpoint — see po-e24). |
| `giftless.yaml` | Config: JWT auth (no anon), `basic` transfer → `R2Storage`, JWT-signed verify callbacks. |
| `docker-compose.yml` | One-command run; reads R2 creds from `.env`, RS256 keypair from `./jwt_private_key` + `./jwt_public_key`. |
| `mint-token.py` | Mint a client JWT for a repo. HS256 (stdlib) or RS256 (`--algorithm RS256`, needs `cryptography`). |
| `r2-cors.json` | CORS policy for the data bucket — browser range fetch (phase 3). |
| `scripts/gen-rs256-keys.sh` | Generate the prod RS256 keypair (`./jwt_private_key` + `./jwt_public_key`). |
| `scripts/gen-key.sh` | DEPRECATED — the legacy HS256 key (`./jwt_key`); superseded by the RS256 keypair. |
| `scripts/smoke-test.sh` | Build → run → JWT-secured LFS round-trip to R2 → assert no-token is rejected. |
| `scripts/set-r2-cors.sh` | Apply `r2-cors.json` to an R2 bucket (via wrangler). |
| `scripts/verify-r2-cors.py` | Prove a browser CORS ranged GET works against R2. |

`jwt_key`, `jwt_private_key`, `jwt_public_key`, and `.env` are gitignored —
**never commit them**.

## Why these choices (from po-e24)

- **Docker image, not `pip install giftless`** — giftless 0.5.0 breaks on modern deps
  (marshmallow 4 dropped `missing=`, Flask 3, …). The image pins a working set.
- **`R2Storage` subclass** — the bundled botocore (1.20.54) is too old to honor
  `AWS_ENDPOINT_URL`, so we rebuild the boto3 clients with `endpoint_url` +
  path-style + SigV4.
- **`basic` transfer (presigned, direct-to-R2)** — sufficient for files < ~5 GB
  (R2 single-PUT limit). `multipart-basic` deferred until individual files exceed that.
- **`--http`, not the image's default uwsgi socket** — so a reverse proxy / LB fronts it.

## Run it locally (against the real R2 prod bucket)

```bash
cd giftless
cp .env.example .env            # fill in R2 creds, or:
                                # set -a && . ~/.config/portaljs/giftless-r2-prod.env && set +a
./scripts/gen-rs256-keys.sh     # writes ./jwt_private_key + ./jwt_public_key
docker compose up --build -d    # serves on http://localhost:8080
```

Verify end-to-end (build, round-trip, teardown):

```bash
./scripts/smoke-test.sh
```

## Authenticating a Git LFS client

Giftless authorizes each request from the `scopes` claim in the JWT. Mint a token
scoped to one repo, then point Git LFS at the server.

**Default issuer — the Arc API (po-g9y.13).** Hosted portals mint tokens from
**arc-api**, which holds the RS256 signer as a Worker secret so the private key never
leaves the server. Any authenticated Arc user (the device-flow `PORTALJS_TOKEN`) can
mint a scoped, short-TTL token; this is what `/portaljs-add-dataset` and
`/portaljs-deploy` use. The endpoint returns a ready-to-use credentialed `lfs_url`:

```bash
# ?actions=read → pull-only; ?ttl=<secs> → tune lifetime (default read,write,verify / 3600s).
curl -fsS -X POST https://api.arc.portaljs.com/v1/repos/my-catalog/lfs-token \
  -H "Authorization: Bearer $PORTALJS_TOKEN"
# → { "token": "...", "scope": "obj:datopian/my-catalog/*:read,write,verify",
#     "expires_in": 3600, "lfs_url": "https://_jwt:<token>@lfs.portaljs.com/datopian/my-catalog" }
```

Unauthenticated callers get `401`; a slug owned by another account gets `409`. The
issuer code is `cloud/api/src/lfs.ts` (route `POST /v1/repos/:slug/lfs-token`); it
mirrors `mint-token.py`'s RS256 claim shape exactly.

**Local/OSS fallback — `mint-token.py`.** Without an Arc account (self-host, CI with
the key on hand), sign the token directly with the issuer's private key:

```bash
# Prod (RS256): sign with the issuer's private key. (HS256 legacy: drop the flags.)
TOKEN=$(python3 mint-token.py --org datopian --repo my-catalog --ttl 3600 \
  --algorithm RS256 --key-file jwt_private_key)
```

The JWT provider accepts the token two ways:

- **HTTP Basic piggyback** (recommended for git-lfs): username `_jwt`, password = token.
  Keep the committed `.lfsconfig` clean and put the credentialed URL in **local**
  config only:

  ```bash
  git config -f .lfsconfig lfs.url https://giftless.example/datopian/my-catalog   # committed, no secret
  git config           lfs.url https://_jwt:$TOKEN@giftless.example/datopian/my-catalog  # local only
  ```

- **Bearer header**: `Authorization: Bearer <token>`.

> **Gotcha:** do **not** use a broad `http.extraHeader = Authorization: …`. git-lfs
> would replay it onto the presigned R2 PUT (R2 → `400`, conflicting auth) and onto
> the verify callback (clobbers Giftless's own verify token). The `_jwt` Basic
> piggyback is scoped by git-lfs to the LFS API host only, which avoids both.

### Pushing objects without a Git remote

A **GitHub (or any git) remote is NOT required to store data.** `lfs.url` alone
determines where the bytes go — git-lfs talks to Giftless over HTTP (the LFS batch
API at `lfs.url`), which is fully independent of any configured git remote. A remote
(GitHub) only shares commits + LFS *pointers* with collaborators; that's orthogonal to
byte storage.

This matters because scaffolded PortalJS portals are **local-only by default**
(`create-portaljs` runs `git init` + an initial commit but adds **no remote**), so a
bare `git push` fails with `No configured push destination`. To push LFS objects to R2
without a remote, add a throwaway local remote just so git-lfs has an object source,
then `git lfs push` — the bytes route to Giftless via `lfs.url` regardless of that
remote's URL (it is never contacted for the transfer):

```bash
git config lfs.url "https://_jwt:$TOKEN@lfs.portaljs.com/datopian/my-catalog"  # local only
git remote add r2-lfs . 2>/dev/null || true          # throwaway; URL is irrelevant
git -c lfs.locksverify=false lfs push r2-lfs "$(git rev-parse --abbrev-ref HEAD)"
```

`git lfs push <remote> <ref>` needs only a remote *name* to enumerate objects from the
branch; with `lfs.url` set, the batch API hits Giftless and the remote's own git URL is
never used. `locksverify` is disabled because Giftless exposes no locking API (the check
is cosmetic). `/portaljs-add-dataset` automates exactly this: it uses a real remote's
`git push` when one exists, and falls back to the throwaway-remote `git lfs push` when
the portal is local-only.

### Scope format

```
obj:{org}/{repo}/{oid}:{actions}      # actions: read,write,verify  (or *)
```

`mint-token.py` grants `obj:<org>/<repo>/*:read,write,verify` (all objects in one
repo). Use `--actions read` for a read-only (pull) token.

## JWT model: production (RS256, single keypair)

**Production (this config): RS256, ONE keypair.** Giftless holds the **public** key
(`public_key_file`) to verify every incoming token — both client tokens and its own
short-lived "verify" callbacks — and the **private** key (`private_key_file`) to sign
those callbacks (`PRE_AUTHORIZED_ACTION_PROVIDER`). The token issuer (the Arc API /
CI) holds the same private key to mint client tokens. Generate it with
`scripts/gen-rs256-keys.sh`; both halves ship as Worker secrets (the container
materializes them — see `cloudflare/container-entrypoint.sh`).

> **Why one keypair, not two.** The bead originally called for a *separate* keypair
> for the verify callbacks. That does not work with stock giftless: its auth chain
> **aborts on the first provider that rejects a token's signature** (it catches
> `Unauthorized` and stops — `giftless/auth/__init__.py`), so two keypairs on one
> auth path can't coexist. A single keypair, whose public key verifies everything,
> is the only config that authenticates both client tokens and verify callbacks.
> **Trade-off:** because the private signer is injected into the container (a Worker
> secret), a Giftless host compromise leaks it — accepted for prod (po-g9y.11).

**Staging legacy (po-g9y.10): HS256, one shared secret** in `jwt_key` — Giftless
used the single symmetric key to both verify and sign. Superseded by the RS256
cutover above; `scripts/gen-key.sh` is kept only for reference.

## Deploying to a live host (infra handoff)

> **Live (po-g9y.10):** this image runs on **Cloudflare Containers**; staging is
> `https://giftless-staging.datopian.workers.dev`. The **production cutover**
> (po-g9y.11 — RS256, `portaljs-giftless` bucket, `lfs.portaljs.com`) is prepared in
> [`cloudflare/`](cloudflare/) but **not yet deployed** (blocked on a prod R2 token +
> DNS). Deploy: `cd cloudflare && ./scripts/deploy.sh`, verify with
> `./scripts/smoke-remote.sh`. Full status + finish-up steps:
> [`cloudflare/README.md`](cloudflare/README.md#go-live-status-po-g9y11).
> The generic checklist below is retained for reference / alternative hosts.

Giftless is a long-running Python/uwsgi container — it does **not** run on
Cloudflare Workers (unlike the Arc workers in `cloud/`). A live
`giftless.staging.portaljs.com` needs, mirroring `cloud/INFRA.md`:

1. **A container host** — Cloudflare Containers, Fly.io, Render, or a small VM.
   Run the image from this `Dockerfile`.
2. **R2** — prod bucket `portaljs-giftless` (account
   `83025b28472d6aa2bf5ae59f3724aa78`); scoped token creds at
   `~/.config/portaljs/giftless-r2-prod.env`.
3. **Secrets on the host** — R2 creds as `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`
   + `R2_ENDPOINT`; the RS256 keypair mounted at `/etc/giftless/jwt_public_key` +
   `/etc/giftless/jwt_private_key` (platform secrets, not the repo).
4. **DNS + TLS** — a hostname pointed at the container, HTTPS terminated (LB or the
   platform's edge). Giftless serves plain HTTP on `:5000` behind it.
5. **R2 bucket CORS** — required for **browser** range fetches in the later
   DuckDB-over-Parquet tier. **Verified** in phase 3 (po-g9y.2) — see below.

Until a host is provisioned, the smoke test stands the server up locally against the
real R2 bucket and proves the full JWT-secured round-trip.

## R2 CORS for browser range fetch (phase 3, po-g9y.2)

The query tier (DuckDB-Wasm over Parquet) has the browser issue cross-origin HTTP
**range** requests straight at R2. That needs CORS on the bucket, exposing the
range-response headers. The policy lives in [`r2-cors.json`](r2-cors.json):
`GET`/`HEAD` from any origin, `range` allowed on the request, and
`Content-Range` / `Accept-Ranges` / `Content-Length` / `ETag` / `Content-Type`
exposed to the page.

```bash
./scripts/set-r2-cors.sh              # apply r2-cors.json to the bucket (uses wrangler)
python3 scripts/verify-r2-cors.py     # prove a real ranged GET + preflight works
```

> **Why wrangler, not the R2 token?** Bucket-level CORS (`PutBucketCors`) is an
> account operation; the object-scoped R2 token Giftless uses gets `AccessDenied`.
> `set-r2-cors.sh` uses wrangler (account-authenticated). The verify script only
> needs the object token — it presigns a GET (exactly what Giftless's `basic`
> transfer hands the browser) and checks the CORS + range response.

**Verified against `portaljs-giftless-staging` (2026-06-21):** OPTIONS preflight →
`204` with `Access-Control-Allow-*`; ranged `GET` → `206 Partial Content`,
`Content-Range: bytes 0-9/200`, `Accept-Ranges: bytes`, `Access-Control-Allow-Origin`
and `Access-Control-Expose-Headers` present. The spike's open question — *does
browser range fetch work against R2?* — is answered: **yes.**

Apply this same policy to any data bucket a deployed portal serves from
(`./scripts/set-r2-cors.sh <bucket>`).
