---
title: "Building Moat: Auth, On-Chain Receipts, and 117 Integration Tests in One Week"
description: "How I built a policy-enforced execution layer for AI agents with HTTP proxy allowlists, IRSB on-chain receipts, and 117 integration tests — plus the CI saga that took 6 commits to fix."
date: "2026-02-21"
tags: ["security", "authentication", "testing", "python", "ci-cd", "blockchain", "proxy"]
featured: false
---
## What Moat Does

Moat is a policy-enforced execution and trust layer for AI agents. When an autonomous agent wants to call an API, send a Slack message, or spend money, it goes through Moat. Every request gets evaluated against a policy engine, executed through a sandboxed adapter, and receipted — both off-chain in a database and on-chain on Sepolia.

Four FastAPI microservices make up the system: a Control Plane (capability registry), Gateway (execution choke-point), Trust Plane (reliability scoring), and an MCP Server (agent-facing tool surface).

## HTTP Proxy with Domain Allowlists

The first big feature was an `HttpProxyAdapter` that lets sandboxed agents make outbound HTTPS requests — but only to approved domains.

The security model is simple and opinionated: allowlists beat blocklists. A blocklist means you're playing whack-a-mole with every new malicious domain. An allowlist means the agent can only reach what you explicitly permit.

```python
class HttpProxyAdapter(AdapterInterface):
    """Generic HTTPS proxy adapter with domain allowlist enforcement."""

    async def execute(self, capability_id, capability_name, params, credential):
        url = params["url"]
        hostname = urlparse(url).hostname

        # Private IP blocking
        if hostname in ("localhost", "127.0.0.1") or hostname.endswith((".local", ".internal")):
            return {"status": "denied", "reason": "private network access blocked"}

        # Domain allowlist enforcement
        if hostname not in self._allowed_domains:
            return {"status": "denied", "reason": f"domain {hostname} not in allowlist"}

        # HTTPS only (HTTP allowed only for localhost in tests)
        if not url.startswith("https://"):
            return {"status": "denied", "reason": "HTTPS required"}

        async with self._client as client:
            resp = await client.request(method, url, headers=safe_headers, content=body)
            return {"status": "success", "http_status": resp.status_code, "body": resp.text}
```

The default allowlist covers the APIs agents actually need: `api.github.com`, `api.gitcoin.co`, blockchain RPC endpoints on Alchemy. Loaded from the `HTTP_PROXY_DOMAIN_ALLOWLIST` environment variable, so operators can customize without touching code.

Dangerous headers get stripped (hop-by-hop headers, host, content-length). Connection pooling via a persistent `httpx.AsyncClient` with 30-second timeouts and a 5-redirect cap.

## Wiring Real IRSB On-Chain Receipts

The Gateway now submits cryptographic receipts to the blockchain after every successful execution. Every Moat execution produces two audit records: an off-chain Moat Receipt (immediate, database-backed) and an IRSB IntentReceipt (on-chain, Sepolia). Both share the same `intentId`, so you can cross-reference between the audit log and the chain.

The receipt computation uses five keccak256 hashes:

```python
def compute_intent_hash(capability_id, input_hash, tenant_id, timestamp) -> bytes:
    preimage = f"{capability_id}:{input_hash}:{tenant_id}:{timestamp}"
    return _keccak256(preimage.encode())
```

Plus `outcome_hash`, `constraints_hash`, `route_hash`, and `evidence_hash` — all deterministic from the execution metadata. The receipt gets signed via EIP-191 `personal_sign` and submitted to the `IntentReceiptHub` contract on Sepolia.

What makes this production-viable is the graceful degradation chain. The system defaults to `dry_run` mode — it computes and logs the full receipt but doesn't submit to chain. If no RPC URL is configured: `dry_run_no_rpc`. No signing key: `dry_run_no_key`. Full submission: `sepolia`. And if the on-chain submission fails, it's marked `sepolia_failed` but the execution still succeeds. On-chain receipts are non-blocking by design.

## The Policy Engine: Default-Deny Everything

The policy engine is default-deny. Five denial rules evaluate in priority order, and the first failure short-circuits:

1. **No policy bundle** → DENY (no policy = no access)
2. **Scope not allowed** → DENY
3. **Daily budget exceeded** → DENY
4. **Domain allowlist conflict** → DENY
5. **Requires approval** → DENY

Only if all five pass does the request get through.

At Gateway startup, seven default `PolicyBundle` objects get seeded for the "automaton" tenant. The `http.proxy` capability gets a $150/day budget ceiling with domain-allowlist enforcement. `slack.send` gets $50/day. Each capability has explicit budget limits that the policy engine enforces per-tenant.

## 117 Integration Tests

The test suite breaks down into two core modules:

**55 Policy Bridge tests** cover default-deny enforcement, budget ceilings, scope denial, spend tracking, and domain allowlist conflict detection.

**62 IRSB Receipt tests** verify the 5-hash computation (determinism, 32-byte length, input sensitivity), EIP-191 signing (65-byte signature format), dry-run modes, error handling, and non-success receipt filtering.

That's 117 tests just for the policy and receipt layers. The execute pipeline has its own test suite covering the full 10-step pipeline, idempotency key caching, capability-not-found (404), inactive capabilities (403), missing tenant (422), policy denial, and adapter routing.

Every test runs against real SQLite databases with async SQLAlchemy. No mocking the policy engine or receipt computation — these are integration tests that prove the actual code paths work.

## The CI Saga: 6 Commits for One Import Bug

This is the part nobody talks about. The feature code took one day. Getting CI green took six commits across a single afternoon.

**The problem:** Multiple services have `tests/` directories. When pytest runs from the monorepo root, it treats those directories as a namespace package and throws `ModuleNotFoundError: No module named tests.conftest`.

**Attempt 1:** Add a root `conftest.py` to establish pytest boundaries. Doesn't fully solve namespace collisions.

**Attempt 2:** Remove `tests/__init__.py` from each service. Now tests can't import from their own `app` module.

**Attempt 3:** Add `import_mode = "importlib"` to `pyproject.toml`. Turns out that's a CLI flag, not a valid ini option.

**Attempt 4:** Move to `addopts = "--import-mode=importlib"`. Better, but still need per-service isolation.

**Attempt 5:** Add explicit `sys.path` manipulation in each service's `conftest.py`. Ruff fires an E402 lint error — imports must come before `sys.path` setup.

**Attempt 6:** Reorder the conftest to put all stdlib imports first, `sys.path` setup in the middle, and `from app.xxx` imports last:

```python
import os
import sys
from pathlib import Path

_service_root = str(Path(__file__).resolve().parent.parent)
if _service_root not in sys.path:
    sys.path.insert(0, _service_root)

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_test_db_path}"
os.environ["MOAT_AUTH_DISABLED"] = "true"
```

Green. Finally.

On top of that, 47 lint errors needed fixing: merging multiple `endswith()` calls into tuples (`PIE810`), adding `from None` to re-raised exceptions (`B904`), replacing `dict()` with dict literals, removing unused imports, sorting import blocks. Ruff is unforgiving and that's the point.

## What I Learned

**Allowlists are safer than blocklists.** It's tempting to block known-bad domains. But agents are creative — they'll find domains you didn't block. An allowlist means nothing unexpected gets through, period.

**On-chain receipts should be non-blocking.** The blockchain is slow and unreliable. Making execution depend on on-chain submission would mean agents fail when Sepolia has issues. The graceful degradation chain means receipts are best-effort without compromising the primary workflow.

**Monorepo test isolation is genuinely hard.** Six commits for what amounts to an import path problem. Python's namespace package behavior interacts badly with pytest's collection strategy when multiple services share the same directory structure. The `sys.path` solution isn't elegant, but it's explicit and it works.

**Write the tests before fixing CI.** I had 117 tests written and passing locally before any of the CI drama. That meant every CI fix attempt was validated against a real test suite — I could distinguish "CI is broken" from "tests are broken" immediately.
