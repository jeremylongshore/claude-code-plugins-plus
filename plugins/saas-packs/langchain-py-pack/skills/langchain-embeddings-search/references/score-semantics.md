# Similarity Score Semantics

Why `score > 0.8` means completely different things in FAISS and Pinecone, and
how to derive a normalized similarity in [0, 1] regardless of backend.

## The underlying math

Each backend stores a distance or similarity function. LangChain passes the raw
value through `similarity_search_with_score` without normalizing.

### FAISS (default)

Metric: **L2 (Euclidean) distance** between the query vector and the document
vector, on *non-normalized* vectors.

```
score = sqrt(sum((q[i] - d[i])**2 for i in range(dim)))
```

Range: `[0, +infinity)`. `0` = identical. Lower = more similar.

For `text-embedding-3-small` (1536 dims, length-normalized by OpenAI), typical
L2 distances:

- Identical: 0.0
- Near-duplicate (same topic, same phrasing): 0.2-0.4
- Related (same topic, different phrasing): 0.5-0.9
- Unrelated: 1.0-1.5
- Opposite: 1.4+

### Pinecone (cosine default)

Metric: **cosine similarity** between query and doc vectors.

```
score = (q . d) / (||q|| * ||d||)
```

Range: `[-1, 1]`. For length-normalized embeddings (which OpenAI returns),
effectively `[0, 1]`. `1` = identical. Higher = more similar.

Typical values on OpenAI embeddings:

- Identical: 1.0
- Near-duplicate: 0.85-0.95
- Related: 0.70-0.84
- Unrelated: 0.30-0.70
- Opposite: 0.0-0.30

### PGVector (cosine distance)

Metric: **cosine distance** = `1 - cosine_similarity`.

Range: `[0, 2]`. `0` = identical. Lower = more similar.

### Chroma (cosine)

Configurable; the LangChain default is cosine similarity, same as Pinecone.

## Normalization recipe

Everything downstream of the retriever should see similarity in `[0, 1]`, `1` =
identical:

```python
def normalize(score: float, store_type: str) -> float:
    """Return similarity in [0, 1] where 1 = identical."""
    if store_type == "faiss_l2":
        # Collapse unbounded distance into similarity-like value.
        # The formula below is robust to the full distance range;
        # calibrate the constant on your dataset if you need exact comparability.
        return 1.0 / (1.0 + score)
    if store_type == "faiss_cosine":
        # FAISS can be configured with METRIC_INNER_PRODUCT for cosine on
        # length-normalized vectors. Score is then already in [-1, 1].
        return max(0.0, min(1.0, (score + 1.0) / 2.0))
    if store_type == "pgvector_cosine_distance":
        return 1.0 - score / 2.0
    if store_type in {"pinecone", "chroma_cosine"}:
        return max(0.0, min(1.0, score))
    raise ValueError(f"Unknown store_type: {store_type}")
```

Then thresholds mean the same thing regardless of backend:

```python
results = store.similarity_search_with_score(query, k=20)
normalized = [(doc, normalize(s, "pinecone")) for doc, s in results]
keep = [(d, s) for d, s in normalized if s > 0.7]
```

## Score thresholds: how to pick

Do not pick 0.7 because it "sounds right." Calibrate on a golden set:

1. Prepare 50-100 (query, expected_doc) pairs sampled from real user traffic.
2. Run each query, extract the top-20 results with normalized scores.
3. For each pair: note the score of the expected_doc (if retrieved at all) and
   the score of the first irrelevant result.
4. The optimal threshold is just below the lowest expected-doc score and just
   above the highest irrelevant-doc score. If they overlap, your embeddings
   are not strong enough — consider a reranker.

Typical picked thresholds on OpenAI `text-embedding-3-small` + cosine:
`0.55-0.65` for "relevant enough to show," `0.75+` for "likely answer."

## Common mistakes

- **Filtering FAISS by `score < 0.5` and thinking that is similar.** 0.5 is
  moderately similar on OpenAI normalized vectors (recall the distance table).
  Want highly similar? Try `< 0.35`.
- **Assuming symmetric ranges.** L2 distance is unbounded above; cosine is
  bounded. Filtering the top-20 of a long-tail query on FAISS returns very
  different shape than on Pinecone.
- **Mixing normalized scores with raw scores.** Always pick a side at the
  retriever boundary. If any code path reads raw scores, all of it must.

## When scores lie

Embedding models trained on short web snippets (like OpenAI's general-purpose
models) produce unreliable scores on:

- **Very short text** (< 5 words). Cosine similarity approaches 1.0 for any two
  short texts that share a word.
- **Code snippets**. Specialized code embeddings (e.g., `text-embedding-3-large`
  fine-tuned, or a code-specific model) are noticeably better.
- **Non-English**. Multilingual performance is uneven. Evaluate on your
  language before trusting scores.

For these cases, a reranker is usually cheaper than a different embedding model.
