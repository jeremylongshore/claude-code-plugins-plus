# Cache Tuning

Three layers. Pick by workload shape.

| Layer | Library | When to use | Hit-rate reality |
|-------|---------|-------------|-------------------|
| Exact cache | `SQLiteCache` / `RedisCache` / `InMemoryCache` | Deterministic prompts (temperature=0), small key space | 10-60% depending on traffic |
| Semantic cache | `RedisSemanticCache` (requires embeddings) | Paraphrased user queries, chatbots, FAQ | 20-50% once threshold is tuned |
| None | — | Unique prompts, streaming audits, compliance runs | n/a |

LangChain 1.0 caches operate on the full `ChatModel.invoke` call, keyed by the serialized prompt + model config + bound tools. Including bound tools in the key is critical (P61 — tool drift caused silent cache poisoning pre-fix).

## Exact Cache Setup (Redis)

```python
from langchain_core.globals import set_llm_cache
from langchain_community.cache import RedisCache
import redis

r = redis.Redis.from_url("redis://cache:6379/0", socket_timeout=2)
set_llm_cache(RedisCache(r))
```

Key hygiene:

- Include the model string, temperature, top_p, and tool signatures in the derived key (LangChain 1.0 does this; verify in `cache_key` debug logs).
- Apply an explicit TTL (`r.expire(...)` via a keyspace notification, or migrate to a wrapper that sets TTL per-set). Default Redis keys are immortal.
- Separate caches per tenant to prevent cross-tenant leakage — use a Redis logical DB or key prefix.

## Semantic Cache Setup

```python
from langchain_community.cache import RedisSemanticCache
from langchain_openai import OpenAIEmbeddings

set_llm_cache(
    RedisSemanticCache(
        redis_url="redis://cache:6379/1",
        embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        score_threshold=0.88,   # override the 0.95 default — see P62
    )
)
```

### Threshold Tuning Procedure (P62)

The default `score_threshold=0.95` yields under 5% hit rate on real chat traffic. Tune with a golden set.

1. Collect 200-500 real user prompts from logs with human-labeled "should hit" pairs (duplicates, paraphrases, trivial rewrites).
2. For each pair, compute the cosine similarity with your chosen embedding model.
3. Plot the distribution. Pick the threshold that maximizes F1 between "should hit" and "should miss".
4. Typical answer: **0.85 to 0.90** for `text-embedding-3-small`; **0.80 to 0.88** for `text-embedding-3-large`.
5. Re-tune quarterly or after any embedding model swap. Write the golden set into `tests/fixtures/cache_golden.jsonl`.

### Temperature Caveat

Semantic cache on `temperature > 0` returns cached completions from a different random draw — users notice. Options:

- Force `temperature=0` on any route behind semantic cache.
- Disable semantic cache for creative routes; keep exact cache only.
- Cache the *retrieval* and regenerate final answers (RAG pattern).

## TTL Strategy

| Content class | TTL | Reason |
|---------------|-----|--------|
| Deterministic extraction / classification | 7-30 days | Prompts and schemas change slowly |
| Chat Q&A | 24-72 hours | Underlying knowledge drifts |
| RAG retrieval embeddings | Tied to doc refresh cadence | Match source-of-truth update frequency |
| Per-tenant config prompts | Invalidate on config change | Use a version key component |

## Invalidation

Bake a `prompt_version` and `tools_version` into the cache key. Bumping either value retires stale entries immediately, avoiding a full `FLUSHDB`.

## Checklist

- [ ] Semantic cache threshold is tuned on a golden set, not left at 0.95.
- [ ] Cache key includes model + temperature + tool signatures + prompt version.
- [ ] Redis keys have an explicit TTL.
- [ ] Hit rate is exported as a metric (`cache_hit_total` / `cache_miss_total`).
- [ ] Per-tenant isolation via DB or key prefix.
