# clade-architecture-variants — One-Pager

Five proven architecture patterns for building Claude-powered applications.

## The Problem

Developers starting a Claude integration face a blank canvas. Should they build a simple chatbot, a RAG system with vector search, an agentic tool-use loop, a batch content pipeline, or an evaluation harness? Each pattern has fundamentally different latency, cost, and complexity tradeoffs, and choosing wrong means rearchitecting later.

## The Solution

This skill presents five complete architecture patterns — Chatbot, RAG, Agent, Content Pipeline, and Evaluation — each with production-ready TypeScript code and a comparison table covering latency, cost, and complexity. You pick the pattern that fits your requirements and adapt the code.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers and architects designing new Claude-powered applications |
| **What** | Choose between five architecture patterns (Chatbot, RAG, Agent, Pipeline, Evaluation) with complete implementations |
| **When** | At project start, when deciding how to structure your Claude integration |

## Key Features

1. **Chatbot pattern** — Stateless API wrapper with streaming, ideal for customer support and Q&A interfaces
2. **RAG pattern** — Retrieval-augmented generation with vector search (Voyage/OpenAI/Cohere embeddings), grounded answers with source context
3. **Agent pattern** — Tool use loop where Claude decides which functions to call, executes them, and iterates until the task is complete
4. **Content Pipeline** — Batch API for processing thousands of documents at 50% cost savings with a 24-hour SLA
5. **Evaluation pattern** — Use Claude (Opus) as a judge to score AI outputs or human content on accuracy, relevance, and completeness

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
