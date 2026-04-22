# langchain-data-handling — One-Pager

Load and chunk documents for LangChain 1.0 RAG pipelines correctly — language-aware splitters, table-safe PDF loaders, Cloudflare-compatible web loaders, chunk-boundary strategies that survive real-world document structure.

## The Problem

`RecursiveCharacterTextSplitter` with default separators `["\n\n", "\n", " ", ""]` splits on any blank line — including **inside** triple-backtick code fences in Markdown. A RAG system over a Python docs site retrieves the first half of a function (signature + one line) in one chunk and the body in another, then the LLM hallucinates what the function does. `PyPDFLoader` splits documents page-by-page, tearing multi-row tables in half so RAG answers misquote numeric rows. `WebBaseLoader`'s default User-Agent looks like a bot; Cloudflare-protected sites return a 403 interstitial HTML blob instead of real content, and the crawler indexes the challenge page. All three failures are silent — no exceptions, just bad retrieval.

## The Solution

This skill gives you a loader-selection matrix (PDF / web / Markdown / code / corpus) mapped to the right LangChain 1.0 loader with strengths, gotchas, and cost notes; a splitter decision tree that routes Markdown to `Language.MARKDOWN`, Python to `Language.PYTHON`, and long HTML to `HTMLHeaderTextSplitter`; chunk-size and overlap presets (1000/100 for prose, 1500/150 for code, 500/50 for FAQs) calibrated against retrieval eval sets; a table-preservation pattern that detects tables in PDFs and indexes them as separate structured records; and a crawler-hygiene reference covering User-Agent headers, `robots.txt`, rate limiting, and Cloudflare-friendly patterns. Pinned to LangChain 1.0.x with four deep references.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python engineers and researchers ingesting documents for RAG pipelines — PDFs, Markdown docs sites, web pages, code repos — using LangChain 1.0 |
| **What** | Loader-selection matrix, splitter decision tree, chunk-size presets, table-detection and indexing pattern, crawler-hygiene guide, 4 references (loader-selection-matrix, language-aware-splitters, table-preservation, crawler-hygiene) |
| **When** | When building a RAG pipeline, diagnosing why retrieval misquotes a table, debugging a web crawler that returns blank content, or tuning chunk boundaries for a documentation site with mixed prose and code |

## Key Features

1. **Language-aware splitting that respects code fences** — `RecursiveCharacterTextSplitter.from_language(Language.MARKDOWN)` keeps triple-backtick fences intact, so function signatures and bodies stay in the same chunk; `Language.PYTHON` splits at `class`/`def` boundaries instead of blank lines
2. **Table-safe PDF loading with separate structured indexing** — `PyMuPDFLoader` / `UnstructuredPDFLoader` detect table structure and emit them as distinct elements; tables are indexed as structured records (one record per row with column metadata), so numeric answers don't span chunk boundaries
3. **Crawler hygiene for Cloudflare-protected sites** — `header_template={"User-Agent": "Mozilla/5.0 ..."}` plus `robots.txt` respect and per-host rate limiting (default 1 req/sec) prevents 403 interstitials and courteous crawler behavior; RSS/sitemap loaders preferred when available

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
