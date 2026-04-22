# Hybrid Search: BM25 + Vector

Pure vector search misses exact-match keywords (SKUs, error codes, function
names, version numbers). Pure BM25 misses paraphrase. Ensemble retrieval solves
both — and the weight between them is the knob that most RAG tuning lives on.

## Pattern

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = FAISS.from_documents(docs, embedding=embeddings)

bm25 = BM25Retriever.from_documents(docs)
bm25.k = 10  # return top-10 from keyword search

vector = vector_store.as_retriever(search_kwargs={"k": 10})

hybrid = EnsembleRetriever(
    retrievers=[bm25, vector],
    weights=[0.4, 0.6],
    # EnsembleRetriever uses Reciprocal Rank Fusion (RRF) to merge.
    # weights scale the RRF score contribution of each retriever.
)

results = hybrid.invoke("What does E429 mean in our API?")
```

## Why Reciprocal Rank Fusion (RRF)?

RRF combines rankings from two incomparable score scales (BM25 TF-IDF vs
cosine similarity) without trying to calibrate either. The formula:

```
rrf_score(doc) = sum(weight_r / (k + rank_r(doc))  for r in retrievers)
```

where `k=60` is the standard RRF constant and `rank_r(doc)` is the doc's
position in retriever `r`'s returned list (1-indexed).

This is robust. It does not care that BM25 returns 12.4 and vector returns 0.87.

## Weight tuning procedure

1. Prepare 50-100 representative `(query, expected_doc_ids)` pairs.
2. Run each query at five settings: weights `[0.2, 0.8]`, `[0.4, 0.6]`,
   `[0.5, 0.5]`, `[0.6, 0.4]`, `[0.8, 0.2]`.
3. Measure Recall@5 and MRR@10 per setting.
4. Pick the setting with the best tradeoff. In our experience (RAG over
   technical docs): `[0.4, 0.6]` (BM25 40%, vector 60%) is a common winner.
5. For exact-match-heavy domains (product catalogs, error-code-lookup):
   shift toward `[0.6, 0.4]`.
6. For paraphrase-heavy domains (customer support, legal research):
   shift toward `[0.3, 0.7]`.

## Evaluation harness

```python
def evaluate_retriever(retriever, golden_set, k=5):
    """Return (recall@k, mrr@k) on the golden set."""
    hits, mrr_sum = 0, 0.0
    for query, expected_ids in golden_set:
        results = retriever.invoke(query)
        ids = [doc.metadata["id"] for doc in results[:k]]
        matched = [i for i, did in enumerate(ids) if did in expected_ids]
        if matched:
            hits += 1
            mrr_sum += 1.0 / (matched[0] + 1)
    n = len(golden_set)
    return hits / n, mrr_sum / n
```

## When to add a reranker on top

If hybrid Recall@20 is high (you are retrieving the right docs in the top 20)
but Recall@5 is lower than you need (you are not ranking them into the top 5),
a reranker is the right next step.

If hybrid Recall@20 is low, the embeddings or BM25 corpus has a deeper problem
(chunking, embedding model, metadata filtering) — a reranker cannot rescue bad
retrieval.

## BM25 gotchas

- `BM25Retriever.from_documents` builds the index in-memory on every init. For
  large corpora (> 100K docs), persist with `pickle` and reload on startup.
- BM25 has no built-in metadata filter. For multi-tenant isolation, construct
  a per-tenant `BM25Retriever` from the tenant's doc subset at request time.
  Cache these with an LRU per tenant.
- Chinese/Japanese/Korean text needs `jieba`/`fugashi`/`konoha` for tokenization
  before `BM25Retriever` can produce reasonable results.

## Debugging low recall

When hybrid recall is worse than either component alone:

1. Check RRF is actually merging — the `EnsembleRetriever` should return a
   deduplicated list. If you see duplicates, you have two separately-indexed
   copies of the same doc with different IDs.
2. Check metadata filters apply to both retrievers — if only vector filter
   applied, BM25 leaks other-tenant results.
3. Spot-check top-20 from each retriever separately. If BM25 returns nothing
   for short-word queries, it is tokenization not weights.
