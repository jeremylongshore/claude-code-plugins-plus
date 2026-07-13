# langchain-embeddings-search — One-Pager

Build and query vector stores with LangChain 1.0 without getting burned by flipped score semantics, dim mismatches, reranker quirks, or chunk-splitter bugs.

## The Problem

`FAISS.similarity_search_with_score()` returns L2 distance (**lower is better**); `Pinecone.similarity_search_with_score()` returns cosine similarity (**higher is better**). Swap vector stores and your `if score > 0.8` filter now keeps the garbage and drops the good results — silently, with no error. Embedding-dim mismatches (1536 vs 3072) crash at insert time after 10 minutes of processing, not at `VectorStore.__init__`. `RecursiveCharacterTextSplitter` default separators break inside Markdown code fences, truncating code examples mid-function. Cohere/Jina reranker scores are within-query relative, so filtering by threshold drops the right answer for low-variance queries.

## The Solution

This skill gives you a startup dim-assertion guard, a score normalizer at the retriever boundary so downstream code never sees raw store-specific scores, a vector-store comparison matrix (FAISS/Chroma/PGVector/Pinecone) with score direction and latency tradeoffs, language-aware text splitters (`Language.MARKDOWN`, `Language.PYTHON`) that respect structural boundaries, an `EnsembleRetriever` pattern combining BM25 + vector with tuned weights, and a reranker pattern that filters by rank (not threshold). Pinned to LangChain 1.0.x with three deep references.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python engineers building RAG pipelines, migrating between vector stores, or tuning retrieval quality with LangChain 1.0 |
| **What** | Dim-assertion guard, score normalizer, vector-store comparison matrix, language-aware chunking, BM25 + vector hybrid retriever, rerank-by-rank pattern, 3 references (vector-store-comparison, score-semantics, hybrid-search) |
| **When** | When building a RAG retriever, choosing or swapping vector stores, tuning similarity thresholds, or diagnosing why retrieval quality dropped after a migration |

## Key Features

1. **Score normalizer at retriever boundary** — Collapses FAISS L2 distance, PGVector cosine distance, and Pinecone cosine similarity into a single `[0, 1]` similarity scale where 1 = identical, so thresholds mean the same thing regardless of backend
2. **Vector-store comparison matrix with migration checklist** — Score metric, direction, typical latency, filtering support, and namespace isolation for FAISS / Chroma / PGVector / Pinecone, plus a five-step migration procedure (re-embed → dim assertion → dual-write → shadow-read → cutover)
3. **Hybrid search via `EnsembleRetriever` with weight tuning procedure** — BM25 + vector combined with RRF, plus a 50-100-pair golden-set evaluation harness that measures Recall@5 and MRR@10 to pick the right weight split for your corpus (exact-match-heavy → 0.6/0.4; paraphrase-heavy → 0.3/0.7)

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
