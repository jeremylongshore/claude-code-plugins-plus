# Giftless on Cloudflare Containers — production host

Runs the [`giftless/`](../) LFS-on-R2 image as a live HTTPS endpoint on **Cloudflare
Containers**, with a thin Worker in front for TLS + routing. Staging stood up in
po-g9y.10 (HS256, `portaljs-giftless-staging`, `workers.dev`); this is the
**production cutover** (po-g9y.11): RS256 auth, the `portaljs-giftless` bucket, and
the `lfs.portaljs.com` custom hostname.

**Prod endpoint:** `https://lfs.portaljs.com`
(also reachable at `https://giftless.<account>.workers.dev`)

> **✅ LIVE (2026-06-27).** Prod Git LFS is deployed and verified end-to-end on
> `lfs.portaljs.com` (worker `giftless`, RS256, `portaljs-giftless` R2 bucket).
> See [Go-live status](#go-live-status-po-g9y11) below. The old `giftless-staging`
> worker is superseded and pending deletion.

```
git-lfs client ──JWT──> Worker (edge TLS) ──> GiftlessContainer (:5000) ──presigned──> R2
                                                       │
                                          bytes go client <──────────────────────> R2 directly
```

The Worker forwards every request to a single warm container; Giftless brokers LFS
metadata and signs presigned R2 URLs. **File bytes never transit the Worker or the
container** — the client PUT/GETs R2 directly — so this is a light, low-bandwidth,
scale-to-zero workload.

## Why Containers (not a Worker)

Giftless is a long-running uwsgi/WSGI Python service; it can't run on the Workers
runtime. Cloudflare Containers run the Docker image as-is, fronted by a Worker for
hostname/TLS/edge. One account, one bill, one creds story with Arc (Workers + R2 are
already in CF account `83025b28472d6aa2bf5ae59f3724aa78`). Decision locked in
po-g9y.10; fallback is Fly.io (same image, the statelessness makes it portable).

## What's here

| File | Purpose |
|------|---------|
| `wrangler.jsonc` | Worker + container config: `[[containers]]` → `../Dockerfile.cloudflare`, DO binding, `v1` migration, `basic` instance, `workers_dev`. |
| `src/index.ts` | `GiftlessContainer` (port 5000, `sleepAfter=10m`, R2/JWT secrets → container env) + the fronting Worker (singleton route). |
| `../Dockerfile.cloudflare` | The CF image: extends `datopian/giftless:latest`, reuses `r2storage.py`+`giftless.yaml` (shared build context `..`), adds the entrypoint. |
| `container-entrypoint.sh` | Materializes `/etc/giftless/jwt_public_key` + `jwt_private_key` from `$GIFTLESS_JWT_PUBLIC_KEY` / `$GIFTLESS_JWT_PRIVATE_KEY` (Containers have no secret-file mounts), then execs uwsgi. |
| `scripts/deploy.sh` | Push the 4 secrets, build the image, deploy the Worker. |
| `scripts/smoke-remote.sh` | Live JWT-secured push/pull round-trip + cold-start probe against the deployed endpoint. |

## Deploy

```bash
cd giftless && ./scripts/gen-rs256-keys.sh  # writes ../giftless/jwt_private_key + jwt_public_key
cd cloudflare && npm install
./scripts/deploy.sh                          # secrets + build + deploy
```

`deploy.sh` reads **prod** R2 creds from `~/.config/portaljs/giftless-r2-prod.env`
(scoped to `portaljs-giftless` — the staging token will `AccessDenied`) and the RS256
keypair from `../jwt_private_key` + `../jwt_public_key`, pushes all four as Worker
secrets (`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `GIFTLESS_JWT_PUBLIC_KEY`,
`GIFTLESS_JWT_PRIVATE_KEY`), then `wrangler deploy` builds the image, pushes it to the
CF registry, and rolls the Worker. **Secrets and the key files are never committed** —
`R2_ENDPOINT`/`R2_REGION` are the only non-secret values (in `[vars]`).

## Verify (live)

```bash
# Pre-DNS: validate the RS256 + prod-R2 config on workers.dev first.
./scripts/smoke-remote.sh https://giftless.<account>.workers.dev
# Post-DNS (route uncommented + deployed):
GIFTLESS_URL=https://lfs.portaljs.com ./scripts/smoke-remote.sh
```

Mints a client token (RS256, signs with `../jwt_private_key`), runs a full push → R2 →
fresh-clone pull, asserts byte-exact, asserts a no-token request is rejected (401),
and prints cold vs warm latency. Authenticating a git-lfs client is unchanged from
[`../README.md`](../README.md#authenticating-a-git-lfs-client) (mint a token, `_jwt`
Basic piggyback) — just point `lfs.url` at the endpoint above.

**Staging baseline (po-g9y.10, 2026-06-22):** push+pull byte-exact (3 MB random),
no-token → 401, cold ≈ 3.4 s, warm ≈ 0.8 s. The prod config below has **not** been
smoke-tested yet (blocked — see status).

## Cold start

The container scales to zero after `sleepAfter` (10 m). The **first request after
idle wakes it: ≈ 3.4 s** (container boot + uwsgi); subsequent requests ≈ 0.8 s. For
prod the cost/latency trade was **decided: accept the cold start, no keep-warm** (bead
prereq #4). So `sleepAfter` stays at 10 m and no minimum-instance / ping is added. To
revisit, raise `sleepAfter` or add a keep-warm ping (more $).

## Go-live status (po-g9y.11)

**✅ LIVE (2026-06-27).**

Production Git LFS is **live at `https://lfs.portaljs.com`**, backed by the
`portaljs-giftless` R2 bucket. Both prereqs landed and the deploy is done +
verified end-to-end (RS256 client token → presigned R2 URL → verify callback,
HTTP 200 over the custom hostname; cold start ~1.7s; valid Let's Encrypt cert).

| # | Prerequisite | Status |
|---|--------------|--------|
| 1 | **Prod R2 token** at `~/.config/portaljs/giftless-r2-prod.env` (Object R&W, scoped to `portaljs-giftless`) | ✅ in place |
| 2 | **DNS + cert** for `lfs.portaljs.com` | ✅ auto via `custom_domain: true` (no manual DNS/ACM) |

The RS256 keypair is persisted at `~/.config/portaljs/giftless-rs256-{private,public}.pem`
— the **private** key is the signer the token issuer (Arc/CI) uses to mint client
tokens, and is also the `GIFTLESS_JWT_PRIVATE_KEY` Worker secret. Rotate by
re-running `gen-rs256-keys.sh` (delete old keys first) + re-pushing secrets.

**To redeploy / rotate** (the repo now reflects prod — no flips needed):

1. `cd giftless/cloudflare && npm install && ./scripts/deploy.sh` — pushes the 4
   secrets + deploys the `giftless` worker (reads prod R2 creds from
   `~/.config/portaljs/giftless-r2-prod.env` and the RS256 keypair from `../jwt_*`).
2. Verify: `GIFTLESS_URL=https://lfs.portaljs.com ./scripts/smoke-remote.sh`
   (and/or `https://giftless.<account>.workers.dev`).
3. CORS is already applied to `portaljs-giftless`; re-run `./scripts/set-r2-cors.sh`
   only if the policy changes.

**Remaining cleanup:** delete the old `giftless-staging` worker (superseded by prod).

### Why ONE RS256 keypair (not the "separate verify keypair")

giftless's auth chain **aborts on the first provider that rejects a token's
signature** — it does not fall through to a second provider (`giftless/auth/__init__.py`
catches `Unauthorized` and stops). So two keypairs cannot coexist on one auth path: a
client token would hit the verify-callback provider first, fail, and 401. The working
model is a **single keypair**: its public key verifies both client tokens (issuer-signed)
and Giftless's own verify callbacks; its private key signs those callbacks and is also
held by the issuer to mint client tokens. Trade-off: a Giftless host compromise leaks
the signer (the private key is injected as a Worker secret) — **accepted** (bead
prereq #3: "store PRIVATE signer as a wrangler secret"). See
[`../README.md`](../README.md#jwt-model-staging-vs-production).
