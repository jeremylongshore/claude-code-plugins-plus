---
name: langchain-reference-architecture
description: |
  Implement LangChain reference architecture patterns for production.
  Use when designing LangChain systems, implementing scalable patterns,
  or architecting enterprise LLM applications.
  Trigger with phrases like "langchain architecture", "langchain design",
  "langchain scalable", "langchain enterprise", "langchain patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# LangChain Reference Architecture

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Production-ready architectural patterns for building scalable, maintainable LangChain applications including layered architecture, provider abstraction, chain registry, RAG, and multi-agent orchestration.

## Prerequisites
- Understanding of LangChain fundamentals
- Experience with software architecture
- Knowledge of cloud infrastructure

## Instructions

### Step 1: Adopt Layered Architecture
Organize code into API, core (business logic), infrastructure, and config layers. Each layer has clear responsibilities and dependencies flow inward.

### Step 2: Implement Provider Abstraction
Use an `LLMFactory` with abstract `LLMProvider` classes to decouple from specific LLM vendors (OpenAI, Anthropic, etc.).

### Step 3: Set Up Chain Registry
Create a `ChainRegistry` to manage named chains at runtime, enabling dynamic chain selection via API endpoints.

### Step 4: Build RAG Architecture
Combine a retriever (vector store) with an LLM chain using `RunnablePassthrough` for context injection.

### Step 5: Orchestrate Multi-Agent Systems
Use an `AgentOrchestrator` with LLM-based routing to dispatch requests to specialized agents.

### Step 6: Use Configuration-Driven Design
Leverage `pydantic_settings.BaseSettings` for validated, environment-driven configuration.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete code patterns and architecture diagrams.

## Output
- Layered architecture with clear separation
- Provider abstraction for LLM flexibility
- Chain registry for runtime management
- Multi-agent orchestration pattern

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Wrong layering | Separate concerns strictly by layer |
| Provider not found | Missing registration | Check LLMFactory provider map |
| Chain not found | Unregistered chain | Register chains at startup |

## Examples
```python
# Quick provider abstraction usage
from infrastructure.llm.provider import LLMFactory
llm = LLMFactory.create("openai", model="gpt-4o-mini")

# Quick chain registry usage
chain = ChainRegistry.get("rag")
result = await chain.ainvoke({"question": "What is LangChain?"})
```

## Resources
- [LangChain Architecture Guide](https://python.langchain.com/docs/concepts/architecture/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)

## Next Steps
Use `langchain-multi-env-setup` for environment management.
