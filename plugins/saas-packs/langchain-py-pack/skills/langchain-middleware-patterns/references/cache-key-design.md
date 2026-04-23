# Cache Key Design

The cache key is the single most dangerous primitive in your middleware stack.
Get it wrong and you leak PII across tenants (P24), miss tool-context changes
(P61), or silently serve stale responses after a schema upgrade. This reference
covers hash inputs, invalidation, backends, and known pitfalls.

## What must go into the key

Every cache key must be a hash over **all** of these:

| Input | Why | Source |
|---|---|---|
| `redacted_prompt` | Tenants share semantic prompts; PII must be removed first (P24) | Output of `redaction_middleware` |
| `tool_schemas_hash` | Two chains with different tools give different answers (P61) | `json.dumps(bound_tools, sort_keys=True)` |
| `tenant_id` | Cross-tenant isolation; same prompt must not cross (P33) | `config["configurable"]["tenant_id"]` |
| `model_id` | Different models give different answers | `model.model_name` |
| `schema_version` | Bump after a tools/system-prompt change to invalidate cache | Constant, update per deploy |
| `temperature` (if > 0) | Non-deterministic output must not be cached across different settings | `model.temperature` |

## Reference implementation

```python
import hashlib
import json
from typing import Any

SCHEMA_VERSION = "2026-04-v1"  # bump on breaking change to prompts/tools/system message

def cache_key(
    redacted_prompt: str,
    bound_tools: list[dict] | None,
    tenant_id: str,
    model_id: str,
    temperature: float = 0.0,
    schema_version: str = SCHEMA_VERSION,
) -> str:
    """Blake2b-16 hash. Deterministic. Tool-aware. Tenant-aware."""
    h = hashlib.blake2b(digest_size=16)
    def _add(part: str | bytes) -> None:
        if isinstance(part, str):
            part = part.encode("utf-8")
        h.update(part)
        h.update(b"\x1f")  # unit separator (U+001F) — not valid in text/JSON
    _add(schema_version)
    _add(model_id)
    _add(f"T={temperature:.2f}")
    _add(tenant_id)
    _add(redacted_prompt)
    if bound_tools:
        _add(json.dumps(bound_tools, sort_keys=True, default=str))
    return h.hexdigest()
```

**Why `blake2b` not `sha256`:** blake2b-16 (128-bit) is ~40% faster than
sha256-32 on short inputs and has no known distinguishing attacks at this size.
For cache keys the collision risk is negligible at 2^64 (birthday bound on 128
bits).

**Why the unit-separator byte:** Concatenating `foo|bar` and `foob|ar` without
a separator gives identical hashes for crafted inputs. `\x1f` is illegal in
UTF-8 text and JSON, so it is a safe concatenation boundary.

## Backend comparison

| Backend | Hit/miss latency | Multi-process? | Persistence | Size limits | Recommended when |
|---|---|---|---|---|---|
| `InMemoryCache` | <0.1ms | **No** (per-process) | None (lost on restart) | RAM only | Dev, tests, single-worker prototypes |
| `SQLiteCache` | 0.2–0.5ms | Yes (single-host) | Disk | File size | Local dev, single-host deploy |
| `RedisCache` | 0.5–2ms (LAN) | Yes (cluster) | Yes (AOF/RDB) | Redis maxmemory | Production multi-worker |
| `RedisSemanticCache` | 5–30ms (embedding) | Yes (cluster) | Yes | Redis maxmemory | High similarity tolerance, expensive models |

**P29 analog:** `InMemoryCache` is per-process — do not use it in a multi-worker
deploy or you get per-worker cache silos and an N-fold larger provider bill.

**P62:** `RedisSemanticCache` hit rate drops below 5% with the default 0.95
threshold. Tune down to 0.85–0.90 after offline eval on a gold pair set.

## Invalidation strategies

### 1. TTL (time-based)

Simple but coarse. Every entry expires after N seconds. Use for prompts whose
answer is time-sensitive (news, stock prices, inventory).

```python
# Redis: SET key value EX 3600
```

**Drawback:** Stale entries for the first TTL after a schema change.

### 2. Schema version bump (deploy-coupled)

Bump `SCHEMA_VERSION` on every deploy that changes prompts, tools, or system
messages. Old entries become unreachable because their key prefix no longer
matches.

**Pro:** Instantaneous, atomic.
**Con:** Memory not reclaimed until Redis evicts LRU.

### 3. Tenant-wide purge (incident response)

For a cache-poisoning incident affecting one tenant, scan keys by tenant
prefix and delete. Requires the tenant_id to be visible in the key *outside*
the hash — usually via a Redis key naming convention:

```python
redis_key = f"cache:T={tenant_id}:{hash_value}"
# Purge: SCAN 0 MATCH cache:T=T1:* → DEL
```

**Tradeoff:** Leaking tenant_id in the Redis key is safe for operators with
Redis access but exposes tenant identity in any Redis monitoring UI. For
high-secrecy tenants, use a deterministic HMAC of tenant_id instead.

### 4. Per-tool-schema eviction

When you change a tool's signature, bump its schema version and include it in
`bound_tools`. Old cache keys for that tool become stale. No scan needed — old
keys simply never hit again.

## Known pitfalls

### Pitfall 1 — Hashing the raw prompt (P24)

The #1 cache leak. Fix: always redact first. Assert it in a test (see
`ordering-invariants.md`).

### Pitfall 2 — Ignoring bound tools (P61)

```python
# WRONG — two chains with different tools share the cache:
set_llm_cache(InMemoryCache())
chain_a = prompt | model.bind_tools([search_tool])
chain_b = prompt | model.bind_tools([code_exec_tool])
# chain_a and chain_b may return the same cached answer.
```

Fix: use the custom `cache_key` above, or use `SQLiteCache(database_path=...)`
with a key function override.

### Pitfall 3 — Temperature in the key for deterministic calls only

If `temperature > 0`, caching non-deterministic output gives a false sense of
consistency — users re-asking the same question get the same answer when the
non-cached path would give variation. For creative tasks, either skip caching
or document that cached responses are "frozen."

### Pitfall 4 — Non-JSON-serializable tool bindings

Tools defined from custom Python callables may have Pydantic schemas with
non-stable field ordering. Always `sort_keys=True` in `json.dumps`, and for
tool functions that include lambdas or closures, hash their `.name` and
`.description` only — never the function object itself (memory address
differs between processes).

### Pitfall 5 — Unicode normalization

User input with different Unicode normalizations (NFC vs NFD) gives different
keys for the same visible text. Normalize before hashing:

```python
import unicodedata
redacted_prompt = unicodedata.normalize("NFC", redacted_prompt)
```

### Pitfall 6 — Cache hits counted as zero cost in budget

A cache hit consumes no tokens but still consumes a request slot. Budget
middleware must increment a request counter even on hits (see P29 rate limiting
for the parallel concern). Don't skip budget bookkeeping because the call was
cheap.

## LangChain 1.0 native cache vs custom

```python
# Native — hashes prompt string only (P61)
from langchain_core.globals import set_llm_cache
from langchain.cache import InMemoryCache
set_llm_cache(InMemoryCache())

# Custom — full-featured, recommended for production
# See the cache_middleware in SKILL.md Step 5.
```

Native cache is fine for local dev with a single tool binding. Switch to the
custom middleware as soon as you have tools, tenants, or multi-worker.

## Testing

```python
def test_cache_key_redaction_required():
    """Same semantic prompt with different PII → same key only if redacted."""
    from redact import redact
    a, _ = redact("Email alice@a.com")
    b, _ = redact("Email bob@b.com")
    assert cache_key(a, None, "T", "m", 0.0) == cache_key(b, None, "T", "m", 0.0)

def test_cache_key_tool_sensitivity():
    t1 = [{"name": "search", "parameters": {}}]
    t2 = [{"name": "search", "parameters": {"max_results": {"type": "int"}}}]
    assert cache_key("p", t1, "T", "m") != cache_key("p", t2, "T", "m")

def test_cache_key_schema_version_bump():
    k1 = cache_key("p", None, "T", "m", schema_version="v1")
    k2 = cache_key("p", None, "T", "m", schema_version="v2")
    assert k1 != k2
```

## References

- [LangChain — LLM caching](https://python.langchain.com/docs/how_to/llm_caching/)
- [LangChain — Chat model caching](https://python.langchain.com/docs/how_to/chat_model_caching/)
- [Redis LRU eviction](https://redis.io/docs/latest/develop/reference/eviction/)
- Pack pain catalog entries **P24, P61**, plus P29 (multi-process), P33 (tenant isolation), P62 (semantic cache thresholds)
