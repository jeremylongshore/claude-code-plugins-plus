# langchain-enterprise-rbac — One-Pager

Enforce tenant isolation and role-based access across LangChain 1.0 chains and LangGraph 1.0 agents — retriever-per-request, tenant-scoped rate limits, role-scoped tool allowlists, and structured audit logs.

## The Problem

A B2B SaaS team wired up a RAG pipeline for their first two tenants: build the `PineconeVectorStore` at import time with `namespace="acme-corp"` (the first tenant onboarded), then convert it to a retriever with `.as_retriever(search_kwargs={"k": 4})`. Ship. Six weeks later tenant "Initech" onboarded; their first query returned three Acme Corp documents. The singleton retriever had cached the Acme namespace at process start — every request, regardless of the `tenant_id` in `RunnableConfig`, hit the same Pinecone namespace. Security review caught it three days later and issued a hold on the SOC2 renewal. This is pain-catalog entry P33, and it is the #1 cause of cross-tenant data leaks in LangChain 1.0 production. The sibling failure mode is missing audit logs on tool failures — when the tool raises, the invocation never reaches the cost/compliance sink, and you cannot prove who ran what during an incident.

## The Solution

This skill builds a retriever-per-request factory keyed by `config["configurable"]["tenant_id"]` so the filter / namespace / collection is bound at invocation time, not import time; maps the factory onto Pinecone (namespace), PGVector (row-level security), Chroma (collection-per-tenant), and FAISS (store-per-tenant, noted as a poor fit above 50 tenants); builds agents with role-scoped tool allowlists per-request; emits structured audit logs on both success and failure paths; and ships a two-tenant pytest regression fixture that asserts non-overlap on golden queries. Pinned to LangChain 1.0.x / LangGraph 1.0.x with five deep references.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Backend engineers building multi-tenant LangChain 1.0 / LangGraph 1.0 SaaS, SRE / platform engineers enforcing tenant isolation, security engineers preparing for SOC2 / ISO 27001 review |
| **What** | Retriever-per-request factory pattern, vector-store multi-tenant comparison (Pinecone / PGVector RLS / Chroma / FAISS), role-scoped tool allowlist, per-tenant rate limit and budget hooks, structured audit-log schema, two-tenant pytest regression fixture |
| **When** | Before the second tenant onboards; during SOC2 / ISO 27001 prep; after any cross-tenant leak incident; when adding a new tool that accepts external arguments; when migrating from a single-tenant vector store to a shared one |

## Key Features

1. **Retriever-per-request factory (P33 fix)** — Factory function builds a fresh `VectorStoreRetriever` per invocation, reading `tenant_id` from `RunnableConfig.configurable`; never caches the retriever at module scope; supports Pinecone namespace, PGVector `session.execute("SET LOCAL app.tenant_id = :tid")`, and Chroma collection-per-tenant with a single interface
2. **Role-scoped tool allowlist per-request** — Agent is constructed per-request with only the tools the current user's role permits; forbidden tools are not passed to `create_agent()` at all, so the model cannot call them even if it tries; includes a denylist for dangerous argument patterns (e.g. SQL with `DROP`, shell with `rm -rf`)
3. **Structured audit log on every invocation** — JSON log with `user_id`, `tenant_id`, `chain_name`, `tools_called`, `input_tokens`, `output_tokens`, `cost_usd`, `outcome` (success / error / tool_denied), `latency_ms`, `trace_id`; emitted in both the success path and the exception path via a `try / finally`; shipped to SIEM or BigQuery for query recipes like "show me every tool call by user X in the last 24h"
4. **Two-tenant regression test fixture** — `pytest` fixture seeds Tenant A and Tenant B with distinct documents; golden query asserts Tenant A's retriever never returns Tenant B's documents and vice versa; catches P33 on import-time binding regression

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
