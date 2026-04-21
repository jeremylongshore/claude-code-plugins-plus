# Cache Economics

Three kinds of caching, three different break-even calculations, three
different ways to misconfigure. This reference covers when each pays off,
the threshold tuning procedure for semantic caches, and the break-even math
that tells you whether caching is earning its keep.

## The three cache types

| Type | Scope | Hit criterion | LangChain class | Best for |
|---|---|---|---|---|
| **Exact** | LangChain-level | Prompt string equality | `SQLiteCache`, `InMemoryCache` | Deterministic queries, memoized tools |
| **Semantic** | LangChain-level | Embedding similarity > threshold | `RedisSemanticCache` | FAQ-style workloads, paraphrased queries |
| **Prompt cache** | Provider-native (Anthropic) | Prefix tokens match within cache TTL | `ChatAnthropic` with `cache_control` blocks | Long shared system prompts, RAG context |

They compose. You can (and often should) layer Anthropic prompt caching for
the static prefix with exact caching for the full deterministic queries. Do
**not** use `InMemoryCache` on tool-binding chains — it ignores bound tools in
the cache key and returns wrong answers (P61).

## Break-even: Anthropic prompt cache

Anthropic prompt cache:
- **Cache write:** 1.25x the input rate
- **Cache read:** 0.10x the input rate
- **TTL:** 5 minutes default, 1 hour with extended-cache beta

Break-even formula: a cached prefix pays for itself on the **4th use** within
the TTL window.

```
cost_no_cache = N * prefix_tokens * 1.00 * rate
cost_cached   = 1 * prefix_tokens * 1.25 * rate  +  (N - 1) * prefix_tokens * 0.10 * rate
break_even = cost_no_cache > cost_cached
           = N * 1.00 > 1.25 + (N - 1) * 0.10
           = N * 0.90 > 1.15
           = N > 1.278
```

Wait — the algebra says 1.28. Why do we say "4th use" as the rule of thumb?
Because you only cache chunks of the prefix that are **≥1024 tokens** (the
Anthropic minimum), and the TTL expires aggressively. In practice, prefixes
used 2-3 times within 5 minutes do not pay back because your actual hit rate
is below the theoretical maximum. Real-world break-even lands at ~4 uses in
production data.

**When caching is losing money:** run the `CacheLedger.savings_vs_no_cache()`
from the main skill Step 5 over a 24h window. If the result is negative or
within ±10% of zero, your cache hit rate is too low — the prefix is probably
too short, too dynamic, or the TTL window is missing the reuse pattern.

## Break-even: exact cache (SQLiteCache, RedisCache)

Exact caches are essentially free to write and free to read at the cache
storage level. The break-even question is different: "is the storage cost and
staleness risk worth the compute savings?"

Rules of thumb:

- **Almost always worth it** for deterministic tool outputs (e.g. a database
  lookup that returns `{"balance": 1234}` for a given user_id). Cache forever.
- **Almost always worth it** for evaluation runs (same prompts, different
  model versions) — cache the old model's results so you don't re-bill.
- **Never** on tool-binding chains unless the cache key includes tool schemas
  (P61).
- **Probably not** on user-facing chat — staleness is more expensive than the
  compute saving.

## Break-even: semantic cache (RedisSemanticCache)

Semantic caches have a very different math. The failure mode is not a wasted
write; it is a **false-positive hit** that returns a semantically wrong answer.

Variables:

- `hit_rate` — fraction of queries that hit above threshold
- `fp_rate` — fraction of hits that return a wrong answer
- `call_cost` — cost of the underlying model call
- `fp_cost` — cost of a wrong answer (support ticket, user churn, etc.)
  — typically 10-100x `call_cost`

```
savings_per_query = hit_rate * call_cost - hit_rate * fp_rate * fp_cost
```

If `fp_rate * fp_cost > call_cost`, the cache loses money even at 100% hit
rate. This is why threshold tuning is non-optional.

## Threshold tuning procedure

1. **Build a gold pair set** (minimum 200 pairs, 100 positive + 100 negative):
   - **Positive pairs** — queries where you want the same cached answer
     ("what's my account balance", "show me my current balance")
   - **Negative pairs** — queries that look similar but need different answers
     ("cancel my Netflix subscription", "cancel my Amazon subscription")

2. **Embed both sides** with your production embedding model
   (`langchain-openai` `text-embedding-3-small`, `langchain-voyageai`
   `voyage-3`, etc. — must match what the cache uses).

3. **Grid search** thresholds from 0.80 to 0.95 in 0.01 increments.
   For each threshold:
   - Hit rate on positives
   - False positive rate on negatives

4. **Pick the lowest threshold where FPR < 2%.** Lower is better (higher hit
   rate) but FPR is a hard constraint. In practice, this lands at 0.85-0.90
   for `text-embedding-3-small`. Default 0.95 is too strict for almost any
   real workload (P62).

5. **Ship with a daily audit** — sample 1% of cache hits, log to a review
   queue. If humans flag > 2% as wrong answers, raise the threshold.

Calibration worksheet (Python):

```python
import numpy as np
from langchain_openai import OpenAIEmbeddings

emb = OpenAIEmbeddings(model="text-embedding-3-small")

positives = [("query_a", "query_a_paraphrase"), ...]  # 100 pairs
negatives = [("query_b", "similar_but_different"), ...]  # 100 pairs

def similarity(a: str, b: str) -> float:
    va, vb = emb.embed_documents([a, b])
    return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb)))

pos_scores = [similarity(a, b) for a, b in positives]
neg_scores = [similarity(a, b) for a, b in negatives]

for t in np.arange(0.80, 0.96, 0.01):
    hit = sum(s > t for s in pos_scores) / len(pos_scores)
    fp  = sum(s > t for s in neg_scores) / len(neg_scores)
    print(f"t={t:.2f}  hit={hit:.1%}  fpr={fp:.1%}")
```

Ship the threshold where FPR first drops below 2%.

## Cache key hygiene

| Cache | Key must include |
|---|---|
| `InMemoryCache` | **Don't use with bound tools** |
| `SQLiteCache` | Prompt + tool schema hash + model + temperature |
| `RedisSemanticCache` | Namespace by tenant; threshold calibrated per tenant if queries differ |
| Anthropic prompt cache | Match `cache_control` blocks must be identical across calls |

Tenant isolation is critical — if Tenant A's cache can serve Tenant B, you
have a PII leak (P24 in the pain catalog). Always namespace Redis keys by
tenant, and never share a cache instance across tenants.

## Performance-tuning pair skill

Cache tuning for **latency** and cache tuning for **cost** use the same tools
but optimize for different metrics. Hit rate helps both. FPR kills quality
(cost concern) but doesn't affect latency directly.

Cross-reference `langchain-performance-tuning` for:
- Cache warm-up strategies
- Multi-layer cache architecture (hot in-process, warm Redis, cold object storage)
- Cache eviction policies

This skill focuses on the money view: break-even, threshold calibration,
ledger math, tenant isolation.
